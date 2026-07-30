from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import TypeVar

from pydantic import ValidationError

from .config import ModelRouteConfig, OracleConfig
from .diagnostics import diagnose_exception
from .errors import OracleError, OracleProtocolError
from .models import (
    EvidenceReviewAuditTrace,
    EvidenceReviewRequest,
    EvidenceReviewResult,
    JsonObject,
    OracleAdjudication,
    OracleAnswer,
    OracleAuditTrace,
    OracleCall,
    OracleDecisionPath,
    OracleMetrics,
    OracleProviderRoleTrace,
    OracleQuestionType,
    OracleRequest,
    OracleResult,
    OracleRole,
    OracleRoleMetrics,
    ProviderTrace,
    RecoveryReason,
    StrictModel,
)
from .prompt import (
    PROMPT_VERSION,
    evidence_review_prompt_version,
    prompt_hash,
    render_evidence_review_messages,
    render_messages,
)
from .provider import OracleProvider, ProviderRequest
from .question_type import classify_oracle_question
from .recovery import (
    combine_recovery_metrics,
    combine_usage,
    current_recovery_budget,
    logical_recovery_budget,
    mark_recovery_exhausted,
    merge_provider_traces,
)
from .sinks import AuditFailure, OracleAuditSink, OracleFailureRecord, OracleSuccessRecord
from .util import (
    canonical_json,
    openrouter_provider_matches,
    safe_json_value,
    sha256_text,
    timestamp,
)

ResultT = TypeVar("ResultT", bound=StrictModel)


def validate_oracle_provider_trace(
    trace: ProviderTrace,
    *,
    config: ModelRouteConfig,
    role: OracleRole,
) -> None:
    if (trace.response_cache_status or "").casefold() == "hit":
        raise OracleProtocolError(
            "OpenRouter response cache replay is prohibited",
            code="response_cache_replay",
            details={"provider_trace": trace.model_dump(mode="json")},
        )
    if role is OracleRole.ORACLE and trace.usage.search_count < 1:
        raise OracleProtocolError(
            "Oracle returned an answer without recorded web search",
            code="web_search_not_used",
            details={"provider_trace": trace.model_dump(mode="json")},
        )
    if role is not OracleRole.ORACLE and trace.usage.search_count != 0:
        raise OracleProtocolError(
            f"{role.value} unexpectedly used web search",
            code=f"{role.value}_web_search_used",
            details={"provider_trace": trace.model_dump(mode="json")},
        )
    if trace.requested_model != config.model or trace.requested_provider != config.provider:
        raise OracleProtocolError(
            "provider trace differs from the configured exact route",
            code="requested_route_mismatch",
            details={"provider_trace": trace.model_dump(mode="json")},
        )
    if trace.resolved_model != trace.requested_model:
        raise OracleProtocolError(
            "resolved model differs from the configured exact model",
            code="resolved_model_mismatch",
            details={"provider_trace": trace.model_dump(mode="json")},
        )
    if trace.resolved_provider is not None and not openrouter_provider_matches(
        trace.requested_provider,
        trace.resolved_provider,
    ):
        raise OracleProtocolError(
            "resolved provider differs from the configured exact provider",
            code="resolved_provider_mismatch",
            details={"provider_trace": trace.model_dump(mode="json")},
        )


