from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Annotated

import typer
from deep20_game.config import BenchmarkMode
from deep20_oracle.catalog import load_subject_catalog
from deep20_oracle.config import PromptProfile
from deep20_oracle.credentials import CredentialLoadError, load_openrouter_api_key
from deep20_oracle.diagnostics import diagnose_exception
from deep20_oracle.util import repository_root

from .artifacts import ArtifactStore
from .canary import StartupCanaryResult, run_guesser_canary, run_startup_canaries
from .catalog import load_benchmark_catalog, load_model_catalog
from .history_cache import LazyOracleHistoryCache
from .logging import configure_benchmark_logging
from .models import (
    BenchmarkExecutionId,
    BenchmarkId,
    BenchmarkModelId,
    BenchmarkRequest,
    ExecutionStatus,
    InfrastructureCircuitBreaker,
    SubjectId,
    TrialRepairPolicy,
)
from .oracle_replay_cli import replay_oracle
from .oracle_suite_cli import test_oracle
from .power import prevent_idle_system_sleep
from .preflight import (
    OpenRouterRouteMetadata,
    validate_catalog_routes,
)
from .runner import BenchmarkRunner
from .runtime import LiveEpisodeExecutor

benchmark_app = typer.Typer(help="Run and observe complete Deep20Bench suites.")
benchmark_app.command("replay-oracle")(replay_oracle)
benchmark_app.command("test-oracle")(test_oracle)
logger = logging.getLogger("deep20.benchmark")


class BenchmarkInfrastructureFailuresRemain(RuntimeError):
    """Raised when the CLI finishes a schedule with infrastructure failures."""

    code = "benchmark_infrastructure_failures_remain"


def _log_startup_canaries(result: StartupCanaryResult) -> None:
    for role in result.roles:
        if not role.valid:
            continue
        logger.info(
            "benchmark.canary role=%s answer=%s searches=%d evidence=%d "
            "cache=%d/%d output_tokens=%d latency_ms=%d cost_usd=%s",
            role.role,
            json.dumps(role.answer),
            role.search_count,
            role.evidence_count,
            role.cached_input_tokens,
            role.cache_write_tokens,
            role.output_tokens,
            role.latency_ms,
            format(role.cost_usd or 0, ".5f"),
        )


