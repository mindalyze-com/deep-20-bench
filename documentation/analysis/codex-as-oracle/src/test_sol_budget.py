"""Offline spend-guard checks; no provider calls or credentials."""

import json
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from deep20_oracle.models import ProviderTrace
from sol_live import Budget, BudgetState, upstream_diagnostics


def payload() -> dict[str, object]:
    return {
        "model": "openai/gpt-5.6-sol",
        "max_tokens": 32768,
        "provider": {"only": ["openai"]},
        "messages": [{"role": "user", "content": "hi"}],
    }


def test_unknown_bills_reserve_before_transport_and_survive_restart(tmp_path: Path) -> None:
    path = tmp_path / "budget.json"
    budget = Budget(path)
    calls: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.content)
        return httpx.Response(500, json={"error": {"message": "offline failure"}})

    with httpx.Client(
        transport=httpx.MockTransport(handler),
        event_hooks={
            "request": [budget.reserve],
            "response": [budget.settle],
        },
    ) as client:
        for _ in range(3):
            client.post("https://example.invalid/chat/completions", json=payload())
        with pytest.raises(RuntimeError, match="spending_cap"):
            client.post("https://example.invalid/chat/completions", json=payload())
    assert len(calls) == 3
    assert all(json.loads(body) == payload() for body in calls)
    restored = Budget(path)
    assert restored.state == budget.state
    assert restored.state.unmetered_attempts == 3
    assert restored.state.legacy_reserved_usd + restored.state.reserved_usd <= Decimal(9)


def test_reported_failure_cost_and_success_cost_share_limit(tmp_path: Path) -> None:
    budget = Budget(tmp_path / "budget.json")
    request = httpx.Request("POST", "https://example.invalid", json=payload())
    for code, cost in ((429, "0"), (200, "0.01"), (500, "0.03")):
        budget.reserve(request)
        budget.settle(httpx.Response(code, json={"usage": {"cost": cost}}))
    assert budget.state.reported_usd == Decimal("0.04")
    assert budget.state.reserved_usd == 0
    assert budget.state.unmetered_attempts == 0
    assert budget.state.attempts == 3


def test_request_outside_priced_scope_is_blocked_without_reservation(tmp_path: Path) -> None:
    budget = Budget(tmp_path / "budget.json")
    changes: tuple[dict[str, object], ...] = (
        {"tools": [{}]},
        {"max_tokens": 32769},
        {"model": "other"},
        {
            "messages": [{"role": "user", "content": "x" * 100000}],
        },
    )
    for change in changes:
        request = httpx.Request("POST", "https://example.invalid", json={**payload(), **change})
        with pytest.raises(ValueError):
            budget.reserve(request)
    assert budget.state == BudgetState()


def test_disconnect_and_bad_billing_keep_the_reservation(tmp_path: Path) -> None:
    budget = Budget(tmp_path / "budget.json")
    request = httpx.Request("POST", "https://example.invalid", json=payload())
    budget.reserve(request)
    original = budget.state
    budget.settle(httpx.Response(502, text="not JSON"))
    assert budget.state == original
    with pytest.raises(ValueError, match="invalid provider cost"):
        budget.settle(httpx.Response(200, json={"usage": {"cost": "NaN"}}))
    assert budget.state == original


def test_nested_upstream_error_retains_cause_without_request_body() -> None:
    trace = ProviderTrace(
        requested_at="2026-09-10T00:00:00Z",
        completed_at="2026-09-10T00:00:01Z",
        latency_ms=1000,
        requested_model="openai/gpt-5.6-sol",
        requested_provider="openai",
        request={"messages": [{"role": "user", "content": "private fixture prompt"}]},
        response={
            "error": {
                "message": "Provider returned error",
                "metadata": {
                    "raw": json.dumps(
                        {"error": {"message": "Unsupported schema field", "code": "bad_schema"}}
                    ),
                },
            }
        },
    )
    result = upstream_diagnostics(trace)
    assert result is not None and result.provider is not None
    assert result.provider.message == "Unsupported schema field"
    assert result.provider.error_code == "bad_schema"
    assert "private fixture prompt" not in result.model_dump_json()
