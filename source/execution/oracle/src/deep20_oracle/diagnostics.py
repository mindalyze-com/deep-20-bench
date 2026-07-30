from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from pydantic import JsonValue, ValidationError

from .models import (
    FailureCause,
    FailureDiagnostics,
    FailureFrame,
    JsonObject,
    ProviderFailureDiagnostics,
    ProviderTrace,
)

_MAX_CAUSES = 8
_MAX_FRAMES = 24
_MAX_SEQUENCE_ITEMS = 20
_MAX_METADATA_DEPTH = 6
_REDACTED = "[REDACTED]"
_SENSITIVE_KEYS = (
    "annotation",
    "api_key",
    "authorization",
    "citation",
    "credential",
    "evidence",
    "guess",
    "header",
    "message_history",
    "messages",
    "password",
    "prompt",
    "provider_trace",
    "raw_output",
    "request",
    "response",
    "secret",
    "subject",
)
_SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(
        r"(?i)\b(api[_-]?key|authorization|bearer|password|secret)"
        r"(\s*[:=]\s*|\s+)([^\s,;]+)"
    ),
)

_OPENROUTER_ERROR_CODES = {
    "authentication": "provider_authentication_failed",
    "payment_required": "provider_payment_required",
    "permission_denied": "provider_permission_denied",
    "content_policy_violation": "provider_content_policy_blocked",
    "rate_limit_exceeded": "provider_rate_limited",
    "provider_overloaded": "provider_overloaded",
    "provider_unavailable": "provider_unavailable",
    "timeout": "provider_timeout",
    "invalid_request": "provider_invalid_request",
    "invalid_prompt": "provider_invalid_request",
    "context_length_exceeded": "provider_invalid_request",
    "max_tokens_exceeded": "provider_invalid_request",
    "token_limit_exceeded": "provider_invalid_request",
    "string_too_long": "provider_invalid_request",
    "not_found": "provider_not_found",
    "precondition_failed": "provider_precondition_failed",
    "payload_too_large": "provider_payload_too_large",
    "unprocessable": "provider_unprocessable_request",
}

_HTTP_ERROR_CODES = {
    400: "provider_invalid_request",
    401: "provider_authentication_failed",
    402: "provider_payment_required",
    403: "provider_permission_denied",
    404: "provider_not_found",
    408: "provider_timeout",
    412: "provider_precondition_failed",
    413: "provider_payload_too_large",
    422: "provider_unprocessable_request",
    429: "provider_rate_limited",
    502: "provider_unavailable",
    503: "provider_overloaded",
}


def provider_failure_code(
    raw_response: Mapping[str, object] | None,
    status_code: int | None,
) -> str:
    """Reduce an OpenRouter response to a stable failure category."""
    error_type = _provider_error_type(raw_response)
    if error_type is not None:
        code = _OPENROUTER_ERROR_CODES.get(error_type.casefold())
        if code is not None:
            return code
    if status_code is None:
        return "provider_request_failed"
    return _HTTP_ERROR_CODES.get(status_code, "provider_request_failed")


def diagnose_exception(error: BaseException) -> FailureDiagnostics:
    """Build a bounded diagnostic projection without private prompts or raw provider data."""
    causes: list[FailureCause] = []
    frames: list[FailureFrame] = []
    provider: ProviderFailureDiagnostics | None = None
    metadata: JsonObject = {}
    seen: set[int] = set()
    current: BaseException | None = error
    exception_index = 0
    while current is not None and id(current) not in seen and exception_index < _MAX_CAUSES:
        seen.add(id(current))
        causes.append(
            FailureCause(
                exception_type=type(current).__name__,
                module=type(current).__module__,
                message=_exception_message(current),
            )
        )
        traceback = current.__traceback__
        while traceback is not None and len(frames) < _MAX_FRAMES:
            frames.append(
                FailureFrame(
                    exception_index=exception_index,
                    module=str(traceback.tb_frame.f_globals.get("__name__", "<unknown>")),
                    function=traceback.tb_frame.f_code.co_name,
                    line=traceback.tb_lineno,
                )
            )
            traceback = traceback.tb_next
        details = getattr(current, "details", None)
        if isinstance(details, Mapping):
            if provider is None:
                provider = _provider_diagnostics(details.get("provider_trace"))
            sanitized = _sanitize_mapping(details, depth=0)
            for key, value in sanitized.items():
                metadata.setdefault(key, value)
        current = current.__cause__ or current.__context__
        exception_index += 1
    return FailureDiagnostics(
        causes=tuple(causes),
        frames=tuple(frames),
        provider=provider,
        metadata=metadata,
    )


