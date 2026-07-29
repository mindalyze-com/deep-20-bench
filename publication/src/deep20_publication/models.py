from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    JsonValue,
    RootModel,
    field_validator,
    model_validator,
)


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


SHA256_PATTERN = r"^[0-9a-f]{64}$"
MODEL_ID_PATTERN = r"^M-[0-9]{4}$"
BENCHMARK_ID_PATTERN = r"^B-[0-9]{4}$"
TARGET_ID_PATTERN = r"^T-[0-9]{4}$"
EXECUTION_ID_PATTERN = r"^BX-[A-Za-z0-9][A-Za-z0-9._-]{0,43}$"
TRIAL_ID_PATTERN = r"^trial-[0-9]{3,5}$"
RUN_ID_PATTERN = r"^BR-[0-9a-f]{40}$"
CALL_ID_PATTERN = r"^(?:GC|OC|VC)-[0-9a-f]{32}$"


class JsonObject(RootModel[dict[str, JsonValue]]):
    model_config = ConfigDict(frozen=True)


class PromptCacheSnapshot(FrozenModel):
    policy: str = Field(min_length=1)
    control: str = Field(min_length=1)
    minimum_cacheable_tokens: int = Field(ge=0)
    ttl_seconds: int | None = Field(default=None, ge=0)
    input_usd_per_million: Decimal = Field(ge=0)
    cached_input_usd_per_million: Decimal = Field(ge=0)
    cache_write_multiplier: Decimal = Field(ge=0)


class RecoveryPolicySnapshot(FrozenModel):
    max_elapsed_seconds: int = Field(ge=0, le=300)
    max_request_attempts: int = Field(ge=1, le=8)
    no_result_retries: int = Field(ge=0, le=1)
    invalid_output_retries: int = Field(ge=0, le=1)
    rate_limit_max_elapsed_seconds: int = Field(ge=0, le=3_600)
    rate_limit_max_request_attempts: int = Field(ge=1, le=50)
    retry_jitter_ms: int = Field(ge=0, le=10_000)


class RecoveryUsageSnapshot(FrozenModel):
    input_tokens: int = Field(default=0, ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    cache_write_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    reasoning_tokens: int = Field(default=0, ge=0)
    search_count: int = Field(default=0, ge=0)
    cost_usd: Decimal | None = Field(default=None, ge=0)
    cache_discount_usd: Decimal | None = None


class RecoveryReasonCountSnapshot(FrozenModel):
    reason: str = Field(min_length=1, max_length=160)
    count: int = Field(ge=1)


class RecoveryTotalsSnapshot(FrozenModel):
    request_attempts: int = Field(default=0, ge=0)
    retried_calls: int = Field(default=0, ge=0)
    recovered_calls: int = Field(default=0, ge=0)
    exhausted_retries: int = Field(default=0, ge=0)
    reasons: tuple[RecoveryReasonCountSnapshot, ...] = ()
    retry_usage: RecoveryUsageSnapshot = Field(default_factory=RecoveryUsageSnapshot)
    retry_latency_ms: int = Field(default=0, ge=0)


class ModelConfigurationSnapshot(FrozenModel):
    configuration_id: str = Field(min_length=1, max_length=160)
    gateway: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=240)
    provider: str = Field(min_length=1, max_length=120)
    reasoning_effort: str = Field(min_length=1, max_length=80)
    reasoning_control: Literal["effort", "generic"] = Field(
        default="effort",
        exclude_if=lambda value: value == "effort",
    )
    allow_fallbacks: bool
    max_output_tokens: int = Field(ge=1)
    timeout_seconds: int = Field(ge=1)
    recovery: RecoveryPolicySnapshot
    seed_capability: str = Field(min_length=1, max_length=80)
    prompt_cache: PromptCacheSnapshot

class ModelSnapshot(FrozenModel):
    model_id: str = Field(pattern=MODEL_ID_PATTERN)
    display_name: str = Field(min_length=1, max_length=160)
    configuration: ModelConfigurationSnapshot
    configuration_hash: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def matching_configuration_id(self) -> ModelSnapshot:
        if self.configuration.configuration_id != self.model_id:
            raise ValueError("model configuration_id must match model_id")
        return self


class ArtifactReference(FrozenModel):
    relative_path: str = Field(min_length=1)
    record_count: int = Field(default=1, ge=0)
    integrity_hash: str | None = Field(default=None, pattern=SHA256_PATTERN)

    @field_validator("relative_path")
    @classmethod
    def safe_relative_path(cls, value: str) -> str:
        if value.startswith("/") or ".." in value.split("/"):
            raise ValueError("artifact reference must be a safe relative path")
        return value


class TrialArtifactReferences(FrozenModel):
    trial_result: ArtifactReference
    error_outputs: ArtifactReference | None = None
    episode_result: ArtifactReference | None = None
    audit_manifest: ArtifactReference | None = None
    episode_events: ArtifactReference | None = None
    guesser_calls: ArtifactReference | None = None
    oracle_calls: ArtifactReference | None = None
    validator_calls: ArtifactReference | None = None


class TrialIdentity(FrozenModel):
    execution_id: str = Field(pattern=EXECUTION_ID_PATTERN)
    model_id: str = Field(pattern=MODEL_ID_PATTERN)
    target_id: str = Field(pattern=TARGET_ID_PATTERN)
    trial_id: str = Field(pattern=TRIAL_ID_PATTERN)
    trial_number: int = Field(ge=1)
    episode_run_id: str = Field(pattern=RUN_ID_PATTERN)


class BenchmarkFailure(FrozenModel):
    code: str = Field(min_length=1, max_length=160)
    type: str = Field(min_length=1, max_length=160)
    message: str = Field(max_length=2_000)
    call_id: str | None = Field(default=None, pattern=CALL_ID_PATTERN)
    diagnostics: JsonObject | None = None


class ErrorOutputPreview(FrozenModel):
    component: Literal[
        "guesser",
        "oracle",
        "reviewer",
        "judge",
        "guess_validator",
    ]
    attempt_number: int = Field(ge=1)
    finish_reason: str | None = None
    text: str = Field(min_length=1, max_length=250)
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
        if self.truncated and preview_characters != 250:
            raise ValueError("truncated error-output previews must use the full preview limit")
        return self


