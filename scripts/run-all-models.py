#!/usr/bin/env python3
"""Launch an explicit benchmark batch with persisted history settings."""

from __future__ import annotations

import argparse
import fcntl
import logging
import os
import shlex
import signal
import subprocess
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from types import FrameType
from typing import Literal, NoReturn

from deep20_benchmark.catalog import load_benchmark_catalog, load_model_catalog
from deep20_benchmark.edition_models import EditionExecution
from deep20_benchmark.launch import plan_summary, prepare_request, request_definition
from deep20_benchmark.models import BenchmarkExecutionId, BenchmarkId, BenchmarkModelId
from deep20_game.config import BenchmarkMode
from deep20_oracle.catalog import load_subject_catalog
from deep20_oracle.models import StrictModel
from pydantic import AwareDatetime, Field, ValidationError

LOGGER = logging.getLogger("deep20.batch")


class BatchOptions(StrictModel):
    all_models: bool = False
    edition_id: str | None = None
    variant_name: str | None = None
    base_seed: int | None = None
    target_ids: tuple[str, ...] | None = None
    benchmark_id: BenchmarkId | None = None
    mode: BenchmarkMode | None = None
    sequence: str = Field(pattern=r"^[0-9]{3}$")
    iterations: int | None = Field(default=None, ge=1, le=100)
    model_ids: tuple[BenchmarkModelId, ...] = ()
    excluded_model_ids: tuple[BenchmarkModelId, ...] = ()
    oracle_cache: bool = True
    oracle_history_before: AwareDatetime | None = None
    # None selects the default for new batches and preserves saved settings on resume.
    refresh_oracle_history: Literal[True] | None = None
    dry_run: bool = False


class BatchPlan(StrictModel):
    schema_version: Literal[1, 2] = 2
    edition: EditionExecution | None = None
    benchmark_id: BenchmarkId
    mode: BenchmarkMode
    sequence: str = Field(pattern=r"^[0-9]{3}$")
    run_date: str = Field(pattern=r"^[0-9]{8}$")
    iterations: int = Field(ge=1, le=100)
    model_ids: tuple[BenchmarkModelId, ...] = Field(min_length=1)
    oracle_history_before: AwareDatetime | None
    refresh_oracle_history: bool = Field(default=False, exclude_if=lambda v: not v)
    base_seed: int = Field(default=0, ge=0, le=(2**31) - 1)

    @property
    def batch_id(self) -> str:
        return f"BX-{self.run_date}-{self.benchmark_id}-{self.mode}-ALL-{self.sequence}"

    def execution_id(self, model_id: BenchmarkModelId) -> str:
        return (
            f"BX-{self.run_date}-{self.benchmark_id}-{self.mode}-"
            f"{str(model_id).replace('-', '')}-{self.sequence}"
        )

    def command(self, model_id: BenchmarkModelId) -> list[str]:
        command = [
            "uv", "run", "deep20", "benchmark", "run", str(self.benchmark_id),
            "--model", str(model_id), "--benchmark-mode", self.mode.value,
            "--run-id", self.execution_id(model_id), "--canary",
        ]
        if self.edition is None:
            raise ValueError("legacy batch has no edition contract; use a fresh sequence")
        command.extend(["--edition", self.edition.edition_id,
                        "--expected-comparison", self.edition.comparison_hash])
        overrides = self.edition.overrides
        if overrides.iterations is not None:
            command.extend(["--iterations", str(overrides.iterations)])
        if overrides.base_seed is not None:
            command.extend(["--seed", str(overrides.base_seed)])
        if overrides.variant_name is not None:
            command.extend(["--variant", overrides.variant_name])
        for target in overrides.target_ids or ():
            command.extend(["--targets", target])
        if self.refresh_oracle_history:
            command.append("--oracle-cache")
        elif self.oracle_history_before is None:
            command.append("--no-oracle-cache")
        else:
            command.extend(["--oracle-history-before", self.oracle_history_before.isoformat()])
        return command


@dataclass(frozen=True)
class RunningJob:
    model_id: BenchmarkModelId
    process: subprocess.Popen[bytes]
    log_path: Path


