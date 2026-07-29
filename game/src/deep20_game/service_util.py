from __future__ import annotations

from decimal import Decimal
from typing import Any

from deep20_oracle.models import ProviderTrace
from deep20_oracle.util import openrouter_provider_matches
from pydantic import ValidationError

from .config import ModelConfig
from .errors import GameProviderError
from .models import CallMetrics

MILLION = Decimal(1_000_000)


def estimated_cache_savings(trace: ProviderTrace, config: ModelConfig) -> Decimal:
    usage = trace.usage
    cache = config.prompt_cache
    base = cache.input_usd_per_million / MILLION
    cached = cache.cached_input_usd_per_million / MILLION
    write = base * cache.cache_write_multiplier
    cached_tokens = min(usage.cached_input_tokens, usage.input_tokens)
    write_tokens = min(
        usage.cache_write_tokens,
        max(usage.input_tokens - cached_tokens, 0),
    )
    ordinary_tokens = max(usage.input_tokens - cached_tokens - write_tokens, 0)
    baseline = Decimal(usage.input_tokens) * base
    actual = (
        Decimal(ordinary_tokens) * base
        + Decimal(cached_tokens) * cached
        + Decimal(write_tokens) * write
    )
    return baseline - actual


def metrics_from_trace(trace: ProviderTrace, config: ModelConfig) -> CallMetrics:
    usage = trace.usage
    return CallMetrics(
        cost_usd=usage.cost_usd,
        latency_ms=trace.latency_ms,
        input_tokens=usage.input_tokens,
        cached_input_tokens=usage.cached_input_tokens,
        cache_write_tokens=usage.cache_write_tokens,
        output_tokens=usage.output_tokens,
        reasoning_tokens=usage.reasoning_tokens,
        cache_discount_usd=usage.cache_discount_usd,
        estimated_cache_savings_usd=estimated_cache_savings(trace, config),
        recovery=trace.recovery,
    )


def validate_game_trace(trace: ProviderTrace, config: ModelConfig) -> None:
    if trace.resolved_model != trace.requested_model:
        raise GameProviderError(
            "resolved model differs from the configured exact model",
            code="resolved_model_mismatch",
            details={"provider_trace": trace.model_dump(mode="json")},
        )
    if (
        trace.resolved_provider is not None
        and not openrouter_provider_matches(
            trace.requested_provider,
            trace.resolved_provider,
        )
    ):
        raise GameProviderError(
            "resolved provider differs from the configured exact provider",
            code="resolved_provider_mismatch",
            details={"provider_trace": trace.model_dump(mode="json")},
        )
    if trace.usage.search_count != 0:
        raise GameProviderError(
            "non-Oracle model unexpectedly used web search",
            code="unexpected_web_search",
            details={"provider_trace": trace.model_dump(mode="json")},
        )
    if (trace.response_cache_status or "").casefold() == "hit":
        raise GameProviderError(
            "OpenRouter response cache replay is prohibited",
            code="response_cache_replay",
            details={"provider_trace": trace.model_dump(mode="json")},
        )


def provider_trace_from_error(error: Exception) -> ProviderTrace | None:
    if not hasattr(error, "details"):
        return None
    value: Any = getattr(error, "details", {}).get("provider_trace")
    if not isinstance(value, dict):
        return None
    try:
        return ProviderTrace.model_validate(value)
    except ValidationError:
        return None