class PartialTrialMetrics(FrozenModel):
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
    estimated_cache_savings_usd: Decimal = Decimal(0)
    latency_ms: int = Field(default=0, ge=0)
    duration_ms: int = Field(default=0, ge=0)
    recovery: RecoveryTotalsSnapshot = Field(default_factory=RecoveryTotalsSnapshot)


class SupersededInfrastructureAttemptSnapshot(FrozenModel):
    attempt_number: int = Field(ge=1)
    failure: BenchmarkFailure
    partial_metrics: PartialTrialMetrics
    error_output_preview: ErrorOutputPreview | None = None
    superseded_at: datetime


class ContractReliabilitySnapshot(FrozenModel):
    evaluated_outputs: int = Field(ge=0)
    valid_outputs: int = Field(ge=0)
    violations: int = Field(ge=0)
    counted_penalties: int = Field(ge=0)
    affected_trials: int = Field(ge=0)
    compliance_rate: Decimal | None = Field(default=None, ge=0, le=1)
    status: Literal["clean", "breached", "not_evaluable"]

    @model_validator(mode="after")
    def counts_and_status_match(self) -> ContractReliabilitySnapshot:
        if self.valid_outputs + self.violations != self.evaluated_outputs:
            raise ValueError("valid outputs plus violations must equal evaluated outputs")
        if self.counted_penalties > self.violations:
            raise ValueError("counted contract penalties cannot exceed violations")
        if self.evaluated_outputs == 0:
            if self.compliance_rate is not None or self.status != "not_evaluable":
                raise ValueError("unevaluated contract reliability must be not_evaluable")
        else:
            expected_rate = Decimal(self.valid_outputs) / Decimal(self.evaluated_outputs)
            expected_status = "breached" if self.violations else "clean"
            if self.compliance_rate != expected_rate or self.status != expected_status:
                raise ValueError("contract compliance rate or status does not match counts")
        return self


class CompletedTrialSummary(FrozenModel):
    status: Literal["completed"] = "completed"
    identity: TrialIdentity
    success: bool
    scoring_eligible: bool
    publication_eligible: bool
    failure: BenchmarkFailure | None = None
    counted_questions: int = Field(ge=0)
    contract: ContractReliabilitySnapshot
    cost_usd: Decimal = Field(ge=0)
    duration_ms: int = Field(ge=0)
    superseded_attempt_count: int = Field(default=0, ge=0)
    artifacts: TrialArtifactReferences


class InfrastructureFailedTrialSummary(FrozenModel):
    status: Literal["infrastructure_failed"] = "infrastructure_failed"
    identity: TrialIdentity
    failure: BenchmarkFailure
    partial_metrics: PartialTrialMetrics
    superseded_attempt_count: int = Field(default=0, ge=0)
    artifacts: TrialArtifactReferences


TrialSummary = Annotated[
    CompletedTrialSummary | InfrastructureFailedTrialSummary,
    Field(discriminator="status"),
]


class DistributionSummary(FrozenModel):
    count: int = Field(ge=0)
    minimum: Decimal | None = None
    p25: Decimal | None = None
    median: Decimal | None = None
    p75: Decimal | None = None
    maximum: Decimal | None = None
    mean: Decimal | None = None
    sample_standard_deviation: Decimal | None = None


class ResultCounts(FrozenModel):
    scheduled: int = Field(ge=0)
    started: int = Field(ge=0)
    terminal: int = Field(ge=0)
    scoring_eligible: int = Field(ge=0)
    publication_eligible: int = Field(ge=0)
    successful: int = Field(ge=0)
    model_failed: int = Field(ge=0)
    infrastructure_failed: int = Field(ge=0)


class FailureCodeCount(FrozenModel):
    code: str = Field(min_length=1, max_length=160)
    count: int = Field(ge=1)


class RepairAggregateSnapshot(FrozenModel):
    superseded_attempts: int = Field(default=0, ge=0)
    affected_trials: int = Field(default=0, ge=0)
    partial_metrics: PartialTrialMetrics = Field(default_factory=PartialTrialMetrics)
    failure_codes: tuple[FailureCodeCount, ...] = ()


OracleQuestionType = Literal[
    "temporal_comparison",
    "quantitative_comparison",
    "negation",
    "other",
]


class OracleQuestionTypeAggregateSnapshot(FrozenModel):
    question_type: OracleQuestionType
    reviewed_questions: int = Field(default=0, ge=0)
    disagreements: int = Field(default=0, ge=0)
    disagreement_rate: Decimal | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def counts_match_rate(self) -> OracleQuestionTypeAggregateSnapshot:
        if self.disagreements > self.reviewed_questions:
            raise ValueError("question-type disagreements cannot exceed reviews")
        if (self.disagreement_rate is None) != (self.reviewed_questions == 0):
            raise ValueError("question-type disagreement rate requires reviewed questions")
        return self


class OracleQualityAggregateSnapshot(FrozenModel):
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
    question_types: tuple[OracleQuestionTypeAggregateSnapshot, ...] = ()

    @model_validator(mode="after")
    def quality_counts_are_consistent(self) -> OracleQualityAggregateSnapshot:
        if self.agreements + self.disagreements != self.reviewed_questions:
            raise ValueError("reviewed questions must split into agreement and disagreement")
        if self.judge_invocations != self.disagreements:
            raise ValueError("every disagreement must invoke exactly one Judge")
        if (
            self.judge_yes_answers
            + self.judge_no_answers
            + self.judge_unknown_answers
            != self.judge_invocations
        ):
            raise ValueError("Judge answer distribution must match Judge invocations")
        if self.oracle_answers_changed > self.judge_invocations:
            raise ValueError("only Judge decisions may change an Oracle answer")
        if self.quality_control_cost_usd != (
            self.reviewer_cost_usd + self.judge_cost_usd
        ):
            raise ValueError("quality-control cost must equal Reviewer plus Judge cost")
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


