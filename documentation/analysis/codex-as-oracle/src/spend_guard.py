"""Model-independent attempt accounting for the on-demand interactive experiment."""

from __future__ import annotations

import threading
from collections.abc import Callable
from decimal import Decimal, InvalidOperation

import httpx
from deep20_game.config import CacheControl, ModelConfig
from deep20_oracle.models import JsonObject, StrictModel
from pydantic import Field, JsonValue, TypeAdapter

JSON_OBJECT: TypeAdapter[JsonObject] = TypeAdapter(JsonObject)
_RESERVATION = "deep20_interactive_budget"


class Rate(StrictModel):
    input_per_token: Decimal = Field(ge=0, allow_inf_nan=False)
    output_per_token: Decimal = Field(ge=0, allow_inf_nan=False)
    per_request: Decimal = Field(ge=0, allow_inf_nan=False)


class PriceBound(StrictModel):
    model: str
    provider: str
    context_tokens: int = Field(gt=0)
    max_output_tokens: int = Field(gt=0)
    rate: Rate
    margin: Decimal = Field(default=Decimal("1.10"), ge=1, allow_inf_nan=False)


class BudgetState(StrictModel):
    limit_usd: Decimal = Field(gt=0, allow_inf_nan=False)
    reported_usd: Decimal = Field(default=Decimal(0), ge=0, allow_inf_nan=False)
    reserved_usd: Decimal = Field(default=Decimal(0), ge=0, allow_inf_nan=False)
    attempts: int = Field(default=0, ge=0)
    unmetered_attempts: int = Field(default=0, ge=0)


def _amount(value: JsonValue) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise TypeError("missing or invalid pricing amount")
    try:
        amount = Decimal(str(value))
    except InvalidOperation:
        raise ValueError("invalid pricing amount") from None
    if not amount.is_finite() or amount < 0:
        raise ValueError("invalid pricing amount")
    return amount


def _rate(pricing: JsonObject, base: JsonObject, config: ModelConfig) -> Rate:
    prompt = _amount(pricing.get("prompt", base.get("prompt")))
    completion = _amount(pricing.get("completion", base.get("completion")))
    inputs = [prompt]
    for key in ("input_cache_read", "input_cache_write"):
        value = pricing.get(key, base.get(key))
        if value is not None:
            inputs.append(_amount(value))
        elif (
            key == "input_cache_write" and config.prompt_cache.control is not CacheControl.AUTOMATIC
        ):
            raise ValueError("explicit prompt caching requires an advertised write rate")
    return Rate(
        input_per_token=max(inputs),
        output_per_token=completion,
        per_request=_amount(pricing.get("request", base.get("request", 0))),
    )


def price_bound(raw: bytes, config: ModelConfig) -> PriceBound:
    """Use the most expensive advertised rate across the exact route and its tiers."""
    if config.gateway != "openrouter" or config.allow_fallbacks:
        raise ValueError("budgeted experiments require an exact OpenRouter route")
    payload = JSON_OBJECT.validate_json(raw)
    data = payload.get("data")
    if not isinstance(data, dict) or data.get("id") != config.model:
        raise ValueError("pricing metadata does not match the selected model")
    endpoints = data.get("endpoints")
    if not isinstance(endpoints, list):
        raise TypeError("missing pricing endpoints")
    rates: list[Rate] = []
    contexts: list[int] = []
    for endpoint in endpoints:
        if not isinstance(endpoint, dict):
            raise TypeError("invalid pricing endpoint")
        tag = endpoint.get("tag")
        if not isinstance(tag, str):
            raise TypeError("missing pricing route")
        if not (
            tag.casefold() == config.provider.casefold()
            or tag.casefold().startswith(config.provider.casefold() + "/")
        ):
            continue
        if endpoint.get("status") != 0:
            continue
        context = endpoint.get("context_length")
        if isinstance(context, bool) or not isinstance(context, int) or context <= 0:
            raise ValueError("missing route context ceiling")
        contexts.append(context)
        pricing = endpoint.get("pricing")
        if not isinstance(pricing, dict):
            raise TypeError("missing route prices")
        rates.append(_rate(pricing, pricing, config))
        overrides = pricing.get("overrides", [])
        if not isinstance(overrides, list):
            raise TypeError("invalid pricing tiers")
        for override in overrides:
            if not isinstance(override, dict):
                raise TypeError("invalid pricing tier")
            rates.append(_rate(override, pricing, config))
    if not rates:
        raise ValueError("no active pricing endpoint for the selected provider")
    return PriceBound(
        model=config.model,
        provider=config.provider,
        context_tokens=max(contexts),
        max_output_tokens=config.max_output_tokens,
        rate=Rate(
            input_per_token=max(rate.input_per_token for rate in rates),
            output_per_token=max(rate.output_per_token for rate in rates),
            per_request=max(rate.per_request for rate in rates),
        ),
    )


