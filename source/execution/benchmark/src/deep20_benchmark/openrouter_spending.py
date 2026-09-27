"""Conservative per-HTTP-attempt bounds, including native search and all SDK retries."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from urllib.parse import quote

import httpx
from deep20_backends.budget import Reservation, SpendingLedger
from deep20_backends.models import BackendError, FrozenModel, JsonObject
from deep20_game.config import CacheControl, ModelConfig
from deep20_oracle.config import ModelRouteConfig, OracleConfig, ProviderRouting
from pydantic import Field, JsonValue, TypeAdapter

_JSON: TypeAdapter[JsonObject] = TypeAdapter(JsonObject)
_RESERVATION = "deep20_spending_reservation"


class OpenRouterPriceBound(FrozenModel):
    model: str
    provider: str
    automatic: bool
    allow_fallbacks: bool
    context_tokens: int = Field(gt=0)
    max_output_tokens: int = Field(gt=0)
    input_per_token: Decimal = Field(ge=0, allow_inf_nan=False)
    output_per_token: Decimal = Field(ge=0, allow_inf_nan=False)
    per_request: Decimal = Field(ge=0, allow_inf_nan=False)
    max_search_requests: int = Field(default=0, ge=0)
    # Conservative maximum of the documented Parallel search modes, before margin.
    search_per_request: Decimal = Field(default=Decimal("0.005"), ge=0, allow_inf_nan=False)
    margin: Decimal = Field(default=Decimal("1.25"), ge=1, allow_inf_nan=False)


def amount(value: JsonValue) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise BackendError("invalid_provider_pricing", "provider pricing is missing or invalid")
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise BackendError("invalid_provider_pricing", "provider pricing is invalid") from None
    if not result.is_finite() or result < 0:
        raise BackendError("invalid_provider_pricing", "provider pricing must be finite and nonnegative")
    return result


def price_bound(payload: JsonObject, config: ModelConfig | ModelRouteConfig) -> OpenRouterPriceBound:
    data = payload.get("data")
    if not isinstance(data, dict) or data.get("id") != config.model:
        raise BackendError("pricing_model_mismatch", "pricing metadata does not match the configured model")
    endpoints = data.get("endpoints")
    if not isinstance(endpoints, list):
        raise BackendError("pricing_endpoints_missing", "provider endpoint pricing is missing")
    automatic = isinstance(config, ModelRouteConfig) and config.provider_routing is ProviderRouting.AUTOMATIC
    rates: list[JsonObject] = []
    contexts: list[int] = []
    for endpoint in endpoints:
        if not isinstance(endpoint, dict) or endpoint.get("status") != 0:
            continue
        tag = endpoint.get("tag")
        if not isinstance(tag, str) or (not automatic and not (
            tag.casefold() == config.provider.casefold()
            or tag.casefold().startswith(config.provider.casefold() + "/")
        )):
            continue
        pricing, context = endpoint.get("pricing"), endpoint.get("context_length")
        if not isinstance(pricing, dict) or type(context) is not int or context <= 0:
            raise BackendError("pricing_endpoint_invalid", "selected endpoint lacks a valid price or context bound")
        contexts.append(context)
        rates.append(pricing)
        overrides = pricing.get("overrides", [])
        if not isinstance(overrides, list):
            raise BackendError("pricing_tiers_invalid", "endpoint pricing tiers are invalid")
        for override in overrides:
            if not isinstance(override, dict):
                raise BackendError("pricing_tiers_invalid", "endpoint pricing tier is invalid")
            rates.append({**pricing, **override})
    if not rates:
        raise BackendError("pricing_route_unavailable", "no active priced endpoint matches the route")
    inputs: list[Decimal] = []
    for rate in rates:
        if (isinstance(config, ModelConfig) and config.prompt_cache.control is not CacheControl.AUTOMATIC
            and "input_cache_write" not in rate):
            raise BackendError("cache_write_price_missing", "explicit prompt caching requires verified cache-write pricing")
        inputs.append(amount(rate.get("prompt")))
        for key in ("input_cache_read", "input_cache_write"):
            if key in rate:
                inputs.append(amount(rate[key]))
    return OpenRouterPriceBound(
        model=config.model, provider=config.provider, automatic=automatic,
        allow_fallbacks=config.allow_fallbacks,
        context_tokens=max(contexts), max_output_tokens=config.max_output_tokens,
        input_per_token=max(inputs), output_per_token=max(amount(r.get("completion")) for r in rates),
        per_request=max(amount(r.get("request", 0)) for r in rates),
        max_search_requests=config.research_search_limit if isinstance(config, OracleConfig) else 0,
    )


def fetch_price_bound(config: ModelConfig | ModelRouteConfig) -> OpenRouterPriceBound:
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get("https://openrouter.ai/api/v1/models/" + quote(config.model, safe="/") + "/endpoints")
            response.raise_for_status()
            payload = _JSON.validate_json(response.content)
    except (httpx.HTTPError, ValueError):
        raise BackendError("pricing_preflight_failed", "could not verify public OpenRouter pricing") from None
    return price_bound(payload, config)


class OpenRouterSpendingGuard:
    def __init__(self, ledger: SpendingLedger, pricing: OpenRouterPriceBound):
        self.ledger = ledger
        self.pricing = pricing

    def bound(self, request: httpx.Request) -> Decimal:
        if (request.method != "POST" or request.url.scheme != "https" or request.url.host != "openrouter.ai"
            or request.url.path != "/api/v1/chat/completions"):
            raise BackendError("budget_endpoint_mismatch", "request does not use the priced inference endpoint")
        payload = _JSON.validate_json(request.content)
        pricing = self.pricing
        provider = payload.get("provider")
        if (payload.get("model") != pricing.model or not isinstance(provider, dict)
            or provider.get("allow_fallbacks") is not pricing.allow_fallbacks
            or (not pricing.automatic and provider.get("only") != [pricing.provider])):
            raise BackendError("budget_route_mismatch", "request does not match its priced route")
        maximum = payload.get("max_tokens", payload.get("max_completion_tokens"))
        if type(maximum) is not int or not 1 <= maximum <= pricing.max_output_tokens:
            raise BackendError("budget_output_unbounded", "request does not have a priced output limit")
        if payload.get("stream") or payload.get("plugins"):
            raise BackendError("budget_request_unsupported", "request contains an unpriced capability")
        searches = 0
        tools = payload.get("tools")
        if tools:
            if not isinstance(tools, list) or len(tools) != 1 or not isinstance(tools[0], dict):
                raise BackendError("budget_tools_unsupported", "request contains unpriced tools")
            tool = tools[0]
            parameters = tool.get("parameters")
            limit = payload.get("max_tool_calls")
            if (tool.get("type") != "openrouter:web_search" or not isinstance(parameters, dict)
                or parameters.get("engine") != "parallel" or type(limit) is not int
                or not 1 <= limit <= pricing.max_search_requests
                or parameters.get("max_uses") != limit):
                raise BackendError("budget_search_unbounded", "native research requires a finite priced search limit")
            searches = limit
        # A native search can trigger another inference pass. Reserve the complete
        # context/output ceiling for each possible pass, without assumed cache savings.
        inputs = (pricing.context_tokens if searches else
                  min(pricing.context_tokens, len(request.content) * 4 + 65536))
        return ((inputs * pricing.input_per_token + maximum * pricing.output_per_token
                 + pricing.per_request) * (searches + 1)
                + searches * pricing.search_per_request) * pricing.margin

    def before(self, request: httpx.Request) -> None:
        request.extensions[_RESERVATION] = self.ledger.reserve("openrouter", self.bound(request))

    def after(self, response: httpx.Response) -> None:
        response.read()
        try:
            payload = _JSON.validate_json(response.content)
        except ValueError:
            return
        usage = payload.get("usage")
        raw_cost = usage.get("cost") if isinstance(usage, dict) else None
        if raw_cost is None:
            return
        reservation = response.request.extensions.get(_RESERVATION)
        if not isinstance(reservation, Reservation):
            raise BackendError("missing_request_reservation", "HTTP response lacks its spending reservation")
        self.ledger.settle(reservation, amount(raw_cost))
