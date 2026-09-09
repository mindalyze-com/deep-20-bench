from __future__ import annotations

import json

import pytest
from deep20_oracle import knowledge_prompts
from deep20_oracle.cache_contract import oracle_contract_hash
from deep20_oracle.config import AdjudicationPolicy
from deep20_oracle.models import (
    Evidence,
    EvidenceKind,
    EvidenceReviewRequest,
    OracleAnswer,
    OracleResearchAttemptResult,
    OracleRole,
)
from deep20_oracle.prompt import render_evidence_review_messages
from deep20_oracle.protocol import answer_output_schema, validate_protocol_result
from test_concise_knowledge import POLICY, PROFILE, research, setup_oracle


@pytest.mark.parametrize("kind", tuple(EvidenceKind))
@pytest.mark.parametrize("characters", (400, 2000))
def test_long_source_context_reaches_both_blind_review_roles_without_retry(
    audit_writer, oracle_request, kind, characters,
):
    context = ("Retrieved context preserving dates, scope and material qualifications. " * 40)
    context = context[:characters - 1] + "."
    payload = json.loads(research(basis="evidence", evidence=True))
    payload["evidence"][0].update(excerpt=context, kind=kind.value)
    oracle, primary, reviewer, judge = setup_oracle(
        audit_writer, json.dumps(payload), reviewer_answer="NO",
    )
    call = oracle.ask(oracle_request)
    assert call.guesser_answer() is OracleAnswer.RATHER_YES
    assert call.result.evidence[0].excerpt == context
    assert call.result.evidence[0].kind is kind
    assert call.metrics.recovery.retried_calls == 0
    assert len(primary.requests) == len(reviewer.requests) == len(judge.requests) == 1
    for request in reviewer.requests + judge.requests:
        data = json.loads(request.messages[1]["content"].split("\n", 1)[1])
        assert set(data) == {"subject", "current_yes_no_question", "numbered_evidence_excerpts"}
        expected = {"number": 1, "excerpt": context}
        if kind is EvidenceKind.SOURCE_SUMMARY:
            expected["kind"] = "source_summary"
        assert data["numbered_evidence_excerpts"] == [expected]
        serialized = json.dumps(request.messages)
        for private in ("PRIVATE_ORACLE_SUPPORT", "PRIVATE_REVIEWER_SUPPORT", "PRIVATE_SEARCH",
                        "https://example.test/fact"):
            assert private not in serialized
        assert "not an exact quotation" in request.messages[0]["content"]
    # There is no word cap, and the original character allowance remains in the live schema.
    fields = primary.requests[0].output_schema["$defs"]["Evidence"]["properties"]
    assert fields["excerpt"]["maxLength"] == 2000
    assert "kind" in fields


def test_old_evidence_round_trip_preserves_signature_payload_and_quote_meaning():
    old = {"source_url": "https://example.test/source", "excerpt": "A source quotation.",
           "validation": "model_reported"}
    evidence = Evidence.model_validate(old)
    assert evidence.kind is EvidenceKind.QUOTATION
    assert evidence.model_dump(mode="json") == old
    summary = Evidence.model_validate({**old, "kind": "source_summary"})
    assert summary.model_dump(mode="json")["kind"] == "source_summary"
    assert Evidence.model_validate_json(summary.model_dump_json()) == summary


def test_source_summaries_require_the_corresponding_live_and_review_policy(oracle_request):
    payload = json.loads(research(basis="evidence", evidence=True))
    payload["evidence"][0]["kind"] = "source_summary"
    result = OracleResearchAttemptResult.model_validate(payload)
    validate_protocol_result(result, PROFILE, policy=POLICY)
    for policy in (AdjudicationPolicy.PROFILE_DEFAULT, AdjudicationPolicy.JUDGE_STABLE_KNOWLEDGE_V1):
        with pytest.raises(ValueError, match="source summaries require"):
            validate_protocol_result(result, PROFILE, policy=policy)
        for role in (OracleRole.REVIEWER, OracleRole.JUDGE):
            with pytest.raises(ValueError, match="source summaries require"):
                render_evidence_review_messages(
                    EvidenceReviewRequest(subject=oracle_request.subject, question=oracle_request.question,
                                          evidence=result.evidence),
                    role=role, profile=PROFILE, policy=policy,
                )


def test_unsupported_evidence_kind_is_rejected():
    payload = json.loads(research(basis="evidence", evidence=True))
    payload["evidence"][0]["kind"] = "remembered_fact"
    with pytest.raises(ValueError):
        OracleResearchAttemptResult.model_validate(payload)


def test_summary_wire_contract_keeps_historical_schemas_and_separates_cache(config, monkeypatch):
    schema = answer_output_schema(OracleResearchAttemptResult, PROFILE, policy=POLICY)
    assert schema["$defs"]["EvidenceKind"]["enum"] == ["quotation", "source_summary"]
    historical = answer_output_schema(OracleResearchAttemptResult, PROFILE)
    assert set(historical["$defs"]["Evidence"]["properties"]) == {
        "source_url", "excerpt", "validation",
    }
    assert "EvidenceKind" not in historical["$defs"]
    concise = config.model_copy(update={"prompt_profile": PROFILE, "adjudication_policy": POLICY})
    current_hash, old_hash = oracle_contract_hash(concise), oracle_contract_hash(config)
    monkeypatch.setattr(knowledge_prompts, "PRIMARY_PROMPT_VERSION", "previous-research-fixture")
    assert oracle_contract_hash(concise) != current_hash
    assert oracle_contract_hash(config) == old_hash
