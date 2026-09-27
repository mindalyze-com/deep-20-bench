from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from fable51_live import Budget, validate_prices


def test_failed_and_retried_attempts_share_the_limit(tmp_path: Path) -> None:
    budget = Budget(tmp_path / "budget.json")
    first = httpx.Request("POST", "https://example.invalid/chat/completions")
    budget.reserve(first)
    budget.settle(httpx.Response(200, request=first, json={"usage": {"cost": "0.10"}}))
    assert budget.state.reported_usd == Decimal("0.10")
    assert budget.state.reserved_usd == 0
    for _ in range(4):
        failed = httpx.Request("POST", "https://example.invalid/chat/completions")
        budget.reserve(failed)
        budget.settle(httpx.Response(500, request=failed, json={"error": "offline fixture"}))
    assert budget.state.unmetered_attempts == 4
    with pytest.raises(RuntimeError, match="spending_cap"):
        budget.reserve(httpx.Request("POST", "https://example.invalid/chat/completions"))
    assert budget.state.attempts == 5
    assert budget.state.reported_usd + budget.state.reserved_usd <= 11


def test_explicit_zero_billing_releases_failed_call_reservation(tmp_path: Path) -> None:
    budget = Budget(tmp_path / "budget.json")
    request = httpx.Request("POST", "https://example.invalid/chat/completions")
    budget.reserve(request)
    budget.settle(httpx.Response(429, request=request, json={"usage": {"cost": 0}}))
    assert budget.state.reserved_usd == 0
    assert budget.state.unmetered_attempts == 0
    with pytest.raises(ValueError, match="fresh live launch"):
        Budget(tmp_path / "budget.json")


def test_oversized_request_stops_before_spending(tmp_path: Path) -> None:
    budget = Budget(tmp_path / "budget.json")
    with pytest.raises(RuntimeError, match="spending_cap"):
        budget.reserve(httpx.Request("POST", "https://example.invalid", content=b"x" * 300000))
    assert budget.state.attempts == 0


def test_prices_must_fit_the_bound() -> None:
    response = httpx.Response(
        200,
        json={
            "data": {
                "id": "anthropic/claude-fable-5.1",
                "endpoints": [
                    {
                        "tag": "anthropic",
                        "context_length": 1000000,
                        "pricing": {
                            "prompt": "0.00001",
                            "input_cache_read": "0.00000025",
                            "input_cache_write": "0.0000125",
                            "completion": "0.00005",
                        },
                    }
                ],
            }
        },
    )
    validate_prices(response.content)
    with pytest.raises(ValueError, match="exceeds budget"):
        validate_prices(response.content.replace(b"0.00005", b"0.00006"))
