from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    JsonValue,
    field_validator,
    model_validator,
)

RUN_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"
TARGET_ID_PATTERN = r"^T-[0-9]{4}$"
CALL_ID_PATTERN = r"^OC-[0-9a-f]{32}$"
type JsonObject = dict[str, JsonValue]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class Subject(StrictModel):
    target_id: str = Field(pattern=TARGET_ID_PATTERN)
    canonical_name: str = Field(min_length=1, max_length=200)
    aliases: tuple[str, ...] = Field(default_factory=tuple, max_length=20)
    entity_type: str = Field(min_length=1, max_length=80, pattern=r"^[a-z][a-z0-9_-]*$")
    description: str = Field(min_length=1, max_length=2_000)
    reference_url: HttpUrl | None = None

    @field_validator("aliases")
    @classmethod
    def unique_nonempty_aliases(cls, aliases: tuple[str, ...]) -> tuple[str, ...]:
        if any(not alias or len(alias) > 200 for alias in aliases):
            raise ValueError("aliases must contain 1 to 200 characters")
        normalized = [alias.casefold() for alias in aliases]
        if len(normalized) != len(set(normalized)):
            raise ValueError("aliases must be unique ignoring case")
        return aliases


class OracleRequest(StrictModel):
    run_id: str = Field(pattern=RUN_ID_PATTERN)
    subject: Subject
    question: str = Field(min_length=1, max_length=1_000)


class OracleAnswer(StrEnum):
    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"


class OracleRole(StrEnum):
    ORACLE = "oracle"
    REVIEWER = "reviewer"
    JUDGE = "judge"


class OracleDecisionPath(StrEnum):
    ORACLE_UNKNOWN = "oracle_unknown"
    REVIEWER_AGREEMENT = "reviewer_agreement"
    JUDGE_DISAGREEMENT = "judge_disagreement"


class OracleQuestionType(StrEnum):
    TEMPORAL_COMPARISON = "temporal_comparison"
    QUANTITATIVE_COMPARISON = "quantitative_comparison"
    NEGATION = "negation"
    OTHER = "other"


class OracleResearchQuestionClass(StrEnum):
    TEMPORAL_STATUS = "temporal_status"
    CLOSED_FACT = "closed_fact"
    ROLE_OR_OCCUPATION = "role_or_occupation"
    PRIMARY_RECOGNITION = "primary_recognition"
    OPEN_WORLD_EVER = "open_world_ever"
    ABSENCE_OR_EXCLUSIVITY = "absence_or_exclusivity"
    COUNT_OR_COMPARISON = "count_or_comparison"
    OTHER = "other"


class OracleResearchOutcome(StrEnum):
    ANSWERED = "answered"
    NO_RESULTS = "no_results"
    IRRELEVANT_RESULTS = "irrelevant_results"
    INSUFFICIENT_COVERAGE = "insufficient_coverage"
    CONFLICTING_SOURCES = "conflicting_sources"
    AMBIGUOUS_QUESTION = "ambiguous_question"
    OPEN_WORLD_NOT_PROVABLE = "open_world_not_provable"


class OracleResearchStrategy(StrEnum):
    PRIMARY = "primary"
    DIVERSIFIED_RECOVERY = "diversified_recovery"


class OracleResearchResolution(StrEnum):
    ANSWERED_PRIMARY = "answered_primary"
    ANSWERED_RECOVERY = "answered_recovery"
    GENUINE_UNKNOWN_PRIMARY = "genuine_unknown_primary"
    GENUINE_UNKNOWN_RECOVERY = "genuine_unknown_recovery"
    RETRIEVAL_EXHAUSTED_UNKNOWN = "retrieval_exhausted_unknown"


