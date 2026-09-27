"""Authorized Luna run with a shared $5 budget across canary, games and retries."""

from __future__ import annotations

import argparse
import os
from decimal import Decimal
from pathlib import Path

import bridge
import httpx
import live_entry
from deep20_game.config import ModelConfig
from deep20_game.errors import GameProviderError
from deep20_game.models import GameProviderExchange, GameProviderRequest
from deep20_game.openrouter_provider import OpenRouterGameProvider
from deep20_oracle.models import JsonObject, StrictModel
from pydantic import Field, TypeAdapter


class BudgetState(StrictModel):
    limit_usd: Decimal = Decimal(5)
    reservation_per_attempt_usd: Decimal = Decimal(2)
    reported_usd: Decimal = Decimal(0)
    reserved_usd: Decimal = Decimal(0)
    attempts: int = Field(default=0, ge=0)
    unmetered_attempts: int = Field(default=0, ge=0)


class Failure(StrictModel):
    code: str
    causes: tuple[str, ...]
    http_status: int | None


class AttemptReceipt(StrictModel):
    attempt: int
    request_bytes: int | None = None
    event: str
    exception_type: str | None = None
    http_status: int | None = None


class Budget:
    def __init__(self, path: Path, previous: BudgetState | None = None):
        if path.exists():
            raise ValueError("budget requires a fresh live launch")
        self.path = path
        self.state = previous or BudgetState()
        self.active_reservation = Decimal(0)
        bridge.write_model(path, self.state)

    def reserve(self, request: httpx.Request) -> None:
        state = self.state
        # Four tokens per serialized byte plus 65,536 tokens for provider rendering
        # is deliberately conservative. Rates cover every advertised OpenAI tier.
        # The complete-context bound remains the ceiling for exceptionally large requests.
        reserve = min(state.reservation_per_attempt_usd, (
            Decimal(len(request.content) * 4 + 65536) * Decimal("0.000001")
            + Decimal(32768) * Decimal("0.0000036")
        ) * Decimal("1.1"))
        if state.reported_usd + state.reserved_usd + reserve > state.limit_usd:
            raise RuntimeError("experiment_spending_cap_reached")
        self.active_reservation = reserve
        self.state = BudgetState(
            reported_usd=state.reported_usd,
            reserved_usd=state.reserved_usd + reserve,
            attempts=state.attempts + 1,
            unmetered_attempts=state.unmetered_attempts + 1,
        )
        bridge.write_model(self.path, self.state)
        bridge.write_model(self.path.with_name("attempt-receipt.json"), AttemptReceipt(
            attempt=self.state.attempts, request_bytes=len(request.content), event="reserved"
        ))
        request.extensions["trace"] = self.trace

    def trace(self, event: str, information: dict[str, object]) -> None:
        if event.endswith(".failed"):
            error = information.get("exception")
            bridge.write_model(self.path.with_name("attempt-receipt.json"), AttemptReceipt(
                attempt=self.state.attempts, event=event, exception_type=type(error).__name__
            ))

    def settle(self, response: httpx.Response) -> None:
        bridge.write_model(self.path.with_name("attempt-receipt.json"), AttemptReceipt(
            attempt=self.state.attempts, event="http_response", http_status=response.status_code
        ))
        response.read()
        try:
            payload: JsonObject = TypeAdapter(JsonObject).validate_json(response.content)
        except ValueError:
            return  # Unknown billing keeps the full reservation, including failed calls.
        usage = payload.get("usage")
        raw_cost = usage.get("cost") if isinstance(usage, dict) else None
        if isinstance(raw_cost, bool) or not isinstance(raw_cost, (str, int, float)):
            return
        cost = Decimal(str(raw_cost))
        if not cost.is_finite() or cost < 0:
            raise RuntimeError("invalid_experiment_billing")
        reserve = self.active_reservation
        self.active_reservation = Decimal(0)
        state = self.state
        self.state = BudgetState(
            reported_usd=state.reported_usd + cost,
            reserved_usd=state.reserved_usd - reserve,
            attempts=state.attempts,
            unmetered_attempts=state.unmetered_attempts - 1,
        )
        bridge.write_model(self.path, self.state)
        if cost > reserve:
            raise RuntimeError("experiment_billing_exceeded_reservation")


