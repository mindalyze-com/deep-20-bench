from __future__ import annotations

import json
from decimal import Decimal

from deep20_oracle.diagnostics import diagnose_exception, provider_failure_code
from deep20_oracle.errors import OracleProviderError
from deep20_oracle.models import ProviderTrace, ProviderUsage


def _raise_diagnostic_error() -> None:
    trace = ProviderTrace(
        requested_at="2026-07-27T10:00:00+00:00",
        completed_at="2026-07-27T10:00:01+00:00",
        latency_ms=1_234,
        http_status_code=429,
        response_id="response-safe-id",
        requested_model="openai/test-model",
        resolved_model=None,
        requested_provider="openai",
        resolved_provider=None,
        fallback_occurred=False,
        request={
            "messages": [{"role": "user", "content": "private subject snapshot"}],
            "authorization": "Bearer should-never-survive",
        },
        response={
            "error": {
                "code": 429,
                "message": "rate limited while using api_key=sk-test-secret-value",
                "metadata": {"error_type": "rate_limit_exceeded"},
            },
            "private_response": "raw provider response must not survive",
        },
        raw_output="private raw model output",
        annotations=({"citation": "private evidence"},),
        usage=ProviderUsage(
            input_tokens=100,
            cached_input_tokens=20,
            cache_write_tokens=0,
            output_tokens=0,
            reasoning_tokens=0,
            search_count=0,
            cost_usd=Decimal("0.001"),
        ),
    )
    try:
        raise RuntimeError("transport failed with Bearer sk-another-secret-value")
    except RuntimeError as cause:
        raise OracleProviderError(
            "OpenRouter request failed",
            code="provider_rate_limited",
            details={
                "provider_trace": trace.model_dump(mode="json"),
                "validation_errors": [
                    {"loc": ["answer"], "type": "missing", "message": "field required"}
                ],
                "subject": "Albert Einstein private snapshot",
            },
        ) from cause


def test_diagnostics_preserve_exception_and_provider_context_without_private_state() -> None:
    try:
        _raise_diagnostic_error()
    except OracleProviderError as error:
        diagnostics = diagnose_exception(error)
    else:
        raise AssertionError("expected diagnostic exception")

    assert [cause.exception_type for cause in diagnostics.causes] == [
        "OracleProviderError",
        "RuntimeError",
    ]
    assert diagnostics.causes[1].message == "transport failed with Bearer [REDACTED]"
    assert diagnostics.frames
    assert diagnostics.frames[-1].module == __name__
    assert diagnostics.frames[-1].function == "_raise_diagnostic_error"
    assert diagnostics.provider is not None
    assert diagnostics.provider.http_status_code == 429
    assert diagnostics.provider.error_type == "rate_limit_exceeded"
    assert diagnostics.provider.error_code == "429"
    assert diagnostics.provider.message == "rate limited while using api_key=[REDACTED]"
    assert diagnostics.provider.requested_model == "openai/test-model"
    assert diagnostics.provider.requested_provider == "openai"
    assert diagnostics.provider.latency_ms == 1_234
    assert diagnostics.provider.request_attempts == 1
    assert diagnostics.provider.usage.input_tokens == 100
    assert diagnostics.provider.usage.cached_input_tokens == 20
    assert diagnostics.metadata["validation_errors"] == [
        {"loc": ["answer"], "type": "missing", "message": "field required"}
    ]

    serialized = json.dumps(diagnostics.model_dump(mode="json"))
    for forbidden in (
        "Albert Einstein",
        "private subject snapshot",
        "private raw model output",
        "raw provider response",
        "private evidence",
        "should-never-survive",
        "sk-test-secret-value",
        "sk-another-secret-value",
    ):
        assert forbidden not in serialized


def test_provider_failure_code_prefers_typed_error_then_http_status() -> None:
    assert (
        provider_failure_code(
            {
                "error": {
                    "code": 503,
                    "metadata": {"error_type": "rate_limit_exceeded"},
                }
            },
            503,
        )
        == "provider_rate_limited"
    )
    assert provider_failure_code({}, 503) == "provider_overloaded"
    assert provider_failure_code({}, 520) == "provider_request_failed"