class RecoveryReason(StrEnum):
    HTTP_400 = "provider_http_400"
    HTTP_408 = "provider_http_408"
    HTTP_429 = "provider_http_429"
    HTTP_500 = "provider_http_500"
    HTTP_502 = "provider_http_502"
    HTTP_503 = "provider_http_503"
    HTTP_504 = "provider_http_504"
    HTTP_524 = "provider_http_524"
    HTTP_529 = "provider_http_529"
    TRANSPORT_ERROR = "provider_transport_error"
    MALFORMED_RESPONSE = "provider_malformed_response"
    EMPTY_RESPONSE = "provider_empty_response"
    INCOMPLETE_RESPONSE = "provider_incomplete_response"
    OUTPUT_LIMIT_EXCEEDED = "provider_output_limit_exceeded"
    INVALID_GUESSER_OUTPUT = "invalid_guesser_output"
    INVALID_ORACLE_OUTPUT = "invalid_oracle_output"
    INVALID_REVIEWER_OUTPUT = "invalid_reviewer_output"
    INVALID_JUDGE_OUTPUT = "invalid_judge_output"
    INVALID_VALIDATOR_OUTPUT = "invalid_validator_output"
    HARD_DEADLINE_EXCEEDED = "provider_hard_deadline_exceeded"


class Evidence(StrictModel):
    source_url: HttpUrl
    excerpt: str = Field(min_length=1, max_length=2_000)
    validation: Literal["model_reported"]

    @model_validator(mode="before")
    @classmethod
    def normalize_provider_url_alias(cls, value: object) -> object:
        """Normalize the provider's common `url` spelling at the validation boundary."""
        if not isinstance(value, dict) or "url" not in value:
            return value
        if "source_url" in value:
            raise ValueError("evidence must not contain both source_url and url")
        return {
            **{key: item for key, item in value.items() if key != "url"},
            "source_url": value["url"],
        }


class OracleResult(StrictModel):
    answer: OracleAnswer
    evidence: tuple[Evidence, ...] = Field(max_length=3)

    @model_validator(mode="after")
    def evidence_matches_answer(self) -> OracleResult:
        if self.answer is OracleAnswer.UNKNOWN and self.evidence:
            raise ValueError("UNKNOWN must not carry answer evidence")
        if self.answer is not OracleAnswer.UNKNOWN and not self.evidence:
            raise ValueError("YES and NO require at least one evidence item")
        return self

    def guesser_answer(self) -> OracleAnswer:
        """Return the only Oracle value permitted in a Guesser prompt."""
        return self.answer


class OracleResearchAttemptResult(StrictModel):
    """One untrusted, web-backed research attempt before final adjudication."""

    answer: OracleAnswer
    evidence: tuple[Evidence, ...] = Field(max_length=3)
    research_outcome: OracleResearchOutcome
    attempted_queries: tuple[str, ...] = Field(min_length=1, max_length=8)

    @field_validator("attempted_queries")
    @classmethod
    def bounded_unique_queries(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(any(ord(character) < 32 for character in value) for value in values):
            raise ValueError("attempted queries must not contain control characters")
        normalized = tuple(" ".join(value.split()) for value in values)
        if any(not value or len(value) > 300 for value in normalized):
            raise ValueError("attempted queries must contain 1 to 300 characters")
        if len({value.casefold() for value in normalized}) != len(normalized):
            raise ValueError("attempted queries must be unique ignoring case")
        return normalized

    @model_validator(mode="after")
    def outcome_matches_answer(self) -> OracleResearchAttemptResult:
        if self.answer is OracleAnswer.UNKNOWN:
            if self.evidence:
                raise ValueError("UNKNOWN research attempts must not carry answer evidence")
            if self.research_outcome is OracleResearchOutcome.ANSWERED:
                raise ValueError("UNKNOWN research attempts cannot be classified as answered")
        else:
            if not self.evidence:
                raise ValueError("YES and NO research attempts require evidence")
            if self.research_outcome is not OracleResearchOutcome.ANSWERED:
                raise ValueError("decisive research attempts must be classified as answered")
        return self

    def final_result(self) -> OracleResult:
        return OracleResult(answer=self.answer, evidence=self.evidence)


class EvidenceReviewRequest(StrictModel):
    subject: Subject
    question: str = Field(min_length=1, max_length=1_000)
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=3)