class AggregateSummary(FrozenModel):
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
    recovery: RecoveryTotalsSnapshot = Field(default_factory=RecoveryTotalsSnapshot)
    repair: RepairAggregateSnapshot = Field(default_factory=RepairAggregateSnapshot)
    contract: ContractReliabilitySnapshot
    oracle_quality: OracleQualityAggregateSnapshot
    failure_codes: tuple[FailureCodeCount, ...] = ()


class SubjectOutcome(FrozenModel):
    complete: bool
    has_infrastructure_failures: bool


class SubjectSummary(FrozenModel):
    target_id: str = Field(pattern=TARGET_ID_PATTERN)
    display_name: str = Field(min_length=1, max_length=200)
    entity_type: str = Field(min_length=1, max_length=80)
    outcome: SubjectOutcome
    summary: AggregateSummary
    trials: tuple[TrialSummary, ...]
    result: ArtifactReference
    summary_markdown: ArtifactReference

    @model_validator(mode="after")
    def consistent_trials(self) -> SubjectSummary:
        if len(self.trials) != self.summary.counts.terminal:
            raise ValueError("subject trial count differs from terminal count")
        for trial in self.trials:
            if trial.identity.target_id != self.target_id:
                raise ValueError("trial target differs from subject target")
        return self


class BenchmarkOutcome(FrozenModel):
    complete: bool
    has_infrastructure_failures: bool
    publication_eligible: bool


class BenchmarkSummaryArtifact(FrozenModel):
    schema_version: Literal[3] = 3
    execution_id: str = Field(pattern=EXECUTION_ID_PATTERN)
    benchmark_id: str = Field(pattern=BENCHMARK_ID_PATTERN)
    display_name: str = Field(min_length=1, max_length=160)
    model: ModelSnapshot
    outcome: BenchmarkOutcome
    summary: AggregateSummary
    subjects: tuple[SubjectSummary, ...]
    result: ArtifactReference
    summary_markdown: ArtifactReference

    @model_validator(mode="after")
    def consistent_identity_and_counts(self) -> BenchmarkSummaryArtifact:
        if self.model.model_id not in self.result.relative_path.split("/"):
            raise ValueError("result reference does not contain model_id")
        terminal = sum(subject.summary.counts.terminal for subject in self.subjects)
        if terminal != self.summary.counts.terminal:
            raise ValueError("subject terminal counts differ from benchmark terminal count")
        for subject in self.subjects:
            for trial in subject.trials:
                if trial.identity.execution_id != self.execution_id:
                    raise ValueError("trial execution differs from summary execution")
                if trial.identity.model_id != self.model.model_id:
                    raise ValueError("trial model differs from summary model")
        return self


class BenchmarkSummaryEnvelope(FrozenModel):
    payload: BenchmarkSummaryArtifact
    integrity_hash: str = Field(pattern=SHA256_PATTERN)