def parse_options(argv: Sequence[str]) -> BatchOptions:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark_id", nargs="?", metavar="B-NNNN")
    parser.add_argument("mode", nargs="?", choices=[mode.value for mode in BenchmarkMode],
                        metavar="<official|experimental>")
    parser.add_argument("sequence", nargs="?", default=None, help="Three-digit batch sequence.")
    parser.add_argument("iterations", nargs="?", type=int,
                        help="Trials per subject/model; defaults to the selected edition profile.")
    parser.add_argument("--edition", default=None, help="Edition profile; defaults to the current release.")
    parser.add_argument("--variant", default=None)
    parser.add_argument("--sequence", dest="sequence_option", default=None)
    parser.add_argument("--iterations", dest="iterations_option", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--targets", action="append", default=None)
    parser.add_argument("--all-models", action="store_true", help="Explicitly select every registered model.")
    parser.add_argument("--model", action="append", default=[],
                        help="Select one registered model; repeat as needed, or use --all-models.")
    parser.add_argument("--exclude-model", action="append", default=[],
                        help="Exclude one registered model; repeat as needed.")
    cache = parser.add_mutually_exclusive_group()
    cache.add_argument("--oracle-history-before", help="Freeze history at a shared past ISO timestamp with timezone.")
    cache.add_argument("--no-oracle-cache", action="store_true", help="Disable all ASK reuse policies.")
    cache.add_argument("--refresh-oracle-history", action="store_true", default=None,
                       help="Discover other runs' completed games when each subject starts (default for new batches).")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without starting or saving a batch.")
    args = parser.parse_args(argv)
    try:
        return BatchOptions(
            all_models=args.all_models, edition_id=args.edition, variant_name=args.variant, base_seed=args.seed,
            target_ids=tuple(args.targets) if args.targets is not None else None,
            benchmark_id=BenchmarkId(args.benchmark_id) if args.benchmark_id else None,
            mode=BenchmarkMode(args.mode) if args.mode else None,
            sequence=args.sequence_option or args.sequence or "001",
            iterations=args.iterations_option if args.iterations_option is not None else args.iterations,
            model_ids=tuple(BenchmarkModelId(value) for value in args.model),
            excluded_model_ids=tuple(BenchmarkModelId(value) for value in args.exclude_model),
            oracle_cache=not args.no_oracle_cache,
            refresh_oracle_history=args.refresh_oracle_history,
            oracle_history_before=(datetime.fromisoformat(args.oracle_history_before)
                                   if args.oracle_history_before else None),
            dry_run=args.dry_run,
        )
    except (ValueError, ValidationError):
        parser.error("Invalid benchmark/model ID, sequence, iteration count, or timezone-aware cutoff.")


def prepare_plan(options: BatchOptions, repository: Path, *, now: datetime) -> BatchPlan:
    if options.refresh_oracle_history and (
        not options.oracle_cache or options.oracle_history_before is not None
    ):
        raise ValueError("Per-subject history cannot use a fixed cutoff or disable ASK reuse.")
    benchmarks = load_benchmark_catalog(repository / "config/benchmarks.yaml")
    subjects = load_subject_catalog(repository / "config/subjects.yaml")
    catalog = load_model_catalog(repository / "config/models.yaml")
    if not options.model_ids and not options.all_models and not options.excluded_model_ids:
        raise ValueError("Select --model or --all-models explicitly.")
    registered = catalog.registered_model_ids()
    for identifier in (*options.model_ids, *options.excluded_model_ids):
        if identifier not in registered:
            raise ValueError(f"Unknown model ID: {identifier}")
    if len(set(options.model_ids)) != len(options.model_ids):
        raise ValueError("Model selections must not contain duplicates.")
    selected = tuple(identifier for identifier in (options.model_ids or registered)
                     if identifier not in options.excluded_model_ids)
    if not selected:
        raise ValueError("The selected model set is empty.")
    run_date = os.environ.get("RUN_DATE", now.astimezone().strftime("%Y%m%d"))
    try:
        date.fromisoformat(run_date)
    except ValueError:
        raise ValueError("The run date must be a valid YYYYMMDD calendar date.") from None
    cutoff = options.oracle_history_before
    if cutoff is not None and cutoff > now:
        raise ValueError("The Oracle history cutoff must be in the past.")
    requests = tuple(prepare_request(
        repository, models=catalog, benchmarks=benchmarks, subjects=subjects,
        model_id=model_id, execution_id=BenchmarkExecutionId("BX-batch-preflight"),
        edition_id=options.edition_id, benchmark_id=str(options.benchmark_id) if options.benchmark_id else None,
        mode=options.mode, iterations=options.iterations, target_ids=options.target_ids,
        base_seed=options.base_seed, variant_name=options.variant_name,
    ) for model_id in selected)
    request = requests[0]
    if request.edition is None:
        raise ValueError("batch launch requires a released edition or named release variant")
    if any(r.edition != request.edition for r in requests):
        raise ValueError("batch models have different comparison contracts")
    definition = request_definition(request, benchmarks, subjects)
    LOGGER.info("benchmark.batch_plan %s", plan_summary(request, definition))
    plan = BatchPlan(
        edition=request.edition, benchmark_id=request.benchmark_id, mode=request.benchmark_mode,
        sequence=options.sequence, run_date=run_date, iterations=definition.iterations,
        model_ids=selected, base_seed=request.base_seed,
        oracle_history_before=cutoff.astimezone(UTC) if cutoff is not None else None,
        refresh_oracle_history=options.oracle_cache and cutoff is None,
    )
    saved_path = repository / "benchmark-logs" / plan.batch_id / "batch.json"
    if saved_path.exists():
        saved = BatchPlan.model_validate_json(saved_path.read_text(encoding="utf-8"))
        if saved.oracle_history_before is not None and saved.oracle_history_before > now:
            raise ValueError("The saved Oracle history cutoff must be in the past.")
        if options.oracle_cache and cutoff is None and options.refresh_oracle_history is None:
            if saved.oracle_history_before is None and not saved.refresh_oracle_history:
                raise ValueError("This batch has ASK reuse disabled; retain --no-oracle-cache.")
            plan = plan.model_copy(update={
                "oracle_history_before": saved.oracle_history_before,
                "refresh_oracle_history": saved.refresh_oracle_history,
            })
        if saved != plan:
            raise ValueError("Batch settings differ from the saved plan; use a fresh sequence.")
        return saved
    return plan


def launch(plan: BatchPlan, repository: Path, *, stagger_seconds: int) -> int:
    log_dir = repository / "benchmark-logs" / plan.batch_id
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / ".launch.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("This batch launcher is already running.") from None
        saved_path = log_dir / "batch.json"
        if saved_path.exists():
            saved = BatchPlan.model_validate_json(saved_path.read_text(encoding="utf-8"))
            if saved != plan:
                raise ValueError("Batch settings changed before launch; retry with the saved plan.")
        else:
            temporary = log_dir / "batch.json.tmp"
            temporary.write_text(plan.model_dump_json(indent=2) + "\n", encoding="utf-8")
            temporary.replace(saved_path)
        LOGGER.info("benchmark.batch_context benchmark=%s models=%d subjects=all logs=%s",
                    plan.benchmark_id, len(plan.model_ids), log_dir)
        jobs: list[RunningJob] = []
        try:
            for model_id in plan.model_ids:
                if jobs and stagger_seconds:
                    time.sleep(stagger_seconds)
                log_path = log_dir / f"{model_id}.log"
                with log_path.open("ab") as output:
                    process = subprocess.Popen(
                        plan.command(model_id), cwd=repository, stdin=subprocess.DEVNULL,
                        stdout=output, stderr=subprocess.STDOUT, start_new_session=True,
                    )
                jobs.append(RunningJob(model_id, process, log_path))
                LOGGER.info("benchmark.batch.job model=%s status=started execution=%s log=%s",
                            model_id, plan.execution_id(model_id), log_path)
            status = 0
            for job in jobs:
                code = job.process.wait()
                if code:
                    status = 1
                    LOGGER.error("benchmark.batch.job model=%s status=failed exit_code=%d log=%s",
                                 job.model_id, code, job.log_path)
                else:
                    LOGGER.info("benchmark.batch.job model=%s status=completed log=%s",
                                job.model_id, job.log_path)
            return status
        finally:
            for job in jobs:
                if job.process.poll() is None:
                    try:
                        os.killpg(job.process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
            for job in jobs:
                if job.process.poll() is None:
                    try:
                        job.process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(job.process.pid, signal.SIGKILL)
                        job.process.wait()


def _interrupt(_signal_number: int, _frame: FrameType | None) -> NoReturn:
    raise KeyboardInterrupt


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s.%(msecs)03d %(levelname)s %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    options = parse_options(sys.argv[1:] if argv is None else argv)
    repository = Path(__file__).resolve().parents[1]
    try:
        try:
            stagger_seconds = int(os.environ.get("DEEP20BENCH_STAGGER_SECONDS", "45"))
        except ValueError:
            raise ValueError("Launch staggering must be a non-negative integer.") from None
        if stagger_seconds < 0:
            raise ValueError("Launch staggering must be non-negative.")
        plan = prepare_plan(options, repository, now=datetime.now(UTC))
        if options.dry_run:
            for model_id in plan.model_ids:
                print(shlex.join(plan.command(model_id)))
            return 0
        signal.signal(signal.SIGTERM, _interrupt)
        return launch(plan, repository, stagger_seconds=stagger_seconds)
    except ValidationError:
        LOGGER.error("benchmark.batch.failed code=invalid_batch_configuration")
        return 2
    except (OSError, ValueError) as error:
        LOGGER.error("benchmark.batch.failed code=invalid_batch_configuration detail=%s", error)
        return 2
    except KeyboardInterrupt:
        LOGGER.error("benchmark.batch.failed code=interrupted")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
