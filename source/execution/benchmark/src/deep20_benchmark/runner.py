from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from deep20_game.models import (
    ActionType,
    CallMetrics,
    ContractViolationProgress,
    EpisodeFinishedProgress,
    EpisodeResult,
    EpisodeStartedProgress,
    EpisodeTerminalFailure,
    GameProgressEvent,
    TerminalReason,
    TurnProgress,
)
from deep20_game.sinks import ExecutionObserver
from deep20_oracle.catalog import SubjectCatalog
from deep20_oracle.diagnostics import diagnose_exception
from deep20_oracle.models import OracleMetrics, RecoveryMetrics, RecoveryTotals
from deep20_oracle.recovery import combine_recovery_totals
from deep20_oracle.util import canonical_json, sha256_text, timestamp

from .aggregation import aggregate_trials
from .artifacts import (
    ArtifactIntegrityError,
    ArtifactStore,
    BenchmarkTrialSink,
    signed_trial_manifest,
)
from .catalog import BenchmarkCatalog, ModelCatalog
from .logging import BLANK_LINE_BEFORE_ATTRIBUTE
from .models import (
    BenchmarkContractViolationEvent,
    BenchmarkEventId,
    BenchmarkFailure,
    BenchmarkFinishedEvent,
    BenchmarkModelId,
    BenchmarkOutcome,
    BenchmarkProgressEvent,
    BenchmarkRequest,
    BenchmarkResult,
    BenchmarkRun,
    BenchmarkStartedEvent,
    BenchmarkState,
    BenchmarkTurnEvent,
    CompletedTrialResult,
    ComponentCallId,
    EpisodeRunId,
    ExecutionResumedEvent,
    ExecutionStatus,
    InfrastructureCircuitBreaker,
    InfrastructureFailedTrialResult,
    ModelStartedEvent,
    PartialTrialMetrics,
    SubjectBenchmarkOutcome,
    SubjectBenchmarkResult,
    SubjectId,
    SubjectStartedEvent,
    SupersededInfrastructureAttempt,
    TrialBenchmarkResult,
    TrialFinishedEvent,
    TrialId,
    TrialIdentity,
    TrialMetricsResolvedEvent,
    TrialRepairPolicy,
    TrialStartedEvent,
)
from .reporting import render_benchmark, render_progress, render_subject
from .runtime import EpisodeExecutor, TrialExecutionContext

logger = logging.getLogger("deep20.benchmark")


def _console_cost(value: Decimal) -> str:
    """Render USD for concise logs without changing stored Decimal precision."""
    return format(value, ".4f")


class BenchmarkCircuitBreakerOpen(RuntimeError):
    """Raised when consecutive infrastructure failures exhaust the circuit breaker."""

    code = "infrastructure_circuit_breaker_open"


def _console_turn_cost(value: Decimal) -> str:
    """Render component cost for turn logs without changing stored Decimal precision."""
    return format(value, ".5f")