class EvidenceDecisionBasis(StrEnum):
    EVIDENCE = "evidence"
    MODEL_KNOWLEDGE = "model_knowledge"


class EvidenceReviewResult(StrictModel):
    answer: OracleAnswer
    basis: EvidenceDecisionBasis
    evidence_indices: tuple[int, ...] = Field(default_factory=tuple, max_length=3)

    @field_validator("evidence_indices")
    @classmethod
    def valid_unique_indices(cls, indices: tuple[int, ...]) -> tuple[int, ...]:
        if any(index < 1 for index in indices):
            raise ValueError("evidence indices are one-based positive integers")
        if len(indices) != len(set(indices)):
            raise ValueError("evidence indices must be unique")
        return indices

    @model_validator(mode="after")
    def support_matches_answer(self) -> EvidenceReviewResult:
        if self.answer is OracleAnswer.UNKNOWN and self.evidence_indices:
            raise ValueError("UNKNOWN must not identify supporting evidence")
        if (
            self.answer is OracleAnswer.UNKNOWN
            and self.basis is EvidenceDecisionBasis.MODEL_KNOWLEDGE
        ):
            raise ValueError("UNKNOWN cannot use model knowledge as its decision basis")
        if (
            self.answer is not OracleAnswer.UNKNOWN
            and self.basis is EvidenceDecisionBasis.EVIDENCE
            and not self.evidence_indices
        ):
            raise ValueError("evidence-based YES and NO require supporting evidence indices")
        if self.basis is EvidenceDecisionBasis.MODEL_KNOWLEDGE and self.evidence_indices:
            raise ValueError("model-knowledge decisions must not identify supporting evidence")
        return self

    def validate_evidence_count(self, evidence_count: int) -> EvidenceReviewResult:
        if any(index > evidence_count for index in self.evidence_indices):
            raise ValueError("evidence index exceeds the supplied evidence count")
        return self


class OracleAdjudication(StrictModel):
    oracle_answer: OracleAnswer
    question_type: OracleQuestionType = OracleQuestionType.OTHER
    reviewer: EvidenceReviewResult | None = None
    judge: EvidenceReviewResult | None = None
    disagreement: bool
    judge_invoked: bool
    final_answer: OracleAnswer
    decision_path: OracleDecisionPath

    @model_validator(mode="after")
    def decisions_match_path(self) -> OracleAdjudication:
        if self.oracle_answer is OracleAnswer.UNKNOWN:
            if (
                self.reviewer is not None
                or self.judge is not None
                or self.disagreement
                or self.judge_invoked
                or self.final_answer is not OracleAnswer.UNKNOWN
                or self.decision_path is not OracleDecisionPath.ORACLE_UNKNOWN
            ):
                raise ValueError("Oracle UNKNOWN must bypass review and remain final")
            return self
        if self.reviewer is None:
            raise ValueError("Oracle YES and NO require a Reviewer decision")
        expected_disagreement = self.reviewer.answer is not self.oracle_answer
        if self.disagreement != expected_disagreement:
            raise ValueError("disagreement does not match Oracle and Reviewer decisions")
        if expected_disagreement:
            if (
                self.judge is None
                or not self.judge_invoked
                or self.final_answer is not self.judge.answer
                or self.decision_path is not OracleDecisionPath.JUDGE_DISAGREEMENT
            ):
                raise ValueError("disagreement requires a final Judge decision")
        elif (
            self.judge is not None
            or self.judge_invoked
            or self.final_answer is not self.oracle_answer
            or self.decision_path is not OracleDecisionPath.REVIEWER_AGREEMENT
        ):
            raise ValueError("agreement must bypass the Judge and keep the shared answer")
        return self

    @property
    def oracle_answer_changed(self) -> bool:
        return self.final_answer is not self.oracle_answer


