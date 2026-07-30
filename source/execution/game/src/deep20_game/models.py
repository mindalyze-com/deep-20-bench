from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from deep20_oracle.config import OracleConfig
from deep20_oracle.models import (
    RUN_ID_PATTERN,
    Evidence,
    FailureDiagnostics,
    JsonObject,
    OracleAdjudication,
    OracleAnswer,
    OracleMetrics,
    OracleQuestionType,
    ProviderTrace,
    RecoveryMetrics,
    RecoveryTotals,
    StrictModel,
    Subject,
)
from pydantic import ConfigDict, Field, model_validator

from .config import ModelConfig

EPISODE_ID_PATTERN = r"^EP-[0-9a-f]{32}$"
GUESSER_CALL_ID_PATTERN = r"^GC-[0-9a-f]{32}$"
VALIDATOR_CALL_ID_PATTERN = r"^VC-[0-9a-f]{32}$"
EVENT_ID_PATTERN = r"^EV-[0-9a-f]{32}$"
GUESSER_ACTION_SCHEMA_NAME = "guesser_action_v3"


class ActionType(StrEnum):
    ASK = "ASK"
    GUESS = "GUESS"


class GuesserAction(StrictModel):
    """Stable provider schema; inactive action fields are explicitly null."""

    action: ActionType
    question: str | None = Field(min_length=1, max_length=1_000)
    name: str | None = Field(min_length=1, max_length=200)
    description: str | None = Field(min_length=1, max_length=1_000)

    @model_validator(mode="after")
    def fields_match_action(self) -> GuesserAction:
        if self.action is ActionType.ASK:
            if self.question is None or self.name is not None or self.description is not None:
                raise ValueError("ASK requires question and null name/description")
        elif self.question is not None or self.name is None or self.description is None:
            raise ValueError("GUESS requires name/description and null question")
        return self


class GuesserActionEnvelope(StrictModel):
    """Provider wire envelope keeping action-specific branches below the schema root."""

    result: GuesserAction


_GUESSER_ACTION_FORMATS = (
    GuesserActionEnvelope(
        result=GuesserAction(
            action=ActionType.ASK,
            question="<non-empty yes-or-no property question>",
            name=None,
            description=None,
        )
    ),
    GuesserActionEnvelope(
        result=GuesserAction(
            action=ActionType.GUESS,
            question=None,
            name="<non-empty candidate name>",
            description="<non-empty identifying description>",
        )
    ),
)


def parse_guesser_action_output(raw_output: str) -> GuesserAction:
    return GuesserActionEnvelope.model_validate_json(raw_output).result


def guesser_action_required_formats() -> JsonObject:
    """Render repair examples from the canonical Guesser action contract."""

    return {
        envelope.result.action.value: envelope.model_dump(mode="json")
        for envelope in _GUESSER_ACTION_FORMATS
    }


def guesser_action_output_schema() -> JsonObject:
    """Render the provider schema from the canonical Guesser action contract."""

    def string_or_null(value: str | None, description: str) -> JsonObject:
        if value is None:
            return {"type": "null"}
        return {
            "type": "string",
            "minLength": 1,
            "description": description,
        }

    def branch(envelope: GuesserActionEnvelope) -> JsonObject:
        action = envelope.result
        action_description = (
            "Ask one yes-or-no property question."
            if action.action is ActionType.ASK
            else "Name the hidden subject."
        )
        properties: JsonObject = {
            "action": {
                "type": "string",
                "const": action.action.value,
                "description": action_description,
            },
            "question": string_or_null(
                action.question,
                "The yes-or-no property question.",
            ),
            "name": string_or_null(action.name, "The guessed subject name."),
            "description": string_or_null(
                action.description,
                "A short identifying description of the guessed subject.",
            ),
        }
        return {
            "type": "object",
            "properties": properties,
            "required": ["action", "question", "name", "description"],
            "additionalProperties": False,
        }

    return {
        "type": "object",
        "description": "Envelope containing exactly one Twenty Questions action.",
        "properties": {
            "result": {
                "description": "The next Twenty Questions action.",
                "anyOf": [branch(envelope) for envelope in _GUESSER_ACTION_FORMATS],
            }
        },
        "required": ["result"],
        "additionalProperties": False,
    }


class GuessValidationResult(StrictModel):
    answer: OracleAnswer
    explanation: str = Field(min_length=1, max_length=2_000)