def _validate_text_messages(value: JsonValue) -> None:
    if not isinstance(value, list) or not value:
        raise ValueError("budget requires text messages")
    for message in value:
        if not isinstance(message, dict):
            raise TypeError("invalid budgeted message")
        content = message.get("content")
        if isinstance(content, str):
            continue
        if not isinstance(content, list) or not content:
            raise ValueError("budget requires text content")
        for part in content:
            if (
                not isinstance(part, dict)
                or part.get("type") != "text"
                or not isinstance(part.get("text"), str)
            ):
                raise ValueError("budget permits only text content")


class Budget:
    """Persist through the launcher's sink before allowing each HTTP attempt."""

    def __init__(
        self, state: BudgetState, pricing: PriceBound, sink: Callable[[BudgetState], None]
    ):
        self.state, self.pricing, self.sink = state, pricing, sink
        self._lock = threading.Lock()

    def bound(self, request: httpx.Request) -> Decimal:
        payload = JSON_OBJECT.validate_json(request.content)
        pricing = self.pricing
        if payload.get("model") != pricing.model:
            raise ValueError("unexpected budgeted model")
        maximum = payload.get("max_tokens")
        if (
            isinstance(maximum, bool)
            or not isinstance(maximum, int)
            or not 1 <= maximum <= pricing.max_output_tokens
        ):
            raise ValueError("unexpected budgeted output ceiling")
        provider = payload.get("provider")
        if (
            not isinstance(provider, dict)
            or provider.get("only") != [pricing.provider]
            or provider.get("allow_fallbacks") is not False
        ):
            raise ValueError("unexpected budgeted provider route")
        if payload.get("tools") or payload.get("plugins") or payload.get("stream"):
            raise ValueError("budget permits only text-only non-streaming requests")
        _validate_text_messages(payload.get("messages"))
        # Include schema/payload bytes and ample provider framing. Use the full route
        # context as the ceiling, maximum output and worst tier without cache discounts.
        inputs = min(pricing.context_tokens, len(request.content) * 4 + 65536)
        return (
            inputs * pricing.rate.input_per_token
            + maximum * pricing.rate.output_per_token
            + pricing.rate.per_request
        ) * pricing.margin

    def reserve(self, request: httpx.Request) -> None:
        amount = self.bound(request)
        with self._lock:
            state = self.state
            if state.reported_usd + state.reserved_usd + amount > state.limit_usd:
                raise RuntimeError("experiment_spending_cap_reached")
            next_state = BudgetState.model_validate(
                {
                    **state.model_dump(),
                    "reserved_usd": state.reserved_usd + amount,
                    "attempts": state.attempts + 1,
                    "unmetered_attempts": state.unmetered_attempts + 1,
                }
            )
            self.sink(next_state)
            self.state = next_state
            request.extensions[_RESERVATION] = amount

    def settle(self, response: httpx.Response) -> None:
        response.read()
        try:
            payload = JSON_OBJECT.validate_json(response.content)
        except ValueError:
            return
        usage = payload.get("usage")
        raw_cost = usage.get("cost") if isinstance(usage, dict) else None
        if raw_cost is None:
            return  # Unknown or failed billing retains its full durable reservation.
        cost = _amount(raw_cost)
        with self._lock:
            reservation = response.request.extensions.get(_RESERVATION)
            if not isinstance(reservation, Decimal):
                raise TypeError("missing attempt reservation")
            state = self.state
            next_state = BudgetState.model_validate(
                {
                    **state.model_dump(),
                    "reported_usd": state.reported_usd + cost,
                    "reserved_usd": state.reserved_usd - reservation,
                    "unmetered_attempts": state.unmetered_attempts - 1,
                }
            )
            self.sink(next_state)
            self.state = next_state
            del response.request.extensions[_RESERVATION]
            if cost > reservation:
                raise RuntimeError("experiment_billing_exceeded_reservation")
