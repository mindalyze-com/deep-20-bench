from __future__ import annotations

import json
from decimal import Decimal

from deep20_oracle.models import ProviderTrace, ProviderUsage
from deep20_oracle.result_audit import provider_result_audit


def test_provider_result_audit_keeps_safe_forensic_facts_only() -> None:
    trace = ProviderTrace(
        requested_at="2026-08-17T10:00:00+00:00",
        completed_at="2026-08-17T10:00:02+00:00",
        latency_ms=2_000,
        http_status_code=200,
        response_id="private-response-id",
        finish_reason="stop",
        requested_model="openai/test-model",
        resolved_model="openai/test-model",
        requested_provider="openai",
        resolved_provider="OpenAI",
        fallback_occurred=False,
        request={"messages": [{"content": "private prompt"}]},
        response={
            "id": "private-response-id",
            "openrouter_metadata": {
                "strategy": "fallback",
                "region": "us-east",
                "attempt": 0,
                "is_byok": False,
                "endpoints": [{"url": "https://private-endpoint.test"}],
                "attempts": [{"provider_name": "OpenAI"}],
                "pipeline": [
                    {
                        "type": "server_tools",
                        "name": "Web search",
                        "mode": "parallel",
                        "tools": ["web_search"],
                        "data": {"private": "must not survive"},
                    }
                ],
            },
        },
        raw_output='{"answer":"UNKNOWN","private":"must not survive"}',
        annotations=(
            {
                "type": "url_citation",
                "url_citation": {"url": "https://private-citation.test"},
            },
            {"type": "other", "content": "private annotation"},
        ),
        usage=ProviderUsage(
            input_tokens=4_356,
            cached_input_tokens=2_164,
            output_tokens=169,
            reasoning_tokens=61,
            search_count=3,
            cost_usd=Decimal("0.00037249"),
        ),
    )

    audit = provider_result_audit(trace)

    assert audit.web_search_requests == 3
    assert audit.annotation_count == 2
    assert audit.url_citation_count == 1
    assert audit.raw_output_present is True
    assert audit.raw_output_characters == len(trace.raw_output or "")
    assert audit.router_metadata is not None
    assert audit.router_metadata.endpoint_count == 1
    assert audit.router_metadata.attempt_count == 1
    assert audit.router_metadata.pipeline[0].tool_types == ("web_search",)
    serialized = json.dumps(audit.model_dump(mode="json"))
    for private_value in (
        "private-response-id",
        "private prompt",
        "private-endpoint.test",
        "private-citation.test",
        "must not survive",
    ):
        assert private_value not in serialized