def _exception_message(error: BaseException) -> str:
    if isinstance(error, ValidationError):
        return "validation failed"
    return _redact(str(error))[:2_000]


def _provider_diagnostics(value: object) -> ProviderFailureDiagnostics | None:
    if not isinstance(value, Mapping):
        return None
    try:
        trace = ProviderTrace.model_validate(value)
    except ValidationError:
        return None
    error_type = _provider_error_type(trace.response)
    error_code, error_message = _provider_error_fields(trace.response)
    return ProviderFailureDiagnostics(
        http_status_code=trace.http_status_code,
        error_type=error_type,
        error_code=error_code,
        message=_redact(error_message)[:2_000] if error_message is not None else None,
        requested_model=trace.requested_model,
        resolved_model=trace.resolved_model,
        requested_provider=trace.requested_provider,
        resolved_provider=trace.resolved_provider,
        fallback_occurred=trace.fallback_occurred,
        response_id=trace.response_id,
        response_cache_status=trace.response_cache_status,
        finish_reason=trace.finish_reason,
        request_attempts=trace.request_attempts,
        retry_after_ms=trace.retry_after_ms,
        recovery=trace.recovery,
        latency_ms=trace.latency_ms,
        usage=trace.usage,
    )


def _provider_error_type(raw_response: Mapping[str, object] | None) -> str | None:
    response = raw_response or {}
    error = response.get("error")
    error_object = error if isinstance(error, Mapping) else {}
    metadata = error_object.get("metadata")
    metadata_object = metadata if isinstance(metadata, Mapping) else {}
    candidates = (
        response.get("error_type"),
        error_object.get("error_type"),
        metadata_object.get("error_type"),
    )
    return next((value for value in candidates if isinstance(value, str)), None)


def _provider_error_fields(
    raw_response: Mapping[str, object] | None,
) -> tuple[str | None, str | None]:
    response = raw_response or {}
    error = response.get("error")
    if not isinstance(error, Mapping):
        return None, None
    code = error.get("code")
    message = error.get("message")
    return (
        str(code)[:200] if isinstance(code, str | int) else None,
        message if isinstance(message, str) else None,
    )


def _sanitize_mapping(value: Mapping[object, object], *, depth: int) -> JsonObject:
    if depth >= _MAX_METADATA_DEPTH:
        return {"truncated": True}
    result: JsonObject = {}
    for raw_key, item in list(value.items())[:_MAX_SEQUENCE_ITEMS]:
        key = str(raw_key)
        normalized = key.casefold().replace("-", "_")
        if any(sensitive in normalized for sensitive in _SENSITIVE_KEYS):
            continue
        result[key] = _sanitize_value(item, depth=depth + 1)
    return result


def _sanitize_value(value: object, *, depth: int) -> JsonValue:
    if depth >= _MAX_METADATA_DEPTH:
        return {"truncated": True}
    if value is None or isinstance(value, bool | int | float):
        return value
    if isinstance(value, str):
        return _redact(value)[:2_000]
    if isinstance(value, Mapping):
        return _sanitize_mapping(value, depth=depth)
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [
            _sanitize_value(item, depth=depth + 1)
            for item in list(value)[:_MAX_SEQUENCE_ITEMS]
        ]
    if isinstance(value, BaseException):
        return {
            "type": type(value).__name__,
            "message": _exception_message(value)[:500],
        }
    return {"unserializable_type": type(value).__name__}


def _redact(value: str) -> str:
    redacted = value
    for pattern in _SECRET_PATTERNS:
        if pattern.groups == 0:
            redacted = pattern.sub(_REDACTED, redacted)
        else:
            redacted = pattern.sub(
                lambda match: f"{match.group(1)}{match.group(2)}{_REDACTED}",
                redacted,
            )
    return redacted