class BenchmarkRequestSnapshot(FrozenModel):
    benchmark_id: str = Field(pattern=BENCHMARK_ID_PATTERN)
    execution_id: str = Field(pattern=EXECUTION_ID_PATTERN)
    model_id: str = Field(pattern=MODEL_ID_PATTERN)
    benchmark_mode: Literal["official", "experimental"]
    target_ids: tuple[str, ...]
    iterations_override: int | None = Field(default=None, ge=1, le=100)
    base_seed: int = Field(ge=0, le=(2**31) - 1)

    @field_validator("target_ids")
    @classmethod
    def valid_target_ids(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("target_ids must be unique")
        if any(re.fullmatch(TARGET_ID_PATTERN, value) is None for value in values):
            raise ValueError("invalid target_id")
        return values


class GamePolicySnapshot(FrozenModel):
    version: Literal[9] = 9
    benchmark_mode: Literal["official", "experimental"]
    max_questions: int = Field(ge=1)
    max_consecutive_contract_violations: int = Field(ge=1)
    reveal_entity_type: bool
    final_guess_after_limit: bool
    include_oracle_evidence: bool
    include_guesser_conversation: bool


class BenchmarkDefinitionSnapshot(FrozenModel):
    benchmark_id: str = Field(pattern=BENCHMARK_ID_PATTERN)
    display_name: str = Field(min_length=1, max_length=160)
    subject_ids: tuple[str, ...]
    iterations: int = Field(ge=1, le=100)
    game_policy: GamePolicySnapshot
    oracle_configuration: JsonObject
    validator_configuration: ModelConfigurationSnapshot
    definition_hash: str = Field(pattern=SHA256_PATTERN)

    @field_validator("subject_ids")
    @classmethod
    def valid_subject_ids(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("subject_ids must be unique")
        if any(re.fullmatch(TARGET_ID_PATTERN, value) is None for value in values):
            raise ValueError("invalid subject_id")
        return values


class BenchmarkManifestArtifact(FrozenModel):
    schema_version: Literal[3] = 3
    request: BenchmarkRequestSnapshot
    definition: BenchmarkDefinitionSnapshot
    model: ModelSnapshot
    subject_catalog_hash: str = Field(pattern=SHA256_PATTERN)
    git_commit: str = Field(min_length=1, max_length=160)
    created_at: datetime
    integrity_hash: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def matching_benchmark_mode(self) -> BenchmarkManifestArtifact:
        if self.request.benchmark_mode != self.definition.game_policy.benchmark_mode:
            raise ValueError("request benchmark_mode differs from definition game policy")
        return self


class BenchmarkStateArtifact(FrozenModel):
    schema_version: Literal[1] = 1
    execution_id: str = Field(pattern=EXECUTION_ID_PATTERN)
    model_id: str = Field(pattern=MODEL_ID_PATTERN)
    status: Literal["running", "completed", "failed"]
    scheduled_trials: int = Field(ge=0)
    started_trials: int = Field(ge=0)
    terminal_trials: int = Field(ge=0)
    current_target_id: str | None = None
    current_trial_id: str | None = None
    current_turn: int | None = Field(default=None, ge=1)
    accumulated_cost_usd: Decimal = Field(ge=0)
    last_failure: BenchmarkFailure | None = None
    updated_at: datetime


class BenchmarkStateEnvelope(FrozenModel):
    payload: BenchmarkStateArtifact
    integrity_hash: str = Field(pattern=SHA256_PATTERN)


class EpisodeAction(FrozenModel):
    action: Literal["ASK", "GUESS"]
    question: str | None = Field(default=None, min_length=1, max_length=1_000)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=1_000)

    @model_validator(mode="after")
    def fields_match_action(self) -> EpisodeAction:
        if self.action == "ASK":
            if self.question is None or self.name is not None or self.description is not None:
                raise ValueError("ASK requires question and null name/description")
        elif self.question is not None or self.name is None or self.description is None:
            raise ValueError("GUESS requires name/description and null question")
        return self


class EpisodeEvidence(FrozenModel):
    source_url: HttpUrl
    excerpt: str = Field(min_length=1, max_length=2_000)
    validation: Literal["model_reported"]


class EvidenceDecisionBasisSnapshot(StrEnum):
    EVIDENCE = "evidence"
    MODEL_KNOWLEDGE = "model_knowledge"


class EvidenceReviewDecisionSnapshot(FrozenModel):
    answer: Literal["YES", "NO", "UNKNOWN"]
    basis: EvidenceDecisionBasisSnapshot
    evidence_indices: tuple[int, ...] = ()

    @field_validator("evidence_indices")
    @classmethod
    def valid_unique_indices(cls, indices: tuple[int, ...]) -> tuple[int, ...]:
        if any(index < 1 for index in indices):
            raise ValueError("evidence indices are one-based positive integers")
        if len(indices) != len(set(indices)):
            raise ValueError("evidence indices must be unique")
        return indices

    @model_validator(mode="after")
    def support_matches_answer(self) -> EvidenceReviewDecisionSnapshot:
        if self.answer == "UNKNOWN" and self.evidence_indices:
            raise ValueError("UNKNOWN must not identify supporting evidence")
        if (
            self.answer == "UNKNOWN"
            and self.basis is EvidenceDecisionBasisSnapshot.MODEL_KNOWLEDGE
        ):
            raise ValueError("UNKNOWN cannot use model knowledge as its decision basis")
        if (
            self.answer != "UNKNOWN"
            and self.basis is EvidenceDecisionBasisSnapshot.EVIDENCE
            and not self.evidence_indices
        ):
            raise ValueError(
                "evidence-based YES and NO require supporting evidence indices"
            )
        if (
            self.basis is EvidenceDecisionBasisSnapshot.MODEL_KNOWLEDGE
            and self.evidence_indices
        ):
            raise ValueError(
                "model-knowledge decisions must not identify supporting evidence"
            )
        return self


class OracleAdjudicationSnapshot(FrozenModel):
    oracle_answer: Literal["YES", "NO", "UNKNOWN"]
    question_type: OracleQuestionType = "other"
    reviewer: EvidenceReviewDecisionSnapshot | None = None
    judge: EvidenceReviewDecisionSnapshot | None = None
    disagreement: bool
    judge_invoked: bool
    final_answer: Literal["YES", "NO", "UNKNOWN"]
    decision_path: Literal[
        "oracle_unknown",
        "reviewer_agreement",
        "judge_disagreement",
    ]

    @model_validator(mode="after")
    def decisions_match_path(self) -> OracleAdjudicationSnapshot:
        if self.oracle_answer == "UNKNOWN":
            if (
                self.reviewer is not None
                or self.judge is not None
                or self.disagreement
                or self.judge_invoked
                or self.final_answer != "UNKNOWN"
                or self.decision_path != "oracle_unknown"
            ):
                raise ValueError("Oracle UNKNOWN must bypass review and remain final")
            return self
        if self.reviewer is None:
            raise ValueError("Oracle YES and NO require a Reviewer decision")
        expected_disagreement = self.reviewer.answer != self.oracle_answer
        if self.disagreement != expected_disagreement:
            raise ValueError("disagreement does not match Oracle and Reviewer decisions")
        if expected_disagreement:
            if (
                self.judge is None
                or not self.judge_invoked
                or self.final_answer != self.judge.answer
                or self.decision_path != "judge_disagreement"
            ):
                raise ValueError("disagreement requires a final Judge decision")
        elif (
            self.judge is not None
            or self.judge_invoked
            or self.final_answer != self.oracle_answer
            or self.decision_path != "reviewer_agreement"
        ):
            raise ValueError("agreement must bypass the Judge and keep the shared answer")
        return self


class EpisodeTurnAdjudication(FrozenModel):
    component: Literal["oracle", "guess_validator"]
    call_id: str = Field(pattern=CALL_ID_PATTERN)
    answer: Literal["YES", "NO", "UNKNOWN"]
    evidence: tuple[EpisodeEvidence, ...] = ()
    explanation: str | None = Field(default=None, max_length=2_000)
    oracle_quality: OracleAdjudicationSnapshot | None = None

    @model_validator(mode="after")
    def details_match_component(self) -> EpisodeTurnAdjudication:
        if self.component == "oracle":
            if self.explanation is not None:
                raise ValueError("Oracle adjudication cannot contain a validator explanation")
            if self.oracle_quality is None:
                raise ValueError("Oracle adjudication requires quality-control decisions")
            if self.answer != self.oracle_quality.final_answer:
                raise ValueError("Oracle turn answer must equal the final quality-control answer")
        elif self.evidence or self.oracle_quality is not None:
            raise ValueError(
                "Guess Validator adjudication cannot contain Oracle evidence or quality data"
            )
        return self


class EpisodeActionTurn(FrozenModel):
    turn_type: Literal["action"] = "action"
    turn_number: int = Field(ge=1)
    action: EpisodeAction
    adjudication: EpisodeTurnAdjudication
    counted: bool
    counted_questions: int = Field(ge=0)
    guesser_call_id: str = Field(pattern=CALL_ID_PATTERN)


class EpisodeContractViolationTurn(FrozenModel):
    turn_type: Literal["contract_violation"] = "contract_violation"
    turn_number: int = Field(ge=1)
    violation_code: Literal["invalid_guesser_output"]
    violation_kind: Literal[
        "invalid_json",
        "invalid_action",
        "output_limit_exceeded",
        "empty_output",
        "incomplete_output",
    ]
    feedback_event: Literal["FORMAT_ERROR"] | None
    counted: bool
    counted_questions: int = Field(ge=0)
    guesser_call_id: str = Field(pattern=CALL_ID_PATTERN)

    @model_validator(mode="after")
    def feedback_matches_counted_turn(self) -> EpisodeContractViolationTurn:
        if self.counted != (self.feedback_event == "FORMAT_ERROR"):
            raise ValueError("only counted contract violations receive FORMAT_ERROR")
        return self


EpisodeTurn = Annotated[
    EpisodeActionTurn | EpisodeContractViolationTurn,
    Field(discriminator="turn_type"),
]


class EpisodeRunSubject(FrozenModel):
    target_id: str = Field(pattern=TARGET_ID_PATTERN)
    canonical_name: str = Field(min_length=1, max_length=200)
    aliases: tuple[str, ...] = ()
    entity_type: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=2_000)
    reference_url: HttpUrl | None = None


