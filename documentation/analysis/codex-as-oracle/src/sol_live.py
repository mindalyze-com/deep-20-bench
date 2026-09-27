"""Sol launch with a durable $9 budget shared by all attempts and retries."""

from __future__ import annotations

import fcntl
from decimal import Decimal
from pathlib import Path

import bridge
import httpx
import live_entry
from deep20_game.config import ModelConfig
from deep20_game.errors import GameError
from deep20_game.models import GameProviderExchange, GameProviderRequest
from deep20_game.openrouter_provider import OpenRouterGameProvider
from deep20_oracle.diagnostics import diagnose_exception
from deep20_oracle.models import FailureDiagnostics, JsonObject, ProviderTrace, StrictModel
from deep20_oracle.result_audit import provider_result_audit
from pydantic import Field, TypeAdapter

JSON_OBJECT: TypeAdapter[JsonObject] = TypeAdapter(JsonObject)
BUDGET_ROOT = bridge.REPOSITORY / "private/reviews/sol-budget-20260910"


class Pricing(StrictModel):
    # Worst advertised OpenAI tier, without relying on discounts or cache hits.
    input_per_token: Decimal = Decimal("0.000005")
    output_per_token: Decimal = Decimal("0.000020")
    long_input_per_token: Decimal = Decimal("0.000010")
    long_output_per_token: Decimal = Decimal("0.000030")
    long_threshold: int = 272000
    margin: Decimal = Decimal("1.10")


class BudgetState(StrictModel):
    limit_usd: Decimal = Field(default=Decimal(9), ge=9, le=9)
    # Eight possible earlier attempts at < $0.768 each, rounded upward.
    # No earlier usage is silently treated as a measured zero.
    legacy_reserved_usd: Decimal = Decimal("6.20")
    reported_usd: Decimal = Decimal(0)
    reserved_usd: Decimal = Decimal(0)
    attempts: int = Field(default=0, ge=0)
    unmetered_attempts: int = Field(default=0, ge=0)


class Budget:
    def __init__(self, path: Path, pricing: Pricing | None = None):
        self.path, self.pricing = path, pricing or Pricing()
        self.state = (
            BudgetState.model_validate_json(path.read_text()) if path.exists() else BudgetState()
        )
        self.active_reservation = Decimal(0)
        bridge.write_model(path, self.state)

    def bound(self, request: httpx.Request) -> Decimal:
        payload = JSON_OBJECT.validate_json(request.content)
        if payload.get("model") != "openai/gpt-5.6-sol":
            raise ValueError("unexpected budgeted model")
        maximum = payload.get("max_tokens")
        if isinstance(maximum, bool) or not isinstance(maximum, int) or not 1 <= maximum <= 32768:
            raise ValueError("unexpected output bound")
        if payload.get("tools") or payload.get("plugins") or payload.get("stream"):
            raise ValueError("budget permits only text-only non-streaming Guesser calls")
        provider = payload.get("provider")
        if not isinstance(provider, dict) or provider.get("only") != ["openai"]:
            raise ValueError("unexpected budgeted route")
        # Every text token consumes at least one UTF-8 byte. Include the full serialized
        # schema/payload and another 4096 tokens for provider framing, rather than an estimate.
        inputs = len(request.content) + 4096
        if inputs > 100000:
            raise ValueError("request exceeds budgeted input ceiling")
        pricing = self.pricing
        input_rate, output_rate = pricing.input_per_token, pricing.output_per_token
        if inputs >= pricing.long_threshold:
            input_rate, output_rate = pricing.long_input_per_token, pricing.long_output_per_token
        return (inputs * input_rate + maximum * output_rate) * pricing.margin

    def reserve(self, request: httpx.Request) -> None:
        reserve = self.bound(request)
        state = self.state
        if (
            state.legacy_reserved_usd + state.reported_usd + state.reserved_usd + reserve
            > state.limit_usd
        ):
            raise RuntimeError("experiment_spending_cap_reached")
        self.active_reservation = reserve
        self.state = BudgetState.model_validate(
            {
                **state.model_dump(),
                "reserved_usd": state.reserved_usd + reserve,
                "attempts": state.attempts + 1,
                "unmetered_attempts": state.unmetered_attempts + 1,
            }
        )
        bridge.write_model(self.path, self.state)

    def settle(self, response: httpx.Response) -> None:
        response.read()
        try:
            payload = JSON_OBJECT.validate_json(response.content)
        except ValueError:
            return  # Keep unknown charges reserved, including failures and disconnects.
        usage = payload.get("usage")
        raw_cost = usage.get("cost") if isinstance(usage, dict) else None
        if isinstance(raw_cost, bool) or not isinstance(raw_cost, (int, float, str)):
            return
        cost = Decimal(str(raw_cost))
        if not cost.is_finite() or cost < 0:
            raise ValueError("invalid provider cost")
        reserve, self.active_reservation = self.active_reservation, Decimal(0)
        state = self.state
        self.state = BudgetState.model_validate(
            {
                **state.model_dump(),
                "reported_usd": state.reported_usd + cost,
                "reserved_usd": state.reserved_usd - reserve,
                "unmetered_attempts": state.unmetered_attempts - 1,
            }
        )
        bridge.write_model(self.path, self.state)
        if cost > reserve:
            raise RuntimeError("provider_cost_exceeds_verified_reservation")