class GuesserSamplingMode(StrEnum):
    PROMPT_NONCE_PLUS_PROVIDER_SEED = "prompt_nonce_plus_provider_seed"
    PROMPT_NONCE_ONLY = "prompt_nonce_only"


class GuesserSamplingContext(StrictModel):
    base_seed: int = Field(default=0, ge=0, le=(2**31) - 1)
    trial_number: int = Field(default=1, ge=1)


class GuesserSamplingDecision(StrictModel):
    mode: GuesserSamplingMode
    base_seed: int = Field(ge=0, le=(2**31) - 1)
    trial_number: int = Field(ge=1)
    turn_number: int = Field(ge=1)
    prompt_nonce: str = Field(pattern=r"^[A-Z2-7]{8}$")
    seed: int | None = Field(default=None, ge=0, le=(2**31) - 1)

    @model_validator(mode="after")
    def seed_matches_mode(self) -> GuesserSamplingDecision:
        if (
            self.mode is GuesserSamplingMode.PROMPT_NONCE_PLUS_PROVIDER_SEED
            and self.seed is None
        ):
            raise ValueError("prompt nonce plus provider seed sampling requires a seed")
        if self.mode is GuesserSamplingMode.PROMPT_NONCE_ONLY and self.seed is not None:
            raise ValueError("prompt nonce only sampling cannot include a provider seed")
        return self


class GameProviderRequest(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=False)

    messages: tuple[dict[str, str], ...]
    output_schema: JsonObject
    schema_name: str = Field(min_length=1, max_length=80)
    session_id: str = Field(min_length=1, max_length=256)
    prompt_cache_key: str = Field(min_length=1, max_length=256)
    seed: int | None = Field(default=None, ge=0, le=(2**31) - 1)


class GameProviderExchange(StrictModel):
    raw_output: str
    trace: ProviderTrace


class CallMetrics(StrictModel):
    cost_usd: Decimal | None
    latency_ms: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    cached_input_tokens: int = Field(ge=0)
    cache_write_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    reasoning_tokens: int = Field(ge=0)
    cache_discount_usd: Decimal | None = None
    estimated_cache_savings_usd: Decimal = Field(default=Decimal(0))
    recovery: RecoveryMetrics = Field(default_factory=RecoveryMetrics)


class GameCallAudit(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=False)

    prompt_version: str
    prompt_hash: str
    messages: tuple[dict[str, str], ...]
    session_id: str
    prompt_cache_key: str
    sampling: GuesserSamplingDecision | None = None
    provider: ProviderTrace


class GuesserCall(StrictModel):
    schema_version: Literal[2] = 2
    call_id: str = Field(pattern=GUESSER_CALL_ID_PATTERN)
    run_id: str = Field(pattern=RUN_ID_PATTERN)
    episode_id: str = Field(pattern=EPISODE_ID_PATTERN)
    action: GuesserAction
    metrics: CallMetrics
    audit: GameCallAudit
    recorded_at: str
    integrity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class GuessValidatorCall(StrictModel):
    schema_version: Literal[2] = 2
    call_id: str = Field(pattern=VALIDATOR_CALL_ID_PATTERN)
    run_id: str = Field(pattern=RUN_ID_PATTERN)
    episode_id: str = Field(pattern=EPISODE_ID_PATTERN)
    subject: Subject
    guess: GuesserAction
    result: GuessValidationResult
    metrics: CallMetrics
    audit: GameCallAudit
    recorded_at: str
    integrity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def guess_action_only(self) -> GuessValidatorCall:
        if self.guess.action is not ActionType.GUESS:
            raise ValueError("Guess Validator calls require a GUESS action")
        return self


class CacheStatus(StrEnum):
    NOT_APPLICABLE = "not_applicable"
    COMPLIANT = "compliant"
    NONCOMPLIANT = "noncompliant"


class ContractReliabilityStatus(StrEnum):
    CLEAN = "clean"
    BREACHED = "breached"
    NOT_EVALUABLE = "not_evaluable"