class EpisodeRunMetadata(FrozenModel):
    run_id: str = Field(pattern=RUN_ID_PATTERN)
    episode_id: str = Field(pattern=r"^EP-[0-9a-f]{32}$")
    subject: EpisodeRunSubject
    started_at: datetime
    completed_at: datetime
    duration_ms: int = Field(ge=0)


class EpisodeOutcomeDetail(FrozenModel):
    success: bool
    terminal_reason: Literal[
        "success",
        "limit_exhausted",
        "validator_unknown",
        "guesser_protocol_failure",
        "infrastructure_failure",
        "interrupted",
    ]
    scoring_eligible: bool
    publication_eligible: bool


class EpisodeComponentCosts(FrozenModel):
    guesser: Decimal = Field(ge=0)
    oracle: Decimal = Field(ge=0)
    validator: Decimal = Field(ge=0)
    total: Decimal = Field(ge=0)


class EpisodeComponentTokens(FrozenModel):
    guesser: int = Field(ge=0)
    oracle: int = Field(ge=0)
    validator: int = Field(ge=0)
    total: int = Field(ge=0)


class OracleQuestionTypeTotalsSnapshot(FrozenModel):
    question_type: OracleQuestionType
    reviewed_questions: int = Field(default=0, ge=0)
    disagreements: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def disagreements_are_reviewed(self) -> OracleQuestionTypeTotalsSnapshot:
        if self.disagreements > self.reviewed_questions:
            raise ValueError("question-type disagreements cannot exceed reviews")
        return self


class OracleQualityTotalsSnapshot(FrozenModel):
    reviewed_questions: int = Field(default=0, ge=0)
    agreements: int = Field(default=0, ge=0)
    disagreements: int = Field(default=0, ge=0)
    judge_invocations: int = Field(default=0, ge=0)
    oracle_answers_changed: int = Field(default=0, ge=0)
    final_unknown_answers: int = Field(default=0, ge=0)
    judge_yes_answers: int = Field(default=0, ge=0)
    judge_no_answers: int = Field(default=0, ge=0)
    judge_unknown_answers: int = Field(default=0, ge=0)
    reviewer_cost_usd: Decimal = Field(default=Decimal(0), ge=0)
    judge_cost_usd: Decimal = Field(default=Decimal(0), ge=0)
    quality_control_cost_usd: Decimal = Field(default=Decimal(0), ge=0)
    question_types: tuple[OracleQuestionTypeTotalsSnapshot, ...] = ()

    @model_validator(mode="after")
    def counts_and_costs_match(self) -> OracleQualityTotalsSnapshot:
        if self.agreements + self.disagreements != self.reviewed_questions:
            raise ValueError("reviewed questions must split into agreement and disagreement")
        if self.judge_invocations != self.disagreements:
            raise ValueError("every disagreement must invoke exactly one Judge")
        if (
            self.judge_yes_answers
            + self.judge_no_answers
            + self.judge_unknown_answers
            != self.judge_invocations
        ):
            raise ValueError("Judge answer distribution must match Judge invocations")
        if self.oracle_answers_changed > self.judge_invocations:
            raise ValueError("only Judge decisions may change an Oracle answer")
        if self.quality_control_cost_usd != (
            self.reviewer_cost_usd + self.judge_cost_usd
        ):
            raise ValueError("quality-control cost must equal Reviewer plus Judge cost")
        if len({item.question_type for item in self.question_types}) != len(
            self.question_types
        ):
            raise ValueError("question-type quality totals must be unique")
        if self.question_types and (
            sum(item.reviewed_questions for item in self.question_types)
            != self.reviewed_questions
            or sum(item.disagreements for item in self.question_types)
            != self.disagreements
        ):
            raise ValueError("question-type totals must match overall quality totals")
        return self


class EpisodeSummaryDetail(FrozenModel):
    total_turns: int = Field(ge=0)
    counted_questions: int = Field(ge=0)
    guesser_call_count: int = Field(ge=0)
    ask_count: int = Field(ge=0)
    guess_count: int = Field(ge=0)
    rejected_guess_count: int = Field(ge=0)
    oracle_unknown_count: int = Field(ge=0)
    oracle_quality: OracleQualityTotalsSnapshot
    contract: ContractReliabilitySnapshot
    cache_status: Literal["not_applicable", "compliant", "noncompliant"]
    costs_usd: EpisodeComponentCosts
    tokens: EpisodeComponentTokens


class EpisodeModelVersion(FrozenModel):
    role: Literal["guesser", "oracle", "validator"]
    configuration_id: str | None
    requested_model: str = Field(min_length=1)
    requested_provider: str = Field(min_length=1)
    resolved_models: tuple[str, ...]
    resolved_providers: tuple[str, ...]
    reasoning_effort: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)


class EpisodeModelVersions(FrozenModel):
    under_test: EpisodeModelVersion
    oracle: EpisodeModelVersion
    validator: EpisodeModelVersion


