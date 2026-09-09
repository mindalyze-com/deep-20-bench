from __future__ import annotations

import json
from decimal import Decimal

import httpx
import pytest
from deep20_oracle import cache_contract, search_budget
from deep20_oracle.audit import RunAuditWriter
from deep20_oracle.config import AdjudicationPolicy, OracleConfig, ParallelSearchMode, PromptProfile
from deep20_oracle.errors import OracleProtocolError, OracleProviderError
from deep20_oracle.models import (
    EvidenceDecisionBasis,
    EvidenceReviewResult,
    OracleAnswer,
    OracleRequest,
    OracleResearchAttemptResult,
    OracleResearchResolution,
    OracleRole,
    ProviderTrace,
)
from deep20_oracle.openrouter_provider import OpenRouterProvider
from deep20_oracle.protocol import answer_output_schema, validate_protocol_result
from deep20_oracle.provider import ProviderRequest
from deep20_oracle.service import Oracle

from conftest import FakeProvider

POLICY = AdjudicationPolicy.CONCISE_KNOWLEDGE_V1
PROFILE = PromptProfile.QUALIFIED_V1


def research(answer: str = "YES", basis: str = "other", evidence: bool = False) -> str:
    return json.dumps({
        "answer": answer, "basis": basis,
        "supporting_statement": "PRIVATE_ORACLE_SUPPORT: remembered factual support or unresolved gap.",
        "evidence": ([{"source_url": "https://example.test/fact", "excerpt": "PRIVATE_SOURCE",
                      "validation": "model_reported"}] if evidence else []),
        "research_outcome": "answered" if answer != "UNKNOWN" else "insufficient_coverage",
        "attempted_queries": ["PRIVATE_SEARCH"],
    })


def review(answer: str, label: str) -> str:
    return json.dumps({"answer": answer, "basis": "other", "evidence_indices": [],
                       "supporting_statement": f"PRIVATE_{label}_SUPPORT: remembered factual support."})


def setup_oracle(audit_writer: RunAuditWriter, output: str, reviewer_answer: str = "YES",
                 searches: int = 1) -> tuple[Oracle, FakeProvider, FakeProvider, FakeProvider]:
    config = audit_writer.config.model_copy(update={"prompt_profile": PROFILE,
                                                   "adjudication_policy": POLICY})
    audit_writer.config = config
    primary = FakeProvider(output, search_count=searches)
    reviewer = FakeProvider(review(reviewer_answer, "REVIEWER"), search_count=0,
                            model=config.reviewer.model)
    judge = FakeProvider(review("RATHER_YES", "JUDGE"), search_count=0, model=config.judge.model)
    return Oracle(primary, reviewer, judge, audit_writer, config), primary, reviewer, judge


@pytest.mark.parametrize("answer", tuple(OracleAnswer))
def test_only_two_new_basis_values_and_required_bounded_support(answer: OracleAnswer) -> None:
    result = OracleResearchAttemptResult.model_validate_json(research(answer.value))
    validate_protocol_result(result, PROFILE, policy=POLICY, role=OracleRole.ORACLE)
    for model, role in ((OracleResearchAttemptResult, OracleRole.ORACLE),
                        (EvidenceReviewResult, OracleRole.REVIEWER),
                        (EvidenceReviewResult, OracleRole.JUDGE)):
        schema = answer_output_schema(model, PROFILE, policy=POLICY, role=role)
        assert schema["$defs"]["EvidenceDecisionBasis"]["enum"] == ["evidence", "other"]
        assert {"basis", "supporting_statement"} <= set(schema["required"])
        assert schema["properties"]["supporting_statement"]["maxLength"] == 600
    for basis in ("mixed", "unresolved", "model_knowledge"):
        payload = json.loads(research(answer.value))
        payload["basis"] = basis
        with pytest.raises(ValueError):
            parsed = OracleResearchAttemptResult.model_validate(payload)
            validate_protocol_result(parsed, PROFILE, policy=POLICY)
    for change in ({"basis": None, "supporting_statement": None},
                   {"supporting_statement": "x" * 601},
                   {"attempted_queries": ["a", "b", "c", "d", "e", "f"]}):
        payload = {**json.loads(research(answer.value)), **change}
        with pytest.raises(ValueError):
            parsed = OracleResearchAttemptResult.model_validate(payload)
            validate_protocol_result(parsed, PROFILE, policy=POLICY)


