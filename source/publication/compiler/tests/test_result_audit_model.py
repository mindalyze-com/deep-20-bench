from __future__ import annotations

import pytest
from pydantic import ValidationError

from deep20_publication.models import EpisodeResultAuditSnapshot


def _provider_audit() -> dict[str, object]:
    return {
        "schema_version": 1,
        "requested_at": "2026-08-17T10:00:00+00:00",
        "completed_at": "2026-08-17T10:00:01+00:00",
        "latency_ms": 1_000,
        "recovery": {},
        "requested_model": "openai/test-model",
        "resolved_model": "openai/test-model",
        "requested_provider": "openai",
        "resolved_provider": "OpenAI",
        "fallback_occurred": False,
        "usage": {"search_count": 3},
        "web_search_requests": 3,
        "annotation_count": 0,
        "url_citation_count": 0,
        "raw_output_present": True,
        "raw_output_characters": 42,
        "discarded_error_output_count": 0,
        "router_metadata": {
            "attempt_count": 1,
            "pipeline": [
                {
                    "stage_type": "server_tools",
                    "mode": "parallel",
                    "tool_types": ["web_search"],
                }
            ],
        },
    }


def test_private_result_audit_snapshot_is_strict_and_typed() -> None:
    value = EpisodeResultAuditSnapshot.model_validate(
        {
            "schema_version": 1,
            "calls": [
                {
                    "component": "oracle",
                    "call_id": "OC-00000000000000000000000000000001",
                    "turn_number": 1,
                    "status": "success",
                    "oracle": {
                        "role": "oracle",
                        "prompt": {"version": "oracle-v1", "hash": "a" * 64},
                        "provider": _provider_audit(),
                    },
                    "research": {
                        "question_class": "temporal_status",
                        "resolution": "retrieval_exhausted_unknown",
                        "attempts": [
                            {
                                "attempt_number": 1,
                                "strategy": "primary",
                                "outcome": "no_results",
                                "attempted_queries": ["Albert Einstein alive"],
                                "query_provenance": "model_reported",
                                "evidence_count": 0,
                                "prompt": {
                                    "version": "oracle-v1",
                                    "hash": "a" * 64,
                                },
                                "provider": _provider_audit(),
                            },
                            {
                                "attempt_number": 2,
                                "strategy": "diversified_recovery",
                                "outcome": "irrelevant_results",
                                "attempted_queries": ["Albert Einstein death date biography"],
                                "query_provenance": "model_reported",
                                "evidence_count": 0,
                                "prompt": {
                                    "version": "oracle-recovery-v1",
                                    "hash": "b" * 64,
                                },
                                "provider": _provider_audit(),
                            },
                        ],
                    },
                }
            ],
            "unavailable_call_count": 0,
        }
    )

    oracle = value.calls[0]
    assert oracle.component == "oracle"
    assert oracle.research is not None
    assert oracle.research.attempts[1].strategy == "diversified_recovery"


def test_private_result_audit_snapshot_rejects_provider_trace_fields() -> None:
    provider = _provider_audit()
    provider["response_id"] = "must-not-be-retained"

    with pytest.raises(ValidationError, match="response_id"):
        EpisodeResultAuditSnapshot.model_validate(
            {
                "schema_version": 1,
                "calls": [
                    {
                        "component": "guesser",
                        "call_id": "GC-00000000000000000000000000000001",
                        "turn_number": 1,
                        "status": "success",
                        "prompt": {"version": "guesser-v1", "hash": "a" * 64},
                        "provider": provider,
                    }
                ],
            }
        )
