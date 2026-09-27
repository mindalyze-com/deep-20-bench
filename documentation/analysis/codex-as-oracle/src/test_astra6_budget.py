from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from astra6_budget import Budget, reservation


def request() -> httpx.Request:
    return httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions", json={
        "model": "openai/gpt-6-astra", "max_tokens": 32768,
        "provider": {"only": ["openai"], "allow_fallbacks": False,
                     "max_price": {"prompt": "10", "completion": "50"}},
        "messages": [{"role": "user", "content": "private fixture"}],
    })


def test_attempts_with_unknown_billing_cannot_exceed_cap(tmp_path: Path) -> None:
    budget = Budget(tmp_path / "budget.json")
    sent = 0
    while True:
        try:
            budget.reserve(request())
        except RuntimeError as error:
            assert str(error) == "experiment_spending_cap_reached"
            break
        sent += 1
        budget.settle(httpx.Response(400, json={"error": {"code": 400}}))
    assert 0 < sent < 5
    assert budget.state.reserved_usd <= Decimal(9)
    assert budget.state.attempts == sent + 1
    assert budget.state.unmetered_attempts == sent + 1
    assert "private fixture" not in (tmp_path / "budget.json").read_text()


def test_actual_cost_releases_only_current_reservation(tmp_path: Path) -> None:
    budget = Budget(tmp_path / "budget.json")
    budget.reserve(request())
    budget.settle(httpx.Response(200, json={"usage": {"cost": "0.02"}}))
    assert budget.state.reported_usd == Decimal("0.02")
    assert budget.state.reserved_usd == Decimal("2.10")
    budget.reserve(request())
    budget.settle(httpx.Response(429, json={"usage": {"cost": 0}}))
    assert budget.state.reserved_usd == Decimal("2.10")


def test_unexpected_route_and_long_context_fail_before_send(tmp_path: Path) -> None:
    budget = Budget(tmp_path / "budget.json")
    with pytest.raises(ValueError, match="unexpected budgeted"):
        budget.reserve(httpx.Request("POST", "https://example.invalid", json={}))
    with pytest.raises(ValueError, match="pricing bound"):
        reservation(272000, 32768)
    assert budget.state.attempts == 1
    with pytest.raises(ValueError, match="fresh launch"):
        Budget(tmp_path / "budget.json")


def test_request_hook_rejection_never_reaches_http_transport(tmp_path: Path) -> None:
    budget = Budget(tmp_path / "budget.json")
    sent: list[httpx.Request] = []

    def transport(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(200, json={})

    with httpx.Client(
        transport=httpx.MockTransport(transport),
        event_hooks={"request": [budget.reserve], "response": [budget.settle]},
    ) as client, pytest.raises(ValueError, match="unexpected budgeted"):
        client.post("https://openrouter.ai/api/v1/chat/completions", json={
            "model": "openai/gpt-6-astra", "provider": None, "max_tokens": 32768,
        })
    assert sent == []
    assert budget.state.attempts == 1
    assert budget.state.reserved_usd == Decimal("2.10")
