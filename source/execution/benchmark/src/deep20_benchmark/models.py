from __future__ import annotations

import re
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, ClassVar, Literal

from deep20_game.config import BenchmarkMode, GamePolicy, ModelConfig
from deep20_game.models import (
    ContractViolationProgress,
    EpisodeResult,
    GuesserContractReliability,
    TurnProgress,
)
from deep20_oracle.config import OracleConfig
from deep20_oracle.models import (
    FailureDiagnostics,
    OracleQuestionType,
    ProviderOutputCapture,
    RecoveryMetrics,
    RecoveryTotals,
    StrictModel,
    Subject,
)
from pydantic import ConfigDict, Field, RootModel, field_validator, model_validator

ERROR_OUTPUT_PREVIEW_MAX_CHARACTERS = 250


class _Identifier(RootModel[str]):
    model_config = ConfigDict(frozen=True)
    pattern: ClassVar[str] = ""

    @field_validator("root")
    @classmethod
    def valid_identifier(cls, value: str) -> str:
        if re.fullmatch(cls.pattern, value) is None:
            raise ValueError(f"invalid {cls.__name__}: {value!r}")
        return value

    def __str__(self) -> str:
        return self.root


class BenchmarkId(_Identifier):
    pattern = r"B-[0-9]{4}"


class BenchmarkExecutionId(_Identifier):
    pattern = r"BX-[A-Za-z0-9][A-Za-z0-9._-]{0,43}"


class BenchmarkModelId(_Identifier):
    pattern = r"M-[0-9]{4}"


class BenchmarkLlmRole(StrEnum):
    GUESSER = "guesser"
    ORACLE = "oracle"
    REVIEWER = "reviewer"
    JUDGE = "judge"
    VALIDATOR = "validator"


class TrialId(_Identifier):
    pattern = r"trial-[0-9]{3,5}"


class SubjectId(_Identifier):
    pattern = r"T-[0-9]{4}"


class EpisodeRunId(_Identifier):
    pattern = r"BR-[0-9a-f]{40}"


class ComponentCallId(_Identifier):
    pattern = r"(?:GC|OC|VC)-[0-9a-f]{32}"


class BenchmarkEventId(_Identifier):
    pattern = r"BE-[0-9a-f]{32}"


class BenchmarkRequest(StrictModel):
    benchmark_id: BenchmarkId
    execution_id: BenchmarkExecutionId
    model_id: BenchmarkModelId
    benchmark_mode: BenchmarkMode = Field(
        description="Required benchmark mode: official or experimental."
    )
    target_ids: tuple[SubjectId, ...] = ()
    iterations_override: int | None = Field(default=None, ge=1, le=100)
    base_seed: int = Field(default=0, ge=0, le=(2**31) - 1)

    @model_validator(mode="before")
    @classmethod
    def require_benchmark_mode(cls, value: object) -> object:
        if isinstance(value, dict) and "benchmark_mode" not in value:
            raise ValueError("benchmark_mode is required; choose 'official' or 'experimental'")
        return value

    @field_validator("target_ids")
    @classmethod
    def unique_selection_ids(cls, identifiers: tuple[_Identifier, ...]) -> tuple[_Identifier, ...]:
        values = [str(identifier) for identifier in identifiers]
        if len(values) != len(set(values)):
            raise ValueError("selection IDs must be unique")
        return identifiers


class BenchmarkModelSnapshot(StrictModel):
    model_id: BenchmarkModelId
    display_name: str = Field(min_length=1, max_length=160)
    configuration: ModelConfig
    configuration_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class BenchmarkDefinitionSnapshot(StrictModel):
    benchmark_id: BenchmarkId
    display_name: str = Field(min_length=1, max_length=160)
    subject_ids: tuple[SubjectId, ...] = Field(min_length=1)
    iterations: int = Field(ge=1, le=100)
    game_policy: GamePolicy
    oracle_configuration: OracleConfig
    validator_configuration: ModelConfig
    definition_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class TrialIdentity(StrictModel):
    execution_id: BenchmarkExecutionId
    model_id: BenchmarkModelId
    target_id: SubjectId
    trial_id: TrialId
    trial_number: int = Field(ge=1)
    episode_run_id: EpisodeRunId