def _execute_suite(
    *,
    benchmark_id: str,
    run_id: str,
    model_id: str,
    benchmark_mode: BenchmarkMode,
    target_ids: list[str] | None,
    iterations: int | None,
    base_seed: int,
    log_level: str,
    models_path: Path | None,
    benchmarks_path: Path | None,
    subjects_path: Path | None,
    canary: bool,
    max_consecutive_infrastructure_failures: int,
    repair: TrialRepairPolicy | None,
    oracle_cache: bool = True,
    oracle_history_before: str | None = None,
) -> None:
    configure_benchmark_logging(log_level)
    with prevent_idle_system_sleep():
        root = repository_root()
        try:
            request = BenchmarkRequest(
                benchmark_id=BenchmarkId(benchmark_id),
                execution_id=BenchmarkExecutionId(run_id),
                model_id=BenchmarkModelId(model_id),
                benchmark_mode=benchmark_mode,
                target_ids=tuple(SubjectId(target_id) for target_id in (target_ids or ())),
                iterations_override=iterations,
                base_seed=base_seed,
            )
            models = load_model_catalog(models_path or root / "config" / "models.yaml")
            benchmarks = load_benchmark_catalog(
                benchmarks_path or root / "config" / "benchmarks.yaml"
            )
            benchmark = benchmarks.entry(request.benchmark_id)
            revised_prompts = (
                benchmark.game_policy.prompt_profile is not PromptProfile.STANDARD
                or benchmark.oracle_configuration.prompt_profile is not PromptProfile.STANDARD
            )
            if revised_prompts and benchmark_mode is BenchmarkMode.OFFICIAL:
                raise ValueError("revised prompts require experimental benchmark mode")
            store = ArtifactStore(root)
            existing_state = store.load_state(
                request.model_id,
                request.execution_id,
            )
            execution_is_completed = (
                existing_state is not None and existing_state.status is ExecutionStatus.COMPLETED
            )
            if not oracle_cache and oracle_history_before is not None:
                raise ValueError("Oracle history cutoff requires --oracle-cache")
            history_cache = LazyOracleHistoryCache(
                root, before=oracle_history_before,
                judge_ignored_providers=repair.judge_ignored_providers if repair else (),
            ) if oracle_cache else None
            api_key = load_openrouter_api_key(root)
            if (
                (benchmark_mode is BenchmarkMode.OFFICIAL or revised_prompts)
                and canary and not execution_is_completed
            ):
                model = models.model(request.model_id)
                canary_result = run_startup_canaries(
                    model,
                    benchmark,
                    api_key=api_key,
                    judge_ignored_providers=(
                        repair.judge_ignored_providers if repair is not None else ()
                    ),
                )
                _log_startup_canaries(canary_result)
                if not canary_result.valid:
                    failures = "; ".join(
                        f"{role.role}: {role.error_code}"
                        for role in canary_result.roles
                        if not role.valid
                    )
                    raise ValueError(f"LLM startup canary failed: {failures}")
            subjects = load_subject_catalog(subjects_path or root / "config" / "subjects.yaml")
            runner = BenchmarkRunner(
                store=store,
                model_catalog=models,
                benchmark_catalog=benchmarks,
                subject_catalog=subjects,
                oracle_cache=history_cache,
                executor=LiveEpisodeExecutor(
                    oracle_cache=history_cache,
                    api_key=api_key,
                    judge_ignored_providers=(
                        repair.judge_ignored_providers if repair is not None else ()
                    ),
                ),
            )
            result = runner.run(
                request,
                repair=repair,
                circuit_breaker=InfrastructureCircuitBreaker(
                    max_consecutive_infrastructure_failures=(
                        max_consecutive_infrastructure_failures
                    ),
                ),
            )
            if result.outcome.has_infrastructure_failures:
                raise BenchmarkInfrastructureFailuresRemain(
                    "benchmark execution "
                    f"{request.execution_id} contains "
                    f"{result.summary.counts.infrastructure_failed} "
                    "infrastructure-failed terminal trial(s); repair the execution "
                    "after resolving the provider issue"
                )
        except (CredentialLoadError, OSError, RuntimeError, TypeError, ValueError) as error:
            diagnostics = diagnose_exception(error)
            typer.echo(
                json.dumps(
                    {
                        "error": {
                            "code": getattr(error, "code", "benchmark_failed"),
                            "message": diagnostics.causes[0].message,
                            "diagnostics": diagnostics.model_dump(mode="json"),
                        }
                    }
                ),
                err=True,
            )
            raise typer.Exit(1) from error