@pytest.mark.parametrize("reviewer_answer", ("YES", "NO"))
def test_source_free_answer_is_reviewed_blindly_and_support_is_audited(
    audit_writer: RunAuditWriter, oracle_request: OracleRequest, reviewer_answer: str,
) -> None:
    oracle, primary, reviewer, judge = setup_oracle(audit_writer, research(), reviewer_answer)
    call = oracle.ask(oracle_request)
    assert call.result.basis is EvidenceDecisionBasis.OTHER
    assert call.result.evidence == ()
    assert call.result.supporting_statement is not None
    assert len(reviewer.requests) == 1
    assert len(judge.requests) == int(reviewer_answer == "NO")
    assert call.guesser_answer().value == ("YES" if reviewer_answer == "YES" else "RATHER_YES")
    for request in reviewer.requests + judge.requests:
        data = json.loads(request.messages[1]["content"].split("\n", 1)[1])
        assert set(data) == {"subject", "current_yes_no_question", "numbered_evidence_excerpts"}
        assert data["numbered_evidence_excerpts"] == []
        assert "PRIVATE_ORACLE_SUPPORT" not in json.dumps(request.messages)
        assert "PRIVATE_REVIEWER_SUPPORT" not in json.dumps(request.messages)
        assert "PRIVATE_SEARCH" not in json.dumps(request.messages)
        assert request.max_web_search_requests is None
    assert primary.requests[0].max_web_search_requests == 5
    assert call.audit.research.summary().attempts[0].basis is EvidenceDecisionBasis.OTHER


@pytest.mark.parametrize("target,searches,reported_queries", ((3, 4, 3), (3, 4, 4), (3, 5, 5), (5, 7, 7)))
def test_search_headroom_preserves_answer_review_and_actual_usage(
    audit_writer: RunAuditWriter, oracle_request: OracleRequest,
    target: int, searches: int, reported_queries: int,
) -> None:
    # The live failure reported four searches while its answer listed three queries.
    payload = json.loads(research())
    payload["attempted_queries"] = [f"PRIVATE_SEARCH_{i}" for i in range(reported_queries)]
    audit_writer.config = audit_writer.config.model_copy(update={"research_query_target": target})
    oracle, primary, reviewer, judge = setup_oracle(
        audit_writer, json.dumps(payload), reviewer_answer="NO", searches=searches,
    )
    call = oracle.ask(oracle_request)
    assert call.guesser_answer() is OracleAnswer.RATHER_YES
    assert len(primary.requests) == len(reviewer.requests) == len(judge.requests) == 1
    assert call.metrics.search_count == searches
    assert call.metrics.cost_usd == Decimal("0.03")
    assert call.audit.research.attempts[0].result.attempted_queries == tuple(payload["attempted_queries"])
    assert f"at most {target} queries total" in primary.requests[0].messages[0]["content"]
    assert primary.requests[0].max_web_search_requests == target + 2
    assert primary.requests[0].output_schema["properties"]["attempted_queries"]["maxItems"] == target + 2
    for request in reviewer.requests + judge.requests:
        assert "PRIVATE_SEARCH" not in json.dumps(request.messages)


@pytest.mark.parametrize("target", (3, 5))
def test_completed_answer_above_hard_search_limit_still_fails_without_review(
    audit_writer: RunAuditWriter, oracle_request: OracleRequest, target: int,
) -> None:
    audit_writer.config = audit_writer.config.model_copy(update={"research_query_target": target})
    oracle, primary, reviewer, judge = setup_oracle(audit_writer, research(), searches=target + 3)
    with pytest.raises(OracleProtocolError) as caught:
        oracle.ask(oracle_request)
    assert caught.value.code == "web_search_budget_exceeded"
    assert len(primary.requests) == 1
    assert not reviewer.requests and not judge.requests


