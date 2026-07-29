from __future__ import annotations

import time
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from decimal import Decimal

from .config import RecoveryPolicy
from .models import (
    ProviderTrace,
    ProviderUsage,
    RecoveryMetrics,
    RecoveryReason,
    RecoveryReasonCount,
    RecoveryTotals,
)
from .provider_output import error_outputs_from_trace

_ACTIVE_RECOVERY_BUDGET: ContextVar[LogicalRecoveryBudget | None]


class RecoveryAttemptLimitExceeded(RuntimeError):
    """The shared logical-call request-attempt budget is exhausted."""


@dataclass
class LogicalRecoveryBudget:
    """In-memory wall-clock and request budget shared by exact request replays."""

    max_request_attempts: int
    deadline_monotonic: float
    request_attempts: int = 0
    max_rate_limited_attempt_extension: int = 0
    rate_limited_attempt_extension: int = 0

    @property
    def remaining_seconds(self) -> float:
        return max(self.deadline_monotonic - time.monotonic(), 0.0)

    @property
    def allowed_request_attempts(self) -> int:
        return self.max_request_attempts + self.rate_limited_attempt_extension

    @property
    def request_attempts_remaining(self) -> int:
        return max(self.allowed_request_attempts - self.request_attempts, 0)

    def reserve_request_attempt(self) -> None:
        if self.request_attempts >= self.allowed_request_attempts:
            raise RecoveryAttemptLimitExceeded(
                "logical provider call exhausted its request-attempt budget"
            )
        self.request_attempts += 1

    def extend_for_rate_limit(self) -> None:
        """Grant one extra attempt after an observed provider rate limit."""

        if self.rate_limited_attempt_extension < self.max_rate_limited_attempt_extension:
            self.rate_limited_attempt_extension += 1


_ACTIVE_RECOVERY_BUDGET = ContextVar(
    "deep20_active_recovery_budget",
    default=None,
)


def current_recovery_budget() -> LogicalRecoveryBudget | None:
    return _ACTIVE_RECOVERY_BUDGET.get()


@contextmanager
def logical_recovery_budget(
    policy: RecoveryPolicy,
    generation_timeout_seconds: int,
) -> Iterator[LogicalRecoveryBudget]:
    """Share one timeout-plus-recovery window across structured-output replays."""

    active = current_recovery_budget()
    if active is not None:
        yield active
        return
    budget = LogicalRecoveryBudget(
        max_request_attempts=policy.max_request_attempts,
        deadline_monotonic=(
            time.monotonic()
            + generation_timeout_seconds
            + max(policy.max_elapsed_seconds, policy.rate_limit_max_elapsed_seconds)
        ),
        max_rate_limited_attempt_extension=max(
            policy.rate_limit_max_request_attempts - policy.max_request_attempts,
            0,
        ),
    )
    token: Token[LogicalRecoveryBudget | None] = _ACTIVE_RECOVERY_BUDGET.set(budget)
    try:
        yield budget
    finally:
        _ACTIVE_RECOVERY_BUDGET.reset(token)


def combine_usage(left: ProviderUsage, right: ProviderUsage) -> ProviderUsage:
    def optional_sum(
        first: Decimal | None,
        second: Decimal | None,
    ) -> Decimal | None:
        if first is None and second is None:
            return None
        return (first or Decimal(0)) + (second or Decimal(0))

    return ProviderUsage(
        input_tokens=left.input_tokens + right.input_tokens,
        cached_input_tokens=left.cached_input_tokens + right.cached_input_tokens,
        cache_write_tokens=left.cache_write_tokens + right.cache_write_tokens,
        output_tokens=left.output_tokens + right.output_tokens,
        reasoning_tokens=left.reasoning_tokens + right.reasoning_tokens,
        search_count=left.search_count + right.search_count,
        cost_usd=optional_sum(left.cost_usd, right.cost_usd),
        cache_discount_usd=optional_sum(
            left.cache_discount_usd,
            right.cache_discount_usd,
        ),
    )


def recovery_reason_counts(
    reasons: Iterable[RecoveryReason],
) -> tuple[RecoveryReasonCount, ...]:
    counts: dict[RecoveryReason, int] = {}
    for reason in reasons:
        counts[reason] = counts.get(reason, 0) + 1
    return tuple(
        RecoveryReasonCount(reason=reason, count=count)
        for reason, count in sorted(counts.items(), key=lambda item: item[0].value)
    )


