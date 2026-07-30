from __future__ import annotations

from collections.abc import Mapping, Sequence

from .models import ProviderOutputCapture, ProviderTrace


def raw_provider_output(raw_response: Mapping[str, object] | None) -> str | None:
    """Extract the provider's visible textual completion once at the shared boundary."""

    response = raw_response or {}
    choices = response.get("choices")
    if not isinstance(choices, Sequence) or isinstance(choices, str | bytes) or not choices:
        return None
    first = choices[0]
    if not isinstance(first, Mapping):
        return None
    message = first.get("message")
    if not isinstance(message, Mapping):
        return None
    content = message.get("content")
    return content if isinstance(content, str) else None


def capture_provider_output(
    raw_response: Mapping[str, object] | None,
    *,
    attempt_number: int,
) -> ProviderOutputCapture | None:
    """Project one provider response to the error-output fields safe to retain."""

    output = raw_provider_output(raw_response)
    if not output:
        return None
    response = raw_response or {}
    choices = response.get("choices")
    first = (
        choices[0]
        if isinstance(choices, Sequence)
        and not isinstance(choices, str | bytes)
        and choices
        and isinstance(choices[0], Mapping)
        else {}
    )
    response_id = response.get("id")
    finish_reason = first.get("finish_reason")
    return ProviderOutputCapture(
        attempt_number=attempt_number,
        response_id=response_id if isinstance(response_id, str) else None,
        finish_reason=finish_reason if isinstance(finish_reason, str) else None,
        output=output,
    )


def error_outputs_from_trace(
    trace: ProviderTrace,
    *,
    include_current: bool,
) -> tuple[ProviderOutputCapture, ...]:
    """Return discarded attempts plus the current completion for a failed call."""

    outputs = list(trace.discarded_error_outputs)
    if include_current:
        current = capture_provider_output(
            trace.response,
            attempt_number=trace.request_attempts,
        )
        if current is None and trace.raw_output:
            current = ProviderOutputCapture(
                attempt_number=trace.request_attempts,
                response_id=trace.response_id,
                finish_reason=trace.finish_reason,
                output=trace.raw_output,
            )
        if current is not None:
            outputs.append(current)
    return tuple(
        output.model_copy(update={"attempt_number": index})
        for index, output in enumerate(outputs, start=1)
    )