class GuesserContractReliability(StrictModel):
    evaluated_outputs: int = Field(default=0, ge=0)
    valid_outputs: int = Field(default=0, ge=0)
    violations: int = Field(default=0, ge=0)
    counted_penalties: int = Field(default=0, ge=0)
    affected_trials: int = Field(default=0, ge=0)
    compliance_rate: Decimal | None = Field(default=None, ge=0, le=1)
    status: ContractReliabilityStatus = ContractReliabilityStatus.NOT_EVALUABLE

    @model_validator(mode="after")
    def counts_and_status_match(self) -> GuesserContractReliability:
        if self.valid_outputs + self.violations != self.evaluated_outputs:
            raise ValueError("valid outputs plus violations must equal evaluated outputs")
        if self.counted_penalties > self.violations:
            raise ValueError("counted contract penalties cannot exceed violations")
        if self.evaluated_outputs == 0:
            if (
                self.compliance_rate is not None
                or self.status is not ContractReliabilityStatus.NOT_EVALUABLE
            ):
                raise ValueError("unevaluated contract reliability must be not_evaluable")
        else:
            expected_rate = Decimal(self.valid_outputs) / Decimal(self.evaluated_outputs)
            expected_status = (
                ContractReliabilityStatus.BREACHED
                if self.violations
                else ContractReliabilityStatus.CLEAN
            )
            if self.compliance_rate != expected_rate or self.status is not expected_status:
                raise ValueError("contract compliance rate or status does not match counts")
        return self


def guesser_contract_reliability(
    *,
    evaluated_outputs: int,
    violations: int,
    counted_penalties: int,
    affected_trials: int,
) -> GuesserContractReliability:
    valid_outputs = evaluated_outputs - violations
    return GuesserContractReliability(
        evaluated_outputs=evaluated_outputs,
        valid_outputs=valid_outputs,
        violations=violations,
        counted_penalties=counted_penalties,
        affected_trials=affected_trials,
        compliance_rate=(
            Decimal(valid_outputs) / Decimal(evaluated_outputs)
            if evaluated_outputs
            else None
        ),
        status=(
            ContractReliabilityStatus.BREACHED
            if violations
            else (
                ContractReliabilityStatus.CLEAN
                if evaluated_outputs
                else ContractReliabilityStatus.NOT_EVALUABLE
            )
        ),
    )


class TerminalReason(StrEnum):
    SUCCESS = "success"
    LIMIT_EXHAUSTED = "limit_exhausted"
    VALIDATOR_UNKNOWN = "validator_unknown"
    GUESSER_PROTOCOL_FAILURE = "guesser_protocol_failure"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"
    INTERRUPTED = "interrupted"


class ComponentTotals(StrictModel):
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
    recovery: RecoveryTotals = Field(default_factory=RecoveryTotals)


class EpisodeTotals(StrictModel):
    guesser: ComponentTotals
    oracle: ComponentTotals
    validator: ComponentTotals


class GameLlmDetails(StrictModel):
    configuration: ModelConfig
    metrics: ComponentTotals


class OracleLlmDetails(StrictModel):
    configuration: OracleConfig
    metrics: ComponentTotals


class EpisodeLlmDetails(StrictModel):
    guesser: GameLlmDetails
    oracle: OracleLlmDetails
    validator: GameLlmDetails


class LlmVersion(StrictModel):
    role: Literal["guesser", "oracle", "validator"]
    configuration_id: str | None
    requested_model: str
    requested_provider: str
    resolved_models: tuple[str, ...]
    resolved_providers: tuple[str, ...]
    reasoning_effort: str
    prompt_version: str


class EpisodeModelVersions(StrictModel):
    under_test: LlmVersion
    oracle: LlmVersion
    validator: LlmVersion


class ComponentCosts(StrictModel):
    guesser: Decimal = Field(ge=0)
    oracle: Decimal = Field(ge=0)
    validator: Decimal = Field(ge=0)
    total: Decimal = Field(ge=0)


class ComponentTokens(StrictModel):
    guesser: int = Field(ge=0)
    oracle: int = Field(ge=0)
    validator: int = Field(ge=0)
    total: int = Field(ge=0)


class OracleQuestionTypeTotals(StrictModel):
    question_type: OracleQuestionType
    reviewed_questions: int = Field(default=0, ge=0)
    disagreements: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def disagreements_are_reviewed(self) -> OracleQuestionTypeTotals:
        if self.disagreements > self.reviewed_questions:
            raise ValueError("question-type disagreements cannot exceed reviews")
        return self


class OracleQualityTotals(StrictModel):
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
    question_types: tuple[OracleQuestionTypeTotals, ...] = ()

    @model_validator(mode="after")
    def counts_and_costs_match(self) -> OracleQualityTotals:
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


