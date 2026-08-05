from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Literal, Protocol, cast

from deep20_oracle.config import OracleConfig
from deep20_oracle.diagnostics import diagnose_exception
from deep20_oracle.errors import OracleError
from deep20_oracle.models import (
    Evidence,
    OracleAdjudication,
    OracleAnswer,
    OracleCall,
    OracleProviderRoleTrace,
    OracleQuestionType,
    OracleRequest,
    ProviderTrace,
    RecoveryTotals,
    Subject,
)
from deep20_oracle.prompt import PROMPT_VERSION as ORACLE_PROMPT_VERSION
from deep20_oracle.recovery import combine_recovery_totals
from deep20_oracle.service import Oracle
from deep20_oracle.util import timestamp
from pydantic import ValidationError

from .config import BenchmarkMode, GamePolicy, ModelConfig
from .errors import GameError, GuesserProtocolError
from .models import (
    ActionTurnResult,
    ActionType,
    CacheStatus,
    CallMetrics,
    ComponentCosts,
    ComponentTokens,
    ComponentTotals,
    ContractViolationEvent,
    ContractViolationKind,
    ContractViolationPayload,
    ContractViolationProgress,
    ContractViolationTurnResult,
    EpisodeFinishedEvent,
    EpisodeFinishedPayload,
    EpisodeFinishedProgress,
    EpisodeLlmDetails,
    EpisodeModelVersions,
    EpisodeOutcome,
    EpisodeResult,
    EpisodeRun,
    EpisodeStartedEvent,
    EpisodeStartedPayload,
    EpisodeStartedProgress,
    EpisodeSummary,
    EpisodeTerminalFailure,
    GameLlmDetails,
    GameRequest,
    GuesserAction,
    GuesserCall,
    GuesserConversationMessage,
    GuesserSamplingDecision,
    GuessValidatorCall,
    LlmVersion,
    OracleLlmDetails,
    OracleProviderUsage,
    OracleQualityTotals,
    OracleQuestionTypeTotals,
    ResolvedProviderUsage,
    RoleProviderUsage,
    TerminalReason,
    TurnAdjudication,
    TurnProgress,
    TurnResolvedEvent,
    TurnResolvedPayload,
    TurnResult,
    guesser_contract_reliability,
)
from .prompt import (
    GUESSER_PROMPT_VERSION,
    VALIDATOR_PROMPT_VERSION,
    append_visible_action,
    append_visible_format_error,
    append_visible_turn,
    initial_guesser_messages,
)
from .sampling import derive_guesser_prompt_nonce, guesser_sampling_decision
from .service_util import metrics_from_trace, provider_trace_from_error
from .sinks import ExecutionObserver, GameAuditSink, NullExecutionObserver


def _reported_guesser_conversation(
    messages: tuple[dict[str, str], ...],
) -> tuple[GuesserConversationMessage, ...]:
    """Add report-only turn links without changing Guesser-visible messages."""
    turn_number = 0
    reported: list[GuesserConversationMessage] = []
    for message in messages:
        message_turn: int | None = None
        if message["role"] == "assistant" or (
            message["role"] == "user"
            and _is_format_error_message(message["content"])
        ):
            turn_number += 1
            message_turn = turn_number
        elif message["role"] == "user" and turn_number > 0:
            message_turn = turn_number
        reported.append(
            GuesserConversationMessage(
                role=cast(
                    Literal["system", "user", "assistant"],
                    message["role"],
                ),
                content=message["content"],
                turn_number=message_turn,
            )
        )
    return tuple(reported)


def _is_format_error_message(content: str) -> bool:
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        return False
    return isinstance(value, dict) and value.get("event") == "FORMAT_ERROR"


class GuesserClient(Protocol):
    def next_action(
        self,
        *,
        run_id: str,
        episode_id: str,
        messages: tuple[dict[str, str], ...],
        sampling: GuesserSamplingDecision,
    ) -> GuesserCall: ...


class ValidatorClient(Protocol):
    def validate(
        self,
        *,
        run_id: str,
        episode_id: str,
        subject: Subject,
        guess: GuesserAction,
    ) -> GuessValidatorCall: ...


@dataclass
class _MutableResolvedProviderUsage:
    provider: str
    calls: int = 0
    cost_usd: Decimal = Decimal(0)
    latency_ms: int = 0