def validate_reservation(path: Path) -> None:
    """Check every OpenAI tier and long-context rate before any paid call."""
    payload: JsonObject = TypeAdapter(JsonObject).validate_json(path.read_text())
    data = payload.get("data")
    if not isinstance(data, dict) or data.get("id") != "openai/gpt-5.6-luna":
        raise ValueError("wrong budget pricing model")
    endpoints = data.get("endpoints")
    if not isinstance(endpoints, list):
        raise ValueError("missing budget pricing endpoints")  # noqa: TRY004 - invalid provider data.
    bounds: list[Decimal] = []
    for endpoint in endpoints:
        if not isinstance(endpoint, dict):
            continue
        tag = endpoint.get("tag")
        if not isinstance(tag, str) or not (tag == "openai" or tag.startswith("openai/")):
            continue
        context, pricing = endpoint.get("context_length"), endpoint.get("pricing")
        if not isinstance(context, int) or not isinstance(pricing, dict):
            raise ValueError("missing context or rate bound")  # noqa: TRY004 - invalid provider data.
        rates: list[JsonObject] = [pricing]
        overrides = pricing.get("overrides", [])
        if isinstance(overrides, list):
            rates.extend(item for item in overrides if isinstance(item, dict))
        for rate in rates:
            input_rate = max(
                Decimal(str(rate.get(key, pricing.get(key, "0"))))
                for key in ("prompt", "input_cache_read", "input_cache_write")
            )
            output_rate = Decimal(str(rate.get("completion", pricing.get("completion"))))
            if input_rate > Decimal("0.000001") or output_rate > Decimal("0.0000036"):
                raise ValueError("route prices exceed request-size reservation rates")
            bounds.append((Decimal(context) * input_rate + 32768 * output_rate) * Decimal("1.1"))
    if not bounds or max(bounds) > BudgetState().reservation_per_attempt_usd:
        raise ValueError("route maximum exceeds per-attempt budget reservation")


def main() -> None:
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if not args.live or bridge.EXPERIMENT != "luna":
        parser.error("requires DEEP20_CODEX_EXPERIMENT=luna and --live")
    validate_reservation(bridge.ROOT / "route-pricing.json")
    previous_path = bridge.ROOT / "previous-budget.json"
    previous = BudgetState.model_validate_json(previous_path.read_text()) if previous_path.exists() else None
    budget = Budget(bridge.ROOT / "budget.json", previous)

    class BudgetedProvider(OpenRouterGameProvider):
        def __init__(self, api_key: str, config: ModelConfig, *, title: str):
            if config.model != "openai/gpt-5.6-luna" or config.max_output_tokens > 32768:
                raise ValueError("unexpected budgeted model configuration")
            super().__init__(api_key, config, title=title)
            self.http_client._client.event_hooks = {
                "request": [budget.reserve], "response": [budget.settle]
            }

        def complete(self, request: GameProviderRequest) -> GameProviderExchange:
            try:
                return super().complete(request)
            except GameProviderError as error:
                causes: list[str] = []
                cause: BaseException | None = error
                while cause is not None:
                    causes.append(type(cause).__name__)
                    cause = cause.__cause__
                bridge.write_model(
                    bridge.ROOT / "provider-failure.json",
                    Failure(code=error.code, causes=tuple(causes),
                            http_status=self.http_client.last_status_code),
                )
                raise

    # Rebind imported provider classes for this compatibility entry point.
    setattr(bridge, "OpenRouterGameProvider", BudgetedProvider)  # noqa: B010
    setattr(live_entry, "OpenRouterGameProvider", BudgetedProvider)  # noqa: B010
    try:
        live_entry.main()
    except Exception as error:  # noqa: BLE001 - redact executable-boundary diagnostics.
        live_entry.status("interrupted", f"Experiment stopped with {type(error).__name__}.")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
