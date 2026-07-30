from __future__ import annotations

import uuid

from deep20_oracle.diagnostics import diagnose_exception
from deep20_oracle.models import ProviderTrace, RecoveryReason, Subject
from deep20_oracle.recovery import (
    current_recovery_budget,
    logical_recovery_budget,
    mark_recovery_exhausted,
    merge_provider_traces,
)
from deep20_oracle.util import canonical_json, safe_json_value, sha256_text, timestamp
from pydantic import ValidationError

from .config import ModelConfig
from .errors import GameError, ValidatorProtocolError
from .models import (
    ActionType,
    FailedGameCallAudit,
    GameCallAudit,
    GameComponentFailure,
    GameProviderRequest,
    GuesserAction,
    GuessValidationResult,
    GuessValidatorCall,
    ValidatorFailureRecord,
    ValidatorSuccessRecord,
)
from .prompt import VALIDATOR_PROMPT_VERSION, prompt_hash, validator_messages
from .provider import GameModelProvider
from .service_util import (
    metrics_from_trace,
    provider_trace_from_error,
    validate_game_trace,
)
from .sinks import GameAuditSink


class GuessValidator:
    """Strict, independent, no-web semantic identity adjudicator."""

    def __init__(
        self,
        provider: GameModelProvider,
        audit_writer: GameAuditSink,
        config: ModelConfig,
    ):
        self.provider = provider
        self.audit_writer = audit_writer
        self.config = config

    def validate(
        self,
        *,
        run_id: str,
        episode_id: str,
        subject: Subject,
        guess: GuesserAction,
    ) -> GuessValidatorCall:
        if guess.action is not ActionType.GUESS:
            raise ValueError("Guess Validator requires a GUESS action")
        call_id = f"VC-{uuid.uuid7().hex}"
        messages = validator_messages(subject, guess)
        session_id = f"deep20-validator-{episode_id}"
        cache_material = canonical_json(
            {
                "configuration_id": self.config.configuration_id,
                "prompt_version": VALIDATOR_PROMPT_VERSION,
                "subject": subject.model_dump(mode="json"),
            }
        )
        cache_key = f"deep20-validator-{sha256_text(cache_material)[:40]}"
        rendered_hash = prompt_hash(messages)
        trace: ProviderTrace | None = None
        try:
            provider_request = GameProviderRequest(
                messages=messages,
                output_schema=GuessValidationResult.model_json_schema(),
                schema_name="guess_validation_result",
                session_id=session_id,
                prompt_cache_key=cache_key,
            )
            result, trace = self._complete_validation(provider_request)
            audit = GameCallAudit(
                prompt_version=VALIDATOR_PROMPT_VERSION,
                prompt_hash=rendered_hash,
                messages=messages,
                session_id=session_id,
                prompt_cache_key=cache_key,
                provider=trace,
            )
            metrics = metrics_from_trace(trace, self.config)
            call = self.audit_writer.persist_validator_success(
                ValidatorSuccessRecord(
                    call_id=call_id,
                    run_id=run_id,
                    episode_id=episode_id,
                    subject=subject,
                    guess=guess,
                    result=result,
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
            self.audit_writer.persist_validator_failure(
                ValidatorFailureRecord(
                    call_id=call_id,
                    run_id=run_id,
                    episode_id=episode_id,
                    subject=subject,
                    guess=guess,
                    metrics=metrics_from_trace(trace, self.config) if trace else None,
                    audit=FailedGameCallAudit(
                        prompt_version=VALIDATOR_PROMPT_VERSION,
                        prompt_hash=rendered_hash,
                        messages=messages,
                        session_id=session_id,
                        prompt_cache_key=cache_key,
                        provider=trace,
                    ),
                    failure=GameComponentFailure(
                        code=getattr(error, "code", "unexpected_validator_failure"),
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
            raise ValidatorProtocolError(
                "unexpected Guess Validator failure",
                code="unexpected_validator_failure",
                call_id=call_id,
                details={
                    "exception_type": type(error).__name__,
                    "diagnostics": diagnostics.model_dump(mode="json"),
                },
            ) from error

    def _complete_validation(
        self,
        provider_request: GameProviderRequest,
    ) -> tuple[GuessValidationResult, ProviderTrace]:
        with logical_recovery_budget(
            self.config.recovery,
            self.config.timeout_seconds,
        ):
            exchange = self.provider.complete(provider_request)
            trace = exchange.trace
            validate_game_trace(trace, self.config)
            try:
                return (
                    GuessValidationResult.model_validate_json(exchange.raw_output),
                    trace,
                )
            except ValidationError as first_error:
                budget = current_recovery_budget()
                if (
                    self.config.recovery.invalid_output_retries == 0
                    or trace.request_attempts
                    >= self.config.recovery.max_request_attempts
                    or (budget is not None and budget.remaining_seconds <= 0)
                ):
                    trace = mark_recovery_exhausted(trace)
                    raise self._invalid_output_error(first_error, trace) from first_error
                try:
                    retry_exchange = self.provider.complete(provider_request)
                except Exception as retry_error:
                    retry_trace = provider_trace_from_error(retry_error)
                    if retry_trace is not None:
                        trace = merge_provider_traces(
                            trace,
                            retry_trace,
                            reason=RecoveryReason.INVALID_VALIDATOR_OUTPUT,
                            recovered=False,
                            exhausted=True,
                        )
                        if isinstance(retry_error, GameError):
                            retry_error.details["provider_trace"] = trace.model_dump(
                                mode="json"
                            )
                    raise
                trace = merge_provider_traces(
                    trace,
                    retry_exchange.trace,
                    reason=RecoveryReason.INVALID_VALIDATOR_OUTPUT,
                    recovered=True,
                )
                validate_game_trace(trace, self.config)
                try:
                    return (
                        GuessValidationResult.model_validate_json(
                            retry_exchange.raw_output
                        ),
                        trace,
                    )
                except ValidationError as error:
                    trace = mark_recovery_exhausted(
                        trace.model_copy(
                            update={
                                "recovery": trace.recovery.model_copy(
                                    update={"recovered_calls": 0}
                                )
                            }
                        )
                    )
                    raise self._invalid_output_error(error, trace) from error

    @staticmethod
    def _invalid_output_error(
        error: ValidationError,
        trace: ProviderTrace,
    ) -> ValidatorProtocolError:
        return ValidatorProtocolError(
            "provider output did not match the Guess Validator schema",
            code="invalid_validator_output",
            details={
                "validation_errors": safe_json_value(
                    error.errors(include_input=False)
                ),
                "provider_trace": trace.model_dump(mode="json"),
            },
        )