@dataclass
class _MutableRoleProviderUsage:
    providers: dict[str, _MutableResolvedProviderUsage] = field(
        default_factory=dict
    )
    unreported_calls: int = 0
    fallback_calls: int = 0

    def observe(
        self,
        trace: ProviderTrace,
        *,
        cost_usd: Decimal | None,
        latency_ms: int,
    ) -> None:
        self.fallback_calls += int(
            getattr(trace, "fallback_occurred", None) is True
        )
        if trace.resolved_provider is None:
            self.unreported_calls += 1
            return
        key = trace.resolved_provider.casefold()
        usage = self.providers.get(key)
        if usage is None:
            usage = _MutableResolvedProviderUsage(provider=trace.resolved_provider)
            self.providers[key] = usage
        usage.calls += 1
        usage.cost_usd += cost_usd or Decimal(0)
        usage.latency_ms += latency_ms

    def frozen(self) -> RoleProviderUsage:
        return RoleProviderUsage(
            providers=tuple(
                ResolvedProviderUsage(
                    provider=usage.provider,
                    calls=usage.calls,
                    cost_usd=usage.cost_usd,
                    latency_ms=usage.latency_ms,
                )
                for usage in sorted(
                    self.providers.values(),
                    key=lambda item: item.provider.casefold(),
                )
            ),
            unreported_calls=self.unreported_calls,
            fallback_calls=self.fallback_calls,
        )


@dataclass
class _MutableTotals:
    calls: int = 0
    cost_usd: Decimal = Decimal(0)
    latency_ms: int = 0
    input_tokens: int = 0
    cached_input_tokens: int = 0
    cache_write_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    estimated_cache_savings_usd: Decimal = Decimal(0)
    recovery: RecoveryTotals = field(default_factory=RecoveryTotals)
    evaluated_outputs: int = 0
    contract_violations: int = 0
    contract_penalties: int = 0
    resolved_models: set[str] = field(default_factory=set)
    resolved_providers: set[str] = field(default_factory=set)
    reviewed_questions: int = 0
    agreements: int = 0
    disagreements: int = 0
    judge_invocations: int = 0
    oracle_answers_changed: int = 0
    final_unknown_answers: int = 0
    judge_yes_answers: int = 0
    judge_no_answers: int = 0
    judge_unknown_answers: int = 0
    reviewer_cost_usd: Decimal = Decimal(0)
    judge_cost_usd: Decimal = Decimal(0)
    question_type_reviews: dict[OracleQuestionType, int] = field(
        default_factory=dict
    )
    question_type_disagreements: dict[OracleQuestionType, int] = field(
        default_factory=dict
    )
    provider_usage: _MutableRoleProviderUsage = field(
        default_factory=lambda: _MutableRoleProviderUsage()
    )
    reviewer_provider_usage: _MutableRoleProviderUsage = field(
        default_factory=lambda: _MutableRoleProviderUsage()
    )
    judge_provider_usage: _MutableRoleProviderUsage = field(
        default_factory=lambda: _MutableRoleProviderUsage()
    )

    def add_metrics(
        self,
        metrics: CallMetrics,
        trace: ProviderTrace | None = None,
    ) -> None:
        self.calls += 1
        self.cost_usd += metrics.cost_usd or Decimal(0)
        self.latency_ms += metrics.latency_ms
        self.input_tokens += metrics.input_tokens
        self.cached_input_tokens += metrics.cached_input_tokens
        self.cache_write_tokens += metrics.cache_write_tokens
        self.output_tokens += metrics.output_tokens
        self.reasoning_tokens += metrics.reasoning_tokens
        self.estimated_cache_savings_usd += metrics.estimated_cache_savings_usd
        self.recovery = combine_recovery_totals(self.recovery, metrics.recovery)
        if trace is not None:
            self._add_route(trace)
            self.provider_usage.observe(
                trace,
                cost_usd=metrics.cost_usd,
                latency_ms=metrics.latency_ms,
            )

    def add_oracle(self, call: OracleCall) -> None:
        self.calls += 1
        self.cost_usd += call.metrics.cost_usd or Decimal(0)
        self.latency_ms += call.metrics.latency_ms
        self.input_tokens += call.metrics.input_tokens
        self.cached_input_tokens += call.metrics.cached_input_tokens
        self.cache_write_tokens += call.metrics.cache_write_tokens
        self.output_tokens += call.metrics.output_tokens
        self.reasoning_tokens += call.metrics.reasoning_tokens
        self.recovery = combine_recovery_totals(
            self.recovery,
            call.metrics.recovery,
        )
        self._add_route(call.audit.provider)
        oracle_metrics = call.metrics.oracle or call.metrics
        self.provider_usage.observe(
            call.audit.provider,
            cost_usd=oracle_metrics.cost_usd,
            latency_ms=oracle_metrics.latency_ms,
        )
        adjudication = call.adjudication
        if adjudication.reviewer is not None:
            self.reviewed_questions += 1
            self.agreements += int(not adjudication.disagreement)
            self.disagreements += int(adjudication.disagreement)
            question_type = adjudication.question_type
            self.question_type_reviews[question_type] = (
                self.question_type_reviews.get(question_type, 0) + 1
            )
            self.question_type_disagreements[question_type] = (
                self.question_type_disagreements.get(question_type, 0)
                + int(adjudication.disagreement)
            )
        self.judge_invocations += int(adjudication.judge_invoked)
        self.oracle_answers_changed += int(adjudication.oracle_answer_changed)
        self.final_unknown_answers += int(
            adjudication.final_answer is OracleAnswer.UNKNOWN
        )
        if adjudication.judge is not None:
            self.judge_yes_answers += int(
                adjudication.judge.answer is OracleAnswer.YES
            )
            self.judge_no_answers += int(
                adjudication.judge.answer is OracleAnswer.NO
            )
            self.judge_unknown_answers += int(
                adjudication.judge.answer is OracleAnswer.UNKNOWN
            )
        if call.metrics.reviewer is not None:
            self.reviewer_cost_usd += call.metrics.reviewer.cost_usd or Decimal(0)
            reviewer_audit = getattr(call.audit, "reviewer", None)
            if reviewer_audit is not None:
                self.reviewer_provider_usage.observe(
                    reviewer_audit.provider,
                    cost_usd=call.metrics.reviewer.cost_usd,
                    latency_ms=call.metrics.reviewer.latency_ms,
                )
            else:
                self.reviewer_provider_usage.unreported_calls += 1
        if call.metrics.judge is not None:
            self.judge_cost_usd += call.metrics.judge.cost_usd or Decimal(0)
            judge_audit = getattr(call.audit, "judge", None)
            if judge_audit is not None:
                self.judge_provider_usage.observe(
                    judge_audit.provider,
                    cost_usd=call.metrics.judge.cost_usd,
                    latency_ms=call.metrics.judge.latency_ms,
                )
            else:
                self.judge_provider_usage.unreported_calls += 1

    def _add_route(self, trace: ProviderTrace) -> None:
        if trace.resolved_model:
            self.resolved_models.add(trace.resolved_model)
        if trace.resolved_provider:
            self.resolved_providers.add(trace.resolved_provider)

    def observe_valid_output(self) -> None:
        self.evaluated_outputs += 1

    def observe_contract_violation(self, *, counted: bool) -> None:
        self.evaluated_outputs += 1
        self.contract_violations += 1
        self.contract_penalties += int(counted)

    def frozen(self) -> ComponentTotals:
        return ComponentTotals(
            calls=self.calls,
            cost_usd=self.cost_usd,
            latency_ms=self.latency_ms,
            total_tokens=self.input_tokens + self.output_tokens,
            input_tokens=self.input_tokens,
            cached_input_tokens=self.cached_input_tokens,
            cache_write_tokens=self.cache_write_tokens,
            output_tokens=self.output_tokens,
            reasoning_tokens=self.reasoning_tokens,
            estimated_cache_savings_usd=self.estimated_cache_savings_usd,
            recovery=self.recovery,
        )

    def frozen_oracle_quality(self) -> OracleQualityTotals:
        return OracleQualityTotals(
            reviewed_questions=self.reviewed_questions,
            agreements=self.agreements,
            disagreements=self.disagreements,
            judge_invocations=self.judge_invocations,
            oracle_answers_changed=self.oracle_answers_changed,
            final_unknown_answers=self.final_unknown_answers,
            judge_yes_answers=self.judge_yes_answers,
            judge_no_answers=self.judge_no_answers,
            judge_unknown_answers=self.judge_unknown_answers,
            reviewer_cost_usd=self.reviewer_cost_usd,
            judge_cost_usd=self.judge_cost_usd,
            quality_control_cost_usd=(
                self.reviewer_cost_usd + self.judge_cost_usd
            ),
            question_types=tuple(
                OracleQuestionTypeTotals(
                    question_type=question_type,
                    reviewed_questions=self.question_type_reviews[question_type],
                    disagreements=self.question_type_disagreements[question_type],
                )
                for question_type in sorted(
                    self.question_type_reviews,
                    key=lambda item: item.value,
                )
            ),
        )

    def frozen_oracle_provider_usage(self) -> OracleProviderUsage:
        return OracleProviderUsage(
            oracle=self.provider_usage.frozen(),
            reviewer=self.reviewer_provider_usage.frozen(),
            judge=self.judge_provider_usage.frozen(),
        )