class EpisodeComponentMetrics(FrozenModel):
    calls: int = Field(default=0, ge=0)
    cost_usd: Decimal = Field(default=Decimal(0), ge=0)
    latency_ms: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    cache_write_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    reasoning_tokens: int = Field(default=0, ge=0)
    estimated_cache_savings_usd: Decimal = Decimal(0)
    recovery: RecoveryTotalsSnapshot = Field(default_factory=RecoveryTotalsSnapshot)


class EvidenceReviewConfigurationSnapshot(FrozenModel):
    gateway: str = Field(min_length=1)
    model: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    reasoning_effort: str = Field(min_length=1)
    allow_fallbacks: bool
    max_output_tokens: int = Field(ge=1)
    timeout_seconds: int = Field(ge=1)
    recovery: RecoveryPolicySnapshot


class OracleConfigurationSnapshot(EvidenceReviewConfigurationSnapshot):
    parallel_search: bool
    max_search_results: int = Field(ge=1)
    reviewer: EvidenceReviewConfigurationSnapshot
    judge: EvidenceReviewConfigurationSnapshot

class ModelLlmDetail(FrozenModel):
    configuration: ModelConfigurationSnapshot
    metrics: EpisodeComponentMetrics


class OracleLlmDetail(FrozenModel):
    configuration: OracleConfigurationSnapshot
    metrics: EpisodeComponentMetrics


class EpisodeLlmDetails(FrozenModel):
    guesser: ModelLlmDetail
    oracle: OracleLlmDetail
    validator: ModelLlmDetail


class GuesserConversationMessage(FrozenModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=False,
    )

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)
    turn_number: int | None = Field(default=None, ge=1)


class EpisodeTerminalFailure(FrozenModel):
    code: str = Field(min_length=1, max_length=160)
    type: str = Field(min_length=1, max_length=160)
    message: str = Field(max_length=2_000)
    call_id: str | None = Field(default=None, pattern=CALL_ID_PATTERN)
    diagnostics: JsonObject | None = None


class EpisodeResultArtifact(FrozenModel):
    schema_version: Literal[9] = 9
    run: EpisodeRunMetadata
    outcome: EpisodeOutcomeDetail
    summary: EpisodeSummaryDetail
    models: EpisodeModelVersions
    turns: tuple[EpisodeTurn, ...]
    guesser_conversation: tuple[GuesserConversationMessage, ...]
    llm_details: EpisodeLlmDetails
    failure: EpisodeTerminalFailure | None = None

    @model_validator(mode="after")
    def consistent_detail(self) -> EpisodeResultArtifact:
        if self.summary.total_turns != self.summary.guesser_call_count:
            raise ValueError("episode total turns differ from guesser call count")
        unresolved_terminal_attempts = self.summary.total_turns - len(self.turns)
        if unresolved_terminal_attempts not in {0, 1}:
            raise ValueError("episode resolved turn count differs from summary")
        if unresolved_terminal_attempts == 1 and self.outcome.terminal_reason not in {
            "guesser_protocol_failure",
            "infrastructure_failure",
        }:
            raise ValueError("only an exceptional terminal attempt may remain unresolved")
        if self.failure is not None and self.outcome.success:
            raise ValueError("successful episode cannot carry terminal failure")
        return self


class CompletedTrialArtifact(FrozenModel):
    status: Literal["completed"] = "completed"
    identity: TrialIdentity
    attempt_number: int = Field(default=1, ge=1)
    result: EpisodeResultArtifact
    failure: BenchmarkFailure | None = None
    error_output_preview: ErrorOutputPreview | None = None
    superseded_attempts: tuple[SupersededInfrastructureAttemptSnapshot, ...] = ()
    artifacts: TrialArtifactReferences

    @model_validator(mode="after")
    def consistent_episode_identity(self) -> CompletedTrialArtifact:
        if self.identity.episode_run_id != self.result.run.run_id:
            raise ValueError("trial and episode run IDs differ")
        if self.identity.target_id != self.result.run.subject.target_id:
            raise ValueError("trial and episode target IDs differ")
        attempt_numbers = tuple(
            attempt.attempt_number for attempt in self.superseded_attempts
        )
        if len(set(attempt_numbers)) != len(attempt_numbers):
            raise ValueError("superseded attempt numbers must be unique")
        if any(number >= self.attempt_number for number in attempt_numbers):
            raise ValueError("superseded attempts must precede the terminal attempt")
        return self


class CompletedTrialArtifactEnvelope(FrozenModel):
    payload: CompletedTrialArtifact
    integrity_hash: str = Field(pattern=SHA256_PATTERN)


class LoadedEpisode(FrozenModel):
    identity: TrialIdentity
    result: EpisodeResultArtifact
    relative_path: str = Field(min_length=1)
    integrity_hash: str = Field(pattern=SHA256_PATTERN)


class CatalogModel(FrozenModel):
    model_id: str = Field(pattern=MODEL_ID_PATTERN)
    display_name: str = Field(min_length=1, max_length=160)
    configuration: ModelConfigurationSnapshot

    @model_validator(mode="after")
    def matching_ids(self) -> CatalogModel:
        if self.configuration.configuration_id != self.model_id:
            raise ValueError("catalog model and configuration IDs differ")
        return self


class ModelCatalog(FrozenModel):
    version: Literal[3] = 3
    models: dict[str, CatalogModel]

    @model_validator(mode="after")
    def matching_keys(self) -> ModelCatalog:
        if any(key != value.model_id for key, value in self.models.items()):
            raise ValueError("model catalog key differs from model_id")
        return self


class SubjectCatalogEntry(FrozenModel):
    target_id: str = Field(pattern=TARGET_ID_PATTERN)
    canonical_name: str = Field(min_length=1, max_length=200)
    aliases: tuple[str, ...] = ()
    entity_type: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=2_000)
    reference_url: HttpUrl | None = None


class SubjectCatalog(FrozenModel):
    version: Literal[1] = 1
    subjects: dict[str, SubjectCatalogEntry]

    @model_validator(mode="after")
    def matching_keys(self) -> SubjectCatalog:
        if any(key != value.target_id for key, value in self.subjects.items()):
            raise ValueError("subject catalog key differs from target_id")
        return self