class TrialRepairPolicy(StrictModel):
    """Bounded re-execution of infrastructure-failed trials with unchanged identity."""

    max_attempts_per_trial: int = Field(default=3, ge=1, le=10)


class InfrastructureCircuitBreaker(StrictModel):
    """Stop scheduling new trials after a run of consecutive infrastructure failures."""

    max_consecutive_infrastructure_failures: int = Field(default=5, ge=1, le=100)


class ArtifactFileReference(StrictModel):
    relative_path: str = Field(min_length=1)
    record_count: int = Field(default=1, ge=0)
    integrity_hash: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @field_validator("relative_path")
    @classmethod
    def safe_relative_path(cls, value: str) -> str:
        if value.startswith("/") or ".." in value.split("/"):
            raise ValueError("artifact paths must be safe relative paths")
        return value


class TrialArtifactReferences(StrictModel):
    trial_result: ArtifactFileReference
    error_outputs: ArtifactFileReference | None = None
    episode_result: ArtifactFileReference | None = None
    audit_manifest: ArtifactFileReference | None = None
    episode_events: ArtifactFileReference | None = None
    guesser_calls: ArtifactFileReference | None = None
    oracle_calls: ArtifactFileReference | None = None
    validator_calls: ArtifactFileReference | None = None


class BenchmarkRunArtifactReferences(StrictModel):
    manifest: ArtifactFileReference
    state: ArtifactFileReference
    events: ArtifactFileReference
    result: ArtifactFileReference
    summary_yaml: ArtifactFileReference
    summary_markdown: ArtifactFileReference


class BenchmarkManifest(StrictModel):
    schema_version: Literal[3] = 3
    request: BenchmarkRequest
    definition: BenchmarkDefinitionSnapshot
    model: BenchmarkModelSnapshot
    subject_catalog_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    git_commit: str
    created_at: str
    integrity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def matching_benchmark_mode(self) -> BenchmarkManifest:
        if self.request.benchmark_mode is not self.definition.game_policy.benchmark_mode:
            raise ValueError("request benchmark_mode differs from definition game policy")
        return self


class TrialAuditManifest(StrictModel):
    schema_version: Literal[3] = 3
    identity: TrialIdentity
    subject_catalog_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    subject: Subject
    model: BenchmarkModelSnapshot
    game_policy: GamePolicy
    oracle_configuration: OracleConfig
    validator_configuration: ModelConfig
    created_at: str
    integrity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class BenchmarkFailure(StrictModel):
    code: str = Field(min_length=1, max_length=160)
    type: str = Field(min_length=1, max_length=160)
    message: str = Field(max_length=2_000)
    call_id: ComponentCallId | None = None
    diagnostics: FailureDiagnostics | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )


class ErrorOutputRecord(StrictModel):
    """Private error-only completion record, never part of model-visible state."""

    schema_version: Literal[1] = 1
    component: Literal[
        "guesser",
        "oracle",
        "reviewer",
        "judge",
        "guess_validator",
    ]
    call_id: ComponentCallId
    failure_code: str | None = Field(default=None, min_length=1, max_length=160)
    recovered: bool
    recovery: RecoveryMetrics
    outputs: tuple[ProviderOutputCapture, ...] = Field(min_length=1)
    recorded_at: str