def validate_pricing(path: Path, expected: Pricing) -> None:
    payload = JSON_OBJECT.validate_json(path.read_text())
    data = payload.get("data")
    if not isinstance(data, dict) or data.get("id") != "openai/gpt-5.6-sol":
        raise ValueError("incorrect pricing model")
    endpoints = data.get("endpoints")
    if not isinstance(endpoints, list):
        raise TypeError("missing pricing endpoints")
    checked = 0
    for endpoint in endpoints:
        if not isinstance(endpoint, dict):
            continue
        tag = endpoint.get("tag")
        if not isinstance(tag, str) or not (tag == "openai" or tag.startswith("openai/")):
            continue
        pricing = endpoint.get("pricing")
        if not isinstance(pricing, dict):
            raise TypeError("missing route prices")
        for key in ("prompt", "input_cache_read", "input_cache_write"):
            if Decimal(str(pricing.get(key))) > expected.input_per_token:
                raise ValueError("input price exceeds reservation")
        if Decimal(str(pricing.get("completion"))) > expected.output_per_token:
            raise ValueError("output price exceeds reservation")
        overrides = pricing.get("overrides", [])
        if not isinstance(overrides, list):
            raise TypeError("invalid pricing overrides")
        for override in overrides:
            if not isinstance(override, dict):
                raise TypeError("invalid pricing override")
            threshold = override.get("min_prompt_tokens")
            if not isinstance(threshold, int) or threshold < expected.long_threshold:
                raise ValueError("unexpected pricing threshold")
        checked += 1
    if checked == 0:
        raise ValueError("no matching pricing route")


def upstream_diagnostics(trace: ProviderTrace) -> FailureDiagnostics | None:
    """Extract a nested upstream error through the redacted diagnostic projection."""
    error = (trace.response or {}).get("error")
    metadata = error.get("metadata") if isinstance(error, dict) else None
    raw = metadata.get("raw") if isinstance(metadata, dict) else None
    if not isinstance(raw, str) or not raw:
        return None
    try:
        parsed = JSON_OBJECT.validate_json(raw)
    except ValueError:
        parsed = {"error": {"message": raw}}
    projected = ProviderTrace.model_validate({**trace.model_dump(), "response": parsed})
    failure = GameError(
        "Upstream provider rejected the request",
        code="upstream_provider_error",
        details={"provider_trace": projected.model_dump(mode="json")},
    )
    return diagnose_exception(failure)


def main() -> None:
    if (bridge.ROOT / "launch-status.json").exists():
        raise ValueError("preserve earlier launches and select fresh attempt identifiers")
    pricing = Pricing()
    validate_pricing(BUDGET_ROOT / "route-pricing.json", pricing)
    # One operator/Guesser process owns the shared ledger across sequential fresh attempts.
    with (BUDGET_ROOT / "budget.lock").open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        budget = Budget(BUDGET_ROOT / "budget.json", pricing)

        class BudgetedProvider(OpenRouterGameProvider):
            def __init__(self, api_key: str, config: ModelConfig, *, title: str):
                if "Canary" in title:
                    # A diagnostic startup uses one HTTP attempt; generation parameters
                    # are unchanged. Games retain the registered recovery policy.
                    config = ModelConfig.model_validate(
                        {
                            **config.model_dump(),
                            "recovery": {
                                **config.recovery.model_dump(),
                                "max_elapsed_seconds": 0,
                                "max_request_attempts": 1,
                                "rate_limit_max_elapsed_seconds": 0,
                                "rate_limit_max_request_attempts": 1,
                            },
                        }
                    )
                super().__init__(api_key, config, title=title)
                self.http_client._client.event_hooks = {
                    "request": [budget.reserve],
                    "response": [budget.settle],
                }

            def complete(self, request: GameProviderRequest) -> GameProviderExchange:
                try:
                    return super().complete(request)
                except GameError as error:
                    bridge.write_model(
                        bridge.ROOT / "provider-failure.json", diagnose_exception(error)
                    )
                    raw_trace = error.details.get("provider_trace")
                    if raw_trace is not None:
                        trace = ProviderTrace.model_validate(raw_trace)
                        bridge.write_model(
                            bridge.ROOT / "provider-failure-usage.json",
                            provider_result_audit(trace),
                        )
                        upstream = upstream_diagnostics(trace)
                        if upstream is not None:
                            bridge.write_model(bridge.ROOT / "upstream-failure.json", upstream)
                    raise

        try:
            live_entry.main(provider_factory=BudgetedProvider)
        except Exception as error:  # noqa: BLE001 - redact executable-boundary diagnostics.
            live_entry.status("interrupted", f"Experiment stopped with {type(error).__name__}.")
            raise SystemExit(1) from None
