from __future__ import annotations

import signal

import httpx
import pytest
from deep20_oracle.models import RecoveryReason
from deep20_oracle.openrouter_retry import (
    ProviderDeadlineExceeded,
    embedded_status_code,
    hard_deadline,
    is_malformed_response_error,
    is_transport_error,
    no_sdk_retry_config,
    parse_retry_after_ms,
    recovery_reason,
    retry_delay_ms,
)
from openrouter.errors import ResponseValidationError


def test_sdk_retries_are_disabled_for_project_bounded_policy() -> None:
    retry = no_sdk_retry_config()

    assert retry.strategy == "none"
    assert retry.status_codes_override == []
    assert retry.retry_connection_errors is False


def test_transient_retry_delays_are_status_specific_and_bounded() -> None:
    assert retry_delay_ms(
        status_code=429,
        request_attempts=1,
        retry_after_ms=None,
        elapsed_ms=0,
        max_elapsed_seconds=75,
    ) == 5_000
    assert retry_delay_ms(
        status_code=503,
        request_attempts=2,
        retry_after_ms=30_000,
        elapsed_ms=10_000,
        max_elapsed_seconds=75,
    ) == 30_000
    assert (
        retry_delay_ms(
            status_code=429,
            request_attempts=3,
            retry_after_ms=60_000,
            elapsed_ms=20_000,
            max_elapsed_seconds=75,
        )
        is None
    )
    assert retry_delay_ms(
        status_code=502,
        request_attempts=1,
        retry_after_ms=None,
        elapsed_ms=0,
        max_elapsed_seconds=75,
    ) == 5_000
    assert retry_delay_ms(
        status_code=None,
        connection_error=True,
        request_attempts=1,
        retry_after_ms=None,
        elapsed_ms=75_000,
        max_elapsed_seconds=300,
    ) == 5_000
    assert (
        retry_delay_ms(
            status_code=None,
            connection_error=True,
            request_attempts=1,
            retry_after_ms=None,
            elapsed_ms=75_000,
            max_elapsed_seconds=75,
        )
        is None
    )
    assert (
        retry_delay_ms(
            status_code=429,
            request_attempts=1,
            retry_after_ms=None,
            elapsed_ms=0,
            max_elapsed_seconds=0,
        )
        is None
    )


def test_retry_after_parser_accepts_seconds_and_milliseconds() -> None:
    assert parse_retry_after_ms({"retry-after": "12.5"}) == 12_500
    assert parse_retry_after_ms({"retry-after-ms": "2500"}) == 2_500
    assert parse_retry_after_ms({"retry-after": "invalid"}) is None


@pytest.mark.parametrize("status_code", [400, 408, 429, 500, 502, 503, 504, 524, 529])
def test_all_recoverable_statuses_are_retryable(status_code: int) -> None:
    assert retry_delay_ms(
        status_code=status_code,
        request_attempts=1,
        retry_after_ms=None,
        elapsed_ms=0,
        max_elapsed_seconds=300,
        max_request_attempts=8,
    ) == 5_000
    assert (
        retry_delay_ms(
            status_code=status_code,
            request_attempts=8,
            retry_after_ms=None,
            elapsed_ms=0,
            max_elapsed_seconds=300,
            max_request_attempts=8,
        )
        is None
    )


@pytest.mark.parametrize("status_code", [401, 402, 403, 404, 405, 413, 422])
def test_permanent_client_errors_are_not_retryable(status_code: int) -> None:
    assert recovery_reason(status_code=status_code) is None
    assert (
        retry_delay_ms(
            status_code=status_code,
            request_attempts=1,
            retry_after_ms=None,
            elapsed_ms=0,
            max_elapsed_seconds=300,
            max_request_attempts=8,
        )
        is None
    )


def test_embedded_transient_status_overrides_http_200() -> None:
    assert embedded_status_code({"error": {"code": 400}}, 400) == 400
    assert embedded_status_code({"error": {"code": 503}}, 200) == 503
    assert embedded_status_code({"error": {"code": "529"}}, 200) == 529
    assert embedded_status_code({"error": {"code": 401}}, 200) == 401


