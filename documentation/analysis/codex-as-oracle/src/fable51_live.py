"""Run the authorized Fable experiment with an $11 limit across all HTTP attempts."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import bridge
import httpx
import live_entry
from deep20_game.config import ModelConfig
from deep20_game.openrouter_provider import OpenRouterGameProvider
from deep20_oracle.models import JsonObject, StrictModel
from pydantic import Field, TypeAdapter

MODEL = "anthropic/claude-fable-5.1"
INPUT_RATE = Decimal("0.0000125")
OUTPUT_RATE = Decimal("0.00005")
CONTEXT_LIMIT = 1_000_000
OUTPUT_LIMIT = 32768


class BudgetState(StrictModel):
    limit_usd: Decimal = Decimal(11)
    reported_usd: Decimal = Field(default=Decimal(0), ge=0)
    reserved_usd: Decimal = Field(default=Decimal(0), ge=0)
    attempts: int = Field(default=0, ge=0)
    unmetered_attempts: int = Field(default=0, ge=0)


class Budget:
    def __init__(self, path: Path):
        if path.exists():
            raise ValueError("budget requires a fresh live launch")
        self.path = path
        self.state = BudgetState()
        bridge.write_model(path, self.state)

    def reserve(self, request: httpx.Request) -> None:
        # Conservative text/schema bound: four tokens per serialized byte, plus
        # 65,536 tokens for provider rendering, capped at the full route context.
        # Reserve maximum output, expensive five-minute writes and 10% headroom.
        # This changes no request, prompt, route, output ceiling or cache policy.
        input_bound = min(CONTEXT_LIMIT, len(request.content) * 4 + 65536)
        reservation = (
            Decimal(input_bound) * INPUT_RATE + Decimal(OUTPUT_LIMIT) * OUTPUT_RATE
        ) * Decimal("1.1")
        state = self.state
        if state.reported_usd + state.reserved_usd + reservation > state.limit_usd:
            raise RuntimeError("experiment_spending_cap_reached")
        request.extensions["fable_budget_reservation"] = reservation
        self.state = BudgetState(
            reported_usd=state.reported_usd,
            reserved_usd=state.reserved_usd + reservation,
            attempts=state.attempts + 1,
            unmetered_attempts=state.unmetered_attempts + 1,
        )
        bridge.write_model(self.path, self.state)

    def settle(self, response: httpx.Response) -> None:
        response.read()
        try:
            payload: JsonObject = TypeAdapter(JsonObject).validate_json(response.content)
        except ValueError:
            return
        usage = payload.get("usage")
        raw_cost = usage.get("cost") if isinstance(usage, dict) else None
        if isinstance(raw_cost, bool) or not isinstance(raw_cost, (str, int, float)):
            return  # Missing billing, including transport failures, stays fully reserved.
        cost = Decimal(str(raw_cost))
        if not cost.is_finite() or cost < 0:
            raise RuntimeError("invalid_experiment_billing")
        reservation = response.request.extensions.pop("fable_budget_reservation", None)
        if not isinstance(reservation, Decimal):
            raise TypeError("missing_experiment_reservation")
        state = self.state
        self.state = BudgetState(
            reported_usd=state.reported_usd + cost,
            reserved_usd=state.reserved_usd - reservation,
            attempts=state.attempts,
            unmetered_attempts=state.unmetered_attempts - 1,
        )
        bridge.write_model(self.path, self.state)
        if cost > reservation:
            raise RuntimeError("experiment_billing_exceeded_reservation")


def validate_prices(raw: bytes) -> None:
    payload: JsonObject = TypeAdapter(JsonObject).validate_json(raw)
    data = payload.get("data")
    if not isinstance(data, dict) or data.get("id") != MODEL:
        raise ValueError("unexpected budget pricing model")
    endpoints = data.get("endpoints")
    if not isinstance(endpoints, list):
        raise TypeError("missing budget pricing endpoints")
    matched = False
    for endpoint in endpoints:
        if not isinstance(endpoint, dict) or endpoint.get("tag") != "anthropic":
            continue
        matched = True
        context, pricing = endpoint.get("context_length"), endpoint.get("pricing")
        if not isinstance(context, int) or context > CONTEXT_LIMIT or context <= 0:
            raise ValueError("unexpected route context limit")
        if not isinstance(pricing, dict) or pricing.get("overrides"):
            raise ValueError("missing or tiered route pricing")
        for key, bound in (
            ("prompt", INPUT_RATE),
            ("input_cache_read", INPUT_RATE),
            ("input_cache_write", INPUT_RATE),
            ("completion", OUTPUT_RATE),
        ):
            raw_rate = pricing.get(key)
            if isinstance(raw_rate, bool) or not isinstance(raw_rate, (str, int, float)):
                raise TypeError("missing route rate")
            rate = Decimal(str(raw_rate))
            if not rate.is_finite() or rate < 0 or rate > bound:
                raise ValueError("route rate exceeds budget reservation")
    if not matched:
        raise ValueError("missing exact Anthropic route")


def main() -> None:
    if (bridge.ROOT / "budget.json").exists() or (bridge.ROOT / "runs").exists():
        raise ValueError("budgeted launch requires a fresh experiment")
    response = httpx.get(f"https://openrouter.ai/api/v1/models/{MODEL}/endpoints", timeout=30)
    response.raise_for_status()
    validate_prices(response.content)
    pricing_path = bridge.ROOT / "route-pricing.json"
    pricing_path.write_bytes(response.content)
    pricing_path.chmod(0o600)
    budget = Budget(bridge.ROOT / "budget.json")

    class BudgetedProvider(OpenRouterGameProvider):
        def __init__(self, api_key: str, config: ModelConfig, *, title: str):
            if (
                config.model != MODEL
                or config.provider != "anthropic"
                or config.allow_fallbacks
                or config.max_output_tokens > OUTPUT_LIMIT
                or config.prompt_cache.control.value != "ephemeral_5m"
            ):
                raise ValueError("unexpected budgeted model configuration")
            super().__init__(api_key, config, title=title)
            self.http_client._client.event_hooks = {
                "request": [budget.reserve],
                "response": [budget.settle],
            }

    provider_attribute = "OpenRouterGameProvider"
    setattr(bridge, provider_attribute, BudgetedProvider)
    setattr(live_entry, provider_attribute, BudgetedProvider)
    live_entry.main()