@pytest.mark.parametrize("target,limit", ((3, 5), (5, 7), (28, 30)))
def test_query_target_configuration_derives_limit_and_round_trips(target: int, limit: int) -> None:
    config = OracleConfig(model="openai/test-model", provider="openai",
                          prompt_profile=PROFILE, adjudication_policy=POLICY,
                          research_query_target=target)
    assert config.research_search_limit == limit
    assert OracleConfig.model_validate_json(config.model_dump_json()).research_search_limit == limit
    assert ("research_query_target" in config.model_dump()) == (target != 3)


@pytest.mark.parametrize("target", (0, 29, True, "5"))
def test_invalid_query_target_is_rejected(target) -> None:
    with pytest.raises(ValueError):
        OracleConfig(model="openai/test-model", provider="openai",
                     prompt_profile=PROFILE, adjudication_policy=POLICY,
                     research_query_target=target)


def test_search_limits_are_part_of_concise_contract_only(config: OracleConfig, monkeypatch) -> None:
    concise = config.model_copy(update={"prompt_profile": PROFILE, "adjudication_policy": POLICY})
    original = cache_contract.oracle_contract_hash(concise)
    standard = cache_contract.oracle_contract_hash(config)
    monkeypatch.setattr(search_budget, "SEARCH_CALL_BONUS", 3)
    assert cache_contract.oracle_contract_hash(concise) != original
    assert cache_contract.oracle_contract_hash(config) == standard


def test_unknown_retains_context_without_a_second_research_attempt(
    audit_writer: RunAuditWriter, oracle_request: OracleRequest,
) -> None:
    oracle, primary, reviewer, judge = setup_oracle(audit_writer, research("UNKNOWN", evidence=True))
    call = oracle.ask(oracle_request)
    assert call.guesser_answer() is OracleAnswer.UNKNOWN
    assert len(call.result.evidence) == 1
    assert len(primary.requests) == 1
    assert not reviewer.requests and not judge.requests
    assert call.audit.research.resolution is OracleResearchResolution.BOUNDED_UNKNOWN


@pytest.mark.parametrize("characters", (400, 2000))
def test_long_evidence_is_preserved_and_does_not_trigger_recovery(
    audit_writer: RunAuditWriter, oracle_request: OracleRequest, characters: int,
) -> None:
    context = ("Relevant source context with important qualifications. " * 40)[:characters - 1] + "."
    payload = json.loads(research(basis="evidence", evidence=True))
    payload["evidence"][0]["excerpt"] = context
    oracle, primary, reviewer, judge = setup_oracle(audit_writer, json.dumps(payload))
    call = oracle.ask(oracle_request)
    assert call.guesser_answer() is OracleAnswer.YES
    assert call.result.evidence[0].excerpt == context
    data = json.loads(reviewer.requests[0].messages[1]["content"].split("\n", 1)[1])
    assert data["numbered_evidence_excerpts"][0]["excerpt"] == context
    assert len(primary.requests) == len(reviewer.requests) == 1
    assert not judge.requests
    assert call.metrics.recovery.retried_calls == 0


@pytest.mark.parametrize("searches,expected_calls", ((1, 2), (3, 2), (4, 2), (5, 1), (6, 1)))
def test_bad_output_never_restarts_a_full_search_budget(
    audit_writer: RunAuditWriter, oracle_request: OracleRequest, searches: int, expected_calls: int,
) -> None:
    oracle, primary, _, _ = setup_oracle(audit_writer, "invalid JSON", searches=searches)
    with pytest.raises(OracleProtocolError):
        oracle.ask(oracle_request)
    assert len(primary.requests) == expected_calls
    if expected_calls == 2:
        assert primary.requests[1].max_web_search_requests == 5 - searches
        assert primary.requests[1].messages[:2] == primary.requests[0].messages[:2]