class Oracle:
    """Research, blind review, and blind judgment behind one typed adjudication call."""

    def __init__(
        self,
        provider: OracleProvider,
        reviewer_provider: OracleProvider,
        judge_provider: OracleProvider,
        audit_writer: OracleAuditSink,
        config: OracleConfig,
    ):
        self.provider = provider
        self.reviewer_provider = reviewer_provider
        self.judge_provider = judge_provider
        self.audit_writer = audit_writer
        self.config = config

    def ask(self, request: OracleRequest) -> OracleCall:
        call_id = f"OC-{uuid.uuid7().hex}"
        oracle_messages = render_messages(request)
        active_role = OracleRole.ORACLE
        active_messages = oracle_messages
        active_prompt_version = PROMPT_VERSION
        active_trace: ProviderTrace | None = None
        role_traces: list[OracleProviderRoleTrace] = []
        try:
            self.audit_writer.prepare_run(request.run_id)
        except OracleError as error:
            error.call_id = call_id
            raise
        try:
            oracle_provider_request = ProviderRequest(
                messages=oracle_messages,
                output_schema=OracleResult.model_json_schema(),
                response_schema_name="oracle_result",
                session_id=f"deep20-oracle-{request.run_id}-{request.subject.target_id}",
                prompt_cache_key=self._prompt_cache_key(
                    role=OracleRole.ORACLE,
                    prompt_version=PROMPT_VERSION,
                    request=request,
                ),
            )
            result, oracle_trace = self._complete_structured_result(
                provider=self.provider,
                provider_request=oracle_provider_request,
                result_model=OracleResult,
                config=self.config,
                role=OracleRole.ORACLE,
            )
            active_trace = oracle_trace
            role_traces.append(
                OracleProviderRoleTrace(
                    role=OracleRole.ORACLE,
                    provider=oracle_trace,
                )
            )
            reviewer_audit: EvidenceReviewAuditTrace | None = None
            judge_audit: EvidenceReviewAuditTrace | None = None
            question_type: OracleQuestionType = classify_oracle_question(
                request.question
            )

            if result.answer is OracleAnswer.UNKNOWN:
                adjudication = OracleAdjudication(
                    oracle_answer=result.answer,
                    question_type=question_type,
                    disagreement=False,
                    judge_invoked=False,
                    final_answer=OracleAnswer.UNKNOWN,
                    decision_path=OracleDecisionPath.ORACLE_UNKNOWN,
                )
            else:
                review_request = EvidenceReviewRequest(
                    subject=request.subject,
                    question=request.question,
                    evidence=result.evidence,
                )
                active_role = OracleRole.REVIEWER
                active_prompt_version = evidence_review_prompt_version(
                    OracleRole.REVIEWER
                )
                active_messages = render_evidence_review_messages(
                    review_request,
                    role=OracleRole.REVIEWER,
                )
                reviewer_provider_request = self._review_provider_request(
                    request=request,
                    review_request=review_request,
                    role=active_role,
                    messages=active_messages,
                    prompt_version=active_prompt_version,
                )
                reviewer_result, reviewer_trace = self._complete_structured_result(
                    provider=self.reviewer_provider,
                    provider_request=reviewer_provider_request,
                    result_model=EvidenceReviewResult,
                    config=self.config.reviewer,
                    role=active_role,
                    validate=lambda decision: decision.validate_evidence_count(
                        len(review_request.evidence)
                    ),
                )
                active_trace = reviewer_trace
                role_traces.append(
                    OracleProviderRoleTrace(
                        role=OracleRole.REVIEWER,
                        provider=reviewer_trace,
                    )
                )
                reviewer_audit = EvidenceReviewAuditTrace(
                    role=OracleRole.REVIEWER,
                    prompt_version=active_prompt_version,
                    prompt_hash=prompt_hash(active_messages),
                    messages=active_messages,
                    provider=reviewer_trace,
                )
                disagreement = reviewer_result.answer is not result.answer
                judge_result: EvidenceReviewResult | None = None
                if disagreement:
                    active_role = OracleRole.JUDGE
                    active_prompt_version = evidence_review_prompt_version(
                        OracleRole.JUDGE
                    )
                    active_messages = render_evidence_review_messages(
                        review_request,
                        role=OracleRole.JUDGE,
                    )
                    judge_provider_request = self._review_provider_request(
                        request=request,
                        review_request=review_request,
                        role=active_role,
                        messages=active_messages,
                        prompt_version=active_prompt_version,
                    )
                    judge_result, judge_trace = self._complete_structured_result(
                        provider=self.judge_provider,
                        provider_request=judge_provider_request,
                        result_model=EvidenceReviewResult,
                        config=self.config.judge,
                        role=active_role,
                        validate=lambda decision: decision.validate_evidence_count(
                            len(review_request.evidence)
                        ),
                    )
                    active_trace = judge_trace
                    role_traces.append(
                        OracleProviderRoleTrace(
                            role=OracleRole.JUDGE,
                            provider=judge_trace,
                        )
                    )
                    judge_audit = EvidenceReviewAuditTrace(
                        role=OracleRole.JUDGE,
                        prompt_version=active_prompt_version,
                        prompt_hash=prompt_hash(active_messages),
                        messages=active_messages,
                        provider=judge_trace,
                    )
                    adjudication = OracleAdjudication(
                        oracle_answer=result.answer,
                        question_type=question_type,
                        reviewer=reviewer_result,
                        judge=judge_result,
                        disagreement=True,
                        judge_invoked=True,
                        final_answer=judge_result.answer,
                        decision_path=OracleDecisionPath.JUDGE_DISAGREEMENT,
                    )
                else:
                    adjudication = OracleAdjudication(
                        oracle_answer=result.answer,
                        question_type=question_type,
                        reviewer=reviewer_result,
                        disagreement=False,
                        judge_invoked=False,
                        final_answer=result.answer,
                        decision_path=OracleDecisionPath.REVIEWER_AGREEMENT,
                    )

            audit = OracleAuditTrace(
                prompt_version=PROMPT_VERSION,
                prompt_hash=prompt_hash(oracle_messages),
                messages=oracle_messages,
                evidence_validation="model_reported",
                provider=oracle_trace,
                reviewer=reviewer_audit,
                judge=judge_audit,
            )
            metrics = self._metrics(audit)
            return self.audit_writer.persist_oracle_success(
                OracleSuccessRecord(
                    call_id=call_id,
                    request=request,
                    result=result,
                    adjudication=adjudication,
                    metrics=metrics,
                    audit=audit,
                    recorded_at=timestamp(),
                )
            )
        except Exception as error:
            if isinstance(error, OracleError):
                error.call_id = call_id
                details_trace = error.details.get("provider_trace")
                if isinstance(details_trace, dict):
                    active_trace = self._valid_trace_or_none(details_trace) or active_trace
                if active_trace is not None and (
                    not role_traces
                    or role_traces[-1].role is not active_role
                    or role_traces[-1].provider != active_trace
                ):
                    role_traces.append(
                        OracleProviderRoleTrace(
                            role=active_role,
                            provider=active_trace,
                        )
                    )
                error.details["oracle_role_traces"] = [
                    item.model_dump(mode="json") for item in role_traces
                ]
            try:
                details = safe_json_value(getattr(error, "details", {}))
                diagnostics = diagnose_exception(error)
                self.audit_writer.persist_oracle_failure(
                    OracleFailureRecord(
                        call_id=call_id,
                        request=request,
                        component=active_role,
                        prompt_version=active_prompt_version,
                        prompt_hash=prompt_hash(active_messages),
                        messages=active_messages,
                        failure=AuditFailure(
                            code=getattr(error, "code", "unexpected_error"),
                            type=type(error).__name__,
                            message=diagnostics.causes[0].message,
                            details=details if isinstance(details, dict) else {"value": details},
                            diagnostics=diagnostics,
                        ),
                        provider_trace=active_trace,
                        recorded_at=timestamp(),
                        role_traces=tuple(role_traces),
                    )
                )
            except Exception as audit_error:
                if isinstance(audit_error, OracleError):
                    audit_error.call_id = call_id
                raise audit_error from error
            if isinstance(error, OracleError):
                raise
            diagnostics = diagnose_exception(error)
            raise OracleProtocolError(
                f"unexpected {active_role.value} failure",
                code=f"unexpected_{active_role.value}_failure",
                call_id=call_id,
                details={
                    "exception_type": type(error).__name__,
                    "diagnostics": diagnostics.model_dump(mode="json"),
                },
            ) from error

    def _review_provider_request(
        self,
        *,
        request: OracleRequest,
        review_request: EvidenceReviewRequest,
        role: OracleRole,
        messages: tuple[dict[str, str], ...],
        prompt_version: str,
    ) -> ProviderRequest:
        if role not in {OracleRole.REVIEWER, OracleRole.JUDGE}:
            raise ValueError("evidence review requests require Reviewer or Judge role")
        return ProviderRequest(
            messages=messages,
            output_schema=EvidenceReviewResult.model_json_schema(),
            response_schema_name=f"{role.value}_result",
            session_id=(
                f"deep20-oracle-{role.value}-{request.run_id}-{request.subject.target_id}"
            ),
            prompt_cache_key=self._prompt_cache_key(
                role=role,
                prompt_version=prompt_version,
                request=request,
            ),
        )

    @staticmethod
    def _prompt_cache_key(
        *,
        role: OracleRole,
        prompt_version: str,
        request: OracleRequest,
    ) -> str:
        role_code = {
            OracleRole.ORACLE: "o",
            OracleRole.REVIEWER: "r",
            OracleRole.JUDGE: "j",
        }[role]
        return (
            f"deep20-o-{role_code}-"
            + sha256_text(
                canonical_json(
                    {
                        "role": role,
                        "prompt_version": prompt_version,
                        "subject": request.subject.model_dump(mode="json"),
                    }
                )
            )[:40]
        )

    def _complete_structured_result(
        self,
        *,
        provider: OracleProvider,
        provider_request: ProviderRequest,
        result_model: type[ResultT],
        config: ModelRouteConfig,
        role: OracleRole,
        validate: Callable[[ResultT], ResultT] | None = None,
    ) -> tuple[ResultT, ProviderTrace]:
        def parse(raw_output: str) -> ResultT:
            parsed = result_model.model_validate_json(raw_output)
            return validate(parsed) if validate is not None else parsed

        with logical_recovery_budget(config.recovery, config.timeout_seconds):
            exchange = provider.complete(provider_request)
            provider_trace = exchange.trace
            validate_oracle_provider_trace(provider_trace, config=config, role=role)
            try:
                return parse(exchange.raw_output), provider_trace
            except (ValidationError, ValueError) as first_error:
                budget = current_recovery_budget()
                if (
                    config.recovery.invalid_output_retries == 0
                    or provider_trace.request_attempts
                    >= config.recovery.max_request_attempts
                    or (budget is not None and budget.remaining_seconds <= 0)
                ):
                    provider_trace = mark_recovery_exhausted(provider_trace)
                    raise self._invalid_output_error(
                        first_error,
                        provider_trace,
                        role=role,
                    ) from first_error
                try:
                    retry_exchange = provider.complete(provider_request)
                except Exception as retry_error:
                    retry_trace = self._trace_from_error(retry_error)
                    if retry_trace is not None:
                        provider_trace = merge_provider_traces(
                            provider_trace,
                            retry_trace,
                            reason=self._invalid_output_reason(role),
                            recovered=False,
                            exhausted=True,
                        )
                        if isinstance(retry_error, OracleError):
                            retry_error.details["provider_trace"] = (
                                provider_trace.model_dump(mode="json")
                            )
                    raise
                provider_trace = merge_provider_traces(
                    provider_trace,
                    retry_exchange.trace,
                    reason=self._invalid_output_reason(role),
                    recovered=True,
                )
                validate_oracle_provider_trace(provider_trace, config=config, role=role)
                try:
                    return parse(retry_exchange.raw_output), provider_trace
                except (ValidationError, ValueError) as error:
                    provider_trace = mark_recovery_exhausted(
                        provider_trace.model_copy(
                            update={
                                "recovery": provider_trace.recovery.model_copy(
                                    update={"recovered_calls": 0}
                                )
                            }
                        )
                    )
                    raise self._invalid_output_error(
                        error,
                        provider_trace,
                        role=role,
                    ) from error

    @staticmethod
    def _role_metrics(trace: ProviderTrace) -> OracleRoleMetrics:
        usage = trace.usage
        return OracleRoleMetrics(
            cost_usd=usage.cost_usd,
            latency_ms=trace.latency_ms,
            input_tokens=usage.input_tokens,
            cached_input_tokens=usage.cached_input_tokens,
            cache_write_tokens=usage.cache_write_tokens,
            output_tokens=usage.output_tokens,
            reasoning_tokens=usage.reasoning_tokens,
            search_count=usage.search_count,
            recovery=trace.recovery,
        )

    @classmethod
    def _metrics(cls, audit: OracleAuditTrace) -> OracleMetrics:
        traces = [
            audit.provider,
            *(
                (audit.reviewer.provider,)
                if audit.reviewer is not None
                else ()
            ),
            *((audit.judge.provider,) if audit.judge is not None else ()),
        ]
        usage = traces[0].usage
        for trace in traces[1:]:
            usage = combine_usage(usage, trace.usage)
        return OracleMetrics(
            cost_usd=usage.cost_usd,
            latency_ms=sum(trace.latency_ms for trace in traces),
            input_tokens=usage.input_tokens,
            cached_input_tokens=usage.cached_input_tokens,
            cache_write_tokens=usage.cache_write_tokens,
            output_tokens=usage.output_tokens,
            reasoning_tokens=usage.reasoning_tokens,
            search_count=usage.search_count,
            recovery=combine_recovery_metrics(*(trace.recovery for trace in traces)),
            oracle=cls._role_metrics(audit.provider),
            reviewer=(
                cls._role_metrics(audit.reviewer.provider)
                if audit.reviewer is not None
                else None
            ),
            judge=(
                cls._role_metrics(audit.judge.provider)
                if audit.judge is not None
                else None
            ),
        )

    @staticmethod
    def _valid_trace_or_none(value: JsonObject) -> ProviderTrace | None:
        try:
            return ProviderTrace.model_validate(value)
        except ValidationError:
            return None

    @classmethod
    def _trace_from_error(cls, error: Exception) -> ProviderTrace | None:
        details = getattr(error, "details", {})
        value = details.get("provider_trace") if isinstance(details, dict) else None
        return cls._valid_trace_or_none(value) if isinstance(value, dict) else None

    @staticmethod
    def _invalid_output_reason(role: OracleRole) -> RecoveryReason:
        return {
            OracleRole.ORACLE: RecoveryReason.INVALID_ORACLE_OUTPUT,
            OracleRole.REVIEWER: RecoveryReason.INVALID_REVIEWER_OUTPUT,
            OracleRole.JUDGE: RecoveryReason.INVALID_JUDGE_OUTPUT,
        }[role]

    @staticmethod
    def _invalid_output_error(
        error: ValidationError | ValueError,
        trace: ProviderTrace,
        *,
        role: OracleRole,
    ) -> OracleProtocolError:
        if isinstance(error, ValidationError):
            provider_validation_errors = error.errors(include_input=False)
            validation_errors = safe_json_value(provider_validation_errors)
            issue_summary = ", ".join(
                f"{'.'.join(str(part) for part in issue['loc'])}:{issue['type']}"
                for issue in provider_validation_errors[:5]
            )
        else:
            validation_errors = safe_json_value(
                [{"type": "value_error", "loc": (), "msg": str(error)}]
            )
            issue_summary = "semantic_validation:value_error"
        return OracleProtocolError(
            f"provider output did not match the {role.value} result schema"
            + (f" ({issue_summary})" if issue_summary else ""),
            code="invalid_structured_output",
            details={
                "component": role,
                "validation_errors": validation_errors,
                "provider_trace": trace.model_dump(mode="json"),
            },
        )