class SiteMetadata(FrozenModel):
    title: str = Field(min_length=1, max_length=100)
    short_title: str = Field(min_length=1, max_length=40)
    description: str = Field(min_length=1, max_length=300)
    base_path: str = Field(pattern=r"^/[A-Za-z0-9._/-]*/$")
    creator_name: str = Field(min_length=1, max_length=160)
    citation_label: str = Field(min_length=1, max_length=240)


class B20ScorePolicy(FrozenModel):
    version: Literal["b20-linear-v1"] = "b20-linear-v1"
    target_questions: int = Field(default=20, ge=1, le=1_000)


class ScorePolicy(FrozenModel):
    version: Literal["penalized-mean-v1"] = "penalized-mean-v1"
    failure_penalty_offset: int = Field(default=1, ge=1, le=100)
    b20: B20ScorePolicy


class CohortConfig(FrozenModel):
    cohort_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,63}$")
    display_name: str = Field(min_length=1, max_length=160)
    active: bool = False
    benchmark_id: str = Field(pattern=BENCHMARK_ID_PATTERN)
    benchmark_version: Literal[9] = 9
    target_ids: tuple[str, ...] = Field(min_length=1)
    iterations: int = Field(ge=1, le=100)
    base_seed: int = Field(ge=0, le=(2**31) - 1)
    max_questions: int = Field(ge=1)
    model_ids: tuple[str, ...] = Field(min_length=1)

    @field_validator("target_ids")
    @classmethod
    def valid_targets(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("cohort target_ids must be unique")
        if any(re.fullmatch(TARGET_ID_PATTERN, value) is None for value in values):
            raise ValueError("invalid cohort target_id")
        return values

    @field_validator("model_ids")
    @classmethod
    def valid_models(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("cohort model_ids must be unique")
        if any(re.fullmatch(MODEL_ID_PATTERN, value) is None for value in values):
            raise ValueError("invalid cohort model_id")
        return values


class PublicationConfig(FrozenModel):
    version: Literal[1] = 1
    site: SiteMetadata
    score: ScorePolicy
    cohorts: tuple[CohortConfig, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def exactly_one_active_cohort(self) -> PublicationConfig:
        if sum(cohort.active for cohort in self.cohorts) != 1:
            raise ValueError("publication config requires exactly one active cohort")
        if len({cohort.cohort_id for cohort in self.cohorts}) != len(self.cohorts):
            raise ValueError("cohort IDs must be unique")
        if any(
            cohort.max_questions + self.score.failure_penalty_offset
            <= self.score.b20.target_questions
            for cohort in self.cohorts
        ):
            raise ValueError(
                "B20 target must be below every cohort's failure penalty"
            )
        return self

    @property
    def active_cohort(self) -> CohortConfig:
        return next(cohort for cohort in self.cohorts if cohort.active)


class LoadedRun(FrozenModel):
    summary: BenchmarkSummaryArtifact
    manifest: BenchmarkManifestArtifact
    state: BenchmarkStateArtifact
    episodes: tuple[LoadedEpisode, ...] = ()
    summary_path: str = Field(min_length=1)

    @model_validator(mode="after")
    def matching_artifacts(self) -> LoadedRun:
        identities = {
            self.summary.execution_id,
            self.manifest.request.execution_id,
            self.state.execution_id,
        }
        models = {
            self.summary.model.model_id,
            self.manifest.request.model_id,
            self.manifest.model.model_id,
            self.state.model_id,
        }
        if len(identities) != 1 or len(models) != 1:
            raise ValueError("run artifacts disagree on execution or model identity")
        if (
            self.summary.model.configuration_hash
            != self.manifest.model.configuration_hash
        ):
            raise ValueError("summary and manifest model configurations differ")
        if self.summary.benchmark_id != self.manifest.definition.benchmark_id:
            raise ValueError("summary and manifest benchmark IDs differ")
        expected = {
            (
                trial.identity.target_id,
                trial.identity.trial_id,
                trial.identity.episode_run_id,
            )
            for subject in self.summary.subjects
            for trial in subject.trials
            if isinstance(trial, CompletedTrialSummary)
        }
        actual = {
            (
                episode.identity.target_id,
                episode.identity.trial_id,
                episode.identity.episode_run_id,
            )
            for episode in self.episodes
        }
        if actual and actual != expected:
            raise ValueError("loaded episode details do not match completed summary trials")
        return self


class PublicEvidence(FrozenModel):
    source_url: HttpUrl
    excerpt: str
    validation: Literal["model_reported"]


class PublicActionTurn(FrozenModel):
    turn_type: Literal["action"] = "action"
    turn_number: int
    action: Literal["ASK", "GUESS"]
    question: str | None
    guess_name: str | None
    guess_description: str | None
    adjudicator: Literal["oracle", "guess_validator"]
    answer: Literal["YES", "NO", "UNKNOWN"]
    validator_explanation: str | None
    counted: bool
    counted_questions: int
    evidence: tuple[PublicEvidence, ...]
    recorded_output: str | None


class PublicContractViolationTurn(FrozenModel):
    turn_type: Literal["contract_violation"] = "contract_violation"
    turn_number: int
    violation_code: Literal["invalid_guesser_output"]
    violation_kind: Literal[
        "invalid_json",
        "invalid_action",
        "output_limit_exceeded",
        "empty_output",
        "incomplete_output",
    ]
    feedback_event: Literal["FORMAT_ERROR"] | None
    counted: bool
    counted_questions: int


PublicTurn = Annotated[
    PublicActionTurn | PublicContractViolationTurn,
    Field(discriminator="turn_type"),
]


class PublicEpisodeModelVersion(FrozenModel):
    role: Literal["guesser", "oracle", "validator"]
    configuration_id: str | None
    requested_model: str
    requested_provider: str
    resolved_models: tuple[str, ...]
    resolved_providers: tuple[str, ...]
    reasoning_effort: str
    prompt_version: str


class PublicComponentTelemetry(FrozenModel):
    calls: int
    cost_usd: Decimal
    latency_ms: int
    total_tokens: int
    input_tokens: int
    cached_input_tokens: int
    cache_write_tokens: int
    output_tokens: int
    reasoning_tokens: int
    estimated_cache_savings_usd: Decimal


class PublicEpisodeTelemetry(FrozenModel):
    guesser: PublicComponentTelemetry
    oracle: PublicComponentTelemetry
    validator: PublicComponentTelemetry


class PublicOracleSupportRole(FrozenModel):
    requested_model: str
    requested_provider: str
    reasoning_effort: str
    calls: int = Field(ge=0)
    cost_usd: Decimal = Field(ge=0)


class PublicOracleSupportUsage(FrozenModel):
    oracle: PublicOracleSupportRole
    reviewer: PublicOracleSupportRole
    judge: PublicOracleSupportRole


class PublicGuesserDisclosure(FrozenModel):
    system_message: str
    begin_message: str
    output_storage: Literal["canonical_structured_action"] = (
        "canonical_structured_action"
    )


class PublicEpisodeDetail(FrozenModel):
    episode_run_id: str
    episode_id: str
    subject_name: str
    subject_description: str
    subject_reference_url: HttpUrl | None
    started_at: datetime
    completed_at: datetime
    duration_ms: int
    success: bool
    terminal_reason: str
    scoring_eligible: bool
    publication_eligible: bool
    total_turns: int
    counted_questions: int
    ask_count: int
    guess_count: int
    rejected_guess_count: int
    oracle_unknown_count: int
    cache_status: str
    total_cost_usd: Decimal
    total_tokens: int
    contract: ContractReliabilitySnapshot
    models: tuple[PublicEpisodeModelVersion, ...]
    oracle_support: PublicOracleSupportUsage
    guesser_disclosure: PublicGuesserDisclosure | None
    telemetry: PublicEpisodeTelemetry
    turns: tuple[PublicTurn, ...]


class PublicTrial(FrozenModel):
    trial_id: str
    trial_number: int
    status: Literal["success", "model_failure", "infrastructure_failure"]
    counted_questions: int
    scored_questions: Decimal | None
    b20_score: Decimal | None
    cost_usd: Decimal
    duration_ms: int
    contract: ContractReliabilitySnapshot | None
    failure_code: str | None = None
    episode: PublicEpisodeDetail | None = None


class PublicSubject(FrozenModel):
    target_id: str
    display_name: str
    entity_type: str
    success_rate: Decimal | None
    subject_score: Decimal | None
    b20_score: Decimal | None
    successful: int
    model_failed: int
    infrastructure_failed: int
    contract: ContractReliabilitySnapshot
    trials: tuple[PublicTrial, ...]


class PublicRunCostTotals(FrozenModel):
    guesser: Decimal = Field(ge=0)
    primary_oracle: Decimal = Field(ge=0)
    reviewer: Decimal = Field(ge=0)
    judge: Decimal = Field(ge=0)
    validator: Decimal = Field(ge=0)
    total: Decimal = Field(ge=0)

    @model_validator(mode="after")
    def components_match_total(self) -> PublicRunCostTotals:
        component_total = (
            self.guesser
            + self.primary_oracle
            + self.reviewer
            + self.judge
            + self.validator
        )
        if abs(self.total - component_total) > Decimal("0.00000001"):
            raise ValueError("public run component costs must equal the total")
        return self


class PublicRunTotals(FrozenModel):
    costs_usd: PublicRunCostTotals
    total_tokens: int = Field(ge=0)
    runtime_ms: int = Field(ge=0)
    guesser_think_time_ms: int = Field(ge=0)


class PublicRun(FrozenModel):
    execution_id: str
    model_id: str
    model_name: str
    benchmark_id: str
    benchmark_name: str
    classification: Literal["official", "lab"]
    reason_codes: tuple[str, ...]
    completed_at: datetime
    created_at: datetime
    git_commit: str
    benchmark_mode: str
    target_ids: tuple[str, ...]
    iterations: int
    base_seed: int
    max_questions: int
    success_rate: Decimal | None
    descriptive_score: Decimal | None
    descriptive_b20_score: Decimal | None
    penalized_score: Decimal | None
    b20_score: Decimal | None
    total_cost_usd: Decimal
    successful: int
    model_failed: int
    infrastructure_failed: int
    terminal_trials: int
    contract: ContractReliabilitySnapshot
    totals: PublicRunTotals
    subjects: tuple[PublicSubject, ...]

    @model_validator(mode="after")
    def repeated_total_cost_matches(self) -> PublicRun:
        if self.total_cost_usd != self.totals.costs_usd.total:
            raise ValueError("public run total cost fields disagree")
        return self


class PublicModel(FrozenModel):
    model_id: str
    display_name: str
    route: str
    provider: str
    reasoning_effort: str
    seed_capability: str
    configuration_hash: str


class LeaderboardRow(FrozenModel):
    rank: int | None
    model: PublicModel
    status: Literal["evaluated", "awaiting_official_run"]
    execution_id: str | None = None
    completed_at: datetime | None = None
    penalized_score: Decimal | None = None
    b20_score: Decimal | None = None
    success_rate: Decimal | None = None
    total_cost_usd: Decimal | None = None
    successful: int = 0
    terminal_trials: int = 0
    contract: ContractReliabilitySnapshot | None = None


class Winner(FrozenModel):
    model_ids: tuple[str, ...]
    display_names: tuple[str, ...]
    penalized_score: Decimal
    b20_score: Decimal
    joint: bool


class DatasetProvenance(FrozenModel):
    source_run_count: int = Field(ge=0)
    official_run_count: int = Field(ge=0)
    lab_run_count: int = Field(ge=0)
    latest_completed_at: datetime | None = None
    subject_catalog_hash: str = Field(pattern=SHA256_PATTERN)


class PublishedDataset(FrozenModel):
    schema_version: Literal[3] = 3
    site: SiteMetadata
    score_policy: ScorePolicy
    active_cohort: CohortConfig
    provenance: DatasetProvenance
    winner: Winner | None
    leaderboard: tuple[LeaderboardRow, ...]
    models: tuple[PublicModel, ...]
    official_runs: tuple[PublicRun, ...]
    lab_runs: tuple[PublicRun, ...]