class _CacheTracker:
    def __init__(self, config: ModelConfig):
        self.config = config
        self.status = CacheStatus.NOT_APPLICABLE
        self.previous_trace: ProviderTrace | None = None

    def observe(self, trace: ProviderTrace) -> CacheStatus:
        if trace.usage.cached_input_tokens > 0 and self.status is not CacheStatus.NONCOMPLIANT:
            self.status = CacheStatus.COMPLIANT
        if self.previous_trace is not None:
            previous = self.previous_trace
            eligible = (
                previous.usage.input_tokens >= self.config.prompt_cache.minimum_cacheable_tokens
            )
            within_ttl = (
                self._seconds_between(
                    previous.completed_at,
                    trace.requested_at,
                )
                <= self.config.prompt_cache.ttl_seconds
            )
            if eligible and within_ttl and trace.usage.cached_input_tokens == 0:
                self.status = CacheStatus.NONCOMPLIANT
        self.previous_trace = trace
        return self.status

    @staticmethod
    def _seconds_between(earlier: str, later: str) -> float:
        try:
            return max(
                (datetime.fromisoformat(later) - datetime.fromisoformat(earlier)).total_seconds(),
                0,
            )
        except ValueError:
            return 0


class GameEngine:
    """Deterministically orchestrate one guessing episode and its terminal result."""

    def __init__(
        self,
        *,
        guesser: GuesserClient,
        oracle: Oracle,
        validator: ValidatorClient,
        audit_writer: GameAuditSink,
        policy: GamePolicy,
        guesser_config: ModelConfig,
        oracle_config: OracleConfig,
        validator_config: ModelConfig,
        observer: ExecutionObserver | None = None,
    ):
        self.guesser = guesser
        self.oracle = oracle
        self.validator = validator
        self.audit_writer = audit_writer
        self.policy = policy
        self.guesser_config = guesser_config
        self.oracle_config = oracle_config
        self.validator_config = validator_config
        self.observer = observer or NullExecutionObserver()

    def play(self, request: GameRequest) -> EpisodeResult:
        episode_id = f"EP-{uuid.uuid7().hex}"
        started_at = timestamp()
        self.audit_writer.prepare_run(request.run_id)
        self.audit_writer.persist_episode_event(
            EpisodeStartedEvent(
                event_id=f"EV-{uuid.uuid7().hex}",
                run_id=request.run_id,
                episode_id=episode_id,
                payload=EpisodeStartedPayload(
                    subject=request.subject,
                    started_at=started_at,
                ),
                recorded_at=timestamp(),
            )
        )
        self.observer.observe(
            EpisodeStartedProgress(
                run_id=request.run_id,
                episode_id=episode_id,
                target_id=request.subject.target_id,
                started_at=started_at,
            )
        )
        prompt_nonce = derive_guesser_prompt_nonce(
            base_seed=request.guesser_sampling.base_seed,
            trial_number=request.guesser_sampling.trial_number,
        )
        messages = initial_guesser_messages(
            self.policy.max_questions,
            request.subject.entity_type,
            prompt_nonce,
        )
        conversation = messages
        counted_questions = 0
        consecutive_contract_violations = 0
        guesser_call_count = 0
        ask_count = 0
        guess_count = 0
        rejected_guess_count = 0
        oracle_unknown_count = 0
        turns: list[TurnResult] = []
        totals = {
            "guesser": _MutableTotals(),
            "oracle": _MutableTotals(),
            "validator": _MutableTotals(),
        }
        cache = _CacheTracker(self.guesser_config)

        while True:
            final_opportunity = counted_questions >= self.policy.max_questions
            guesser_call_count += 1
            try:
                sampling = guesser_sampling_decision(
                    capability=self.guesser_config.seed_capability,
                    base_seed=request.guesser_sampling.base_seed,
                    trial_number=request.guesser_sampling.trial_number,
                    turn_number=guesser_call_count,
                )
                guesser_call = self.guesser.next_action(
                    run_id=request.run_id,
                    episode_id=episode_id,
                    messages=messages,
                    sampling=sampling,
                )
            except GuesserProtocolError as error:
                error_trace = provider_trace_from_error(error)
                if error_trace is not None:
                    cache.observe(error_trace)
                self._add_error_trace(
                    totals["guesser"],
                    error,
                    self.guesser_config,
                )
                if error.code == "invalid_guesser_output":
                    counted = not final_opportunity
                    if counted:
                        counted_questions += 1
                    totals["guesser"].observe_contract_violation(counted=counted)
                    violation_kind_value = error.details.get("violation_kind")
                    violation_kind = (
                        ContractViolationKind(violation_kind_value)
                        if isinstance(violation_kind_value, str)
                        and violation_kind_value
                        in {kind.value for kind in ContractViolationKind}
                        else ContractViolationKind.INVALID_ACTION
                    )
                    violation_turn = self._contract_violation_event(
                        request.run_id,
                        episode_id,
                        call_id=error.call_id,
                        turn_number=len(turns) + 1,
                        violation_kind=violation_kind,
                        counted=counted,
                        counted_questions=counted_questions,
                        cache_status=cache.status,
                    )
                    turns.append(violation_turn)
                    self.observer.observe(
                        ContractViolationProgress(
                            run_id=request.run_id,
                            episode_id=episode_id,
                            turn=violation_turn,
                            guesser_metrics=(
                                metrics_from_trace(error_trace, self.guesser_config)
                                if error_trace is not None
                                else CallMetrics(
                                    cost_usd=None,
                                    latency_ms=0,
                                    input_tokens=0,
                                    cached_input_tokens=0,
                                    cache_write_tokens=0,
                                    output_tokens=0,
                                    reasoning_tokens=0,
                                )
                            ),
                        )
                    )
                    if counted:
                        consecutive_contract_violations += 1
                        messages = append_visible_format_error(messages)
                        conversation = messages
                        if (
                            consecutive_contract_violations
                            < self.policy.max_consecutive_contract_violations
                        ):
                            continue
                        return self._finish(
                            request,
                            episode_id,
                            started_at,
                            success=False,
                            terminal_reason=TerminalReason.GUESSER_PROTOCOL_FAILURE,
                            scoring_eligible=True,
                            counted_questions=counted_questions,
                            guesser_call_count=guesser_call_count,
                            ask_count=ask_count,
                            guess_count=guess_count,
                            rejected_guess_count=rejected_guess_count,
                            oracle_unknown_count=oracle_unknown_count,
                            cache_status=cache.status,
                            totals=totals,
                            turns=turns,
                            guesser_conversation=conversation,
                            error=GuesserProtocolError(
                                "the model under test exceeded the consecutive "
                                "contract-violation limit",
                                code="consecutive_contract_violations_exhausted",
                                call_id=error.call_id,
                            ),
                        )
                return self._finish(
                    request,
                    episode_id,
                    started_at,
                    success=False,
                    terminal_reason=TerminalReason.GUESSER_PROTOCOL_FAILURE,
                    scoring_eligible=True,
                    counted_questions=counted_questions,
                    guesser_call_count=guesser_call_count,
                    ask_count=ask_count,
                    guess_count=guess_count,
                    rejected_guess_count=rejected_guess_count,
                    oracle_unknown_count=oracle_unknown_count,
                    cache_status=cache.status,
                    totals=totals,
                    turns=turns,
                    guesser_conversation=conversation,
                    error=error,
                )
            except (GameError, OracleError) as error:
                error_trace = provider_trace_from_error(error)
                if error_trace is not None:
                    cache.observe(error_trace)
                self._add_error_trace(
                    totals["guesser"],
                    error,
                    self.guesser_config,
                )
                return self._infrastructure_failure(
                    request,
                    episode_id,
                    started_at,
                    counted_questions,
                    guesser_call_count,
                    ask_count,
                    guess_count,
                    rejected_guess_count,
                    oracle_unknown_count,
                    cache.status,
                    totals,
                    turns,
                    conversation,
                    error,
                )

            totals["guesser"].add_metrics(
                guesser_call.metrics,
                guesser_call.audit.provider,
            )
            totals["guesser"].observe_valid_output()
            consecutive_contract_violations = 0
            cache.observe(guesser_call.audit.provider)
            action = guesser_call.action
            messages = guesser_call.audit.messages
            conversation = append_visible_action(messages, action)
            if final_opportunity and action.action is ActionType.ASK:
                return self._finish(
                    request,
                    episode_id,
                    started_at,
                    success=False,
                    terminal_reason=TerminalReason.GUESSER_PROTOCOL_FAILURE,
                    scoring_eligible=True,
                    counted_questions=counted_questions,
                    guesser_call_count=guesser_call_count,
                    ask_count=ask_count,
                    guess_count=guess_count,
                    rejected_guess_count=rejected_guess_count,
                    oracle_unknown_count=oracle_unknown_count,
                    cache_status=cache.status,
                    totals=totals,
                    turns=turns,
                    guesser_conversation=conversation,
                    error=GuesserProtocolError(
                        "ASK is forbidden on the final guess-only opportunity",
                        code="ask_after_question_limit",
                        call_id=guesser_call.call_id,
                    ),
                )

            if action.action is ActionType.ASK:
                ask_count += 1
                assert action.question is not None
                try:
                    oracle_call = self.oracle.ask(
                        OracleRequest(
                            run_id=request.run_id,
                            subject=request.subject,
                            question=action.question,
                        )
                    )
                except OracleError as error:
                    self._add_oracle_error_trace(totals["oracle"], error)
                    return self._infrastructure_failure(
                        request,
                        episode_id,
                        started_at,
                        counted_questions,
                        guesser_call_count,
                        ask_count,
                        guess_count,
                        rejected_guess_count,
                        oracle_unknown_count,
                        cache.status,
                        totals,
                        turns,
                        conversation,
                        error,
                    )
                totals["oracle"].add_oracle(oracle_call)
                answer = oracle_call.guesser_answer()
                counted_questions += 1
                if answer is OracleAnswer.UNKNOWN:
                    oracle_unknown_count += 1
                messages = append_visible_turn(messages, action, str(answer))
                conversation = messages
                action_turn = self._turn_event(
                    request.run_id,
                    episode_id,
                    guesser_call,
                    turn_number=len(turns) + 1,
                    adjudicator="oracle",
                    adjudicator_call_id=oracle_call.call_id,
                    answer=answer,
                    evidence=(
                        oracle_call.result.evidence
                        if self.policy.include_oracle_evidence
                        else ()
                    ),
                    explanation=None,
                    oracle_quality=oracle_call.adjudication,
                    counted=True,
                    counted_questions=counted_questions,
                    cache_status=cache.status,
                )
                turns.append(action_turn)
                self.observer.observe(
                    TurnProgress(
                        run_id=request.run_id,
                        episode_id=episode_id,
                        turn=action_turn,
                        guesser_metrics=guesser_call.metrics,
                        adjudicator_metrics=oracle_call.metrics,
                    )
                )
                continue

            guess_count += 1
            try:
                validator_call = self.validator.validate(
                    run_id=request.run_id,
                    episode_id=episode_id,
                    subject=request.subject,
                    guess=action,
                )
            except (GameError, OracleError) as error:
                self._add_error_trace(
                    totals["validator"],
                    error,
                    self.validator_config,
                )
                return self._infrastructure_failure(
                    request,
                    episode_id,
                    started_at,
                    counted_questions,
                    guesser_call_count,
                    ask_count,
                    guess_count,
                    rejected_guess_count,
                    oracle_unknown_count,
                    cache.status,
                    totals,
                    turns,
                    conversation,
                    error,
                )
            totals["validator"].add_metrics(
                validator_call.metrics,
                validator_call.audit.provider,
            )
            answer = validator_call.result.answer
            counted = not final_opportunity and answer is not OracleAnswer.YES
            if counted:
                counted_questions += 1
            if answer is not OracleAnswer.YES:
                rejected_guess_count += 1
            action_turn = self._turn_event(
                request.run_id,
                episode_id,
                guesser_call,
                turn_number=len(turns) + 1,
                adjudicator="guess_validator",
                adjudicator_call_id=validator_call.call_id,
                answer=answer,
                evidence=(),
                explanation=validator_call.result.explanation,
                oracle_quality=None,
                counted=counted,
                counted_questions=counted_questions,
                cache_status=cache.status,
            )
            turns.append(action_turn)
            self.observer.observe(
                TurnProgress(
                    run_id=request.run_id,
                    episode_id=episode_id,
                    turn=action_turn,
                    guesser_metrics=guesser_call.metrics,
                    adjudicator_metrics=validator_call.metrics,
                )
            )
            if answer is OracleAnswer.YES:
                return self._finish(
                    request,
                    episode_id,
                    started_at,
                    success=True,
                    terminal_reason=TerminalReason.SUCCESS,
                    scoring_eligible=True,
                    counted_questions=counted_questions,
                    guesser_call_count=guesser_call_count,
                    ask_count=ask_count,
                    guess_count=guess_count,
                    rejected_guess_count=rejected_guess_count,
                    oracle_unknown_count=oracle_unknown_count,
                    cache_status=cache.status,
                    totals=totals,
                    turns=turns,
                    guesser_conversation=conversation,
                )
            if answer is OracleAnswer.UNKNOWN:
                return self._finish(
                    request,
                    episode_id,
                    started_at,
                    success=False,
                    terminal_reason=TerminalReason.VALIDATOR_UNKNOWN,
                    scoring_eligible=True,
                    counted_questions=counted_questions,
                    guesser_call_count=guesser_call_count,
                    ask_count=ask_count,
                    guess_count=guess_count,
                    rejected_guess_count=rejected_guess_count,
                    oracle_unknown_count=oracle_unknown_count,
                    cache_status=cache.status,
                    totals=totals,
                    turns=turns,
                    guesser_conversation=conversation,
                )
            if final_opportunity:
                return self._finish(
                    request,
                    episode_id,
                    started_at,
                    success=False,
                    terminal_reason=TerminalReason.LIMIT_EXHAUSTED,
                    scoring_eligible=True,
                    counted_questions=counted_questions,
                    guesser_call_count=guesser_call_count,
                    ask_count=ask_count,
                    guess_count=guess_count,
                    rejected_guess_count=rejected_guess_count,
                    oracle_unknown_count=oracle_unknown_count,
                    cache_status=cache.status,
                    totals=totals,
                    turns=turns,
                    guesser_conversation=conversation,
                )
            messages = append_visible_turn(messages, action, str(answer))
            conversation = messages

    def _infrastructure_failure(
        self,
        request: GameRequest,
        episode_id: str,
        started_at: str,
        counted_questions: int,
        guesser_call_count: int,
        ask_count: int,
        guess_count: int,
        rejected_guess_count: int,
        oracle_unknown_count: int,
        cache_status: CacheStatus,
        totals: dict[str, _MutableTotals],
        turns: list[TurnResult],
        guesser_conversation: tuple[dict[str, str], ...],
        error: Exception,
    ) -> EpisodeResult:
        return self._finish(
            request,
            episode_id,
            started_at,
            success=False,
            terminal_reason=TerminalReason.INFRASTRUCTURE_FAILURE,
            scoring_eligible=False,
            counted_questions=counted_questions,
            guesser_call_count=guesser_call_count,
            ask_count=ask_count,
            guess_count=guess_count,
            rejected_guess_count=rejected_guess_count,
            oracle_unknown_count=oracle_unknown_count,
            cache_status=cache_status,
            totals=totals,
            turns=turns,
            guesser_conversation=guesser_conversation,
            error=error,
        )

    def _finish(
        self,
        request: GameRequest,
        episode_id: str,
        started_at: str,
        *,
        success: bool,
        terminal_reason: TerminalReason,
        scoring_eligible: bool,
        counted_questions: int,
        guesser_call_count: int,
        ask_count: int,
        guess_count: int,
        rejected_guess_count: int,
        oracle_unknown_count: int,
        cache_status: CacheStatus,
        totals: dict[str, _MutableTotals],
        turns: list[TurnResult],
        guesser_conversation: tuple[dict[str, str], ...],
        error: Exception | None = None,
    ) -> EpisodeResult:
        completed_at = timestamp()
        publication_eligible = (
            self.policy.benchmark_mode is BenchmarkMode.OFFICIAL
            and scoring_eligible
        )
        frozen_totals = {name: component.frozen() for name, component in totals.items()}
        total_cost_usd = sum(
            (component.cost_usd for component in frozen_totals.values()),
            start=Decimal(0),
        )
        total_tokens = sum(component.total_tokens for component in frozen_totals.values())
        duration_ms = max(
            round(
                (
                    datetime.fromisoformat(completed_at) - datetime.fromisoformat(started_at)
                ).total_seconds()
                * 1_000
            ),
            0,
        )
        failure = None
        if error is not None:
            diagnostics = diagnose_exception(error)
            failure = EpisodeTerminalFailure(
                code=getattr(error, "code", "unexpected_game_failure"),
                type=type(error).__name__,
                message=diagnostics.causes[0].message,
                call_id=getattr(error, "call_id", None),
                diagnostics=diagnostics,
            )
        result = EpisodeResult(
            run=EpisodeRun(
                run_id=request.run_id,
                episode_id=episode_id,
                subject=request.subject,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
            ),
            outcome=EpisodeOutcome(
                success=success,
                terminal_reason=terminal_reason,
                scoring_eligible=scoring_eligible,
                publication_eligible=publication_eligible,
            ),
            summary=EpisodeSummary(
                total_turns=guesser_call_count,
                counted_questions=counted_questions,
                guesser_call_count=guesser_call_count,
                ask_count=ask_count,
                guess_count=guess_count,
                rejected_guess_count=rejected_guess_count,
                oracle_unknown_count=oracle_unknown_count,
                oracle_quality=totals["oracle"].frozen_oracle_quality(),
                contract=guesser_contract_reliability(
                    evaluated_outputs=totals["guesser"].evaluated_outputs,
                    violations=totals["guesser"].contract_violations,
                    counted_penalties=totals["guesser"].contract_penalties,
                    affected_trials=int(totals["guesser"].contract_violations > 0),
                ),
                cache_status=cache_status,
                costs_usd=ComponentCosts(
                    guesser=frozen_totals["guesser"].cost_usd,
                    oracle=frozen_totals["oracle"].cost_usd,
                    validator=frozen_totals["validator"].cost_usd,
                    total=total_cost_usd,
                ),
                tokens=ComponentTokens(
                    guesser=frozen_totals["guesser"].total_tokens,
                    oracle=frozen_totals["oracle"].total_tokens,
                    validator=frozen_totals["validator"].total_tokens,
                    total=total_tokens,
                ),
            ),
            models=EpisodeModelVersions(
                under_test=LlmVersion(
                    role="guesser",
                    configuration_id=self.guesser_config.configuration_id,
                    requested_model=self.guesser_config.model,
                    requested_provider=self.guesser_config.provider,
                    resolved_models=tuple(sorted(totals["guesser"].resolved_models)),
                    resolved_providers=tuple(sorted(totals["guesser"].resolved_providers)),
                    reasoning_effort=self.guesser_config.reasoning_effort,
                    prompt_version=GUESSER_PROMPT_VERSION,
                ),
                oracle=LlmVersion(
                    role="oracle",
                    configuration_id=None,
                    requested_model=self.oracle_config.model,
                    requested_provider=self.oracle_config.provider,
                    resolved_models=tuple(sorted(totals["oracle"].resolved_models)),
                    resolved_providers=tuple(sorted(totals["oracle"].resolved_providers)),
                    reasoning_effort=self.oracle_config.reasoning_effort,
                    prompt_version=ORACLE_PROMPT_VERSION,
                ),
                validator=LlmVersion(
                    role="validator",
                    configuration_id=self.validator_config.configuration_id,
                    requested_model=self.validator_config.model,
                    requested_provider=self.validator_config.provider,
                    resolved_models=tuple(sorted(totals["validator"].resolved_models)),
                    resolved_providers=tuple(sorted(totals["validator"].resolved_providers)),
                    reasoning_effort=self.validator_config.reasoning_effort,
                    prompt_version=VALIDATOR_PROMPT_VERSION,
                ),
            ),
            turns=tuple(turns),
            guesser_conversation=(
                _reported_guesser_conversation(guesser_conversation)
                if self.policy.include_guesser_conversation
                else ()
            ),
            llm_details=EpisodeLlmDetails(
                guesser=GameLlmDetails(
                    configuration=self.guesser_config,
                    metrics=frozen_totals["guesser"],
                    provider_usage=totals["guesser"].provider_usage.frozen(),
                ),
                oracle=OracleLlmDetails(
                    configuration=self.oracle_config,
                    metrics=frozen_totals["oracle"],
                    provider_usage=totals["oracle"].frozen_oracle_provider_usage(),
                ),
                validator=GameLlmDetails(
                    configuration=self.validator_config,
                    metrics=frozen_totals["validator"],
                    provider_usage=totals["validator"].provider_usage.frozen(),
                ),
            ),
            failure=failure,
        )
        self.audit_writer.persist_episode_event(
            EpisodeFinishedEvent(
                event_id=f"EV-{uuid.uuid7().hex}",
                run_id=request.run_id,
                episode_id=episode_id,
                payload=EpisodeFinishedPayload(result=result, failure=failure),
                recorded_at=timestamp(),
            )
        )
        self.audit_writer.persist_episode_result(result)
        self.observer.observe(EpisodeFinishedProgress(result=result))
        return result

    def _turn_event(
        self,
        run_id: str,
        episode_id: str,
        guesser_call: GuesserCall,
        *,
        turn_number: int,
        adjudicator: Literal["oracle", "guess_validator"],
        adjudicator_call_id: str,
        answer: OracleAnswer,
        evidence: tuple[Evidence, ...],
        explanation: str | None,
        oracle_quality: OracleAdjudication | None,
        counted: bool,
        counted_questions: int,
        cache_status: CacheStatus,
    ) -> ActionTurnResult:
        turn = ActionTurnResult(
            turn_number=turn_number,
            action=guesser_call.action,
            adjudication=TurnAdjudication(
                component=adjudicator,
                call_id=adjudicator_call_id,
                answer=answer,
                evidence=evidence,
                explanation=explanation,
                oracle_quality=oracle_quality,
            ),
            counted=counted,
            counted_questions=counted_questions,
            guesser_call_id=guesser_call.call_id,
        )
        self.audit_writer.persist_episode_event(
            TurnResolvedEvent(
                event_id=f"EV-{uuid.uuid7().hex}",
                run_id=run_id,
                episode_id=episode_id,
                payload=TurnResolvedPayload(
                    turn=turn,
                    cache_status=cache_status,
                ),
                recorded_at=timestamp(),
            )
        )
        return turn

    def _contract_violation_event(
        self,
        run_id: str,
        episode_id: str,
        *,
        call_id: str | None,
        turn_number: int,
        violation_kind: ContractViolationKind,
        counted: bool,
        counted_questions: int,
        cache_status: CacheStatus,
    ) -> ContractViolationTurnResult:
        if call_id is None:
            raise ValueError("contract violation requires a Guesser call ID")
        turn = ContractViolationTurnResult(
            turn_number=turn_number,
            violation_kind=violation_kind,
            feedback_event="FORMAT_ERROR" if counted else None,
            counted=counted,
            counted_questions=counted_questions,
            guesser_call_id=call_id,
        )
        self.audit_writer.persist_episode_event(
            ContractViolationEvent(
                event_id=f"EV-{uuid.uuid7().hex}",
                run_id=run_id,
                episode_id=episode_id,
                payload=ContractViolationPayload(
                    turn=turn,
                    cache_status=cache_status,
                ),
                recorded_at=timestamp(),
            )
        )
        return turn

    @staticmethod
    def _add_error_trace(
        totals: _MutableTotals,
        error: Exception,
        config: ModelConfig,
    ) -> None:
        trace = provider_trace_from_error(error)
        if trace is not None:
            totals.add_metrics(metrics_from_trace(trace, config), trace)

    @staticmethod
    def _add_oracle_error_trace(totals: _MutableTotals, error: Exception) -> None:
        details = getattr(error, "details", {})
        if not isinstance(details, dict):
            return
        role_values = details.get("oracle_role_traces")
        traces: tuple[ProviderTrace, ...] = ()
        if isinstance(role_values, list):
            try:
                traces = tuple(
                    OracleProviderRoleTrace.model_validate(value).provider
                    for value in role_values
                )
            except ValidationError:
                traces = ()
        if not traces:
            value = details.get("provider_trace")
            if not isinstance(value, dict):
                return
            try:
                traces = (ProviderTrace.model_validate(value),)
            except ValidationError:
                return
        totals.calls += 1
        for trace in traces:
            totals.cost_usd += trace.usage.cost_usd or Decimal(0)
            totals.latency_ms += trace.latency_ms
            totals.input_tokens += trace.usage.input_tokens
            totals.cached_input_tokens += trace.usage.cached_input_tokens
            totals.cache_write_tokens += trace.usage.cache_write_tokens
            totals.output_tokens += trace.usage.output_tokens
            totals.reasoning_tokens += trace.usage.reasoning_tokens
            totals.recovery = combine_recovery_totals(
                totals.recovery,
                trace.recovery,
            )
            totals._add_route(trace)
