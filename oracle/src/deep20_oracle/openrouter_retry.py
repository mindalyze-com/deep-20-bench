from __future__ import annotations

import random
import signal
import threading
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime
from email.utils import parsedate_to_datetime
from types import FrameType

import httpx
from openrouter.errors import ResponseValidationError
from openrouter.utils import BackoffStrategy, RetryConfig

from .models import JsonObject, RecoveryReason

# OpenRouter can report a response-less provider failure as a generic HTTP 400.
# Repeating the unchanged generation request is safe within the normal recovery budget.
_RETRYABLE_STATUS_CODES = frozenset({400, 408, 429, 500, 502, 503, 504, 524, 529})


class ProviderDeadlineExceeded(TimeoutError):
    """The hard wall-clock deadline for one logical provider call elapsed."""


def no_sdk_retry_config() -> RetryConfig:
    """Disable the SDK's unbounded Retry-After sleep in favor of the project policy."""

    return RetryConfig(
        "none",
        BackoffStrategy(0, 0, 1, 0, jitter_ms=0),
        False,
        [],
    )


def retry_delay_ms(
    *,
    status_code: int | None,
    connection_error: bool = False,
    malformed_response: bool = False,
    request_attempts: int,
    logical_request_attempts: int | None = None,
    retry_after_ms: int | None,
    elapsed_ms: int,
    max_elapsed_seconds: int,
    max_request_attempts: int = 8,
    rate_limit_max_elapsed_seconds: int | None = None,
    rate_limit_max_request_attempts: int | None = None,
    jitter_ms: int = 0,
) -> int | None:
    """Choose a bounded delay for an explicit no-result transient response.

    Rate-limited (429) responses may use a dedicated, larger attempt and elapsed
    budget so a provider rate-limit storm outlasts neither budget prematurely,
    while every other transient failure class keeps the strict default bounds.
    A small random jitter decorrelates concurrent clients retrying in lockstep.
    """

    rate_limited = status_code == 429
    attempt_limit = (
        max(rate_limit_max_request_attempts, max_request_attempts)
        if rate_limited and rate_limit_max_request_attempts is not None
        else max_request_attempts
    )
    elapsed_budget_seconds = (
        max(rate_limit_max_elapsed_seconds, max_elapsed_seconds)
        if rate_limited and rate_limit_max_elapsed_seconds is not None
        else max_elapsed_seconds
    )
    if (
        max_elapsed_seconds == 0
        or (
            status_code not in _RETRYABLE_STATUS_CODES
            and not connection_error
            and not malformed_response
        )
        or (
            logical_request_attempts
            if logical_request_attempts is not None
            else request_attempts
        )
        >= attempt_limit
    ):
        return None
    backoff_cap_ms = 60_000 if rate_limited else 20_000
    delay_ms = (
        retry_after_ms
        if retry_after_ms is not None
        else min(5_000 * (2 ** (request_attempts - 1)), backoff_cap_ms)
    )
    if jitter_ms > 0:
        delay_ms += random.randint(0, jitter_ms)
    if elapsed_ms + delay_ms > elapsed_budget_seconds * 1_000:
        return None
    return delay_ms


def embedded_status_code(
    raw_response: JsonObject | None,
    http_status_code: int | None,
) -> int | None:
    """Prefer a retryable embedded provider status from an HTTP-200 SDK failure."""

    if http_status_code in _RETRYABLE_STATUS_CODES:
        return http_status_code
    error = (raw_response or {}).get("error")
    if not isinstance(error, dict):
        return http_status_code
    code = error.get("code")
    if isinstance(code, int):
        return code
    if isinstance(code, str) and code.isdigit():
        return int(code)
    return http_status_code


def recovery_reason(
    *,
    status_code: int | None,
    connection_error: bool = False,
    malformed_response: bool = False,
) -> RecoveryReason | None:
    if connection_error:
        return RecoveryReason.TRANSPORT_ERROR
    if malformed_response:
        return RecoveryReason.MALFORMED_RESPONSE
    if status_code not in _RETRYABLE_STATUS_CODES:
        return None
    return RecoveryReason(f"provider_http_{status_code}")


def is_transport_error(error: BaseException) -> bool:
    """Recognize transport failures even when the SDK wraps the original error."""

    return _exception_chain_contains(error, httpx.TransportError)


def is_malformed_response_error(error: BaseException) -> bool:
    """Recognize SDK response-validation failures without retaining their bodies."""

    return _exception_chain_contains(error, ResponseValidationError)


def _exception_chain_contains(
    error: BaseException,
    expected: type[BaseException],
) -> bool:
    current: BaseException | None = error
    visited: set[int] = set()
    while current is not None and id(current) not in visited:
        if isinstance(current, expected):
            return True
        visited.add(id(current))
        current = current.__cause__ or current.__context__
    return False


@contextmanager
def hard_deadline(seconds: float) -> Iterator[None]:
    """Interrupt a blocking synchronous request on supported main-thread runtimes."""

    if seconds <= 0:
        raise ProviderDeadlineExceeded(
            "provider logical call exhausted its hard deadline"
        )
    if (
        threading.current_thread() is not threading.main_thread()
        or not hasattr(signal, "setitimer")
    ):
        yield
        return

    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)

    def deadline_handler(_signum: int, _frame: FrameType | None) -> None:
        raise ProviderDeadlineExceeded(
            f"provider logical call exceeded its {seconds}-second hard deadline"
        )

    signal.signal(signal.SIGALRM, deadline_handler)
    signal.setitimer(signal.ITIMER_REAL, float(seconds))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, *previous_timer)


def parse_retry_after_ms(headers: Mapping[str, str]) -> int | None:
    """Parse Retry-After without retaining or exposing the response headers."""

    milliseconds = headers.get("retry-after-ms")
    if milliseconds is not None:
        try:
            return max(round(float(milliseconds)), 0)
        except (OverflowError, ValueError):
            return None
    seconds = headers.get("retry-after")
    if seconds is None:
        return None
    try:
        return max(round(float(seconds) * 1_000), 0)
    except ValueError:
        pass
    try:
        retry_date = parsedate_to_datetime(seconds)
        delta = (retry_date - datetime.now(retry_date.tzinfo)).total_seconds()
        return max(round(delta * 1_000), 0)
    except (TypeError, ValueError):
        return None
