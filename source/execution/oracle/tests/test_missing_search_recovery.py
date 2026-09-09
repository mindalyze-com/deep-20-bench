"""Offline regression for a completed Oracle reply that skipped its required search."""
import json
from contextlib import contextmanager
from decimal import Decimal

import httpx
import pytest
from deep20_oracle.errors import OracleProtocolError
from deep20_oracle.models import OracleAnswer, ProviderTrace
from deep20_oracle.openrouter_provider import OpenRouterProvider
from deep20_oracle.service import Oracle
from test_concise_knowledge import POLICY, PROFILE, research, review

from conftest import FakeProvider


@contextmanager
def http_oracle(audit_writer, replies, *, target=3, retries=1):
    config = audit_writer.config.model_copy(update={
        "prompt_profile": PROFILE, "adjudication_policy": POLICY,
        "research_query_target": target,
        "recovery": audit_writer.config.recovery.model_copy(update={"invalid_output_retries": retries}),
    })
    audit_writer.config = config
    bodies = []

    def handle(request):
        bodies.append(json.loads(request.content))
        output, searches, changes = replies[len(bodies) - 1]
        usage = {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15, "cost": 0.01}
        if searches is not None:
            usage["server_tool_use_details"] = {"web_search_requests": searches}
        return httpx.Response(200, json={
            "id": f"test-{len(bodies)}", "model": config.model, "provider": config.provider,
            "object": "chat.completion", "created": 0, "system_fingerprint": None,
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": output}}],
            "usage": usage, **changes,
        })

    reviewer = FakeProvider(review("YES", "REVIEWER"), search_count=0, model=config.reviewer.model)
    judge = FakeProvider("unused", search_count=0, model=config.judge.model)
    with OpenRouterProvider("test-key", config) as provider:
        provider.http_client._client.close()
        provider.http_client._client = httpx.Client(transport=httpx.MockTransport(handle))
        yield Oracle(provider, reviewer, judge, audit_writer, config), bodies, reviewer, judge


@pytest.mark.parametrize("target", (3, 5))
@pytest.mark.parametrize("answer", ("YES", "UNKNOWN"))
def test_zero_search_reply_gets_one_blind_budgeted_retry(audit_writer, oracle_request, target, answer):
    first = research("UNKNOWN").replace("PRIVATE_ORACLE_SUPPORT", "PRIVATE_DISCARDED_ZERO_SEARCH")
    with http_oracle(audit_writer, [(first, 0, {}), (research(answer), 1, {})], target=target) as case:
        oracle, bodies, reviewer, judge = case
        call = oracle.ask(oracle_request)
    assert call.guesser_answer() is OracleAnswer(answer)
    assert [body["max_tool_calls"] for body in bodies] == [target + 2, target + 2]
    assert [body["tools"][0]["parameters"]["max_uses"] for body in bodies] == [target + 2] * 2
    assert bodies[0]["messages"][:-1] == bodies[1]["messages"][:-1]
    assert bodies[0]["messages"][-1] != bodies[1]["messages"][-1]
    assert "PRIVATE_DISCARDED_ZERO_SEARCH" not in json.dumps(bodies)
    trace = call.audit.provider
    assert trace.request_attempts == 2
    assert trace.usage.search_count == 1
    assert trace.usage.cost_usd == Decimal("0.02")
    assert trace.recovery.recovered_calls == 1 and trace.recovery.exhausted_retries == 0
    assert trace.discarded_error_outputs[0].output == first
    assert len(reviewer.requests) == int(answer == "YES") and not judge.requests
    for request in reviewer.requests:
        assert "PRIVATE_DISCARDED_ZERO_SEARCH" not in json.dumps(request.messages)
        data = json.loads(request.messages[1]["content"].split("\n", 1)[1])
        assert set(data) == {"subject", "current_yes_no_question", "numbered_evidence_excerpts"}


@pytest.mark.parametrize("first_output,first_searches", ((research(), 0), ("PRIVATE_BAD_JSON", 2)))
def test_retry_without_search_still_fails_and_keeps_all_costs(
    audit_writer, oracle_request, first_output, first_searches,
):
    with http_oracle(audit_writer, [(first_output, first_searches, {}), (research(), 0, {})]) as case:
        oracle, bodies, reviewer, judge = case
        with pytest.raises(OracleProtocolError) as caught:
            oracle.ask(oracle_request)
    assert caught.value.code == "web_search_not_used"
    trace = ProviderTrace.model_validate(caught.value.details["provider_trace"])
    assert len(bodies) == trace.request_attempts == 2
    assert [b["max_tool_calls"] for b in bodies] == [5, 5 - first_searches]
    assert trace.usage.cost_usd == Decimal("0.02")
    assert trace.recovery.recovered_calls == 0 and trace.recovery.exhausted_retries == 1
    assert not reviewer.requests and not judge.requests


@pytest.mark.parametrize("searches,changes,code", (
    (None, {}, "web_search_not_used"),
    (0, {"model": "wrong/model"}, "resolved_model_mismatch"),
    (0, {"provider": "wrong-provider"}, "resolved_provider_mismatch"),
    (0, {"provider": None}, "web_search_not_used"),
    (6, {}, "web_search_budget_exceeded"),
))
def test_missing_telemetry_or_other_trace_faults_do_not_retry(
    audit_writer, oracle_request, searches, changes, code,
):
    with http_oracle(audit_writer, [(research(), searches, changes)]) as case:
        oracle, bodies, reviewer, judge = case
        with pytest.raises(OracleProtocolError) as caught:
            oracle.ask(oracle_request)
    assert caught.value.code == code
    assert len(bodies) == 1
    assert not reviewer.requests and not judge.requests


def test_zero_search_retry_respects_disabled_recovery(audit_writer, oracle_request):
    with http_oracle(audit_writer, [(research(), 0, {})], retries=0) as case:
        oracle, bodies, reviewer, judge = case
        with pytest.raises(OracleProtocolError) as caught:
            oracle.ask(oracle_request)
    assert caught.value.code == "web_search_not_used"
    trace = ProviderTrace.model_validate(caught.value.details["provider_trace"])
    assert len(bodies) == 1 and trace.recovery.exhausted_retries == 1
    assert not reviewer.requests and not judge.requests
