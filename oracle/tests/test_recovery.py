from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from deep20_oracle.config import RecoveryPolicy
from deep20_oracle.recovery import (
    RecoveryAttemptLimitExceeded,
    logical_recovery_budget,
)


def test_nested_exact_replays_share_one_logical_call_budget() -> None:
    policy = RecoveryPolicy(max_request_attempts=3)

    with logical_recovery_budget(policy, 30) as first:
        first.reserve_request_attempt()
        with logical_recovery_budget(policy, 30) as replay:
            replay.reserve_request_attempt()

    assert replay is first
    assert first.request_attempts == 2


def test_concurrent_cli_contexts_have_independent_recovery_budgets() -> None:
    policy = RecoveryPolicy(max_request_attempts=8)
    barrier = Barrier(2)

    def consume(attempts: int) -> tuple[int, int]:
        with logical_recovery_budget(policy, 30) as budget:
            barrier.wait()
            for _ in range(attempts):
                budget.reserve_request_attempt()
            return id(budget), budget.request_attempts

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(consume, 3)
        second = executor.submit(consume, 5)
        first_id, first_attempts = first.result()
        second_id, second_attempts = second.result()

    assert first_id != second_id
    assert (first_attempts, second_attempts) == (3, 5)


def test_rate_limit_extension_grants_bounded_extra_attempts() -> None:
    policy = RecoveryPolicy(
        max_request_attempts=2,
        rate_limit_max_request_attempts=4,
    )

    with logical_recovery_budget(policy, 30) as budget:
        budget.reserve_request_attempt()
        budget.reserve_request_attempt()
        with pytest.raises(RecoveryAttemptLimitExceeded):
            budget.reserve_request_attempt()
        budget.extend_for_rate_limit()
        budget.reserve_request_attempt()
        budget.extend_for_rate_limit()
        budget.reserve_request_attempt()
        budget.extend_for_rate_limit()
        with pytest.raises(RecoveryAttemptLimitExceeded):
            budget.reserve_request_attempt()

    assert budget.request_attempts == 4
    assert budget.rate_limited_attempt_extension == 2


def test_rate_limit_budget_extends_the_logical_deadline() -> None:
    policy = RecoveryPolicy(
        max_elapsed_seconds=300,
        rate_limit_max_elapsed_seconds=900,
    )

    with logical_recovery_budget(policy, 30) as budget:
        assert 925 <= budget.remaining_seconds <= 930