class ErrorOutputPreview(StrictModel):
    """Bounded result-only preview of the latest textual error completion."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=False)

    component: Literal[
        "guesser",
        "oracle",
        "reviewer",
        "judge",
        "guess_validator",
    ]
    attempt_number: int = Field(ge=1)
    finish_reason: str | None = None
    text: str = Field(min_length=1, max_length=ERROR_OUTPUT_PREVIEW_MAX_CHARACTERS)
    original_characters: int = Field(ge=1)
    trailing_whitespace_characters: int = Field(default=0, ge=0)
    truncated: bool

    @model_validator(mode="after")
    def canonical_crop(self) -> ErrorOutputPreview:
        preview_characters = len(self.text)
        if self.original_characters < preview_characters:
            raise ValueError("error-output preview exceeds the original output length")
        if self.trailing_whitespace_characters > self.original_characters:
            raise ValueError("trailing whitespace exceeds the original output length")
        if self.truncated != (self.original_characters > preview_characters):
            raise ValueError("error-output preview truncation flag does not match its lengths")
        if self.truncated and preview_characters != ERROR_OUTPUT_PREVIEW_MAX_CHARACTERS:
            raise ValueError("truncated error-output previews must use the full preview limit")
        return self


class PartialTrialMetrics(StrictModel):
    counted_questions: int = Field(default=0, ge=0)
    guesser_cost_usd: Decimal = Field(default=Decimal(0), ge=0)
    oracle_cost_usd: Decimal = Field(default=Decimal(0), ge=0)
    reviewer_cost_usd: Decimal = Field(default=Decimal(0), ge=0)
    judge_cost_usd: Decimal = Field(default=Decimal(0), ge=0)
    validator_cost_usd: Decimal = Field(default=Decimal(0), ge=0)
    cost_usd: Decimal = Field(default=Decimal(0), ge=0)
    tokens: int = Field(default=0, ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    cache_write_tokens: int = Field(default=0, ge=0)
    estimated_cache_savings_usd: Decimal = Field(default=Decimal(0))
    latency_ms: int = Field(default=0, ge=0)
    duration_ms: int = Field(default=0, ge=0)
    recovery: RecoveryTotals = Field(default_factory=RecoveryTotals)


class SupersededInfrastructureAttempt(StrictModel):
    """One infrastructure-failed attempt retained when repair replaces its result."""

    attempt_number: int = Field(ge=1)
    failure: BenchmarkFailure
    partial_metrics: PartialTrialMetrics
    error_output_preview: ErrorOutputPreview | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    superseded_at: str


class CompletedTrialResult(StrictModel):
    status: Literal["completed"] = "completed"
    identity: TrialIdentity
    attempt_number: int = Field(default=1, ge=1)
    result: EpisodeResult
    failure: BenchmarkFailure | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    error_output_preview: ErrorOutputPreview | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    superseded_attempts: tuple[SupersededInfrastructureAttempt, ...] = ()
    artifacts: TrialArtifactReferences

    @model_validator(mode="after")
    def attempts_precede_terminal_attempt(self) -> CompletedTrialResult:
        attempt_numbers = tuple(
            attempt.attempt_number for attempt in self.superseded_attempts
        )
        if len(set(attempt_numbers)) != len(attempt_numbers):
            raise ValueError("superseded attempt numbers must be unique")
        if any(number >= self.attempt_number for number in attempt_numbers):
            raise ValueError("superseded attempts must precede the terminal attempt")
        return self


class InfrastructureFailedTrialResult(StrictModel):
    status: Literal["infrastructure_failed"] = "infrastructure_failed"
    identity: TrialIdentity
    attempt_number: int = Field(default=1, ge=1)
    failure: BenchmarkFailure
    partial_metrics: PartialTrialMetrics
    error_output_preview: ErrorOutputPreview | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    superseded_attempts: tuple[SupersededInfrastructureAttempt, ...] = ()
    artifacts: TrialArtifactReferences

    @model_validator(mode="after")
    def attempts_precede_terminal_attempt(self) -> InfrastructureFailedTrialResult:
        attempt_numbers = tuple(
            attempt.attempt_number for attempt in self.superseded_attempts
        )
        if len(set(attempt_numbers)) != len(attempt_numbers):
            raise ValueError("superseded attempt numbers must be unique")
        if any(number >= self.attempt_number for number in attempt_numbers):
            raise ValueError("superseded attempts must precede the terminal attempt")
        return self


TrialBenchmarkResult = Annotated[
    CompletedTrialResult | InfrastructureFailedTrialResult,
    Field(discriminator="status"),
]


class DistributionSummary(StrictModel):
    count: int = Field(ge=0)
    minimum: Decimal | None = None
    p25: Decimal | None = None
    median: Decimal | None = None
    p75: Decimal | None = None
    maximum: Decimal | None = None
    mean: Decimal | None = None
    sample_standard_deviation: Decimal | None = None


class ResultCounts(StrictModel):
    scheduled: int = Field(ge=0)
    started: int = Field(ge=0)
    terminal: int = Field(ge=0)
    scoring_eligible: int = Field(ge=0)
    publication_eligible: int = Field(ge=0)
    successful: int = Field(ge=0)
    model_failed: int = Field(ge=0)
    infrastructure_failed: int = Field(ge=0)


class FailureCodeCount(StrictModel):
    code: str = Field(min_length=1, max_length=160)
    count: int = Field(ge=1)


class RepairAggregate(StrictModel):
    superseded_attempts: int = Field(default=0, ge=0)
    affected_trials: int = Field(default=0, ge=0)
    partial_metrics: PartialTrialMetrics = Field(default_factory=PartialTrialMetrics)
    failure_codes: tuple[FailureCodeCount, ...] = ()


class OracleQuestionTypeAggregate(StrictModel):
    question_type: OracleQuestionType
    reviewed_questions: int = Field(default=0, ge=0)
    disagreements: int = Field(default=0, ge=0)
    disagreement_rate: Decimal | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def counts_match_rate(self) -> OracleQuestionTypeAggregate:
        if self.disagreements > self.reviewed_questions:
            raise ValueError("question-type disagreements cannot exceed reviews")
        if (self.disagreement_rate is None) != (self.reviewed_questions == 0):
            raise ValueError("question-type disagreement rate requires reviewed questions")
        return self


class OracleQualityAggregate(StrictModel):
    reviewed_questions: int = Field(default=0, ge=0)
    agreements: int = Field(default=0, ge=0)
    disagreements: int = Field(default=0, ge=0)
    agreement_rate: Decimal | None = Field(default=None, ge=0, le=1)
    disagreement_rate: Decimal | None = Field(default=None, ge=0, le=1)
    judge_invocations: int = Field(default=0, ge=0)
    oracle_answers_changed: int = Field(default=0, ge=0)
    oracle_answer_change_rate: Decimal | None = Field(default=None, ge=0, le=1)
    final_unknown_answers: int = Field(default=0, ge=0)
    judge_yes_answers: int = Field(default=0, ge=0)
    judge_no_answers: int = Field(default=0, ge=0)
    judge_unknown_answers: int = Field(default=0, ge=0)
    reviewer_cost_usd: Decimal = Field(default=Decimal(0), ge=0)
    judge_cost_usd: Decimal = Field(default=Decimal(0), ge=0)
    quality_control_cost_usd: Decimal = Field(default=Decimal(0), ge=0)
    question_types: tuple[OracleQuestionTypeAggregate, ...] = ()

    @model_validator(mode="after")
    def quality_counts_are_consistent(self) -> OracleQualityAggregate:
        if self.agreements + self.disagreements != self.reviewed_questions:
            raise ValueError("reviewed questions must split into agreement and disagreement")
        if self.judge_invocations != self.disagreements:
            raise ValueError("every disagreement must invoke exactly one Judge")
        if self.oracle_answers_changed > self.judge_invocations:
            raise ValueError("changed Oracle answers cannot exceed Judge calls")
        if (
            self.oracle_answer_change_rate is not None
            and self.judge_invocations == 0
        ):
            raise ValueError("Oracle answer change rate requires Judge calls")
        if len({item.question_type for item in self.question_types}) != len(
            self.question_types
        ):
            raise ValueError("question-type aggregates must be unique")
        if self.question_types and (
            sum(item.reviewed_questions for item in self.question_types)
            != self.reviewed_questions
            or sum(item.disagreements for item in self.question_types)
            != self.disagreements
        ):
            raise ValueError("question-type aggregates must match overall quality counts")
        return self


class AggregateSummary(StrictModel):
    counts: ResultCounts
    success_rate: Decimal | None = Field(default=None, ge=0, le=1)
    questions_all_eligible: DistributionSummary
    questions_successful: DistributionSummary
    guesser_cost_usd: DistributionSummary
    oracle_cost_usd: DistributionSummary
    validator_cost_usd: DistributionSummary
    cost_usd: DistributionSummary
    total_cost_usd: Decimal = Field(ge=0)
    tokens: DistributionSummary
    cached_input_tokens: DistributionSummary
    cache_write_tokens: DistributionSummary
    estimated_cache_savings_usd: DistributionSummary
    latency_ms: DistributionSummary
    duration_ms: DistributionSummary
    recovery: RecoveryTotals = Field(default_factory=RecoveryTotals)
    repair: RepairAggregate = Field(default_factory=RepairAggregate)
    contract: GuesserContractReliability = Field(
        default_factory=GuesserContractReliability
    )
    oracle_quality: OracleQualityAggregate = Field(default_factory=OracleQualityAggregate)
    failure_codes: tuple[FailureCodeCount, ...] = ()


class SubjectBenchmarkOutcome(StrictModel):
    complete: bool
    has_infrastructure_failures: bool


class SubjectBenchmarkResult(StrictModel):
    subject: Subject
    outcome: SubjectBenchmarkOutcome
    summary: AggregateSummary
    trials: tuple[TrialBenchmarkResult, ...]


class CompletedTrialSummaryEntry(StrictModel):
    status: Literal["completed"] = "completed"
    identity: TrialIdentity
    success: bool
    scoring_eligible: bool
    publication_eligible: bool
    failure: BenchmarkFailure | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    counted_questions: int = Field(ge=0)
    contract: GuesserContractReliability
    cost_usd: Decimal = Field(ge=0)
    duration_ms: int = Field(ge=0)
    superseded_attempt_count: int = Field(default=0, ge=0)
    artifacts: TrialArtifactReferences


class InfrastructureFailedTrialSummaryEntry(StrictModel):
    status: Literal["infrastructure_failed"] = "infrastructure_failed"
    identity: TrialIdentity
    failure: BenchmarkFailure
    partial_metrics: PartialTrialMetrics
    superseded_attempt_count: int = Field(default=0, ge=0)
    artifacts: TrialArtifactReferences


TrialSummaryEntry = Annotated[
    CompletedTrialSummaryEntry | InfrastructureFailedTrialSummaryEntry,
    Field(discriminator="status"),
]


class SubjectSummaryEntry(StrictModel):
    target_id: SubjectId
    display_name: str = Field(min_length=1, max_length=200)
    entity_type: str = Field(min_length=1, max_length=80)
    outcome: SubjectBenchmarkOutcome
    summary: AggregateSummary
    trials: tuple[TrialSummaryEntry, ...]
    result: ArtifactFileReference
    summary_markdown: ArtifactFileReference


class BenchmarkRun(StrictModel):
    execution_id: BenchmarkExecutionId
    definition: BenchmarkDefinitionSnapshot
    model: BenchmarkModelSnapshot
    base_seed: int = Field(default=0, ge=0, le=(2**31) - 1)
    schedule_order: Literal["subject_trial"] = "subject_trial"
    git_commits: tuple[str, ...] = ()
    started_at: str
    completed_at: str
    duration_ms: int = Field(ge=0)


class BenchmarkOutcome(StrictModel):
    complete: bool
    has_infrastructure_failures: bool
    publication_eligible: bool


class BenchmarkSummaryArtifact(StrictModel):
    schema_version: Literal[3] = 3
    execution_id: BenchmarkExecutionId
    benchmark_id: BenchmarkId
    display_name: str = Field(min_length=1, max_length=160)
    model: BenchmarkModelSnapshot
    outcome: BenchmarkOutcome
    summary: AggregateSummary
    subjects: tuple[SubjectSummaryEntry, ...]
    result: ArtifactFileReference
    summary_markdown: ArtifactFileReference


class BenchmarkResult(StrictModel):
    schema_version: Literal[3] = 3
    run: BenchmarkRun
    outcome: BenchmarkOutcome
    summary: AggregateSummary
    subjects: tuple[SubjectBenchmarkResult, ...]
    artifacts: BenchmarkRunArtifactReferences
    integrity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class ExecutionStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BenchmarkState(StrictModel):
    schema_version: Literal[1] = 1
    execution_id: BenchmarkExecutionId
    model_id: BenchmarkModelId
    status: ExecutionStatus
    scheduled_trials: int = Field(ge=0)
    started_trials: int = Field(ge=0)
    terminal_trials: int = Field(ge=0)
    current_target_id: SubjectId | None = None
    current_trial_id: TrialId | None = None
    current_turn: int | None = Field(default=None, ge=1)
    accumulated_cost_usd: Decimal = Field(default=Decimal(0), ge=0)
    last_failure: BenchmarkFailure | None = None
    updated_at: str


class BenchmarkStartedEvent(StrictModel):
    event_type: Literal["benchmark_started"] = "benchmark_started"
    event_id: BenchmarkEventId
    execution_id: BenchmarkExecutionId
    recorded_at: str


class ModelStartedEvent(StrictModel):
    event_type: Literal["model_started"] = "model_started"
    event_id: BenchmarkEventId
    execution_id: BenchmarkExecutionId
    model_id: BenchmarkModelId
    recorded_at: str


class ExecutionResumedEvent(StrictModel):
    event_type: Literal["execution_resumed"] = "execution_resumed"
    event_id: BenchmarkEventId
    execution_id: BenchmarkExecutionId
    model_id: BenchmarkModelId
    operation: Literal["resume", "repair"]
    git_commit: str
    repair_policy: TrialRepairPolicy | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    recorded_at: str


class SubjectStartedEvent(StrictModel):
    event_type: Literal["subject_started"] = "subject_started"
    event_id: BenchmarkEventId
    execution_id: BenchmarkExecutionId
    model_id: BenchmarkModelId
    target_id: SubjectId
    recorded_at: str


class TrialStartedEvent(StrictModel):
    event_type: Literal["trial_started"] = "trial_started"
    event_id: BenchmarkEventId
    identity: TrialIdentity
    attempt_number: int = Field(default=1, ge=1)
    recorded_at: str


class BenchmarkTurnEvent(StrictModel):
    event_type: Literal["turn_resolved"] = "turn_resolved"
    event_id: BenchmarkEventId
    identity: TrialIdentity
    attempt_number: int = Field(default=1, ge=1)
    progress: TurnProgress
    recorded_at: str


class BenchmarkContractViolationEvent(StrictModel):
    event_type: Literal["contract_violation"] = "contract_violation"
    event_id: BenchmarkEventId
    identity: TrialIdentity
    attempt_number: int = Field(default=1, ge=1)
    progress: ContractViolationProgress
    recorded_at: str


class TrialMetricsResolvedEvent(StrictModel):
    """Complete attempt metrics persisted before the scheduler writes its result."""

    event_type: Literal["trial_metrics_resolved"] = "trial_metrics_resolved"
    event_id: BenchmarkEventId
    identity: TrialIdentity
    attempt_number: int = Field(ge=1)
    partial_metrics: PartialTrialMetrics
    recorded_at: str


class TrialFinishedEvent(StrictModel):
    event_type: Literal["trial_finished"] = "trial_finished"
    event_id: BenchmarkEventId
    identity: TrialIdentity
    attempt_number: int = Field(default=1, ge=1)
    status: Literal["completed", "infrastructure_failed"]
    recorded_at: str


class BenchmarkFinishedEvent(StrictModel):
    event_type: Literal["benchmark_finished"] = "benchmark_finished"
    event_id: BenchmarkEventId
    execution_id: BenchmarkExecutionId
    has_infrastructure_failures: bool
    recorded_at: str


BenchmarkProgressEvent = Annotated[
    BenchmarkStartedEvent
    | ModelStartedEvent
    | ExecutionResumedEvent
    | SubjectStartedEvent
    | TrialStartedEvent
    | BenchmarkTurnEvent
    | BenchmarkContractViolationEvent
    | TrialMetricsResolvedEvent
    | TrialFinishedEvent
    | BenchmarkFinishedEvent,
    Field(discriminator="event_type"),
]
