"""Composition root for private Oracle replay reviews."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Annotated

import typer
from deep20_oracle.artifacts import RunArtifactPolicy
from deep20_oracle.audit import RunAuditWriter
from deep20_oracle.config import load_oracle_config
from deep20_oracle.console import configure_console_logging
from deep20_oracle.credentials import load_openrouter_api_key
from deep20_oracle.openrouter_provider import OpenRouterOracleProviderSet
from deep20_oracle.service import Oracle
from deep20_oracle.util import canonical_json, repository_root, sha256_text, timestamp

from .artifacts import load_benchmark_result_file
from .catalog import load_benchmark_catalog
from .models import SubjectId, TrialId
from .oracle_replay import (
    ReplayInputError,
    ReplayOutcome,
    ReplayReport,
    ReplaySelection,
    ReplayStatus,
    build_replay_plan,
    run_replay,
    summarize_replay,
)
from .oracle_replay_io import ReplayStore
from .oracle_suite import QuestionCase, QuestionSuite
from .oracle_suite_io import write_question_suite
from .power import prevent_idle_system_sleep

logger = logging.getLogger("deep20.oracle_replay")

class ConsoleReplayObserver:
    def completed(self, outcome: ReplayOutcome, total: int) -> None:
        if outcome.status == "success":
            logger.info(
                "oracle_replay.question position=%d/%d answer=%s cost_usd=%s latency_ms=%d",
                outcome.case_number, total, outcome.adjudication.final_answer,
                outcome.metrics.cost_usd, outcome.metrics.latency_ms,
            )
        else:
            logger.error(
                "oracle_replay.failed position=%d/%d code=%s",
                outcome.case_number, total, outcome.code,
            )


def replay_oracle(
    source: Annotated[Path, typer.Argument(help="Completed benchmark directory or result.yml.")],
    run_id: Annotated[str, typer.Option(help="New private replay ID; use --resume to continue it.")],
    oracle_config: Annotated[
        Path | None, typer.Option(help="Override current benchmark Oracle configuration with YAML.")
    ] = None,
    benchmarks_path: Annotated[
        Path | None, typer.Option(help="Current benchmark catalog; default config/benchmarks.yaml.")
    ] = None,
    targets: Annotated[list[str] | None, typer.Option(help="Target ID; repeat to select several.")] = None,
    trials: Annotated[list[int] | None, typer.Option(help="Trial number; repeat to select several.")] = None,
    turns: Annotated[list[int] | None, typer.Option(help="Original turn number; repeatable.")] = None,
    limit: Annotated[int | None, typer.Option(min=1, help="Replay only the first N selected ASKs.")] = None,
    dry_run: Annotated[bool, typer.Option(help="Validate and preview without credentials or calls.")] = False,
    live: Annotated[bool, typer.Option(help="Explicitly opt in to paid replay; default is preview.")] = False,
    export_suite: Annotated[
        Path | None, typer.Option(help="Export selected questions under private/reviews; make no calls.")
    ] = None,
    resume: Annotated[bool, typer.Option(help="Continue the identical saved replay plan.")] = False,
    verbose: Annotated[
        bool, typer.Option(help="Also write review.md and credential-free raw Oracle audits.")
    ] = False,
    max_consecutive_failures: Annotated[
        int, typer.Option(min=1, help="Stop after this many consecutive infrastructure failures.")
    ] = 5,
) -> None:
    """Replay recorded ASK questions through current Oracle/Reviewer/Judge, with no Guesser."""
    configure_console_logging()
    root = repository_root()
    try:
        if live and (dry_run or export_suite is not None):
            raise ReplayInputError("choose --live or preview/export")
        source_file = source / "result.yml" if source.is_dir() else source
        historical = load_benchmark_result_file(source_file)
        if not historical.outcome.complete:
            raise ReplayInputError("source must be a completed benchmark result")
        if oracle_config is not None and benchmarks_path is not None:
            raise ReplayInputError("choose either --oracle-config or --benchmarks-path")
        config = (
            load_oracle_config(oracle_config) if oracle_config is not None
            else load_benchmark_catalog(benchmarks_path or root / "config/benchmarks.yaml")
            .entry(historical.run.definition.benchmark_id).oracle_configuration
        )
        selection = ReplaySelection(
            targets=tuple(SubjectId(value) for value in targets or ()),
            trials=tuple(TrialId(f"trial-{number:03d}") for number in trials or ()),
            turns=tuple(turns or ()), limit=limit,
        )
        plan = build_replay_plan(historical, config, run_id=run_id, selection=selection)
        if export_suite is not None:
            destination = export_suite.resolve()
            if not destination.is_relative_to((root / "private/reviews").resolve()):
                raise ReplayInputError("export suites under private/reviews")
            suite = QuestionSuite(name=run_id, cases=tuple(
                QuestionCase(
                    id=f"{case.identity.target_id}-{case.identity.trial_id}-turn-{case.turn_number:03d}",
                    subject=case.subject, question=case.question,
                    notes=f"Source: {plan.source_execution_id}; original ASK occurrence. "
                          "Historical answers are not ground truth.",
                ) for case in plan.cases
            ))
            write_question_suite(destination, suite)
            logger.info("oracle_replay.export cases=%d suite=%s", len(suite.cases), destination)
            return
        logger.info(
            "oracle_replay.plan source=%s selected=%d available=%d missing_transcripts=%d "
            "profile=%s policy=%s contract=%s",
            plan.source_execution_id, len(plan.cases), plan.source_ask_count,
            plan.source_trials_without_transcript, config.prompt_profile,
            config.adjudication_policy, plan.oracle_contract_hash,
        )
        if not live:
            return
        policy = RunArtifactPolicy(verbose=verbose)
        directory = root / "private/reviews/oracle-replay" / plan.run_id
        store = ReplayStore(directory, policy)
        with store.locked():
            saved = store.load()
            if saved is not None:
                if not resume:
                    raise ReplayInputError("replay already exists; use --resume or a new run ID")
                if saved.plan_hash != plan.content_hash():
                    raise ReplayInputError("source, selection, configuration or prompts changed; use a new ID")
                report = saved
            else:
                if resume:
                    raise ReplayInputError("no replay checkpoint exists")
                now = timestamp()
                report = ReplayReport(
                    plan=plan, plan_hash=plan.content_hash(), started_at=now, updated_at=now,
                )
            if report.status is not ReplayStatus.COMPLETED:
                api_key = load_openrouter_api_key(root)
                # All path choices and artifact policy stay in this composition root.
                writer = RunAuditWriter(
                    directory / "audit", config=config, repository=root,
                    subject_catalog_hash=sha256_text(canonical_json([
                        case.subject.model_dump(mode="json") for case in plan.cases
                    ])), artifact_policy=policy,
                )
                with prevent_idle_system_sleep(), OpenRouterOracleProviderSet(api_key, config) as providers:
                    service = Oracle(
                        providers.oracle, providers.reviewer, providers.judge, writer, config,
                    )
                    report = run_replay(
                        report, service, store, ConsoleReplayObserver(),
                        max_consecutive_failures=max_consecutive_failures,
                    )
            else:
                store.save(report)
            summary = summarize_replay(report)
            logger.info(
                "oracle_replay.result status=%s completed=%d failed=%d changed=%d "
                "known_cost_usd=%s result=%s",
                report.status, summary.completed, summary.failed, summary.changed,
                summary.known_cost_usd, directory / "result.yml",
            )
            if report.status is not ReplayStatus.COMPLETED or summary.failed:
                raise typer.Exit(1)
    except typer.Exit:
        raise
    except ReplayInputError as error:
        logger.error("oracle_replay.failed code=replay_invalid_context message=%s", json.dumps(str(error)))
        raise typer.Exit(2) from error
    except Exception as error:
        # Never render arbitrary source/provider/validation contents on the console.
        logger.error("oracle_replay.failed code=replay_setup_or_execution_failed type=%s",
                     type(error).__name__)
        raise typer.Exit(2) from error
