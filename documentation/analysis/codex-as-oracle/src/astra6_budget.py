"""Astra-only transport budget; local accounting never enters the Guesser transcript."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import bridge
import httpx
import live_entry
from deep20_game.config import ModelConfig
from deep20_game.models import GameProviderRequest
from deep20_game.openrouter_provider import OpenRouterGameProvider
from deep20_oracle.models import JsonObject, StrictModel
from pydantic import Field, TypeAdapter

JSON_OBJECT: TypeAdapter[JsonObject] = TypeAdapter(JsonObject)
INPUT_RATE = Decimal("0.0000125")  # Includes standard-route cache writes.
OUTPUT_RATE = Decimal("0.00005")


class BudgetState(StrictModel):
    limit_usd: Decimal = Decimal(9)
    reported_usd: Decimal = Field(default=Decimal(0), ge=0)
    reserved_usd: Decimal = Field(default=Decimal("2.10"), ge=0)
    attempts: int = Field(default=1, ge=0)
    unmetered_attempts: int = Field(default=1, ge=0)


def reservation(request_bytes: int, max_output: int) -> Decimal:
    # Byte-level text tokenization is bounded by UTF-8 length. Double serialized
    # bytes plus 8,192 tokens covers schema rendering and framing conservatively.
    input_bound = request_bytes * 2 + 8192
    if input_bound >= 272000:
        raise ValueError("request exceeds verified short-context pricing bound")
    return (input_bound * INPUT_RATE + max_output * OUTPUT_RATE) * Decimal("1.10")


class Budget:
    def __init__(self, path: Path):
        if path.exists():
            raise ValueError("budget requires a fresh launch")
        self.path = path
        self.state = BudgetState()
        self.active = Decimal(0)
        bridge.write_model(path, self.state)

    def reserve(self, request: httpx.Request) -> None:
        payload = JSON_OBJECT.validate_json(request.content)
        route = payload.get("provider")
        output = payload.get("max_tokens")
        if (
            request.method != "POST"
            or request.url.host != "openrouter.ai"
            or request.url.path != "/api/v1/chat/completions"
            or payload.get("model") != "openai/gpt-6-astra"
            or not isinstance(route, dict)
            or route.get("only") != ["openai"]
            or route.get("allow_fallbacks") is not False
            or route.get("max_price") != {"prompt": "10", "completion": "50"}
            or payload.get("service_tier") not in (None, "default")
            or "tools" in payload or "plugins" in payload
            or not isinstance(output, int) or isinstance(output, bool)
            or not 1 <= output <= 32768
        ):
            raise ValueError("unexpected budgeted request")
        amount = reservation(len(request.content), output)
        state = self.state
        if state.reported_usd + state.reserved_usd + amount > state.limit_usd:
            raise RuntimeError("experiment_spending_cap_reached")
        self.active = amount
        self.state = BudgetState(
            reported_usd=state.reported_usd,
            reserved_usd=state.reserved_usd + amount,
            attempts=state.attempts + 1,
            unmetered_attempts=state.unmetered_attempts + 1,
        )
        bridge.write_model(self.path, self.state)

    def settle(self, response: httpx.Response) -> None:
        response.read()
        try:
            payload = JSON_OBJECT.validate_json(response.content)
        except ValueError:
            return
        usage = payload.get("usage")
        raw = usage.get("cost") if isinstance(usage, dict) else None
        if isinstance(raw, bool) or not isinstance(raw, (str, int, float)):
            return  # Unreported failures retain their full reservation.
        cost = Decimal(str(raw))
        if not cost.is_finite() or cost < 0:
            raise ValueError("invalid_experiment_billing")
        amount, state = self.active, self.state
        if not amount:
            raise ValueError("response without a budget reservation")
        self.active = Decimal(0)
        self.state = BudgetState(
            reported_usd=state.reported_usd + cost,
            reserved_usd=state.reserved_usd - amount,
            attempts=state.attempts,
            unmetered_attempts=state.unmetered_attempts - 1,
        )
        bridge.write_model(self.path, self.state)
        if cost > amount:
            raise RuntimeError("experiment_billing_exceeded_reservation")


def validate_pricing(path: Path) -> None:
    payload = JSON_OBJECT.validate_json(path.read_text())
    data = payload.get("data")
    if not isinstance(data, dict) or data.get("id") != "openai/gpt-6-astra":
        raise ValueError("wrong budget pricing model")
    endpoints = data.get("endpoints")
    if not isinstance(endpoints, list):
        raise TypeError("missing pricing endpoints")
    # OpenRouter base slugs exclude opt-in flex and priority service tiers.
    standard = [e for e in endpoints if isinstance(e, dict) and e.get("tag") == "openai"]
    if len(standard) != 1:
        raise ValueError("missing standard OpenAI endpoint")
    rates = standard[0].get("pricing")
    if not isinstance(rates, dict):
        raise TypeError("missing standard pricing")
    for key in ("prompt", "input_cache_read", "input_cache_write"):
        if Decimal(str(rates.get(key))) > INPUT_RATE:
            raise ValueError("input pricing exceeds reservation")
    if Decimal(str(rates.get("completion"))) > OUTPUT_RATE:
        raise ValueError("output pricing exceeds reservation")
    overrides = rates.get("overrides", [])
    if not isinstance(overrides, list):
        raise TypeError("invalid pricing overrides")
    for override in overrides:
        threshold = override.get("min_prompt_tokens") if isinstance(override, dict) else None
        if not isinstance(threshold, int) or threshold < 272000:
            raise ValueError("unverified short-context price override")
    for key in ("request", "image", "internal_reasoning"):
        if Decimal(str(rates.get(key, "0"))) != 0:
            raise ValueError("unbudgeted provider fee")


def run() -> None:
    validate_pricing(bridge.ROOT / "route-pricing.json")
    budget = Budget(bridge.ROOT / "budget.json")

    class BudgetedProvider(OpenRouterGameProvider):
        def __init__(self, api_key: str, config: ModelConfig, *, title: str):
            if config.model != "openai/gpt-6-astra" or config.max_output_tokens > 32768:
                raise ValueError("unexpected budgeted model")
            super().__init__(api_key, config, title=title)
            self.http_client._client.event_hooks = {
                "request": [budget.reserve], "response": [budget.settle]
            }

        def _request_payload(self, request: GameProviderRequest) -> JsonObject:
            payload = JSON_OBJECT.validate_python(super()._request_payload(request))
            provider = payload.get("provider")
            if not isinstance(provider, dict):
                raise TypeError("missing provider route")
            provider["max_price"] = {"prompt": "10", "completion": "50"}
            return payload

    try:
        live_entry.main(BudgetedProvider)
    except Exception as error:  # noqa: BLE001 - redact the executable boundary.
        live_entry.status("interrupted", f"Experiment stopped with {type(error).__name__}.")
        raise SystemExit(1) from None