def test_hard_deadline_interrupts_the_active_main_thread() -> None:
    with pytest.raises(ProviderDeadlineExceeded), hard_deadline(30):
        signal.raise_signal(signal.SIGALRM)


def test_wrapped_transport_errors_remain_retryable() -> None:
    transport_error = httpx.ConnectError("temporary connection failure")
    try:
        raise RuntimeError("SDK wrapper") from transport_error
    except RuntimeError as wrapped:
        assert is_transport_error(wrapped)


def test_sdk_response_validation_errors_are_retryable_without_body_inspection() -> None:
    response = httpx.Response(
        200,
        text='{"malformed-output-marker":',
        request=httpx.Request("POST", "https://openrouter.example.test"),
    )
    malformed = ResponseValidationError(
        "Response validation failed",
        response,
        ValueError("EOF while parsing a value"),
    )

    assert is_malformed_response_error(malformed)
    assert recovery_reason(
        status_code=200,
        malformed_response=True,
    ) is RecoveryReason.MALFORMED_RESPONSE
    assert retry_delay_ms(
        status_code=200,
        malformed_response=True,
        request_attempts=1,
        retry_after_ms=None,
        elapsed_ms=0,
        max_elapsed_seconds=300,
    ) == 5_000
    assert (
        retry_delay_ms(
            status_code=200,
            malformed_response=True,
            request_attempts=8,
            retry_after_ms=None,
            elapsed_ms=0,
            max_elapsed_seconds=300,
            max_request_attempts=8,
        )
        is None
    )


def test_shared_logical_attempt_count_caps_a_new_provider_replay() -> None:
    assert (
        retry_delay_ms(
            status_code=503,
            request_attempts=1,
            logical_request_attempts=8,
            retry_after_ms=None,
            elapsed_ms=0,
            max_elapsed_seconds=300,
            max_request_attempts=8,
        )
        is None
    )


def test_rate_limited_retries_use_dedicated_attempt_and_elapsed_budget() -> None:
    assert retry_delay_ms(
        status_code=429,
        request_attempts=12,
        retry_after_ms=None,
        elapsed_ms=400_000,
        max_elapsed_seconds=300,
        max_request_attempts=8,
        rate_limit_max_elapsed_seconds=900,
        rate_limit_max_request_attempts=20,
    ) == 60_000
    assert (
        retry_delay_ms(
            status_code=503,
            request_attempts=12,
            retry_after_ms=None,
            elapsed_ms=400_000,
            max_elapsed_seconds=300,
            max_request_attempts=8,
            rate_limit_max_elapsed_seconds=900,
            rate_limit_max_request_attempts=20,
        )
        is None
    )
    assert (
        retry_delay_ms(
            status_code=429,
            request_attempts=20,
            retry_after_ms=None,
            elapsed_ms=0,
            max_elapsed_seconds=300,
            max_request_attempts=8,
            rate_limit_max_elapsed_seconds=900,
            rate_limit_max_request_attempts=20,
        )
        is None
    )
    assert (
        retry_delay_ms(
            status_code=429,
            request_attempts=2,
            retry_after_ms=None,
            elapsed_ms=895_000,
            max_elapsed_seconds=300,
            max_request_attempts=8,
            rate_limit_max_elapsed_seconds=900,
            rate_limit_max_request_attempts=20,
        )
        is None
    )


def test_retry_jitter_is_bounded_and_additive() -> None:
    delays = {
        retry_delay_ms(
            status_code=503,
            request_attempts=1,
            retry_after_ms=None,
            elapsed_ms=0,
            max_elapsed_seconds=300,
            jitter_ms=1_000,
        )
        for _ in range(64)
    }

    assert all(
        delay is not None and 5_000 <= delay <= 6_000 for delay in delays
    )
    assert retry_delay_ms(
        status_code=503,
        request_attempts=1,
        retry_after_ms=None,
        elapsed_ms=0,
        max_elapsed_seconds=300,
        jitter_ms=0,
    ) == 5_000