class TurnAdjudication(StrictModel):
    component: Literal["oracle", "guess_validator"]
    call_id: str
    answer: OracleAnswer
    evidence: tuple[Evidence, ...] = ()
    explanation: str | None = None
    oracle_quality: OracleAdjudication | None = None

    @model_validator(mode="after")
    def details_match_component(self) -> TurnAdjudication:
        if self.component == "oracle":
            if self.explanation is not None:
                raise ValueError("Oracle adjudication cannot contain a validator explanation")
            if self.oracle_quality is None:
                raise ValueError("Oracle adjudication requires quality-control decisions")
            if self.answer is not self.oracle_quality.final_answer:
                raise ValueError("Oracle turn answer must equal the final quality-control answer")
        elif self.evidence or self.oracle_quality is not None:
            raise ValueError(
                "Guess Validator adjudication cannot contain Oracle evidence or quality data"
            )
        return self


class ActionTurnResult(StrictModel):
    turn_type: Literal["action"] = "action"
    turn_number: int = Field(ge=1)
    action: GuesserAction
    adjudication: TurnAdjudication
    counted: bool
    counted_questions: int = Field(ge=0)
    guesser_call_id: str = Field(pattern=GUESSER_CALL_ID_PATTERN)


class ContractViolationKind(StrEnum):
    INVALID_JSON = "invalid_json"
    INVALID_ACTION = "invalid_action"
    OUTPUT_LIMIT_EXCEEDED = "output_limit_exceeded"
    EMPTY_OUTPUT = "empty_output"
    INCOMPLETE_OUTPUT = "incomplete_output"


class ContractViolationTurnResult(StrictModel):
    turn_type: Literal["contract_violation"] = "contract_violation"
    turn_number: int = Field(ge=1)
    violation_code: Literal["invalid_guesser_output"] = "invalid_guesser_output"
    violation_kind: ContractViolationKind
    feedback_event: Literal["FORMAT_ERROR"] | None
    counted: bool
    counted_questions: int = Field(ge=0)
    guesser_call_id: str = Field(pattern=GUESSER_CALL_ID_PATTERN)

    @model_validator(mode="after")
    def feedback_matches_counted_turn(self) -> ContractViolationTurnResult:
        if self.counted != (self.feedback_event == "FORMAT_ERROR"):
            raise ValueError("only counted contract violations receive FORMAT_ERROR")
        return self


TurnResult = Annotated[
    ActionTurnResult | ContractViolationTurnResult,
    Field(discriminator="turn_type"),
]


class GameRequest(StrictModel):
    run_id: str = Field(pattern=RUN_ID_PATTERN)
    subject: Subject
    guesser_sampling: GuesserSamplingContext = Field(
        default_factory=GuesserSamplingContext
    )


class EpisodeRun(StrictModel):
    run_id: str = Field(pattern=RUN_ID_PATTERN)
    episode_id: str = Field(pattern=EPISODE_ID_PATTERN)
    subject: Subject
    started_at: str
    completed_at: str
    duration_ms: int = Field(ge=0)


class EpisodeOutcome(StrictModel):
    success: bool
    terminal_reason: TerminalReason
    scoring_eligible: bool
    publication_eligible: bool


class EpisodeSummary(StrictModel):
    total_turns: int = Field(ge=0)
    counted_questions: int = Field(ge=0)
    guesser_call_count: int = Field(ge=0)
    ask_count: int = Field(ge=0)
    guess_count: int = Field(ge=0)
    rejected_guess_count: int = Field(ge=0)
    oracle_unknown_count: int = Field(ge=0)
    oracle_quality: OracleQualityTotals = Field(default_factory=OracleQualityTotals)
    contract: GuesserContractReliability = Field(
        default_factory=GuesserContractReliability
    )
    cache_status: CacheStatus
    costs_usd: ComponentCosts
    tokens: ComponentTokens


class GuesserConversationMessage(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=False)

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)
    turn_number: int | None = Field(
        default=None,
        ge=1,
        exclude_if=lambda value: value is None,
    )


class EpisodeTerminalFailure(StrictModel):
    code: str = Field(min_length=1, max_length=160)
    type: str = Field(min_length=1, max_length=160)
    message: str = Field(max_length=2_000)
    call_id: str | None = None
    diagnostics: FailureDiagnostics | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )


class EpisodeResult(StrictModel):
    schema_version: Literal[9] = 9
    run: EpisodeRun
    outcome: EpisodeOutcome
    summary: EpisodeSummary
    models: EpisodeModelVersions
    turns: tuple[TurnResult, ...]
    guesser_conversation: tuple[GuesserConversationMessage, ...]
    llm_details: EpisodeLlmDetails
    failure: EpisodeTerminalFailure | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )

    @model_validator(mode="after")
    def failure_matches_outcome(self) -> EpisodeResult:
        if self.failure is not None and (
            self.outcome.success
            or self.outcome.terminal_reason
            not in {
                TerminalReason.GUESSER_PROTOCOL_FAILURE,
                TerminalReason.INFRASTRUCTURE_FAILURE,
            }
        ):
            raise ValueError("terminal failure details require a failed exceptional outcome")
        return self

    @property
    def run_id(self) -> str:
        return self.run.run_id

    @property
    def episode_id(self) -> str:
        return self.run.episode_id

    @property
    def subject(self) -> Subject:
        return self.run.subject

    @property
    def started_at(self) -> str:
        return self.run.started_at

    @property
    def completed_at(self) -> str:
        return self.run.completed_at

    @property
    def duration_ms(self) -> int:
        return self.run.duration_ms

    @property
    def success(self) -> bool:
        return self.outcome.success

    @property
    def terminal_reason(self) -> TerminalReason:
        return self.outcome.terminal_reason

    @property
    def scoring_eligible(self) -> bool:
        return self.outcome.scoring_eligible

    @property
    def publication_eligible(self) -> bool:
        return self.outcome.publication_eligible

    @property
    def total_turns(self) -> int:
        return self.summary.total_turns

    @property
    def counted_questions(self) -> int:
        return self.summary.counted_questions

    @property
    def guesser_call_count(self) -> int:
        return self.summary.guesser_call_count

    @property
    def ask_count(self) -> int:
        return self.summary.ask_count

    @property
    def guess_count(self) -> int:
        return self.summary.guess_count

    @property
    def rejected_guess_count(self) -> int:
        return self.summary.rejected_guess_count

    @property
    def oracle_unknown_count(self) -> int:
        return self.summary.oracle_unknown_count

    @property
    def cache_status(self) -> CacheStatus:
        return self.summary.cache_status

    @property
    def costs_usd(self) -> ComponentCosts:
        return self.summary.costs_usd

    @property
    def tokens(self) -> ComponentTokens:
        return self.summary.tokens

    @property
    def llm(self) -> EpisodeLlmDetails:
        return self.llm_details


class GameComponentFailure(StrictModel):
    code: str = Field(min_length=1, max_length=160)
    type: str = Field(min_length=1, max_length=160)
    message: str = Field(max_length=2_000)
    details: JsonObject
    diagnostics: FailureDiagnostics | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )


class FailedGameCallAudit(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=False)

    prompt_version: str
    prompt_hash: str
    messages: tuple[dict[str, str], ...]
    session_id: str
    prompt_cache_key: str
    sampling: GuesserSamplingDecision | None = None
    provider: ProviderTrace | None


class GuesserSuccessRecord(StrictModel):
    schema_version: Literal[2] = 2
    status: Literal["success"] = "success"
    call_id: str = Field(pattern=GUESSER_CALL_ID_PATTERN)
    run_id: str = Field(pattern=RUN_ID_PATTERN)
    episode_id: str = Field(pattern=EPISODE_ID_PATTERN)
    action: GuesserAction
    metrics: CallMetrics
    audit: GameCallAudit
    recorded_at: str


class GuesserFailureRecord(StrictModel):
    schema_version: Literal[2] = 2
    status: Literal["failure"] = "failure"
    call_id: str = Field(pattern=GUESSER_CALL_ID_PATTERN)
    run_id: str = Field(pattern=RUN_ID_PATTERN)
    episode_id: str = Field(pattern=EPISODE_ID_PATTERN)
    metrics: CallMetrics | None
    audit: FailedGameCallAudit
    failure: GameComponentFailure
    recorded_at: str


class ValidatorSuccessRecord(StrictModel):
    schema_version: Literal[2] = 2
    status: Literal["success"] = "success"
    call_id: str = Field(pattern=VALIDATOR_CALL_ID_PATTERN)
    run_id: str = Field(pattern=RUN_ID_PATTERN)
    episode_id: str = Field(pattern=EPISODE_ID_PATTERN)
    subject: Subject
    guess: GuesserAction
    result: GuessValidationResult
    metrics: CallMetrics
    audit: GameCallAudit
    recorded_at: str