@benchmark_app.command("run")
def run_benchmark(
    benchmark_id: str,
    run_id: Annotated[str, typer.Option("--run-id", help="Immutable execution ID.")],
    model_id: Annotated[
        str,
        typer.Option(
            "--model",
            help="Registered Guesser ID for this run.",
        ),
    ],
    benchmark_mode: Annotated[
        BenchmarkMode,
        typer.Option(
            "--benchmark-mode",
            help="Required run classification: official or experimental.",
        ),
    ],
    target_ids: Annotated[
        list[str] | None,
        typer.Option(
            "--targets",
            help=(
                "Active subject ID; repeat as needed. Omit for all active subjects in a new "
                "run, or the recorded subjects when resuming."
            ),
        ),
    ] = None,
    iterations: Annotated[
        int | None,
        typer.Option(
            "--iterations",
            "--repetitions",
            help="Iterations for every selected subject; default is 3.",
        ),
    ] = None,
    base_seed: Annotated[
        int,
        typer.Option(
            "--seed",
            min=0,
            max=(2**31) - 1,
            help="Base seed for subject-independent per-trial Guesser seed derivation.",
        ),
    ] = 0,
    log_level: Annotated[
        str,
        typer.Option(help="Benchmark console level: DEBUG, INFO, WARNING, or ERROR."),
    ] = "INFO",
    models_path: Annotated[
        Path | None,
        typer.Option(help="Benchmark model catalog YAML."),
    ] = None,
    benchmarks_path: Annotated[
        Path | None,
        typer.Option(help="Benchmark suite catalog YAML."),
    ] = None,
    subjects_path: Annotated[
        Path | None,
        typer.Option(help="Subject catalog YAML."),
    ] = None,
    canary: Annotated[
        bool,
        typer.Option(
            "--canary/--no-canary",
            help="Probe all roles for official runs and experimental revised prompts.",
        ),
    ] = True,
    oracle_cache: Annotated[
        bool, typer.Option("--oracle-cache/--no-oracle-cache", help="Reuse compatible historical and same-game ASK answers; new executions only."),
    ] = True,
    oracle_history_before: Annotated[
        str | None, typer.Option(help="Freeze history at this ISO timestamp; otherwise discover completed games per subject."),
    ] = None,
    max_consecutive_infrastructure_failures: Annotated[
        int,
        typer.Option(
            "--max-consecutive-infrastructure-failures",
            min=1,
            max=100,
            help="Abort the run after this many consecutive infrastructure failures.",
        ),
    ] = 5,
) -> None:
    _execute_suite(
        benchmark_id=benchmark_id,
        run_id=run_id,
        model_id=model_id,
        benchmark_mode=benchmark_mode,
        target_ids=target_ids,
        iterations=iterations,
        base_seed=base_seed,
        log_level=log_level,
        models_path=models_path,
        benchmarks_path=benchmarks_path,
        subjects_path=subjects_path,
        canary=canary,
        max_consecutive_infrastructure_failures=max_consecutive_infrastructure_failures,
        oracle_cache=oracle_cache,
        oracle_history_before=oracle_history_before,
        repair=None,
    )


@benchmark_app.command("repair")
def repair_benchmark(
    benchmark_id: str,
    run_id: Annotated[str, typer.Option("--run-id", help="Immutable execution ID.")],
    model_id: Annotated[
        str,
        typer.Option(
            "--model",
            help="Registered Guesser ID for this run.",
        ),
    ],
    benchmark_mode: Annotated[
        BenchmarkMode,
        typer.Option(
            "--benchmark-mode",
            help="Required run classification: official or experimental.",
        ),
    ],
    target_ids: Annotated[
        list[str] | None,
        typer.Option(
            "--targets",
            help="Subject ID; repeat as needed. Omit to retain the recorded subjects.",
        ),
    ] = None,
    iterations: Annotated[
        int | None,
        typer.Option(
            "--iterations",
            "--repetitions",
            help="Iterations for every selected subject; default is 3.",
        ),
    ] = None,
    base_seed: Annotated[
        int,
        typer.Option(
            "--seed",
            min=0,
            max=(2**31) - 1,
            help="Base seed for subject-independent per-trial Guesser seed derivation.",
        ),
    ] = 0,
    log_level: Annotated[
        str,
        typer.Option(help="Benchmark console level: DEBUG, INFO, WARNING, or ERROR."),
    ] = "INFO",
    models_path: Annotated[
        Path | None,
        typer.Option(help="Benchmark model catalog YAML."),
    ] = None,
    benchmarks_path: Annotated[
        Path | None,
        typer.Option(help="Benchmark suite catalog YAML."),
    ] = None,
    subjects_path: Annotated[
        Path | None,
        typer.Option(help="Subject catalog YAML."),
    ] = None,
    canary: Annotated[
        bool,
        typer.Option(
            "--canary/--no-canary",
            help="Probe all roles for official repairs and experimental revised prompts.",
        ),
    ] = True,
    max_repair_attempts: Annotated[
        int,
        typer.Option(
            "--max-repair-attempts",
            min=1,
            max=10,
            help="Total start attempts allowed per trial, including the original run.",
        ),
    ] = 3,
    allow_oracle_contract_change: Annotated[
        bool, typer.Option(
            "--allow-oracle-contract-change",
            help="Record a changed Oracle contract for experimental repair; excludes publication.",
        ),
    ] = False,
    judge_ignored_providers: Annotated[
        list[str] | None,
        typer.Option(
            "--judge-ignore-provider",
            help=(
                "OpenRouter provider slug to exclude from Judge calls during repair; "
                "repeat as needed."
            ),
        ),
    ] = None,
    oracle_cache: Annotated[
        bool, typer.Option("--oracle-cache/--no-oracle-cache", help="Reuse compatible historical and same-game ASK answers; new executions only."),
    ] = True,
    oracle_history_before: Annotated[
        str | None, typer.Option(help="Freeze history at this ISO timestamp; otherwise discover completed games per subject."),
    ] = None,
    max_consecutive_infrastructure_failures: Annotated[
        int,
        typer.Option(
            "--max-consecutive-infrastructure-failures",
            min=1,
            max=100,
            help="Abort the repair after this many consecutive infrastructure failures.",
        ),
    ] = 5,
) -> None:
    """Repair infrastructure failures and continue an incomplete execution.

    Repair keeps the immutable execution context, trial identities, and variation
    tokens unchanged. It never re-runs scoring-eligible trials.
    """
    _execute_suite(
        benchmark_id=benchmark_id,
        run_id=run_id,
        model_id=model_id,
        benchmark_mode=benchmark_mode,
        target_ids=target_ids,
        iterations=iterations,
        base_seed=base_seed,
        log_level=log_level,
        models_path=models_path,
        benchmarks_path=benchmarks_path,
        subjects_path=subjects_path,
        canary=canary,
        max_consecutive_infrastructure_failures=max_consecutive_infrastructure_failures,
        oracle_cache=oracle_cache,
        oracle_history_before=oracle_history_before,
        repair=TrialRepairPolicy(
            max_attempts_per_trial=max_repair_attempts,
            allow_oracle_contract_change=allow_oracle_contract_change,
            judge_ignored_providers=tuple(judge_ignored_providers or ()),
        ),
    )


