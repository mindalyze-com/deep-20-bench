from __future__ import annotations

import uuid

from deep20_oracle.diagnostics import diagnose_exception
from deep20_oracle.models import JsonObject, ProviderTrace
from deep20_oracle.util import canonical_json, safe_json_value, sha256_text, timestamp
from pydantic import ValidationError

from .config import GamePolicy, ModelConfig
from .errors import GameError, GameProviderError, GuesserProtocolError
from .models import (
    GUESSER_ACTION_SCHEMA_NAME,
    ContractViolationKind,
    FailedGameCallAudit,
    GameCallAudit,
    GameComponentFailure,
    GameProviderRequest,
    GuesserAction,
    GuesserCall,
    GuesserFailureRecord,
    GuesserSamplingDecision,
    GuesserSuccessRecord,
    guesser_action_output_schema,
    parse_guesser_action_output,
)
from .prompt import GUESSER_PROMPT_VERSION, prompt_hash, validate_guesser_prompt_nonce
from .provider import GameModelProvider
from .service_util import (
    metrics_from_trace,
    provider_trace_from_error,
    validate_game_trace,
)
from .sinks import GameAuditSink

_PROVIDER_OUTPUT_VIOLATION_KINDS: dict[str, ContractViolationKind] = {
    "provider_output_limit_exceeded": ContractViolationKind.OUTPUT_LIMIT_EXCEEDED,
    "provider_empty_response": ContractViolationKind.EMPTY_OUTPUT,
    "provider_incomplete_response": ContractViolationKind.INCOMPLETE_OUTPUT,
}


class Guesser:
    """One audited, session-stable action from the model under evaluation."""

    def __init__(
        self,
        provider: GameModelProvider,
        audit_writer: GameAuditSink,
        config: ModelConfig,
        policy: GamePolicy,
    ):
        self.provider = provider
        self.audit_writer = audit_writer
        self.config = config
        self.policy = policy

    def next_action(
        self,
        *,
        run_id: str,
        episode_id: str,
        messages: tuple[dict[str, str], ...],
        sampling: GuesserSamplingDecision,
    ) -> GuesserCall:
        call_id = f"GC-{uuid.uuid7().hex}"
        session_id = f"deep20-guesser-{episode_id}"
        output_schema = guesser_action_output_schema()
        schema_hash = sha256_text(canonical_json(output_schema))
        cache_material = canonical_json(
            {
                "configuration_id": self.config.configuration_id,
                "prompt_version": GUESSER_PROMPT_VERSION,
                "schema_hash": schema_hash,
                "max_questions": self.policy.max_questions,
            }
        )
        cache_key = f"deep20-guesser-{sha256_text(cache_material)[:40]}"
        rendered_messages = messages
        rendered_hash = prompt_hash(rendered_messages)
        trace: ProviderTrace | None = None
        try:
            validate_guesser_prompt_nonce(rendered_messages, sampling.prompt_nonce)
            provider_request = GameProviderRequest(
                messages=rendered_messages,
                output_schema=output_schema,
                schema_name=GUESSER_ACTION_SCHEMA_NAME,
                session_id=session_id,
                prompt_cache_key=cache_key,
                seed=sampling.seed,
            )
            action, trace = self._complete_action(provider_request)
            audit = GameCallAudit(
                prompt_version=GUESSER_PROMPT_VERSION,
                prompt_hash=rendered_hash,
                messages=rendered_messages,
                session_id=session_id,
                prompt_cache_key=cache_key,
                sampling=sampling,
                provider=trace,
            )
            metrics = metrics_from_trace(trace, self.config)
            call = self.audit_writer.persist_guesser_success(
                GuesserSuccessRecord(
                    call_id=call_id,
                    run_id=run_id,
                    episode_id=episode_id,
                    action=action,
                    metrics=metrics,
                    audit=audit,
                    recorded_at=timestamp(),
                )
            )
            return call
        except Exception as error:
            if isinstance(error, GameError):
                error.call_id = call_id
                if trace is not None and "provider_trace" not in error.details:
                    error.details["provider_trace"] = trace.model_dump(mode="json")
            if trace is None:
                trace = provider_trace_from_error(error)
            details = safe_json_value(getattr(error, "details", {}))
            diagnostics = diagnose_exception(error)
            self.audit_writer.persist_guesser_failure(
                GuesserFailureRecord(
                    call_id=call_id,
                    run_id=run_id,
                    episode_id=episode_id,
                    metrics=metrics_from_trace(trace, self.config) if trace else None,
                    audit=FailedGameCallAudit(
                        prompt_version=GUESSER_PROMPT_VERSION,
                        prompt_hash=rendered_hash,
                        messages=rendered_messages,
                        session_id=session_id,
                        prompt_cache_key=cache_key,
                        sampling=sampling,
                        provider=trace,
                    ),
                    failure=GameComponentFailure(
                        code=getattr(error, "code", "unexpected_guesser_failure"),
                        type=type(error).__name__,
                        message=diagnostics.causes[0].message,
                        details=details if isinstance(details, dict) else {"value": details},
                        diagnostics=diagnostics,
                    ),
                    recorded_at=timestamp(),
                )
            )
            if isinstance(error, GameError):
                raise
            raise GuesserProtocolError(
                "unexpected Guesser failure",
                code="unexpected_guesser_failure",
                call_id=call_id,
                details={
                    "exception_type": type(error).__name__,
                    "diagnostics": diagnostics.model_dump(mode="json"),
                },
            ) from error

    def _complete_action(
        self,
        provider_request: GameProviderRequest,
    ) -> tuple[GuesserAction, ProviderTrace]:
        try:
            exchange = self.provider.complete(provider_request)
        except GameProviderError as error:
            violation_kind = _PROVIDER_OUTPUT_VIOLATION_KINDS.get(error.code)
            if violation_kind is None:
                raise
            raise self._model_output_violation_error(error, violation_kind) from error
        trace = exchange.trace
        validate_game_trace(trace, self.config)
        try:
            return parse_guesser_action_output(exchange.raw_output), trace
        except ValidationError as error:
            raise self._invalid_output_error(error, trace) from error

    @staticmethod
    def _model_output_violation_error(
        error: GameProviderError,
        violation_kind: ContractViolationKind,
    ) -> GuesserProtocolError:
        details: JsonObject = {
            "violation_kind": violation_kind.value,
            "provider_failure_code": error.code,
        }
        provider_trace = error.details.get("provider_trace")
        if isinstance(provider_trace, dict):
            details["provider_trace"] = provider_trace
        return GuesserProtocolError(
            "the model under test did not return a complete structured action",
            code="invalid_guesser_output",
            details=details,
        )

    @staticmethod
    def _invalid_output_error(
        error: ValidationError,
        trace: ProviderTrace,
    ) -> GuesserProtocolError:
        violation_kind = (
            ContractViolationKind.INVALID_JSON
            if any(item.get("type") == "json_invalid" for item in error.errors())
            else ContractViolationKind.INVALID_ACTION
        )
        return GuesserProtocolError(
            "provider output did not match the Guesser action schema",
            code="invalid_guesser_output",
            details={
                "violation_kind": violation_kind.value,
                "validation_errors": safe_json_value(
                    error.errors(include_input=False)
                ),
                "provider_trace": trace.model_dump(mode="json"),
            },
        )