class ValidatorFailureRecord(StrictModel):
    schema_version: Literal[2] = 2
    status: Literal["failure"] = "failure"
    call_id: str = Field(pattern=VALIDATOR_CALL_ID_PATTERN)
    run_id: str = Field(pattern=RUN_ID_PATTERN)
    episode_id: str = Field(pattern=EPISODE_ID_PATTERN)
    subject: Subject
    guess: GuesserAction
    metrics: CallMetrics | None
    audit: FailedGameCallAudit
    failure: GameComponentFailure
    recorded_at: str


class EpisodeStartedPayload(StrictModel):
    subject: Subject
    started_at: str


class TurnResolvedPayload(StrictModel):
    turn: ActionTurnResult
    cache_status: CacheStatus


class ContractViolationPayload(StrictModel):
    turn: ContractViolationTurnResult
    cache_status: CacheStatus


class EpisodeFinishedPayload(StrictModel):
    result: EpisodeResult
    failure: EpisodeTerminalFailure | None = None


class EpisodeStartedEvent(StrictModel):
    schema_version: Literal[1] = 1
    event_id: str = Field(pattern=EVENT_ID_PATTERN)
    run_id: str = Field(pattern=RUN_ID_PATTERN)
    episode_id: str = Field(pattern=EPISODE_ID_PATTERN)
    event_type: Literal["episode_started"] = "episode_started"
    payload: EpisodeStartedPayload
    recorded_at: str


class TurnResolvedEvent(StrictModel):
    schema_version: Literal[1] = 1
    event_id: str = Field(pattern=EVENT_ID_PATTERN)
    run_id: str = Field(pattern=RUN_ID_PATTERN)
    episode_id: str = Field(pattern=EPISODE_ID_PATTERN)
    event_type: Literal["turn_resolved"] = "turn_resolved"
    payload: TurnResolvedPayload
    recorded_at: str


class ContractViolationEvent(StrictModel):
    schema_version: Literal[1] = 1
    event_id: str = Field(pattern=EVENT_ID_PATTERN)
    run_id: str = Field(pattern=RUN_ID_PATTERN)
    episode_id: str = Field(pattern=EPISODE_ID_PATTERN)
    event_type: Literal["contract_violation"] = "contract_violation"
    payload: ContractViolationPayload
    recorded_at: str


class EpisodeFinishedEvent(StrictModel):
    schema_version: Literal[1] = 1
    event_id: str = Field(pattern=EVENT_ID_PATTERN)
    run_id: str = Field(pattern=RUN_ID_PATTERN)
    episode_id: str = Field(pattern=EPISODE_ID_PATTERN)
    event_type: Literal["episode_finished"] = "episode_finished"
    payload: EpisodeFinishedPayload
    recorded_at: str


EpisodeEvent = Annotated[
    EpisodeStartedEvent
    | TurnResolvedEvent
    | ContractViolationEvent
    | EpisodeFinishedEvent,
    Field(discriminator="event_type"),
]


class TurnProgress(StrictModel):
    event_type: Literal["turn_resolved"] = "turn_resolved"
    run_id: str = Field(pattern=RUN_ID_PATTERN)
    episode_id: str = Field(pattern=EPISODE_ID_PATTERN)
    turn: ActionTurnResult
    guesser_metrics: CallMetrics
    adjudicator_metrics: CallMetrics | OracleMetrics


class ContractViolationProgress(StrictModel):
    event_type: Literal["contract_violation"] = "contract_violation"
    run_id: str = Field(pattern=RUN_ID_PATTERN)
    episode_id: str = Field(pattern=EPISODE_ID_PATTERN)
    turn: ContractViolationTurnResult
    guesser_metrics: CallMetrics


class EpisodeStartedProgress(StrictModel):
    event_type: Literal["episode_started"] = "episode_started"
    run_id: str = Field(pattern=RUN_ID_PATTERN)
    episode_id: str = Field(pattern=EPISODE_ID_PATTERN)
    target_id: str
    started_at: str


class EpisodeFinishedProgress(StrictModel):
    event_type: Literal["episode_finished"] = "episode_finished"
    result: EpisodeResult


GameProgressEvent = (
    EpisodeStartedProgress
    | TurnProgress
    | ContractViolationProgress
    | EpisodeFinishedProgress
)
