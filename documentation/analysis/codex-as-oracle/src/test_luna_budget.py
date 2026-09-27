from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from luna_live import Budget


def test_budget_settles_billing_and_retains_unknown_attempts(tmp_path: Path) -> None:
    budget = Budget(tmp_path / "budget.json")
    request = httpx.Request("POST", "https://example.invalid/chat/completions")
    budget.reserve(request)
    budget.settle(httpx.Response(200, json={"usage": {"cost": 0.19}}))
    assert budget.state.reported_usd == Decimal("0.19")
    assert budget.state.reserved_usd == 0
    request = httpx.Request("POST", "https://example.invalid/chat/completions", content=b"x" * 500000)
    budget.reserve(request)
    budget.settle(httpx.Response(500, json={"error": "offline fixture"}))
    budget.reserve(request)
    assert budget.state.reserved_usd == 4
    with pytest.raises(RuntimeError, match="spending_cap"):
        budget.reserve(request)
    assert budget.state.attempts == 3
    assert budget.state.unmetered_attempts == 2


def test_zero_cost_failed_attempt_releases_its_reservation(tmp_path: Path) -> None:
    budget = Budget(tmp_path / "budget.json")
    budget.reserve(httpx.Request("POST", "https://example.invalid/chat/completions"))
    budget.settle(httpx.Response(429, json={"usage": {"cost": 0}}))
    assert budget.state.reserved_usd == 0
    assert budget.state.attempts == 1
    assert budget.state.unmetered_attempts == 0


def test_budget_rejects_existing_launch(tmp_path: Path) -> None:
    path = tmp_path / "budget.json"
    Budget(path)
    with pytest.raises(ValueError, match="fresh live launch"):
        Budget(path)
