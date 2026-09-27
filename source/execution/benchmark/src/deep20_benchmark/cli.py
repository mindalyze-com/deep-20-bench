from __future__ import annotations

import json
import logging
from contextlib import ExitStack, nullcontext
from decimal import Decimal
from pathlib import Path
from typing import Annotated

import typer
from deep20_backends.models import Role
from deep20_game.config import BenchmarkMode
from deep20_oracle.catalog import load_subject_catalog
from deep20_oracle.config import PromptProfile
from deep20_oracle.credentials import CredentialLoadError, load_openrouter_api_key
from deep20_oracle.diagnostics import diagnose_exception
from deep20_oracle.util import repository_root

from .artifacts import ArtifactStore, load_benchmark_manifest_file
from .backend_resolution import resolved_definition, resolved_model
from .canary import StartupCanaryResult, run_guesser_canary, run_startup_canaries
from .catalog import load_benchmark_catalog, load_model_catalog
from .comparison import require_comparable
from .edition_profiles import registered_edition
from .edition_runtime import draft_runs_root, select_runtime
from .history_cache import LazyOracleHistoryCache
from .launch import plan_summary, prepare_request, request_definition, validate_resume
from .logging import configure_benchmark_logging
from .models import (
    BenchmarkExecutionId,
    BenchmarkId,
    BenchmarkModelId,
    ExecutionStatus,
    InfrastructureCircuitBreaker,
    SubjectId,
    TrialRepairPolicy,
)
from .oracle_replay_cli import replay_oracle
from .oracle_suite_cli import test_oracle
from .parallel_credentials import load_parallel_api_key
from .power import prevent_idle_system_sleep
from .preflight import (
    OpenRouterRouteMetadata,
    validate_catalog_routes,
)
from .runner import BenchmarkRunner
from .runtime import LiveEpisodeExecutor
from .runtime_services import RuntimeServices
from .work_cli import work_app

benchmark_app = typer.Typer(help="Run and observe complete Deep20Bench suites.")
benchmark_app.add_typer(work_app, name="work")
benchmark_app.command("replay-oracle")(replay_oracle)
benchmark_app.command("test-oracle")(test_oracle)
logger = logging.getLogger("deep20.benchmark")


@benchmark_app.command("compare")
def compare_benchmarks(left: Path, right: Path) -> None:
    """Check two manifest files for the same recorded comparison contract, offline."""
    configure_benchmark_logging("INFO")
    try:
        first = load_benchmark_manifest_file(left)
        second = load_benchmark_manifest_file(right)
        require_comparable(first, second)
        logger.info("benchmark.comparison status=compatible left=%s right=%s",
                    first.request.execution_id, second.request.execution_id)
    except (OSError, ValueError, RuntimeError) as error:
        logger.error("benchmark.comparison code=incompatible_contract detail=%s", error)
        raise typer.Exit(1) from None