@pytest.mark.parametrize("mode", (ParallelSearchMode.BASIC, ParallelSearchMode.FAST))
@pytest.mark.parametrize("query_target", (3, 5))
def test_actual_sdk_http_request_enforces_search_limit(
    mode: ParallelSearchMode, query_target: int,
) -> None:
    bodies: list[dict] = []

    def handle(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json={
            "id": "test-response", "model": "openai/test-model", "provider": "openai",
            "object": "chat.completion", "created": 0, "system_fingerprint": None,
            "choices": [{"index": 0, "finish_reason": "stop", "message": {
                "role": "assistant", "content": research(),
            }}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15,
                      "server_tool_use_details": {"web_search_requests": 1}},
        })

    config = OracleConfig(model="openai/test-model", provider="openai", prompt_profile=PROFILE,
                          adjudication_policy=POLICY, parallel_search_mode=mode,
                          research_query_target=query_target)
    with OpenRouterProvider("test-key", config) as provider:
        provider.http_client._client.close()
        provider.http_client._client = httpx.Client(transport=httpx.MockTransport(handle))
        for cap in (config.research_search_limit, 1):
            provider.complete(ProviderRequest(
                messages=({"role": "user", "content": "unchanged blind question"},),
                output_schema=answer_output_schema(OracleResearchAttemptResult, PROFILE, policy=POLICY),
                max_web_search_requests=cap,
            ))
    assert [body["max_tool_calls"] for body in bodies] == [query_target + 2, 1]
    assert [body["tools"][0]["parameters"]["max_uses"] for body in bodies] == [query_target + 2, 1]
    assert bodies[0]["messages"] == bodies[1]["messages"]


