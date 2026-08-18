from __future__ import annotations

from deep20_oracle.models import (
    JsonObject,
    ProviderResultAudit,
    ProviderTrace,
    RouterMetadataAudit,
    RouterPipelineStageAudit,
)


def _bounded_text(value: object, *, limit: int) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized[:limit]


def _object(value: object) -> JsonObject | None:
    if not isinstance(value, dict):
        return None
    return {str(key): item for key, item in value.items()}


def _sequence(value: object) -> tuple[object, ...]:
    return tuple(value) if isinstance(value, list | tuple) else ()


def _nonnegative_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    return None


def _pipeline_stage(value: object) -> RouterPipelineStageAudit | None:
    stage = _object(value)
    if stage is None:
        return None
    stage_type = _bounded_text(stage.get("type"), limit=120)
    if stage_type is None:
        return None

    def tool_type(raw: object) -> str | None:
        direct = _bounded_text(raw, limit=120)
        if direct is not None:
            return direct
        tool = _object(raw)
        if tool is None:
            return None
        return _bounded_text(tool.get("type"), limit=120) or _bounded_text(
            tool.get("name"),
            limit=120,
        )

    tool_types = tuple(
        item for raw in _sequence(stage.get("tools"))[:20] if (item := tool_type(raw)) is not None
    )
    return RouterPipelineStageAudit(
        stage_type=stage_type,
        name=_bounded_text(stage.get("name"), limit=160),
        mode=_bounded_text(stage.get("mode"), limit=120),
        tool_types=tool_types,
    )


def _router_metadata(response: JsonObject | None) -> RouterMetadataAudit | None:
    if response is None:
        return None
    metadata = _object(response.get("openrouter_metadata"))
    if metadata is None:
        return None
    pipeline = tuple(
        stage
        for value in _sequence(metadata.get("pipeline"))[:30]
        if (stage := _pipeline_stage(value)) is not None
    )
    is_byok = metadata.get("is_byok")
    return RouterMetadataAudit(
        strategy=_bounded_text(metadata.get("strategy"), limit=160),
        region=_bounded_text(metadata.get("region"), limit=120),
        attempt=_nonnegative_int(metadata.get("attempt")),
        is_byok=is_byok if isinstance(is_byok, bool) else None,
        endpoint_count=len(_sequence(metadata.get("endpoints"))),
        attempt_count=len(_sequence(metadata.get("attempts"))),
        pipeline=pipeline,
    )


def provider_result_audit(trace: ProviderTrace) -> ProviderResultAudit:
    """Project a private provider trace into the durable result allowlist."""

    raw_output_characters = len(trace.raw_output or "")
    url_citation_count = sum(
        1 for annotation in trace.annotations if annotation.get("type") == "url_citation"
    )
    return ProviderResultAudit(
        requested_at=trace.requested_at,
        completed_at=trace.completed_at,
        latency_ms=trace.latency_ms,
        http_status_code=trace.http_status_code,
        response_cache_status=_bounded_text(trace.response_cache_status, limit=120),
        finish_reason=_bounded_text(trace.finish_reason, limit=120),
        retry_after_ms=trace.retry_after_ms,
        recovery=trace.recovery,
        requested_model=(_bounded_text(trace.requested_model, limit=300) or "unreported"),
        resolved_model=_bounded_text(trace.resolved_model, limit=300),
        requested_provider=(_bounded_text(trace.requested_provider, limit=300) or "unreported"),
        resolved_provider=_bounded_text(trace.resolved_provider, limit=300),
        fallback_occurred=trace.fallback_occurred,
        usage=trace.usage,
        web_search_requests=trace.usage.search_count,
        annotation_count=len(trace.annotations),
        url_citation_count=url_citation_count,
        raw_output_present=raw_output_characters > 0,
        raw_output_characters=raw_output_characters,
        discarded_error_output_count=len(trace.discarded_error_outputs),
        router_metadata=_router_metadata(trace.response),
    )