def expand_recovery_reasons(
    metrics: RecoveryMetrics,
) -> tuple[RecoveryReason, ...]:
    return tuple(
        reason_count.reason
        for reason_count in metrics.reasons
        for _ in range(reason_count.count)
    )


def combine_recovery_metrics(
    *metrics: RecoveryMetrics,
) -> RecoveryMetrics:
    if not metrics:
        return RecoveryMetrics()
    retry_usage = ProviderUsage()
    reasons: list[RecoveryReason] = []
    for item in metrics:
        retry_usage = combine_usage(retry_usage, item.retry_usage)
        reasons.extend(expand_recovery_reasons(item))
    return RecoveryMetrics(
        request_attempts=sum(item.request_attempts for item in metrics),
        retried_calls=sum(item.retried_calls for item in metrics),
        recovered_calls=sum(item.recovered_calls for item in metrics),
        exhausted_retries=sum(item.exhausted_retries for item in metrics),
        reasons=recovery_reason_counts(reasons),
        retry_usage=retry_usage,
        retry_latency_ms=sum(item.retry_latency_ms for item in metrics),
    )


def combine_recovery_totals(
    *metrics: RecoveryMetrics | RecoveryTotals,
) -> RecoveryTotals:
    retry_usage = ProviderUsage()
    reasons: list[RecoveryReason] = []
    for item in metrics:
        retry_usage = combine_usage(retry_usage, item.retry_usage)
        reasons.extend(
            reason_count.reason
            for reason_count in item.reasons
            for _ in range(reason_count.count)
        )
    return RecoveryTotals(
        request_attempts=sum(item.request_attempts for item in metrics),
        retried_calls=sum(item.retried_calls for item in metrics),
        recovered_calls=sum(item.recovered_calls for item in metrics),
        exhausted_retries=sum(item.exhausted_retries for item in metrics),
        reasons=recovery_reason_counts(reasons),
        retry_usage=retry_usage,
        retry_latency_ms=sum(item.retry_latency_ms for item in metrics),
    )


def merge_provider_traces(
    prior: ProviderTrace,
    current: ProviderTrace,
    *,
    reason: RecoveryReason,
    recovered: bool,
    exhausted: bool = False,
) -> ProviderTrace:
    """Merge exact structured-output attempts and preserve failed completions for diagnosis."""

    if prior.request != current.request:
        raise ValueError("recovery changed the provider request")
    reasons = [
        *expand_recovery_reasons(prior.recovery),
        reason,
        *expand_recovery_reasons(current.recovery),
    ]
    retry_usage = combine_usage(
        prior.usage,
        current.recovery.retry_usage,
    )
    request_attempts = prior.request_attempts + current.request_attempts
    recovery = RecoveryMetrics(
        request_attempts=request_attempts,
        retried_calls=1,
        recovered_calls=int(recovered),
        exhausted_retries=int(exhausted) + current.recovery.exhausted_retries,
        reasons=recovery_reason_counts(reasons),
        retry_usage=retry_usage,
        retry_latency_ms=prior.latency_ms + current.recovery.retry_latency_ms,
    )
    discarded_error_outputs = (
        *error_outputs_from_trace(prior, include_current=True),
        *current.discarded_error_outputs,
    )
    return current.model_copy(
        update={
            "requested_at": prior.requested_at,
            "latency_ms": prior.latency_ms + current.latency_ms,
            "request_attempts": request_attempts,
            "retry_after_ms": current.retry_after_ms or prior.retry_after_ms,
            "recovery": recovery,
            "usage": combine_usage(prior.usage, current.usage),
            "discarded_error_outputs": tuple(
                output.model_copy(update={"attempt_number": index})
                for index, output in enumerate(discarded_error_outputs, start=1)
            ),
        }
    )


def mark_recovery_exhausted(trace: ProviderTrace) -> ProviderTrace:
    return trace.model_copy(
        update={
            "recovery": trace.recovery.model_copy(
                update={
                    "exhausted_retries": trace.recovery.exhausted_retries + 1,
                }
            )
        }
    )