@benchmark_app.command("canary")
def canary_model(
    model_id: Annotated[
        str,
        typer.Option(
            "--model",
            help="Registered Guesser ID to probe.",
        ),
    ],
    models_path: Annotated[
        Path | None,
        typer.Option(help="Benchmark model catalog YAML."),
    ] = None,
) -> None:
    """Probe one model's exact route with a single real opening Guesser turn."""

    root = repository_root()
    try:
        models = load_model_catalog(models_path or root / "config" / "models.yaml")
        api_key = load_openrouter_api_key(root)
        result = run_guesser_canary(
            models.model(BenchmarkModelId(model_id)),
            api_key=api_key,
        )
    except (CredentialLoadError, OSError, RuntimeError, TypeError, ValueError) as error:
        diagnostics = diagnose_exception(error)
        typer.echo(
            json.dumps(
                {
                    "error": {
                        "code": "guesser_canary_failed",
                        "message": diagnostics.causes[0].message,
                    }
                }
            ),
            err=True,
        )
        raise typer.Exit(1) from error
    typer.echo(result.model_dump_json(indent=2))
    if not result.valid:
        raise typer.Exit(1)


@benchmark_app.command("preflight")
def preflight_routes(
    models_path: Annotated[
        Path | None,
        typer.Option(help="Benchmark model catalog YAML."),
    ] = None,
) -> None:
    """Validate exact public route capabilities without making paid model calls."""

    root = repository_root()
    try:
        models = load_model_catalog(models_path or root / "config" / "models.yaml")
        result = validate_catalog_routes(models, OpenRouterRouteMetadata())
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        diagnostics = diagnose_exception(error)
        typer.echo(
            json.dumps(
                {
                    "error": {
                        "code": "route_preflight_failed",
                        "message": diagnostics.causes[0].message,
                    }
                }
            ),
            err=True,
        )
        raise typer.Exit(1) from error
    typer.echo(result.model_dump_json(indent=2))
    if not result.valid:
        raise typer.Exit(1)