@pytest.mark.parametrize("recovered", (True, False))
@pytest.mark.parametrize("query_target,first_searches", ((3, 1), (3, 4), (5, 6)))
def test_service_format_retry_merges_actual_search_budget_requests(
    audit_writer: RunAuditWriter, oracle_request: OracleRequest, recovered: bool,
    query_target: int, first_searches: int,
) -> None:
    """Exercise the serialized SDK payload that previously broke trace merging."""
    bodies: list[dict] = []
    config = audit_writer.config.model_copy(update={"prompt_profile": PROFILE,
                                                   "adjudication_policy": POLICY,
                                                   "research_query_target": query_target})
    audit_writer.config = config

    def handle(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        output = research() if len(bodies) == 2 and recovered else "PRIVATE_MALFORMED"
        return httpx.Response(200, json={
            "id": f"test-{len(bodies)}", "model": config.model, "provider": config.provider,
            "object": "chat.completion", "created": 0, "system_fingerprint": None,
            "choices": [{"index": 0, "finish_reason": "stop", "message": {
                "role": "assistant", "content": output,
            }}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15,
                      "cost": 0.01, "server_tool_use_details": {
                          "web_search_requests": first_searches if len(bodies) == 1 else 1}},
        })

    reviewer = FakeProvider(review("YES", "REVIEWER"), search_count=0,
                            model=config.reviewer.model)
    judge = FakeProvider("unused", search_count=0, model=config.judge.model)
    with OpenRouterProvider("test-key", config) as provider:
        provider.http_client._client.close()
        provider.http_client._client = httpx.Client(transport=httpx.MockTransport(handle))
        oracle = Oracle(provider, reviewer, judge, audit_writer, config)
        if recovered:
            call = oracle.ask(oracle_request)
            assert call.guesser_answer() is OracleAnswer.YES
            trace = call.audit.provider
        else:
            with pytest.raises(OracleProtocolError) as caught:
                oracle.ask(oracle_request)
            trace = ProviderTrace.model_validate(caught.value.details["provider_trace"])
            assert not reviewer.requests
    assert len(bodies) == 2
    hard_limit = query_target + 2
    assert [body["max_tool_calls"] for body in bodies] == [hard_limit, hard_limit - first_searches]
    assert [body["tools"][0]["parameters"]["max_uses"] for body in bodies] == [hard_limit, hard_limit - first_searches]
    assert bodies[0]["messages"][:-1] == bodies[1]["messages"][:-1]
    assert bodies[0]["messages"][-1] != bodies[1]["messages"][-1]
    assert "PRIVATE_MALFORMED" not in json.dumps(bodies[1])
    assert trace.request_attempts == 2
    assert trace.usage.search_count == first_searches + 1
    assert trace.usage.cost_usd == Decimal("0.02")
    assert trace.recovery.retry_usage.cost_usd == Decimal("0.01")
    assert trace.recovery.recovered_calls == int(recovered)
    assert trace.recovery.exhausted_retries == int(not recovered)
    assert trace.discarded_error_outputs[0].output == "PRIVATE_MALFORMED"
    assert not judge.requests


@pytest.mark.parametrize("query_target,first_searches", ((3, 0), (3, 1), (3, 4), (5, 6)))
@pytest.mark.parametrize("finish_reason", ("content_filter", "length", "stop"))
@pytest.mark.parametrize("recovered", (True, False))
def test_incomplete_research_retries_with_remaining_allowance_and_blind_review(
    audit_writer: RunAuditWriter, oracle_request: OracleRequest, monkeypatch,
    query_target: int, first_searches: int, finish_reason: str, recovered: bool,
) -> None:
    monkeypatch.setattr("deep20_oracle.openrouter_provider.time.sleep", lambda _: None)
    bodies: list[dict] = []
    config = audit_writer.config.model_copy(update={"prompt_profile": PROFILE,
                                                   "adjudication_policy": POLICY,
                                                   "research_query_target": query_target})
    audit_writer.config = config

    def handle(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        success = recovered and len(bodies) == 2
        return httpx.Response(200, json={
            "id": f"test-{len(bodies)}", "model": config.model, "provider": config.provider,
            "object": "chat.completion", "created": 0, "system_fingerprint": None,
            "choices": [{"index": 0, "finish_reason": "stop" if success else finish_reason,
                         "message": {"role": "assistant", "content": research() if success else (
                             "" if finish_reason == "stop" else "PRIVATE_INCOMPLETE")}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15,
                      "cost": 0.01, "server_tool_use_details": {
                          "web_search_requests": first_searches if len(bodies) == 1 else 1}},
        })

    reviewer = FakeProvider(review("NO", "REVIEWER"), search_count=0, model=config.reviewer.model)
    judge = FakeProvider(review("NO", "JUDGE"), search_count=0, model=config.judge.model)
    with OpenRouterProvider("test-key", config) as provider:
        provider.http_client._client.close()
        provider.http_client._client = httpx.Client(transport=httpx.MockTransport(handle))
        oracle = Oracle(provider, reviewer, judge, audit_writer, config)
        if recovered:
            call = oracle.ask(oracle_request)
            assert call.guesser_answer() is OracleAnswer.NO
            assert len(reviewer.requests) == len(judge.requests) == 1
            assert call.metrics.cost_usd == Decimal("0.04")
            trace = call.audit.provider
        else:
            with pytest.raises(OracleProviderError) as caught:
                oracle.ask(oracle_request)
            if finish_reason == "content_filter":
                assert caught.value.code == "provider_content_filtered"
            trace = ProviderTrace.model_validate(caught.value.details["provider_trace"])
            assert not reviewer.requests and not judge.requests
    assert len(bodies) == 2
    limits = [query_target + 2, query_target + 2 - first_searches]
    assert [body["max_tool_calls"] for body in bodies] == limits
    assert [body["tools"][0]["parameters"]["max_uses"] for body in bodies] == limits
    assert bodies[0]["messages"] == bodies[1]["messages"]
    for request in bodies + [r.model_dump(mode="json") for r in reviewer.requests + judge.requests]:
        assert "PRIVATE_INCOMPLETE" not in json.dumps(request)
    assert trace.request_attempts == 2
    assert trace.usage.search_count == first_searches + 1
    assert trace.usage.cost_usd == Decimal("0.02")
    assert trace.recovery.retry_usage.cost_usd == Decimal("0.01")
    assert trace.recovery.recovered_calls == int(recovered)
    assert trace.recovery.exhausted_retries == int(not recovered)
    if finish_reason == "content_filter":
        assert any(reason.reason.value == "provider_content_filtered"
                   for reason in trace.recovery.reasons)
    if finish_reason != "stop":
        assert trace.discarded_error_outputs[0].output == "PRIVATE_INCOMPLETE"


@pytest.mark.parametrize("change", (
    {"usage": {"cost": 0.01}},
    {"usage": {"cost": 0.01, "server_tool_use_details": {"web_search_requests": True}}},
    {"usage": {"cost": 0.01, "server_tool_use_details": {"web_search_requests": "1"}}},
    {"usage": {"cost": 0.01, "server_tool_use_details": {"web_search_requests": 5}}},
    {"usage": {"cost": 0.01, "server_tool_use_details": {"web_search_requests": 6}}},
    {"model": "wrong/model"}, {"provider": "wrong-provider"}, {"provider": None},
))
def test_incomplete_research_does_not_retry_unknown_usage_exhaustion_or_wrong_route(change) -> None:
    bodies: list[dict] = []
    config = OracleConfig(model="openai/test-model", provider="openai", prompt_profile=PROFILE,
                          adjudication_policy=POLICY)

    def handle(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json={
            "id": "test-incomplete", "model": config.model, "provider": config.provider,
            "object": "chat.completion", "created": 0, "system_fingerprint": None,
            "choices": [{"index": 0, "finish_reason": "content_filter", "message": {
                "role": "assistant", "content": "PRIVATE_INCOMPLETE"}}],
            "usage": {"cost": 0.01, "server_tool_use_details": {"web_search_requests": 1}},
            **change,
        })

    with OpenRouterProvider("test-key", config) as provider:
        provider.http_client._client.close()
        provider.http_client._client = httpx.Client(transport=httpx.MockTransport(handle))
        with pytest.raises(OracleProviderError):
            provider.complete(ProviderRequest(
                messages=({"role": "user", "content": "unchanged blind question"},),
                output_schema=answer_output_schema(OracleResearchAttemptResult, PROFILE, policy=POLICY),
                max_web_search_requests=config.research_search_limit,
            ))
    assert len(bodies) == 1


def test_no_result_and_format_retries_share_one_total_allowance(
    audit_writer: RunAuditWriter, oracle_request: OracleRequest, monkeypatch,
) -> None:
    monkeypatch.setattr("deep20_oracle.openrouter_provider.time.sleep", lambda _: None)
    bodies: list[dict] = []
    config = audit_writer.config.model_copy(update={"prompt_profile": PROFILE,
                                                   "adjudication_policy": POLICY})
    audit_writer.config = config

    def handle(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json={
            "id": f"test-{len(bodies)}", "model": config.model, "provider": config.provider,
            "object": "chat.completion", "created": 0, "system_fingerprint": None,
            "choices": [{"index": 0, "finish_reason": "content_filter" if len(bodies) == 1 else "stop",
                         "message": {"role": "assistant", "content": research() if len(bodies) == 3
                                     else "PRIVATE_DISCARDED"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15,
                      "cost": 0.01, "server_tool_use_details": {"web_search_requests": 1}},
        })

    reviewer = FakeProvider(review("YES", "REVIEWER"), search_count=0, model=config.reviewer.model)
    judge = FakeProvider("unused", search_count=0, model=config.judge.model)
    with OpenRouterProvider("test-key", config) as provider:
        provider.http_client._client.close()
        provider.http_client._client = httpx.Client(transport=httpx.MockTransport(handle))
        call = Oracle(provider, reviewer, judge, audit_writer, config).ask(oracle_request)
    assert call.guesser_answer() is OracleAnswer.YES
    assert [body["max_tool_calls"] for body in bodies] == [5, 4, 3]
    assert [body["tools"][0]["parameters"]["max_uses"] for body in bodies] == [5, 4, 3]
    assert bodies[0]["messages"] == bodies[1]["messages"]
    assert bodies[1]["messages"][:-1] == bodies[2]["messages"][:-1]
    assert bodies[1]["messages"][-1] != bodies[2]["messages"][-1]
    assert "PRIVATE_DISCARDED" not in json.dumps(bodies)
    assert call.audit.provider.request_attempts == 3
    assert call.audit.provider.usage.search_count == 3
    assert call.metrics.cost_usd == Decimal("0.04")
    assert len(call.audit.provider.discarded_error_outputs) == 2