class ProviderUsage(StrictModel):
    input_tokens: int = Field(default=0, ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    cache_write_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    reasoning_tokens: int = Field(default=0, ge=0)
    search_count: int = Field(default=0, ge=0)
    cost_usd: Decimal | None = Field(default=None, ge=0)
    cache_discount_usd: Decimal | None = None


class RecoveryReasonCount(StrictModel):
    reason: RecoveryReason
    count: int = Field(ge=1)


class RecoveryMetrics(StrictModel):
    """Typed recovery accounting with no raw response or private-state channel."""

    request_attempts: int = Field(default=1, ge=1)
    retried_calls: int = Field(default=0, ge=0)
    recovered_calls: int = Field(default=0, ge=0)
    exhausted_retries: int = Field(default=0, ge=0)
    reasons: tuple[RecoveryReasonCount, ...] = ()
    retry_usage: ProviderUsage = Field(default_factory=ProviderUsage)
    retry_latency_ms: int = Field(default=0, ge=0)


class RecoveryTotals(StrictModel):
    request_attempts: int = Field(default=0, ge=0)
    retried_calls: int = Field(default=0, ge=0)
    recovered_calls: int = Field(default=0, ge=0)
    exhausted_retries: int = Field(default=0, ge=0)
    reasons: tuple[RecoveryReasonCount, ...] = ()
    retry_usage: ProviderUsage = Field(default_factory=ProviderUsage)
    retry_latency_ms: int = Field(default=0, ge=0)


class ProviderOutputCapture(StrictModel):
    """One model-visible completion retained solely for error diagnosis."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=False)

    attempt_number: int = Field(ge=1)
    response_id: str | None = None
    finish_reason: str | None = None
    output: str = Field(min_length=1)


class ProviderTrace(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=False)

    requested_at: str
    completed_at: str
    latency_ms: int = Field(ge=0)
    http_status_code: int | None = Field(default=None, ge=100, le=599)
    response_id: str | None = None
    response_cache_status: str | None = None
    finish_reason: str | None = None
    request_attempts: int = Field(default=1, ge=1)
    retry_after_ms: int | None = Field(default=None, ge=0)
    recovery: RecoveryMetrics = Field(default_factory=RecoveryMetrics)
    requested_model: str
    resolved_model: str | None = None
    requested_provider: str
    resolved_provider: str | None = None
    fallback_occurred: bool | None = None
    request: JsonObject
    response: JsonObject | None = None
    raw_output: str | None = None
    discarded_error_outputs: tuple[ProviderOutputCapture, ...] = ()
    annotations: tuple[JsonObject, ...] = ()
    usage: ProviderUsage = Field(default_factory=ProviderUsage)

    @model_validator(mode="after")
    def matching_request_attempts(self) -> ProviderTrace:
        if self.request_attempts != self.recovery.request_attempts:
            raise ValueError("provider request attempts differ from recovery metrics")
        return self

    @field_validator("request", "response", "annotations", mode="before")
    @classmethod
    def normalize_provider_json(cls, value: object) -> object:
        def normalize(item: object) -> object:
            if isinstance(item, tuple):
                return [normalize(child) for child in item]
            if isinstance(item, list):
                return [normalize(child) for child in item]
            if isinstance(item, dict):
                return {str(key): normalize(child) for key, child in item.items()}
            return item

        return normalize(value)


class OracleResearchAttemptSummary(StrictModel):
    attempt_number: int = Field(ge=1, le=2)
    strategy: OracleResearchStrategy
    outcome: OracleResearchOutcome
    attempted_queries: tuple[str, ...] = Field(min_length=1, max_length=8)
    query_provenance: Literal["model_reported"] = "model_reported"
    web_search_requests: int = Field(ge=1)
    annotation_count: int = Field(ge=0)
    evidence_count: int = Field(ge=0, le=3)


class OracleResearchSummary(StrictModel):
    question_class: OracleResearchQuestionClass
    resolution: OracleResearchResolution
    attempts: tuple[OracleResearchAttemptSummary, ...] = Field(
        min_length=1,
        max_length=2,
    )


class OracleResearchAttemptAuditTrace(StrictModel):
    attempt_number: int = Field(ge=1, le=2)
    strategy: OracleResearchStrategy
    prompt_version: str = Field(min_length=1, max_length=160)
    prompt_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    messages: tuple[dict[str, str], ...]
    result: OracleResearchAttemptResult
    provider: ProviderTrace


class OracleResearchAuditTrace(StrictModel):
    question_class: OracleResearchQuestionClass
    resolution: OracleResearchResolution
    attempts: tuple[OracleResearchAttemptAuditTrace, ...] = Field(
        min_length=1,
        max_length=2,
    )

    @model_validator(mode="after")
    def attempts_match_resolution(self) -> OracleResearchAuditTrace:
        expected_numbers = tuple(range(1, len(self.attempts) + 1))
        if tuple(attempt.attempt_number for attempt in self.attempts) != expected_numbers:
            raise ValueError("research attempt numbers must be contiguous and one-based")
        if self.attempts[0].strategy is not OracleResearchStrategy.PRIMARY:
            raise ValueError("the first research attempt must use the primary strategy")
        if len(self.attempts) == 2 and (
            self.attempts[1].strategy is not OracleResearchStrategy.DIVERSIFIED_RECOVERY
        ):
            raise ValueError("the second research attempt must use recovery strategy")
        if (
            self.resolution
            in {
                OracleResearchResolution.ANSWERED_PRIMARY,
                OracleResearchResolution.GENUINE_UNKNOWN_PRIMARY,
            }
            and len(self.attempts) != 1
        ):
            raise ValueError("primary research resolutions require one attempt")
        if (
            self.resolution
            in {
                OracleResearchResolution.ANSWERED_RECOVERY,
                OracleResearchResolution.GENUINE_UNKNOWN_RECOVERY,
                OracleResearchResolution.RETRIEVAL_EXHAUSTED_UNKNOWN,
            }
            and len(self.attempts) != 2
        ):
            raise ValueError("recovery research resolutions require two attempts")
        final_answer = self.attempts[-1].result.answer
        if (
            self.resolution
            in {
                OracleResearchResolution.ANSWERED_PRIMARY,
                OracleResearchResolution.ANSWERED_RECOVERY,
            }
            and final_answer is OracleAnswer.UNKNOWN
        ):
            raise ValueError("answered research resolutions require YES or NO")
        if (
            self.resolution
            in {
                OracleResearchResolution.GENUINE_UNKNOWN_PRIMARY,
                OracleResearchResolution.GENUINE_UNKNOWN_RECOVERY,
                OracleResearchResolution.RETRIEVAL_EXHAUSTED_UNKNOWN,
            }
            and final_answer is not OracleAnswer.UNKNOWN
        ):
            raise ValueError("unknown research resolutions require UNKNOWN")
        primary_outcome = self.attempts[0].result.research_outcome
        retrieval_outcomes = {
            OracleResearchOutcome.NO_RESULTS,
            OracleResearchOutcome.IRRELEVANT_RESULTS,
            OracleResearchOutcome.INSUFFICIENT_COVERAGE,
        }
        retryable_outcomes = {
            *retrieval_outcomes,
            OracleResearchOutcome.CONFLICTING_SOURCES,
        }
        genuine_unknown_outcomes = {
            OracleResearchOutcome.CONFLICTING_SOURCES,
            OracleResearchOutcome.AMBIGUOUS_QUESTION,
            OracleResearchOutcome.OPEN_WORLD_NOT_PROVABLE,
        }
        if len(self.attempts) == 2 and primary_outcome not in retryable_outcomes:
            raise ValueError("recovery requires a retryable primary research outcome")
        final_outcome = self.attempts[-1].result.research_outcome
        if (
            self.resolution is OracleResearchResolution.GENUINE_UNKNOWN_PRIMARY
            and final_outcome
            not in {
                OracleResearchOutcome.AMBIGUOUS_QUESTION,
                OracleResearchOutcome.OPEN_WORLD_NOT_PROVABLE,
            }
        ):
            raise ValueError("genuine primary UNKNOWN requires ambiguity or open-world limits")
        if (
            self.resolution is OracleResearchResolution.GENUINE_UNKNOWN_RECOVERY
            and final_outcome not in genuine_unknown_outcomes
        ):
            raise ValueError("genuine recovery UNKNOWN has an invalid research outcome")
        if (
            self.resolution is OracleResearchResolution.RETRIEVAL_EXHAUSTED_UNKNOWN
            and final_outcome not in retrieval_outcomes
        ):
            raise ValueError("retrieval exhaustion requires a retrieval-failure outcome")
        return self

    def summary(self) -> OracleResearchSummary:
        return OracleResearchSummary(
            question_class=self.question_class,
            resolution=self.resolution,
            attempts=tuple(
                OracleResearchAttemptSummary(
                    attempt_number=attempt.attempt_number,
                    strategy=attempt.strategy,
                    outcome=attempt.result.research_outcome,
                    attempted_queries=attempt.result.attempted_queries,
                    web_search_requests=attempt.provider.usage.search_count,
                    annotation_count=len(attempt.provider.annotations),
                    evidence_count=len(attempt.result.evidence),
                )
                for attempt in self.attempts
            ),
        )


class RouterPipelineStageAudit(StrictModel):
    """Bounded OpenRouter pipeline facts safe for retained benchmark results."""

    stage_type: str = Field(min_length=1, max_length=120)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    mode: str | None = Field(default=None, min_length=1, max_length=120)
    tool_types: tuple[str, ...] = Field(default_factory=tuple, max_length=20)

    @field_validator("tool_types")
    @classmethod
    def bounded_tool_types(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not value or len(value) > 120 for value in values):
            raise ValueError("router tool types must contain 1 to 120 characters")
        return values


class RouterMetadataAudit(StrictModel):
    """Allowlisted router metadata without endpoints, payloads, or free-form data."""

    strategy: str | None = Field(default=None, min_length=1, max_length=160)
    region: str | None = Field(default=None, min_length=1, max_length=120)
    attempt: int | None = Field(default=None, ge=0)
    is_byok: bool | None = None
    endpoint_count: int = Field(default=0, ge=0)
    attempt_count: int = Field(default=0, ge=0)
    pipeline: tuple[RouterPipelineStageAudit, ...] = Field(
        default_factory=tuple,
        max_length=30,
    )


class ProviderResultAudit(StrictModel):
    """Sanitized per-call provider facts retained in an episode result."""

    schema_version: Literal[1] = 1
    requested_at: str
    completed_at: str
    latency_ms: int = Field(ge=0)
    http_status_code: int | None = Field(default=None, ge=100, le=599)
    response_cache_status: str | None = Field(default=None, max_length=120)
    finish_reason: str | None = Field(default=None, max_length=120)
    retry_after_ms: int | None = Field(default=None, ge=0)
    recovery: RecoveryMetrics = Field(default_factory=RecoveryMetrics)
    requested_model: str = Field(min_length=1, max_length=300)
    resolved_model: str | None = Field(default=None, min_length=1, max_length=300)
    requested_provider: str = Field(min_length=1, max_length=300)
    resolved_provider: str | None = Field(default=None, min_length=1, max_length=300)
    fallback_occurred: bool | None = None
    usage: ProviderUsage = Field(default_factory=ProviderUsage)
    web_search_requests: int = Field(default=0, ge=0)
    annotation_count: int = Field(default=0, ge=0)
    url_citation_count: int = Field(default=0, ge=0)
    raw_output_present: bool
    raw_output_characters: int = Field(default=0, ge=0)
    discarded_error_output_count: int = Field(default=0, ge=0)
    router_metadata: RouterMetadataAudit | None = None

    @model_validator(mode="after")
    def search_requests_match_usage(self) -> ProviderResultAudit:
        if self.web_search_requests != self.usage.search_count:
            raise ValueError("web-search request count must match provider usage")
        if self.url_citation_count > self.annotation_count:
            raise ValueError("URL citation count cannot exceed annotation count")
        if self.raw_output_present != (self.raw_output_characters > 0):
            raise ValueError("raw-output presence must match its character count")
        return self


class FailureCause(StrictModel):
    exception_type: str = Field(min_length=1, max_length=200)
    module: str = Field(min_length=1, max_length=300)
    message: str = Field(max_length=2_000)


class FailureFrame(StrictModel):
    exception_index: int = Field(ge=0)
    module: str = Field(min_length=1, max_length=300)
    function: str = Field(min_length=1, max_length=300)
    line: int = Field(ge=1)


class ProviderFailureDiagnostics(StrictModel):
    http_status_code: int | None = Field(default=None, ge=100, le=599)
    error_type: str | None = Field(default=None, max_length=200)
    error_code: str | None = Field(default=None, max_length=200)
    message: str | None = Field(default=None, max_length=2_000)
    requested_model: str
    resolved_model: str | None = None
    requested_provider: str
    resolved_provider: str | None = None
    fallback_occurred: bool | None = None
    response_id: str | None = None
    response_cache_status: str | None = None
    finish_reason: str | None = None
    request_attempts: int = Field(default=1, ge=1)
    retry_after_ms: int | None = Field(default=None, ge=0)
    recovery: RecoveryMetrics = Field(default_factory=RecoveryMetrics)
    latency_ms: int = Field(ge=0)
    usage: ProviderUsage


class FailureDiagnostics(StrictModel):
    causes: tuple[FailureCause, ...] = ()
    frames: tuple[FailureFrame, ...] = ()
    provider: ProviderFailureDiagnostics | None = None
    metadata: JsonObject = Field(default_factory=dict)


class EvidenceReviewAuditTrace(StrictModel):
    role: Literal[OracleRole.REVIEWER, OracleRole.JUDGE]
    prompt_version: str
    prompt_hash: str
    messages: tuple[dict[str, str], ...]
    provider: ProviderTrace


class OracleProviderRoleTrace(StrictModel):
    role: OracleRole
    provider: ProviderTrace


class OracleAuditTrace(StrictModel):
    prompt_version: str
    prompt_hash: str
    messages: tuple[dict[str, str], ...]
    evidence_validation: Literal["model_reported"]
    provider: ProviderTrace
    research: OracleResearchAuditTrace | None = None
    reviewer: EvidenceReviewAuditTrace | None = None
    judge: EvidenceReviewAuditTrace | None = None


class OracleRoleMetrics(StrictModel):
    cost_usd: Decimal | None
    latency_ms: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    cache_write_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(ge=0)
    reasoning_tokens: int = Field(ge=0)
    search_count: int = Field(ge=0)
    recovery: RecoveryMetrics = Field(default_factory=RecoveryMetrics)


class OracleMetrics(OracleRoleMetrics):
    oracle: OracleRoleMetrics | None = None
    reviewer: OracleRoleMetrics | None = None
    judge: OracleRoleMetrics | None = None


class OracleCall(StrictModel):
    schema_version: Literal[5] = 5
    call_id: str = Field(pattern=CALL_ID_PATTERN)
    request: OracleRequest
    result: OracleResult
    adjudication: OracleAdjudication
    metrics: OracleMetrics
    audit: OracleAuditTrace
    recorded_at: str
    integrity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    def guesser_answer(self) -> OracleAnswer:
        """Project the complete call to the safe Guesser-facing answer."""
        return self.adjudication.final_answer


class PersistedRecord(StrictModel):
    """Durable acknowledgement returned by an injected audit sink."""

    record_id: str = Field(min_length=1)
    relative_path: str = Field(min_length=1)
    integrity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