@benchmark_app.command("preview")
def preview_benchmark(
    benchmark_id: str,
    model_id: Annotated[str, typer.Option("--model")],
    edition_id: Annotated[str, typer.Option("--edition")],
    runtime_config_path: Annotated[Path | None, typer.Option("--runtime-config")] = None,
    models_path: Annotated[Path | None, typer.Option("--models-path")] = None,
    benchmarks_path: Annotated[Path | None, typer.Option("--benchmarks-path")] = None,
    output: Annotated[Path | None, typer.Option("--output")] = None,
) -> None:
    """Resolve and export a draft without loading credentials or calling providers."""
    configure_benchmark_logging("INFO")
    root = repository_root()
    try:
        models = load_model_catalog(models_path or root / "config" / "models.yaml")
        benchmarks = load_benchmark_catalog(benchmarks_path or root / "config" / "benchmarks.yaml")
        model = models.model(BenchmarkModelId(model_id))
        benchmark = benchmarks.entry(BenchmarkId(benchmark_id))
        runtime = select_runtime(root, edition_id=edition_id, config_path=runtime_config_path,
                                 model=model, benchmark=benchmark)
        if runtime is None:
            raise ValueError("runtime preview requires edition 1.2")
        subjects = load_subject_catalog(root / "config" / "subjects.yaml")
        definition = benchmarks.benchmark(
            benchmark.benchmark_id, benchmark_mode=BenchmarkMode.EXPERIMENTAL,
            subject_ids=tuple(SubjectId(s.target_id) for s in subjects.active_subjects()),
        )
        definition = resolved_definition(definition, runtime)
        model = resolved_model(model, runtime)
        destination = output or (root / "private" / "editions" / edition_id / "previews" / f"{model_id}.json")
        destination.parent.mkdir(parents=True, exist_ok=True)
        ArtifactStore(root)._atomic_write(destination, json.dumps({
            "runtime": runtime.model_dump(mode="json"),
            "runtime_fingerprint": runtime.fingerprint,
            "synthetic": runtime.roles.synthetic,
            "model": model.model_dump(mode="json"),
            "definition": definition.model_dump(mode="json"),
        }, ensure_ascii=False, indent=2) + "\n")
        logger.info("benchmark.preview edition=%s synthetic=%s output=%s",
                    edition_id, runtime.roles.synthetic, destination)
    except (OSError, ValueError, TypeError):
        typer.echo('{"error":{"code":"runtime_preview_failed","message":"Invalid draft configuration."}}', err=True)
        raise typer.Exit(1) from None


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
    benchmark_id: str | None,
    run_id: str,
    model_id: str,
    benchmark_mode: BenchmarkMode | None,
    target_ids: list[str] | None,
    iterations: int | None,
    base_seed: int | None,
    log_level: str,
    models_path: Path | None,
    benchmarks_path: Path | None,
    subjects_path: Path | None,
    canary: bool,
    max_consecutive_infrastructure_failures: int,
    repair: TrialRepairPolicy | None,
    oracle_cache: bool = True,
    oracle_history_before: str | None = None,
    edition_id: str | None = None,
    runtime_config_path: Path | None = None,
    live: bool = False,
    budget_usd: Decimal | None = None,
    variant_name: str | None = None,
    dry_run: bool = False,
    expected_comparison: str | None = None,
) -> None:
    configure_benchmark_logging(log_level)
    with (nullcontext() if dry_run else prevent_idle_system_sleep()), ExitStack() as resources:
        root = repository_root()
        try:
            models = load_model_catalog(models_path or root / "config" / "models.yaml")
            benchmarks = load_benchmark_catalog(benchmarks_path or root / "config" / "benchmarks.yaml")
            subjects = load_subject_catalog(subjects_path or root / "config" / "subjects.yaml")
            selected = registered_edition(root, edition_id)
            store = ArtifactStore(root, runs_root=(
                root / "private" / "editions" / selected.edition_id / "runs"
            ) if selected.runtime_overrides else None)
            existing_manifest = store.load_manifest(BenchmarkModelId(model_id), BenchmarkExecutionId(run_id))
            request = prepare_request(
                root, models=models, benchmarks=benchmarks, subjects=subjects,
                model_id=BenchmarkModelId(model_id), execution_id=BenchmarkExecutionId(run_id),
                edition_id=edition_id, benchmark_id=benchmark_id, mode=benchmark_mode,
                iterations=iterations, target_ids=tuple(target_ids) if target_ids is not None else None,
                base_seed=base_seed, variant_name=variant_name,
                runtime_config_path=runtime_config_path, existing=existing_manifest,
            )
            runtime = request.runtime
            benchmark_mode = request.benchmark_mode
            benchmark = benchmarks.entry(request.benchmark_id)
            definition = request_definition(request, benchmarks, subjects)
            if existing_manifest is not None:
                validate_resume(existing_manifest, request, benchmarks, models, subjects)
            if expected_comparison is not None and (request.edition is None or request.edition.comparison_hash != expected_comparison):
                raise ValueError("edition_contract_mismatch: plan changed after batch preflight")
            logger.info("benchmark.plan %s", plan_summary(request, definition))
            if dry_run:
                return
            if runtime is None and (live or budget_usd is not None):
                raise ValueError("--live and --budget-usd controls require explicit --edition 1.2")
            if runtime is not None:
                paid = any(runtime.roles.binding(role).implementation == "openrouter" for role in Role)
                paid = paid or runtime.roles.oracle.implementation in {"ollama", "interactive"}
                if paid and (not live or budget_usd is None or not budget_usd.is_finite() or budget_usd <= 0):
                    raise ValueError("paid draft execution requires --live and a positive --budget-usd")
            revised_prompts = benchmark.game_policy.prompt_profile is not PromptProfile.STANDARD
            existing_state = store.load_state(
                request.model_id,
                request.execution_id,
            )
            execution_is_completed = (
                existing_state is not None and existing_state.status is ExecutionStatus.COMPLETED
            )
            if runtime is not None and not runtime.roles.factual_cache_eligible:
                oracle_cache = False
            if not oracle_cache and oracle_history_before is not None:
                raise ValueError("Oracle history cutoff requires --oracle-cache")
            history_cache = LazyOracleHistoryCache(
                root, before=oracle_history_before,
                judge_ignored_providers=repair.judge_ignored_providers if repair else (),
                **({"history_roots": (draft_runs_root(root, runtime),)}
                   if runtime is not None else {}),
            ) if oracle_cache else None
            api_key = (load_openrouter_api_key(root) if runtime is None or any(
                runtime.roles.binding(role).implementation == "openrouter" for role in Role
            ) else None)
            if (
                runtime is None and (benchmark_mode is BenchmarkMode.OFFICIAL or revised_prompts)
                and canary and not execution_is_completed
            ):
                assert api_key is not None
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
            services = RuntimeServices(
                store.run_root(request.model_id, request.execution_id), runtime, resources,
                api_key=api_key, budget_usd=budget_usd,
                parallel_api_key=(load_parallel_api_key(root) if runtime is not None and
                                  runtime.roles.oracle.implementation in {"ollama", "interactive"} else None),
                judge_ignored_providers=repair.judge_ignored_providers if repair else (),
            ) if runtime is not None else None
            if services is not None and runtime is not None and not execution_is_completed:
                services.preflight(
                    resolved_definition(benchmarks.benchmark(request.benchmark_id,
                        benchmark_mode=benchmark_mode, subject_ids=request.target_ids or tuple(
                            SubjectId(subject.target_id) for subject in subjects.active_subjects()),
                        iterations_override=request.iterations_override), runtime),
                    resolved_model(models.model(request.model_id), runtime), canary=canary,
                )
            runner = BenchmarkRunner(
                store=store,
                model_catalog=models,
                benchmark_catalog=benchmarks,
                subject_catalog=subjects,
                oracle_cache=history_cache,
                executor=LiveEpisodeExecutor(
                    oracle_cache=history_cache,
                    api_key=api_key,
                    factory_provider=services.factory if services is not None else None,
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
    run_id: Annotated[str, typer.Option("--run-id", help="Immutable execution ID.")],
    model_id: Annotated[
        str,
        typer.Option(
            "--model",
            help="Registered Guesser ID for this run.",
        ),
    ],
    benchmark_mode: Annotated[
        BenchmarkMode | None,
        typer.Option(
            "--benchmark-mode",
            help="Normally derived from the edition; variants use experimental mode.",
        ),
    ] = None,
    benchmark_id: Annotated[str | None, typer.Argument(help="Optional consistency check against the edition.")] = None,
    target_ids: Annotated[
        list[str] | None,
        typer.Option(
            "--targets",
            help=(
                "Active subject ID; repeat as needed. Omit for the edition subjects in a new "
                "run, or the recorded subjects when resuming."
            ),
        ),
    ] = None,
    iterations: Annotated[
        int | None,
        typer.Option(
            "--iterations",
            "--repetitions",
            help="Trials per subject; omit to use the selected edition profile.",
        ),
    ] = None,
    base_seed: Annotated[
        int | None,
        typer.Option(
            "--seed",
            min=0,
            max=(2**31) - 1,
            help="Base seed for subject-independent per-trial Guesser seed derivation.",
        ),
    ] = None,
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
    edition_id: Annotated[str | None, typer.Option("--edition", help="Explicit edition selection.")] = None,
    expected_comparison: Annotated[str | None, typer.Option("--expected-comparison", help="Require the contract validated by the batch plan.")] = None,
    variant_name: Annotated[str | None, typer.Option("--variant", help="Name a deliberate experiment outside the released contract.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Validate and show the full plan without credentials, writes, or paid calls.")] = False,
    runtime_config_path: Annotated[
        Path | None, typer.Option("--runtime-config", help="Draft role bindings.")
    ] = None,
    live: Annotated[bool, typer.Option("--live", help="Allow paid draft calls within the budget.")] = False,
    budget_usd: Annotated[
        float | None, typer.Option("--budget-usd", min=0.000001, help="Total paid draft spending limit.")
    ] = None,
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
        edition_id=edition_id,
        variant_name=variant_name,
        dry_run=dry_run,
        expected_comparison=expected_comparison,
        runtime_config_path=runtime_config_path,
        live=live,
        budget_usd=Decimal(str(budget_usd)) if budget_usd is not None else None,
    )


@benchmark_app.command("repair")
def repair_benchmark(
    run_id: Annotated[str, typer.Option("--run-id", help="Immutable execution ID.")],
    model_id: Annotated[
        str,
        typer.Option(
            "--model",
            help="Registered Guesser ID for this run.",
        ),
    ],
    benchmark_mode: Annotated[
        BenchmarkMode | None,
        typer.Option(
            "--benchmark-mode",
            help="Normally derived from the edition; variants use experimental mode.",
        ),
    ] = None,
    benchmark_id: Annotated[str | None, typer.Argument(help="Optional consistency check against the edition.")] = None,
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
            help="Trials per subject; omit to use the selected edition profile.",
        ),
    ] = None,
    base_seed: Annotated[
        int | None,
        typer.Option(
            "--seed",
            min=0,
            max=(2**31) - 1,
            help="Base seed for subject-independent per-trial Guesser seed derivation.",
        ),
    ] = None,
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
    edition_id: Annotated[str | None, typer.Option("--edition", help="Explicit edition selection.")] = None,
    expected_comparison: Annotated[str | None, typer.Option("--expected-comparison", help="Require the contract validated by the batch plan.")] = None,
    variant_name: Annotated[str | None, typer.Option("--variant", help="Name a deliberate experiment outside the released contract.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Validate and show the full plan without credentials, writes, or paid calls.")] = False,
    runtime_config_path: Annotated[
        Path | None, typer.Option("--runtime-config", help="Draft role bindings.")
    ] = None,
    live: Annotated[bool, typer.Option("--live", help="Allow paid draft calls within the budget.")] = False,
    budget_usd: Annotated[
        float | None, typer.Option("--budget-usd", min=0.000001, help="Total paid draft spending limit.")
    ] = None,
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
        edition_id=edition_id,
        variant_name=variant_name,
        dry_run=dry_run,
        expected_comparison=expected_comparison,
        runtime_config_path=runtime_config_path,
        live=live,
        budget_usd=Decimal(str(budget_usd)) if budget_usd is not None else None,
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