def _console_duration(duration_ms: int) -> str:
    total_seconds = max(duration_ms, 0) // 1_000
    days, remainder = divmod(total_seconds, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes, seconds = divmod(remainder, 60)
    clock = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{days}d{clock}" if days else clock


def _console_local_datetime(value: datetime) -> str:
    return value.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def _partial_metrics_from_episode(episode: EpisodeResult) -> PartialTrialMetrics:
    oracle_quality = episode.summary.oracle_quality
    return PartialTrialMetrics(
        counted_questions=episode.counted_questions,
        guesser_cost_usd=episode.costs_usd.guesser,
        oracle_cost_usd=episode.costs_usd.oracle,
        reviewer_cost_usd=oracle_quality.reviewer_cost_usd,
        judge_cost_usd=oracle_quality.judge_cost_usd,
        validator_cost_usd=episode.costs_usd.validator,
        cost_usd=episode.costs_usd.total,
        tokens=episode.tokens.total,
        cached_input_tokens=(
            episode.llm.guesser.metrics.cached_input_tokens
            + episode.llm.oracle.metrics.cached_input_tokens
            + episode.llm.validator.metrics.cached_input_tokens
        ),
        cache_write_tokens=(
            episode.llm.guesser.metrics.cache_write_tokens
            + episode.llm.oracle.metrics.cache_write_tokens
            + episode.llm.validator.metrics.cache_write_tokens
        ),
        estimated_cache_savings_usd=(
            episode.llm.guesser.metrics.estimated_cache_savings_usd
            + episode.llm.oracle.metrics.estimated_cache_savings_usd
            + episode.llm.validator.metrics.estimated_cache_savings_usd
        ),
        latency_ms=(
            episode.llm.guesser.metrics.latency_ms
            + episode.llm.oracle.metrics.latency_ms
            + episode.llm.validator.metrics.latency_ms
        ),
        duration_ms=episode.duration_ms,
        recovery=combine_recovery_totals(
            episode.llm.guesser.metrics.recovery,
            episode.llm.oracle.metrics.recovery,
            episode.llm.validator.metrics.recovery,
        ),
    )


def _trial_partial_metrics(trial: TrialBenchmarkResult) -> PartialTrialMetrics:
    if isinstance(trial, InfrastructureFailedTrialResult):
        return trial.partial_metrics
    return _partial_metrics_from_episode(trial.result)


@dataclass
class _MutablePartialMetrics:
    counted_questions: int = 0
    guesser_cost_usd: Decimal = Decimal(0)
    oracle_cost_usd: Decimal = Decimal(0)
    reviewer_cost_usd: Decimal = Decimal(0)
    judge_cost_usd: Decimal = Decimal(0)
    validator_cost_usd: Decimal = Decimal(0)
    tokens: int = 0
    cached_input_tokens: int = 0
    cache_write_tokens: int = 0
    estimated_cache_savings_usd: Decimal = Decimal(0)
    latency_ms: int = 0
    duration_ms: int = 0
    recovery: tuple[RecoveryMetrics | RecoveryTotals, ...] = ()

    def add(self, metrics: CallMetrics | OracleMetrics, *, component: str) -> None:
        cost = metrics.cost_usd or Decimal(0)
        if component == "guesser":
            self.guesser_cost_usd += cost
        elif component == "oracle":
            self.oracle_cost_usd += cost
            if isinstance(metrics, OracleMetrics):
                if metrics.reviewer is not None:
                    self.reviewer_cost_usd += (
                        metrics.reviewer.cost_usd or Decimal(0)
                    )
                if metrics.judge is not None:
                    self.judge_cost_usd += metrics.judge.cost_usd or Decimal(0)
        else:
            self.validator_cost_usd += cost
        self.tokens += metrics.input_tokens + metrics.output_tokens
        self.cached_input_tokens += metrics.cached_input_tokens
        self.cache_write_tokens += metrics.cache_write_tokens
        if isinstance(metrics, CallMetrics):
            self.estimated_cache_savings_usd += metrics.estimated_cache_savings_usd
        self.latency_ms += metrics.latency_ms
        self.recovery = (*self.recovery, metrics.recovery)

    def frozen(self) -> PartialTrialMetrics:
        return PartialTrialMetrics(
            counted_questions=self.counted_questions,
            guesser_cost_usd=self.guesser_cost_usd,
            oracle_cost_usd=self.oracle_cost_usd,
            reviewer_cost_usd=self.reviewer_cost_usd,
            judge_cost_usd=self.judge_cost_usd,
            validator_cost_usd=self.validator_cost_usd,
            cost_usd=(
                self.guesser_cost_usd
                + self.oracle_cost_usd
                + self.validator_cost_usd
            ),
            tokens=self.tokens,
            cached_input_tokens=self.cached_input_tokens,
            cache_write_tokens=self.cache_write_tokens,
            estimated_cache_savings_usd=self.estimated_cache_savings_usd,
            latency_ms=self.latency_ms,
            duration_ms=self.duration_ms,
            recovery=combine_recovery_totals(*self.recovery),
        )


@dataclass(frozen=True)
class _ProgressSnapshot:
    progress_percent: Decimal
    elapsed_ms: int
    total_cost_usd: Decimal
    oracle_cost_usd: Decimal
    guesser_cost_usd: Decimal
    judge_cost_usd: Decimal
    reviewer_cost_usd: Decimal
    total_questions: int
    avg_questions_per_trial: Decimal
    eta: datetime


def _progress_snapshot(
    trials: tuple[TrialBenchmarkResult, ...],
    *,
    scheduled_trials: int,
    active_elapsed_ms: int,
    current_time: str,
) -> _ProgressSnapshot:
    terminal_trials = len(trials)
    progress_percent = (
        Decimal(terminal_trials) * Decimal(100) / Decimal(scheduled_trials)
        if scheduled_trials
        else Decimal(100)
    )
    remaining_trials = max(scheduled_trials - terminal_trials, 0)
    remaining_ms = (
        round(active_elapsed_ms * remaining_trials / terminal_trials)
        if terminal_trials
        else 0
    )
    now = datetime.fromisoformat(current_time)

    total_cost_usd = Decimal(0)
    oracle_cost_usd = Decimal(0)
    guesser_cost_usd = Decimal(0)
    judge_cost_usd = Decimal(0)
    reviewer_cost_usd = Decimal(0)
    total_questions = 0
    for trial in trials:
        for attempt in trial.superseded_attempts:
            guesser_cost_usd += attempt.partial_metrics.guesser_cost_usd
            reviewer_cost_usd += attempt.partial_metrics.reviewer_cost_usd
            judge_cost_usd += attempt.partial_metrics.judge_cost_usd
            oracle_cost_usd += max(
                attempt.partial_metrics.oracle_cost_usd
                - attempt.partial_metrics.reviewer_cost_usd
                - attempt.partial_metrics.judge_cost_usd,
                Decimal(0),
            )
            total_cost_usd += attempt.partial_metrics.cost_usd
        if isinstance(trial, CompletedTrialResult):
            quality = trial.result.summary.oracle_quality
            reviewer_cost_usd += quality.reviewer_cost_usd
            judge_cost_usd += quality.judge_cost_usd
            oracle_cost_usd += max(
                trial.result.costs_usd.oracle - quality.quality_control_cost_usd,
                Decimal(0),
            )
            guesser_cost_usd += trial.result.costs_usd.guesser
            total_cost_usd += trial.result.costs_usd.total
            total_questions += trial.result.counted_questions
        else:
            reviewer_cost_usd += trial.partial_metrics.reviewer_cost_usd
            judge_cost_usd += trial.partial_metrics.judge_cost_usd
            oracle_cost_usd += max(
                trial.partial_metrics.oracle_cost_usd
                - trial.partial_metrics.reviewer_cost_usd
                - trial.partial_metrics.judge_cost_usd,
                Decimal(0),
            )
            guesser_cost_usd += trial.partial_metrics.guesser_cost_usd
            total_cost_usd += trial.partial_metrics.cost_usd
            total_questions += trial.partial_metrics.counted_questions

    return _ProgressSnapshot(
        progress_percent=progress_percent,
        elapsed_ms=active_elapsed_ms,
        total_cost_usd=total_cost_usd,
        oracle_cost_usd=oracle_cost_usd,
        guesser_cost_usd=guesser_cost_usd,
        judge_cost_usd=judge_cost_usd,
        reviewer_cost_usd=reviewer_cost_usd,
        total_questions=total_questions,
        avg_questions_per_trial=(
            Decimal(total_questions) / Decimal(terminal_trials)
            if terminal_trials
            else Decimal(0)
        ),
        eta=now + timedelta(milliseconds=remaining_ms),
    )


class _TrialObserver(ExecutionObserver):
    def __init__(
        self,
        runner: BenchmarkRunner,
        identity: TrialIdentity,
        attempt_number: int,
    ):
        self.runner = runner
        self.identity = identity
        self.attempt_number = attempt_number
        self._observed = _MutablePartialMetrics()

    def observe(self, event: GameProgressEvent) -> None:
        if isinstance(event, EpisodeStartedProgress):
            return
        if isinstance(event, EpisodeFinishedProgress):
            partial_metrics = _partial_metrics_from_episode(event.result)
            observed_cost = self._observed.frozen().cost_usd
            missing_cost = max(partial_metrics.cost_usd - observed_cost, Decimal(0))
            state = self.runner.state.model_copy(
                update={
                    "accumulated_cost_usd": (
                        self.runner.state.accumulated_cost_usd + missing_cost
                    ),
                    "updated_at": timestamp(),
                }
            )
            self.runner._persist_progress(
                TrialMetricsResolvedEvent(
                    event_id=self.runner._event_id(),
                    identity=self.identity,
                    attempt_number=self.attempt_number,
                    partial_metrics=partial_metrics,
                    recorded_at=timestamp(),
                ),
                state,
            )
            return
        if isinstance(event, ContractViolationProgress):
            guesser_cost = event.guesser_metrics.cost_usd or Decimal(0)
            self._observed.counted_questions = max(
                self._observed.counted_questions,
                event.turn.counted_questions,
            )
            self._observed.add(event.guesser_metrics, component="guesser")
            state = self.runner.state.model_copy(
                update={
                    "current_turn": event.turn.turn_number,
                    "accumulated_cost_usd": (
                        self.runner.state.accumulated_cost_usd + guesser_cost
                    ),
                    "updated_at": timestamp(),
                }
            )
            self.runner._persist_progress(
                BenchmarkContractViolationEvent(
                    event_id=self.runner._event_id(),
                    identity=self.identity,
                    attempt_number=self.attempt_number,
                    progress=event,
                    recorded_at=timestamp(),
                ),
                state,
            )
            logger.info(
                "benchmark.turn turn=%d contract_violation=%s counted=%s "
                "questions=%d guesser_ms=%d guesser_cost=%s cache=%d/%d attempts=%d",
                event.turn.turn_number,
                event.turn.violation_kind,
                event.turn.counted,
                event.turn.counted_questions,
                event.guesser_metrics.latency_ms,
                _console_turn_cost(guesser_cost),
                event.guesser_metrics.cached_input_tokens,
                event.guesser_metrics.cache_write_tokens,
                event.guesser_metrics.recovery.request_attempts,
            )
            return
        if not isinstance(event, TurnProgress):
            return
        guesser_cost = event.guesser_metrics.cost_usd or Decimal(0)
        adjudicator_cost = event.adjudicator_metrics.cost_usd or Decimal(0)
        self._observed.counted_questions = max(
            self._observed.counted_questions,
            event.turn.counted_questions,
        )
        self._observed.add(event.guesser_metrics, component="guesser")
        self._observed.add(
            event.adjudicator_metrics,
            component=(
                "oracle"
                if event.turn.action.action is ActionType.ASK
                else "validator"
            ),
        )
        state = self.runner.state.model_copy(
            update={
                "current_turn": event.turn.turn_number,
                "accumulated_cost_usd": (
                    self.runner.state.accumulated_cost_usd + guesser_cost + adjudicator_cost
                ),
                "updated_at": timestamp(),
            }
        )
        self.runner._persist_progress(
            BenchmarkTurnEvent(
                event_id=self.runner._event_id(),
                identity=self.identity,
                attempt_number=self.attempt_number,
                progress=event,
                recorded_at=timestamp(),
            ),
            state,
        )
        action = event.turn.action
        if action.action is ActionType.ASK:
            action_part = f"question={json.dumps(action.question, ensure_ascii=False)}"
            adjudicator_part = "oracle"
        else:
            action_part = f"guess={json.dumps(action.name, ensure_ascii=False)}"
            adjudicator_part = "validator"
        logger.info(
            "benchmark.turn turn=%d %s answer=%s guesser_ms=%d guesser_cost=%s "
            "%s_ms=%d %s_cost=%s searches=%d evidence=%d cache=%d/%d "
            "attempts=%d recovered=%d exhausted=%d",
            event.turn.turn_number,
            action_part,
            event.turn.adjudication.answer,
            event.guesser_metrics.latency_ms,
            _console_turn_cost(guesser_cost),
            adjudicator_part,
            event.adjudicator_metrics.latency_ms,
            adjudicator_part,
            _console_turn_cost(adjudicator_cost),
            (
                event.adjudicator_metrics.search_count
                if isinstance(event.adjudicator_metrics, OracleMetrics)
                else 0
            ),
            len(event.turn.adjudication.evidence),
            (
                event.guesser_metrics.cached_input_tokens
                + event.adjudicator_metrics.cached_input_tokens
            ),
            (
                event.guesser_metrics.cache_write_tokens
                + event.adjudicator_metrics.cache_write_tokens
            ),
            (
                event.guesser_metrics.recovery.request_attempts
                + event.adjudicator_metrics.recovery.request_attempts
            ),
            (
                event.guesser_metrics.recovery.recovered_calls
                + event.adjudicator_metrics.recovery.recovered_calls
            ),
            (
                event.guesser_metrics.recovery.exhausted_retries
                + event.adjudicator_metrics.recovery.exhausted_retries
            ),
        )


class BenchmarkRunner:
    """Sequential, resumable, fully typed benchmark scheduler."""

    def __init__(
        self,
        *,
        store: ArtifactStore,
        model_catalog: ModelCatalog,
        benchmark_catalog: BenchmarkCatalog,
        subject_catalog: SubjectCatalog,
        executor: EpisodeExecutor,
    ):
        self.store = store
        self.model_catalog = model_catalog
        self.benchmark_catalog = benchmark_catalog
        self.subject_catalog = subject_catalog
        self.executor = executor
        self.state: BenchmarkState

    def run(
        self,
        request: BenchmarkRequest,
        *,
        repair: TrialRepairPolicy | None = None,
        circuit_breaker: InfrastructureCircuitBreaker | None = None,
    ) -> BenchmarkResult:
        with self.store.execution_lock(request.model_id, request.execution_id):
            return self._run_locked(
                request,
                repair=repair,
                circuit_breaker=circuit_breaker,
            )

    def _run_locked(
        self,
        request: BenchmarkRequest,
        *,
        repair: TrialRepairPolicy | None,
        circuit_breaker: InfrastructureCircuitBreaker | None,
    ) -> BenchmarkResult:
        request = self._resolve_request(request)
        definition = self.benchmark_catalog.benchmark(
            request.benchmark_id,
            benchmark_mode=request.benchmark_mode,
            subject_ids=request.target_ids,
            iterations_override=request.iterations_override,
        )
        model = self.model_catalog.model(request.model_id)
        subjects = tuple(
            self.subject_catalog.subject(str(target_id)) for target_id in definition.subject_ids
        )
        existing_result = self.store.load_benchmark_result(
            request.model_id,
            request.execution_id,
        )
        return_existing_result = False
        if existing_result is not None:
            if (
                existing_result.run.definition != definition
                or existing_result.run.model != model
                or existing_result.run.base_seed != request.base_seed
            ):
                raise ValueError("completed execution does not match the benchmark request")
            return_existing_result = (
                repair is None or not existing_result.outcome.has_infrastructure_failures
            )

        scheduled = len(subjects) * definition.iterations
        scheduled_identities = tuple(
            self._trial_identity(
                request,
                model.model_id,
                SubjectId(subject.target_id),
                trial_number,
            )
            for subject in subjects
            for trial_number in range(1, definition.iterations + 1)
        )
        created_at = timestamp()
        candidate_manifest = self.store.execution_manifest(
            request=request,
            definition=definition,
            model=model,
            subject_catalog_hash=self.subject_catalog.content_hash(),
        )
        existing_manifest = self.store.load_manifest(request.model_id, request.execution_id)
        manifest = existing_manifest or candidate_manifest
        if existing_manifest is not None:
            if (
                existing_manifest.request != request
                or existing_manifest.definition != definition
                or existing_manifest.model != model
                or existing_manifest.subject_catalog_hash != self.subject_catalog.content_hash()
            ):
                raise ValueError("execution ID already has a different immutable context")
            created_at = existing_manifest.created_at
        loaded_state = self.store.load_state(
            request.model_id,
            request.execution_id,
        ) or BenchmarkState(
            execution_id=request.execution_id,
            model_id=request.model_id,
            status=ExecutionStatus.RUNNING,
            scheduled_trials=scheduled,
            started_trials=0,
            terminal_trials=0,
            updated_at=created_at,
        )
        self.state = self._reconcile_state(
            loaded_state,
            scheduled_identities,
            terminal_status=(
                ExecutionStatus.FAILED
                if (
                    existing_result is not None
                    and existing_result.outcome.has_infrastructure_failures
                )
                else (
                    ExecutionStatus.COMPLETED
                    if existing_result is not None
                    else None
                )
            ),
        )
        self.store.prepare_execution(manifest, self.state)
        if self.state != loaded_state:
            self.store.write_state(self.state)
        if return_existing_result:
            assert existing_result is not None
            return existing_result
        if existing_manifest is None:
            self._persist_progress(
                BenchmarkStartedEvent(
                    event_id=self._event_id(),
                    execution_id=request.execution_id,
                    recorded_at=created_at,
                ),
                self.state,
            )
        else:
            resumed_at = timestamp()
            self._persist_progress(
                ExecutionResumedEvent(
                    event_id=self._event_id(),
                    execution_id=request.execution_id,
                    model_id=model.model_id,
                    operation="repair" if repair is not None else "resume",
                    git_commit=candidate_manifest.git_commit,
                    repair_policy=repair,
                    recorded_at=resumed_at,
                ),
                self.state.model_copy(
                    update={
                        "status": ExecutionStatus.RUNNING,
                        "current_turn": None,
                        "updated_at": resumed_at,
                    }
                ),
            )
            self.store.write_markdown(
                self.store.run_root(model.model_id, request.execution_id) / "summary.md",
                render_progress(self.state),
            )
        logger.info(
            "benchmark.run execution=%s benchmark=%s guesser_id=%s guesser=%s "
            "model=%s provider=%s reasoning=%s seed_capability=%s subjects=%d "
            "iterations=%d base_seed=%d policy_version=%d mode=%s max_questions=%d oracle_model=%s "
            "oracle_provider=%s validator_model=%s validator_provider=%s "
            "guesser_retry_s=%d oracle_retry_s=%d validator_retry_s=%d",
            request.execution_id,
            request.benchmark_id,
            model.model_id,
            json.dumps(model.display_name, ensure_ascii=False),
            model.configuration.model,
            model.configuration.provider,
            model.configuration.reasoning_effort,
            model.configuration.seed_capability,
            len(subjects),
            definition.iterations,
            request.base_seed,
            definition.game_policy.version,
            definition.game_policy.benchmark_mode,
            definition.game_policy.max_questions,
            definition.oracle_configuration.model,
            definition.oracle_configuration.provider,
            definition.validator_configuration.model,
            definition.validator_configuration.provider,
            model.configuration.recovery.max_elapsed_seconds,
            definition.oracle_configuration.recovery.max_elapsed_seconds,
            definition.validator_configuration.recovery.max_elapsed_seconds,
        )

        self._persist_progress(
            ModelStartedEvent(
                event_id=self._event_id(),
                execution_id=request.execution_id,
                model_id=model.model_id,
                recorded_at=timestamp(),
            ),
            self.state.model_copy(
                update={
                    "current_target_id": None,
                    "current_trial_id": None,
                    "current_turn": None,
                    "updated_at": timestamp(),
                }
            ),
        )
        subject_results: list[SubjectBenchmarkResult] = []
        progress_trials: dict[str, TrialBenchmarkResult] = {}
        for scheduled_identity in scheduled_identities:
            progress_trial = self.store.load_trial_result(scheduled_identity)
            if progress_trial is not None:
                progress_trials[str(scheduled_identity.episode_run_id)] = progress_trial
        consecutive_infrastructure_failures = 0
        for subject in subjects:
            self._persist_progress(
                SubjectStartedEvent(
                    event_id=self._event_id(),
                    execution_id=request.execution_id,
                    model_id=model.model_id,
                    target_id=SubjectId(subject.target_id),
                    recorded_at=timestamp(),
                ),
                self.state.model_copy(
                    update={
                        "current_target_id": SubjectId(subject.target_id),
                        "current_trial_id": None,
                        "current_turn": None,
                        "updated_at": timestamp(),
                    }
                ),
            )
            trials = []
            for trial_number in range(1, definition.iterations + 1):
                identity = self._trial_identity(
                    request,
                    model.model_id,
                    SubjectId(subject.target_id),
                    trial_number,
                )
                existing_trial = self.store.load_trial_result(identity)
                prior_start_attempts = self.store.trial_event_count(
                    identity,
                    "trial_started",
                )
                had_terminal_result = existing_trial is not None
                context = TrialExecutionContext(
                    identity=identity,
                    definition=definition,
                    model=model,
                    subject=subject,
                    subject_catalog_hash=self.subject_catalog.content_hash(),
                    base_seed=request.base_seed,
                )
                sink = self._trial_sink(context)
                existing_trial, materialized_interruption = (
                    self._materialize_interrupted_attempts(
                        identity,
                        existing_trial,
                        prior_start_attempts,
                        sink,
                    )
                )
                if materialized_interruption:
                    assert existing_trial is not None
                    self.store.write_trial_result(existing_trial)
                if (
                    existing_trial is not None
                    and not self.store.trial_attempt_event_recorded(
                        identity,
                        "trial_finished",
                        existing_trial.attempt_number,
                    )
                ):
                    reconciled_at = timestamp()
                    self._persist_progress(
                        TrialFinishedEvent(
                            event_id=self._event_id(),
                            identity=identity,
                            attempt_number=existing_trial.attempt_number,
                            status=existing_trial.status,
                            recorded_at=reconciled_at,
                        ),
                        self.state.model_copy(
                            update={
                                "terminal_trials": (
                                    self.state.terminal_trials
                                    if had_terminal_result
                                    else self.state.terminal_trials + 1
                                ),
                                "current_trial_id": identity.trial_id,
                                "current_turn": None,
                                "last_failure": (
                                    existing_trial.failure
                                    if existing_trial.failure is not None
                                    else self.state.last_failure
                                ),
                                "updated_at": reconciled_at,
                            }
                        ),
                    )
                repair_attempt = (
                    repair is not None
                    and existing_trial is not None
                    and existing_trial.status == "infrastructure_failed"
                    and existing_trial.attempt_number < repair.max_attempts_per_trial
                )
                if materialized_interruption and not repair_attempt:
                    logger.info(
                        "benchmark.trial_context trial=%s target=%s name=%s",
                        identity.trial_id,
                        subject.target_id,
                        json.dumps(subject.canonical_name, ensure_ascii=False),
                        extra={BLANK_LINE_BEFORE_ATTRIBUTE: True},
                    )
                if existing_trial is not None and not repair_attempt:
                    progress_trials[str(identity.episode_run_id)] = existing_trial
                    trials.append(existing_trial)
                    continue
                attempt_number = prior_start_attempts + 1
                previously_terminal = existing_trial is not None
                superseded_attempt: SupersededInfrastructureAttempt | None = None
                if repair_attempt and isinstance(
                    existing_trial,
                    InfrastructureFailedTrialResult,
                ):
                    observed_attempt_metrics = self._attempt_metrics(
                        identity,
                        existing_trial.attempt_number,
                    )
                    superseded_metrics = existing_trial.partial_metrics.model_copy(
                        update={
                            "reviewer_cost_usd": (
                                existing_trial.partial_metrics.reviewer_cost_usd
                                or observed_attempt_metrics.reviewer_cost_usd
                            ),
                            "judge_cost_usd": (
                                existing_trial.partial_metrics.judge_cost_usd
                                or observed_attempt_metrics.judge_cost_usd
                            ),
                        }
                    )
                    superseded_attempt = SupersededInfrastructureAttempt(
                        attempt_number=existing_trial.attempt_number,
                        failure=existing_trial.failure,
                        partial_metrics=superseded_metrics,
                        error_output_preview=existing_trial.error_output_preview,
                        superseded_at=timestamp(),
                    )
                trial: TrialBenchmarkResult
                self._persist_progress(
                    TrialStartedEvent(
                        event_id=self._event_id(),
                        identity=identity,
                        attempt_number=attempt_number,
                        recorded_at=timestamp(),
                    ),
                    self.state.model_copy(
                        update={
                            "started_trials": (
                                self.state.started_trials
                                if prior_start_attempts > 0
                                else self.state.started_trials + 1
                            ),
                            "current_trial_id": identity.trial_id,
                            "current_turn": None,
                            "updated_at": timestamp(),
                        }
                    ),
                )
                if repair_attempt:
                    logger.info(
                        "benchmark.repair trial=%s target=%s attempt=%d max_attempts=%d",
                        identity.trial_id,
                        subject.target_id,
                        attempt_number,
                        repair.max_attempts_per_trial if repair is not None else 0,
                    )
                logger.info(
                    "benchmark.trial_context trial=%s target=%s name=%s",
                    identity.trial_id,
                    subject.target_id,
                    json.dumps(subject.canonical_name, ensure_ascii=False),
                    extra={BLANK_LINE_BEFORE_ATTRIBUTE: True},
                )
                sink.prepare_run(str(identity.episode_run_id))
                trial = self._execute_trial(
                    context,
                    sink,
                    _TrialObserver(self, identity, attempt_number),
                ).model_copy(update={"attempt_number": attempt_number})
                if (
                    isinstance(trial, InfrastructureFailedTrialResult)
                    and trial.partial_metrics == PartialTrialMetrics()
                ):
                    trial = trial.model_copy(
                        update={
                            "partial_metrics": self._attempt_metrics(
                                identity,
                                attempt_number,
                            )
                        }
                    )
                if not self.store.trial_attempt_event_recorded(
                    identity,
                    "trial_metrics_resolved",
                    attempt_number,
                ):
                    resolved_metrics = _trial_partial_metrics(trial)
                    observed_metrics = self._attempt_metrics(
                        identity,
                        attempt_number,
                    )
                    metrics_at = timestamp()
                    self._persist_progress(
                        TrialMetricsResolvedEvent(
                            event_id=self._event_id(),
                            identity=identity,
                            attempt_number=attempt_number,
                            partial_metrics=resolved_metrics,
                            recorded_at=metrics_at,
                        ),
                        self.state.model_copy(
                            update={
                                "accumulated_cost_usd": (
                                    self.state.accumulated_cost_usd
                                    + max(
                                        resolved_metrics.cost_usd
                                        - observed_metrics.cost_usd,
                                        Decimal(0),
                                    )
                                ),
                                "updated_at": metrics_at,
                            }
                        ),
                    )
                if superseded_attempt is not None and existing_trial is not None:
                    trial = trial.model_copy(
                        update={
                            "superseded_attempts": (
                                *existing_trial.superseded_attempts,
                                superseded_attempt,
                            )
                        }
                    )
                self.store.write_trial_result(trial)
                trials.append(trial)
                progress_trials[str(identity.episode_run_id)] = trial
                finished_at = timestamp()
                self._persist_progress(
                    TrialFinishedEvent(
                        event_id=self._event_id(),
                        identity=identity,
                        attempt_number=attempt_number,
                        status=trial.status,
                        recorded_at=finished_at,
                    ),
                    self.state.model_copy(
                        update={
                            "terminal_trials": (
                                self.state.terminal_trials
                                if previously_terminal
                                else self.state.terminal_trials + 1
                            ),
                            "current_turn": None,
                            "last_failure": (
                                trial.failure
                                if trial.failure is not None
                                else self.state.last_failure
                            ),
                            "updated_at": finished_at,
                        }
                    ),
                )
                if trial.failure is not None:
                    failure_latency_ms = (
                        trial.partial_metrics.latency_ms
                        if isinstance(trial, InfrastructureFailedTrialResult)
                        else (
                            trial.result.llm.guesser.metrics.latency_ms
                            + trial.result.llm.oracle.metrics.latency_ms
                            + trial.result.llm.validator.metrics.latency_ms
                        )
                    )
                    failure_cost_usd = (
                        trial.partial_metrics.cost_usd
                        if isinstance(trial, InfrastructureFailedTrialResult)
                        else trial.result.costs_usd.total
                    )
                    logger.error(
                        "benchmark.failed model_id=%s target=%s trial=%s code=%s "
                        "latency_ms=%d cost_usd=%s",
                        model.model_id,
                        subject.target_id,
                        identity.trial_id,
                        trial.failure.code,
                        failure_latency_ms,
                        _console_cost(failure_cost_usd),
                    )
                progress = _progress_snapshot(
                    tuple(progress_trials.values()),
                    scheduled_trials=scheduled,
                    active_elapsed_ms=self._active_elapsed_ms(
                        self.store.load_events(
                            model.model_id,
                            request.execution_id,
                        ),
                        finished_at,
                    ),
                    current_time=finished_at,
                )
                logger.info(
                    "benchmark.trial model_id=%s target=%s trial=%s status=%s "
                    "reason=%s success=%s questions=%d cost_usd=%s "
                    "progress=%.2f%% elapsed=%s total_cost_usd=%s "
                    "oracle_cost_usd=%s guesser_cost_usd=%s judge_cost_usd=%s "
                    "reviewer_cost_usd=%s total_questions=%d "
                    'avg_questions_per_trial=%.1f eta="%s"',
                    model.model_id,
                    subject.target_id,
                    identity.trial_id,
                    trial.status,
                    (
                        trial.result.terminal_reason
                        if isinstance(trial, CompletedTrialResult)
                        else TerminalReason.INFRASTRUCTURE_FAILURE
                    ),
                    (trial.result.success if isinstance(trial, CompletedTrialResult) else False),
                    (
                        trial.result.counted_questions
                        if isinstance(trial, CompletedTrialResult)
                        else trial.partial_metrics.counted_questions
                    ),
                    _console_cost(
                        trial.result.costs_usd.total
                        if isinstance(trial, CompletedTrialResult)
                        else trial.partial_metrics.cost_usd
                    ),
                    progress.progress_percent,
                    _console_duration(progress.elapsed_ms),
                    _console_cost(progress.total_cost_usd),
                    _console_cost(progress.oracle_cost_usd),
                    _console_cost(progress.guesser_cost_usd),
                    _console_cost(progress.judge_cost_usd),
                    _console_cost(progress.reviewer_cost_usd),
                    progress.total_questions,
                    progress.avg_questions_per_trial,
                    _console_local_datetime(progress.eta),
                )
                self.store.write_markdown(
                    self.store.run_root(model.model_id, request.execution_id) / "summary.md",
                    render_progress(self.state),
                )
                if trial.status == "infrastructure_failed":
                    consecutive_infrastructure_failures += 1
                else:
                    consecutive_infrastructure_failures = 0
                if (
                    circuit_breaker is not None
                    and consecutive_infrastructure_failures
                    >= circuit_breaker.max_consecutive_infrastructure_failures
                ):
                    aborted_at = timestamp()
                    self.state = self.state.model_copy(
                        update={
                            "status": ExecutionStatus.FAILED,
                            "current_turn": None,
                            "updated_at": aborted_at,
                        }
                    )
                    self.store.write_state(self.state)
                    self.store.write_markdown(
                        self.store.run_root(model.model_id, request.execution_id)
                        / "summary.md",
                        render_progress(self.state),
                    )
                    logger.error(
                        "benchmark.circuit_breaker execution=%s model_id=%s "
                        "consecutive_infrastructure_failures=%d limit=%d",
                        request.execution_id,
                        model.model_id,
                        consecutive_infrastructure_failures,
                        circuit_breaker.max_consecutive_infrastructure_failures,
                    )
                    raise BenchmarkCircuitBreakerOpen(
                        "aborted after "
                        f"{consecutive_infrastructure_failures} consecutive "
                        "infrastructure failures; resume or repair the execution "
                        "after resolving the provider issue"
                    )

            trial_tuple = tuple(trials)
            subject_summary = aggregate_trials(
                trial_tuple,
                scheduled=definition.iterations,
            )
            subject_result = SubjectBenchmarkResult(
                subject=subject,
                outcome=SubjectBenchmarkOutcome(
                    complete=len(trial_tuple) == definition.iterations,
                    has_infrastructure_failures=(subject_summary.counts.infrastructure_failed > 0),
                ),
                summary=subject_summary,
                trials=trial_tuple,
            )
            subject_results.append(subject_result)
            self.store.write_subject_result(
                model.model_id,
                request.execution_id,
                subject_result,
            )
            self.store.write_markdown(
                self.store.subject_root(
                    model.model_id,
                    request.execution_id,
                    subject.target_id,
                )
                / "summary.md",
                render_subject(subject_result),
            )

        all_trials = tuple(
            trial for subject_result in subject_results for trial in subject_result.trials
        )
        summary = aggregate_trials(all_trials, scheduled=scheduled)
        completed_at = timestamp()
        has_infrastructure_failures = summary.counts.infrastructure_failed > 0
        final_failure = next(
            (
                trial.failure
                for trial in reversed(all_trials)
                if trial.failure is not None
            ),
            None,
        )
        self._persist_progress(
            BenchmarkFinishedEvent(
                event_id=self._event_id(),
                execution_id=request.execution_id,
                has_infrastructure_failures=has_infrastructure_failures,
                recorded_at=completed_at,
            ),
            self.state.model_copy(
                update={
                    "status": (
                        ExecutionStatus.FAILED
                        if has_infrastructure_failures
                        else ExecutionStatus.COMPLETED
                    ),
                    "current_target_id": None,
                    "current_trial_id": None,
                    "current_turn": None,
                    "last_failure": final_failure,
                    "updated_at": completed_at,
                }
            ),
        )
        active_duration_ms = self._active_elapsed_ms(
            self.store.load_events(model.model_id, request.execution_id),
            completed_at,
        )
        artifacts = self.store.benchmark_artifact_references(
            model.model_id,
            request.execution_id,
        )
        provisional = BenchmarkResult(
            run=BenchmarkRun(
                execution_id=request.execution_id,
                definition=definition,
                model=model,
                base_seed=request.base_seed,
                git_commits=self.store.execution_git_commits(
                    model.model_id,
                    request.execution_id,
                ),
                started_at=created_at,
                completed_at=completed_at,
                duration_ms=active_duration_ms,
            ),
            outcome=BenchmarkOutcome(
                complete=True,
                has_infrastructure_failures=has_infrastructure_failures,
                publication_eligible=(
                    not has_infrastructure_failures
                    and all(
                        isinstance(trial, CompletedTrialResult)
                        and trial.result.publication_eligible
                        for trial in all_trials
                    )
                ),
            ),
            summary=summary,
            subjects=tuple(subject_results),
            artifacts=artifacts,
            integrity_hash="0" * 64,
        )
        summary_reference = self.store.write_markdown(
            self.store.run_root(model.model_id, request.execution_id) / "summary.md",
            render_benchmark(provisional),
        )
        provisional = provisional.model_copy(
            update={
                "artifacts": artifacts.model_copy(update={"summary_markdown": summary_reference})
            }
        )
        integrity_hash = sha256_text(
            canonical_json(provisional.model_dump(mode="json", exclude={"integrity_hash"}))
        )
        result = provisional.model_copy(
            update={
                "artifacts": provisional.artifacts.model_copy(
                    update={
                        "result": provisional.artifacts.result.model_copy(
                            update={"integrity_hash": integrity_hash}
                        )
                    }
                ),
                "integrity_hash": integrity_hash,
            }
        )
        self.store.write_benchmark_result(result)
        self.store.write_benchmark_summary(self.store.build_benchmark_summary(result))
        logger.info(
            "benchmark.result execution=%s model_id=%s trials=%d success_rate=%s "
            "successful=%d scoring_eligible=%d scheduled=%d "
            "infrastructure_failures=%d recovered_calls=%d exhausted_retries=%d "
            "retry_reasons=%s terminal_failures=%s superseded_attempts=%d "
            "superseded_cost_usd=%s cost_usd=%s",
            request.execution_id,
            model.model_id,
            summary.counts.terminal,
            summary.success_rate,
            summary.counts.successful,
            summary.counts.scoring_eligible,
            summary.counts.scheduled,
            summary.counts.infrastructure_failed,
            summary.recovery.recovered_calls,
            summary.recovery.exhausted_retries,
            json.dumps(
                {
                    item.reason.value: item.count
                    for item in summary.recovery.reasons
                },
                separators=(",", ":"),
                sort_keys=True,
            ),
            json.dumps(
                {
                    item.code: item.count
                    for item in summary.failure_codes
                },
                separators=(",", ":"),
                sort_keys=True,
            ),
            summary.repair.superseded_attempts,
            _console_cost(summary.repair.partial_metrics.cost_usd),
            _console_cost(summary.total_cost_usd),
        )
        return result

    def _reconcile_state(
        self,
        state: BenchmarkState,
        identities: tuple[TrialIdentity, ...],
        *,
        terminal_status: ExecutionStatus | None,
    ) -> BenchmarkState:
        """Rebuild durable counters and cost from signed events and typed results."""

        events = self.store.load_events(state.model_id, state.execution_id)
        identity_keys = {
            str(identity.episode_run_id): identity for identity in identities
        }
        results = tuple(
            trial
            for identity in identities
            if (trial := self.store.load_trial_result(identity)) is not None
        )
        started_attempt_keys = {
            (str(event.identity.episode_run_id), event.attempt_number)
            for event in events
            if isinstance(event, TrialStartedEvent)
            and str(event.identity.episode_run_id) in identity_keys
        }
        for trial in results:
            trial_key = str(trial.identity.episode_run_id)
            persisted_attempts = (
                *(attempt.attempt_number for attempt in trial.superseded_attempts),
                trial.attempt_number,
            )
            if any(
                (trial_key, attempt_number) not in started_attempt_keys
                for attempt_number in persisted_attempts
            ):
                raise ArtifactIntegrityError(
                    "trial result attempt has no durable start event"
                )
        started_keys = {
            str(event.identity.episode_run_id)
            for event in events
            if isinstance(event, TrialStartedEvent)
            and str(event.identity.episode_run_id) in identity_keys
        }
        started_keys.update(
            str(trial.identity.episode_run_id) for trial in results
        )

        attempt_keys = {
            (str(event.identity.episode_run_id), event.attempt_number)
            for event in events
            if isinstance(
                event,
                (
                    TrialStartedEvent,
                    BenchmarkTurnEvent,
                    BenchmarkContractViolationEvent,
                    TrialMetricsResolvedEvent,
                    TrialFinishedEvent,
                ),
            )
            and str(event.identity.episode_run_id) in identity_keys
        }
        attempt_costs = {
            key: self._attempt_metrics(
                identity_keys[key[0]],
                key[1],
                events=events,
            ).cost_usd
            for key in attempt_keys
        }
        for trial in results:
            trial_key = str(trial.identity.episode_run_id)
            for attempt in trial.superseded_attempts:
                attempt_costs[(trial_key, attempt.attempt_number)] = (
                    attempt.partial_metrics.cost_usd
                )
            attempt_costs[(trial_key, trial.attempt_number)] = (
                _trial_partial_metrics(trial).cost_usd
            )

        return state.model_copy(
            update={
                "status": (
                    terminal_status if terminal_status is not None else state.status
                ),
                "scheduled_trials": len(identities),
                "started_trials": len(started_keys),
                "terminal_trials": len(results),
                "accumulated_cost_usd": sum(
                    attempt_costs.values(),
                    start=Decimal(0),
                ),
            }
        )

    def _attempt_metrics(
        self,
        identity: TrialIdentity,
        attempt_number: int,
        *,
        events: tuple[BenchmarkProgressEvent, ...] | None = None,
    ) -> PartialTrialMetrics:
        source = events or self.store.load_events(
            identity.model_id,
            identity.execution_id,
        )
        matching = tuple(
            event
            for event in source
            if getattr(event, "identity", None) == identity
            and getattr(event, "attempt_number", None) == attempt_number
        )
        resolved = tuple(
            event
            for event in matching
            if isinstance(event, TrialMetricsResolvedEvent)
        )
        if resolved:
            return resolved[-1].partial_metrics

        metrics = _MutablePartialMetrics()
        started_at = next(
            (
                event.recorded_at
                for event in matching
                if isinstance(event, TrialStartedEvent)
            ),
            None,
        )
        last_progress_at: str | None = None
        for event in matching:
            if isinstance(event, BenchmarkContractViolationEvent):
                metrics.counted_questions = max(
                    metrics.counted_questions,
                    event.progress.turn.counted_questions,
                )
                metrics.add(event.progress.guesser_metrics, component="guesser")
                last_progress_at = event.recorded_at
            elif isinstance(event, BenchmarkTurnEvent):
                metrics.counted_questions = max(
                    metrics.counted_questions,
                    event.progress.turn.counted_questions,
                )
                metrics.add(event.progress.guesser_metrics, component="guesser")
                metrics.add(
                    event.progress.adjudicator_metrics,
                    component=(
                        "oracle"
                        if event.progress.turn.action.action is ActionType.ASK
                        else "validator"
                    ),
                )
                last_progress_at = event.recorded_at
        if started_at is not None and last_progress_at is not None:
            metrics.duration_ms = self._duration_ms(started_at, last_progress_at)
        return metrics.frozen()

    @staticmethod
    def _interrupted_failure() -> BenchmarkFailure:
        return BenchmarkFailure(
            code="interrupted_trial",
            type="InterruptedTrial",
            message="The trial attempt was started without a terminal result.",
        )

    def _materialize_interrupted_attempts(
        self,
        identity: TrialIdentity,
        existing_trial: TrialBenchmarkResult | None,
        prior_start_attempts: int,
        sink: BenchmarkTrialSink,
    ) -> tuple[TrialBenchmarkResult | None, bool]:
        current_attempt = (
            existing_trial.attempt_number if existing_trial is not None else 0
        )
        if current_attempt > prior_start_attempts:
            raise ArtifactIntegrityError(
                "trial result attempt exceeds its durable start count"
            )
        if current_attempt == prior_start_attempts:
            return existing_trial, False
        if isinstance(existing_trial, CompletedTrialResult):
            raise ArtifactIntegrityError(
                "a scoring-eligible trial has a later unfinished attempt"
            )

        superseded = list(
            existing_trial.superseded_attempts
            if existing_trial is not None
            else ()
        )
        detected_at = timestamp()
        if isinstance(existing_trial, InfrastructureFailedTrialResult):
            superseded.append(
                SupersededInfrastructureAttempt(
                    attempt_number=existing_trial.attempt_number,
                    failure=existing_trial.failure,
                    partial_metrics=existing_trial.partial_metrics,
                    error_output_preview=existing_trial.error_output_preview,
                    superseded_at=detected_at,
                )
            )
        for attempt_number in range(current_attempt + 1, prior_start_attempts):
            superseded.append(
                SupersededInfrastructureAttempt(
                    attempt_number=attempt_number,
                    failure=self._interrupted_failure(),
                    partial_metrics=self._attempt_metrics(
                        identity,
                        attempt_number,
                    ),
                    superseded_at=detected_at,
                )
            )
        interrupted = InfrastructureFailedTrialResult(
            identity=identity,
            attempt_number=prior_start_attempts,
            failure=self._interrupted_failure(),
            partial_metrics=self._attempt_metrics(
                identity,
                prior_start_attempts,
            ),
            superseded_attempts=tuple(superseded),
            artifacts=sink.references(),
        )
        return interrupted, True

    def _trial_sink(self, context: TrialExecutionContext) -> BenchmarkTrialSink:
        manifest = signed_trial_manifest(
            identity=context.identity,
            subject_catalog_hash=context.subject_catalog_hash,
            subject=context.subject,
            model=context.model,
            game_policy=context.definition.game_policy,
            oracle_configuration=context.definition.oracle_configuration,
            validator_configuration=context.definition.validator_configuration,
        )
        return BenchmarkTrialSink(self.store, manifest)

    def _execute_trial(
        self,
        context: TrialExecutionContext,
        sink: BenchmarkTrialSink,
        observer: _TrialObserver,
    ) -> CompletedTrialResult | InfrastructureFailedTrialResult:
        try:
            episode = self.executor.execute(
                context,
                sink,
                observer,
            )
            artifacts = sink.references()
            if episode.terminal_reason is TerminalReason.INFRASTRUCTURE_FAILURE:
                terminal_failure = episode.failure or sink.terminal_failure
                return InfrastructureFailedTrialResult(
                    identity=context.identity,
                    failure=BenchmarkFailure(
                        code=(
                            terminal_failure.code
                            if terminal_failure is not None
                            else "episode_infrastructure_failure"
                        ),
                        type=(
                            terminal_failure.type
                            if terminal_failure is not None
                            else "EpisodeInfrastructureFailure"
                        ),
                        message=(
                            terminal_failure.message
                            if terminal_failure is not None
                            else ("The game ended because an infrastructure component failed.")
                        ),
                        call_id=(
                            ComponentCallId(terminal_failure.call_id)
                            if terminal_failure is not None and terminal_failure.call_id is not None
                            else None
                        ),
                        diagnostics=(
                            terminal_failure.diagnostics if terminal_failure is not None else None
                        ),
                    ),
                    partial_metrics=_partial_metrics_from_episode(episode),
                    error_output_preview=sink.latest_error_output_preview,
                    artifacts=artifacts,
                )
            return CompletedTrialResult(
                identity=context.identity,
                result=episode,
                failure=self._terminal_failure(episode.failure or sink.terminal_failure),
                error_output_preview=sink.latest_error_output_preview,
                artifacts=artifacts,
            )
        except Exception as error:  # noqa: BLE001 - trial boundary records typed failures
            diagnostics = diagnose_exception(error)
            failure = BenchmarkFailure(
                code=getattr(error, "code", "unexpected_benchmark_trial_failure"),
                type=type(error).__name__,
                message=diagnostics.causes[0].message,
                call_id=(
                    getattr(error, "call_id", None)
                    if getattr(error, "call_id", None) is not None
                    else None
                ),
                diagnostics=diagnostics,
            )
            return InfrastructureFailedTrialResult(
                identity=context.identity,
                failure=failure,
                partial_metrics=PartialTrialMetrics(),
                error_output_preview=sink.latest_error_output_preview,
                artifacts=sink.references(),
            )

    @staticmethod
    def _terminal_failure(
        failure: EpisodeTerminalFailure | None,
    ) -> BenchmarkFailure | None:
        if failure is None:
            return None
        return BenchmarkFailure(
            code=failure.code,
            type=failure.type,
            message=failure.message,
            call_id=(ComponentCallId(failure.call_id) if failure.call_id is not None else None),
            diagnostics=failure.diagnostics,
        )

    def _persist_progress(
        self,
        event: BenchmarkProgressEvent,
        state: BenchmarkState,
    ) -> None:
        self.store.append_event(state.model_id, state.execution_id, event)
        self.state = state
        self.store.write_state(state)

    def _resolve_request(self, request: BenchmarkRequest) -> BenchmarkRequest:
        target_ids = request.target_ids or tuple(
            SubjectId(subject.target_id) for subject in self.subject_catalog.subjects.values()
        )
        if not target_ids:
            raise ValueError("the subject catalog does not register any targets")
        return request.model_copy(
            update={
                "target_ids": target_ids,
            }
        )

    @staticmethod
    def _trial_identity(
        request: BenchmarkRequest,
        model_id: BenchmarkModelId,
        target_id: SubjectId,
        trial_number: int,
    ) -> TrialIdentity:
        material = canonical_json(
            {
                "execution_id": str(request.execution_id),
                "model_id": str(model_id),
                "target_id": str(target_id),
                "trial_number": trial_number,
            }
        )
        return TrialIdentity(
            execution_id=request.execution_id,
            model_id=model_id,
            target_id=target_id,
            trial_id=TrialId(f"trial-{trial_number:03d}"),
            trial_number=trial_number,
            episode_run_id=EpisodeRunId(f"BR-{sha256_text(material)[:40]}"),
        )

    @staticmethod
    def _event_id() -> BenchmarkEventId:
        return BenchmarkEventId(f"BE-{uuid.uuid7().hex}")

    @staticmethod
    def _active_elapsed_ms(
        events: tuple[BenchmarkProgressEvent, ...],
        current_time: str,
    ) -> int:
        elapsed_ms = 0
        segment_started_at: str | None = None
        segment_last_event_at: str | None = None
        for event in events:
            if isinstance(event, (BenchmarkStartedEvent, ExecutionResumedEvent)):
                if segment_started_at is not None and segment_last_event_at is not None:
                    elapsed_ms += BenchmarkRunner._duration_ms(
                        segment_started_at,
                        segment_last_event_at,
                    )
                segment_started_at = event.recorded_at
                segment_last_event_at = event.recorded_at
                continue
            if segment_started_at is None:
                continue
            segment_last_event_at = event.recorded_at
            if isinstance(event, BenchmarkFinishedEvent):
                elapsed_ms += BenchmarkRunner._duration_ms(
                    segment_started_at,
                    event.recorded_at,
                )
                segment_started_at = None
                segment_last_event_at = None
        if segment_started_at is not None:
            elapsed_ms += BenchmarkRunner._duration_ms(
                segment_started_at,
                current_time,
            )
        return elapsed_ms

    @staticmethod
    def _duration_ms(started_at: str, completed_at: str) -> int:
        return max(
            round(
                (
                    datetime.fromisoformat(completed_at) - datetime.fromisoformat(started_at)
                ).total_seconds()
                * 1_000
            ),
            0,
        )
