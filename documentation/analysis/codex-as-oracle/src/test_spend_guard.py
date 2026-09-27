"""Offline billing fixtures, with no provider calls."""

from decimal import Decimal

import bridge
import httpx
import pytest
from deep20_benchmark.catalog import load_model_catalog
from deep20_benchmark.models import BenchmarkModelId
from deep20_oracle.models import JsonObject
from spend_guard import Budget, BudgetState, PriceBound, Rate, price_bound


def priced() -> PriceBound:
    return PriceBound(
        model="fixture/model",
        provider="fixture",
        context_tokens=100000,
        max_output_tokens=100,
        rate=Rate(
            input_per_token=Decimal("0.000001"),
            output_per_token=Decimal("0.000002"),
            per_request=Decimal(0),
        ),
    )


def payload() -> JsonObject:
    return {
        "model": "fixture/model",
        "max_tokens": 100,
        "provider": {"only": ["fixture"], "allow_fallbacks": False},
        "messages": [{"role": "user", "content": "fixture"}],
    }


def test_all_attempts_share_limit_and_unknown_charges_survive_restart() -> None:
    saved: list[BudgetState] = []
    budget = Budget(BudgetState(limit_usd=Decimal("0.25")), priced(), saved.append)
    calls: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.content)
        return httpx.Response(500, json={"error": "fixture"})

    with httpx.Client(
        transport=httpx.MockTransport(handler),
        event_hooks={"request": [budget.reserve], "response": [budget.settle]},
    ) as client:
        for _ in range(3):
            client.post("https://example.invalid", json=payload())
        with pytest.raises(RuntimeError, match="spending_cap"):
            client.post("https://example.invalid", json=payload())
    assert len(calls) == 3
    assert all(body == calls[0] for body in calls)
    assert budget.state.unmetered_attempts == 3
    restored = Budget(saved[-1], priced(), saved.append)
    with pytest.raises(RuntimeError, match="spending_cap"):
        restored.reserve(httpx.Request("POST", "https://example.invalid", json=payload()))


def test_each_response_settles_its_own_reservation() -> None:
    budget = Budget(BudgetState(limit_usd=Decimal(1)), priced(), lambda state: None)
    first = httpx.Request("POST", "https://example.invalid", json=payload())
    second = httpx.Request("POST", "https://example.invalid", json={**payload(), "max_tokens": 50})
    budget.reserve(first)
    budget.reserve(second)
    budget.settle(httpx.Response(200, request=second, json={"usage": {"cost": "0.01"}}))
    assert budget.state.reserved_usd == budget.bound(first)
    budget.settle(httpx.Response(429, request=first, json={"usage": {"cost": 0}}))
    assert budget.state.reported_usd == Decimal("0.01")
    assert budget.state.reserved_usd == 0
    assert budget.state.unmetered_attempts == 0
    with pytest.raises(TypeError, match="missing attempt"):
        budget.settle(httpx.Response(200, request=first, json={"usage": {"cost": 0}}))


@pytest.mark.parametrize("cost", ["NaN", "Infinity", "-1", "bad", True])
def test_invalid_billing_keeps_reservation(cost: str | bool) -> None:
    budget = Budget(BudgetState(limit_usd=Decimal(1)), priced(), lambda state: None)
    request = httpx.Request("POST", "https://example.invalid", json=payload())
    budget.reserve(request)
    before = budget.state
    with pytest.raises((TypeError, ValueError)):
        budget.settle(httpx.Response(200, request=request, json={"usage": {"cost": cost}}))
    assert budget.state == before


@pytest.mark.parametrize(
    "change",
    [
        {"model": "other"},
        {"max_tokens": 101},
        {"tools": [{}]},
        {"stream": True},
        {"provider": {"only": ["other"], "allow_fallbacks": False}},
        {"provider": {"only": ["fixture"], "allow_fallbacks": True}},
        {
            "messages": [
                {"role": "user", "content": [{"type": "image_url", "image_url": "fixture"}]}
            ]
        },
    ],
)
def test_unpriced_request_is_blocked_before_reserving(change: JsonObject) -> None:
    budget = Budget(BudgetState(limit_usd=Decimal(1)), priced(), lambda state: None)
    with pytest.raises(ValueError):
        budget.reserve(
            httpx.Request("POST", "https://example.invalid", json={**payload(), **change})
        )
    assert budget.state.attempts == 0


@pytest.mark.parametrize("model_id", ["M-0001", "M-0021", "M-0020", "M-0026"])
def test_route_and_tier_prices_come_from_metadata(model_id: str) -> None:
    config = (
        load_model_catalog(bridge.REPOSITORY / "config/models.yaml")
        .model(BenchmarkModelId(model_id))
        .configuration
    )
    metadata = httpx.Response(
        200,
        json={
            "data": {
                "id": config.model,
                "endpoints": [
                    {
                        "tag": config.provider,
                        "status": 0,
                        "context_length": 1000000,
                        "pricing": {
                            "prompt": "0.000001",
                            "completion": "0.000003",
                            "input_cache_write": "0.000002",
                            "overrides": [{"min_prompt_tokens": 100000, "completion": "0.000006"}],
                        },
                    },
                    {
                        "tag": config.provider + "/priority",
                        "status": 0,
                        "context_length": 2000000,
                        "pricing": {
                            "prompt": "0.000004",
                            "completion": "0.000005",
                            "input_cache_write": "0.000008",
                        },
                    },
                ],
            }
        },
    )
    bound = price_bound(metadata.content, config)
    assert bound.model == config.model
    assert bound.provider == config.provider
    assert bound.context_tokens == 2000000
    assert bound.rate.input_per_token == Decimal("0.000008")
    assert bound.rate.output_per_token == Decimal("0.000006")
    with pytest.raises(ValueError, match="selected model"):
        price_bound(metadata.content.replace(config.model.encode(), b"wrong-model"), config)
