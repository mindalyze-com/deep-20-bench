"""Composition root for direct Oracle question and regression suites."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer
from deep20_oracle.artifacts import RunArtifactPolicy
from deep20_oracle.audit import RunAuditWriter
from deep20_oracle.catalog import load_subject_catalog
from deep20_oracle.config import load_oracle_config
from deep20_oracle.console import configure_console_logging
from deep20_oracle.credentials import load_openrouter_api_key
from deep20_oracle.openrouter_provider import OpenRouterOracleProviderSet
from deep20_oracle.service import Oracle
from deep20_oracle.util import canonical_json, repository_root, sha256_text, timestamp

from .catalog import load_benchmark_catalog
from .models import BenchmarkId, SubjectId
from .oracle_replay import ReplayInputError, ReplayStatus
from .oracle_replay_cli import ConsoleReplayObserver
from .oracle_suite import (
    QuestionCase,
    QuestionSuite,
    SuiteReport,
    build_suite_plan,
    run_oracle_suite,
    summarize_suite,
)
from .oracle_suite_io import SuiteStore, load_question_suite, write_question_suite
from .power import prevent_idle_system_sleep

logger = logging.getLogger("deep20.oracle_suite")


def test_oracle(
    run_id: Annotated[str, typer.Option(help="Fresh private test run ID.")],
    suite: Annotated[Path | None, typer.Option(help="Question-suite YAML or JSON file.")] = None,
    target_id: Annotated[str | None, typer.Option(help="Subject for a direct question.")] = None,
    question: Annotated[str | None, typer.Option(help="Direct question; requires --target-id.")] = None,
    cases: Annotated[list[str] | None, typer.Option(help="Suite case ID; repeat to select several.")] = None,
    repeat: Annotated[int, typer.Option(min=1, max=100, help="Fresh repetitions per selected case.")] = 1,
    benchmark_id: Annotated[str, typer.Option(help="Current benchmark Oracle configuration.")] = "B-0003",
    oracle_config: Annotated[Path | None, typer.Option(help="Override Oracle configuration YAML.")] = None,
    subjects_path: Annotated[Path | None, typer.Option(help="Subject catalog for target IDs.")] = None,
    save_suite: Annotated[Path | None, typer.Option(help="Export resolved selected cases; never overwrite.")] = None,
    dry_run: Annotated[bool, typer.Option(help="Validate without credentials or paid calls.")] = False,
    live: Annotated[bool, typer.Option(help="Explicitly opt in to paid Oracle calls; default is preview.")] = False,
    resume: Annotated[bool, typer.Option(help="Resume an identical saved plan.")] = False,
    verbose: Annotated[bool, typer.Option(help="Also write review.md and private raw role audits.")] = False,
    max_consecutive_failures: Annotated[int, typer.Option(min=1)] = 1,
) -> None:
    """Test direct questions through Oracle/Reviewer/Judge, with no Guesser."""
    configure_console_logging()
    root = repository_root()
    try:
        if live and dry_run:
            raise ReplayInputError("choose --live or --dry-run")
        if suite is not None:
            if target_id is not None or question is not None:
                raise ReplayInputError("choose a suite file or a direct target/question pair")
            selected = load_question_suite(suite)
        else:
            if target_id is None or question is None:
                raise ReplayInputError("provide --suite or both --target-id and --question")
            selected = QuestionSuite(name="Direct Oracle question", cases=(
                QuestionCase(id="question", target_id=SubjectId(target_id), question=question),
            ))
        config = (load_oracle_config(oracle_config) if oracle_config is not None
                  else load_benchmark_catalog(root / "config/benchmarks.yaml")
                  .entry(BenchmarkId(benchmark_id)).oracle_configuration)
        catalog = (load_subject_catalog(subjects_path or root / "config/subjects.yaml")
                   if any(case.target_id is not None for case in selected.cases) else None)
        plan = build_suite_plan(selected, config, run_id=run_id, repetitions=repeat,
                                case_ids=tuple(cases or ()), catalog=catalog)
        if save_suite is not None:
            destination = save_suite.resolve()
            if not destination.is_relative_to((root / "private/reviews").resolve()):
                raise ReplayInputError("save suites under private/reviews")
            write_question_suite(destination, plan.suite)
        logger.info("oracle_suite.plan cases=%d repetitions=%d questions=%d contract=%s",
                    len(plan.suite.cases), repeat, plan.total, plan.oracle_contract_hash)
        if not live:
            return
        policy = RunArtifactPolicy(verbose=verbose)
        directory = root / "private/reviews/oracle-suites" / plan.run_id
        store = SuiteStore(directory, policy)
        with store.locked():
            report = store.load()
            if report is not None:
                if not resume or report.plan_hash != plan.content_hash():
                    raise ReplayInputError("existing run requires --resume with an identical plan")
            else:
                if resume:
                    raise ReplayInputError("no saved suite checkpoint exists")
                now = timestamp()
                report = SuiteReport(plan=plan, plan_hash=plan.content_hash(), started_at=now, updated_at=now)
            if report.status is not ReplayStatus.COMPLETED:
                key = load_openrouter_api_key(root)
                writer = RunAuditWriter(directory / "audit", config=config, repository=root,
                    subject_catalog_hash=sha256_text(canonical_json([
                        case.subject.model_dump(mode="json") for case in plan.suite.cases if case.subject
                    ])), artifact_policy=policy)
                with prevent_idle_system_sleep(), OpenRouterOracleProviderSet(key, config) as providers:
                    service = Oracle(providers.oracle, providers.reviewer, providers.judge, writer, config)
                    report = run_oracle_suite(report, service, store, ConsoleReplayObserver(),
                                             max_consecutive_failures=max_consecutive_failures)
            else:
                store.save(report)
            summary = summarize_suite(report)
            logger.info("oracle_suite.result status=%s succeeded=%d failed=%d mismatched=%d "
                        "unstable_cases=%d known_cost_usd=%s result=%s", report.status,
                        summary.succeeded, summary.failed, summary.mismatched, summary.unstable_cases,
                        summary.known_cost_usd, directory / "result.yml")
            if report.status is not ReplayStatus.COMPLETED or summary.failed or summary.mismatched:
                raise typer.Exit(1)
    except typer.Exit:
        raise
    except ReplayInputError as error:
        logger.error("oracle_suite.failed code=suite_invalid_context message=%s", str(error))
        raise typer.Exit(2) from error
    except Exception as error:
        logger.error("oracle_suite.failed code=suite_setup_or_execution_failed type=%s", type(error).__name__)
        raise typer.Exit(2) from error
