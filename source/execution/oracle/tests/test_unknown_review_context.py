"""Offline regressions for UNKNOWN review responses that explain conflicting excerpts."""
import json

import pytest
from deep20_oracle.config import AdjudicationPolicy, PromptProfile
from deep20_oracle.errors import OracleProtocolError
from deep20_oracle.models import EvidenceReviewResult, OracleAnswer, OracleRole
from deep20_oracle.protocol import validate_protocol_result
from test_concise_knowledge import POLICY, PROFILE, research, setup_oracle


def unknown_review(basis, indices):
    return json.dumps({
        "answer": "UNKNOWN", "basis": basis, "evidence_indices": indices,
        "supporting_statement": "PRIVATE_UNCERTAINTY: excerpts do not settle the question.",
    })


@pytest.mark.parametrize("basis", ("evidence", "other"))
@pytest.mark.parametrize("final_answer", tuple(OracleAnswer))
def test_unknown_context_reaches_blind_judge_without_retry(
    audit_writer, oracle_request, basis, final_answer,
) -> None:
    oracle, primary, reviewer, judge = setup_oracle(
        audit_writer, research(evidence=True),
    )
    reviewer.raw_output = unknown_review(basis, [1])
    judge.raw_output = json.dumps({
        "answer": final_answer.value, "basis": basis, "evidence_indices": [1],
        "supporting_statement": "PRIVATE_JUDGE_DECISION: exact claim remains uncertain.",
    })
    call = oracle.ask(oracle_request)
    assert call.guesser_answer() is final_answer
    assert call.adjudication.disagreement and call.adjudication.judge_invoked
    assert call.adjudication.reviewer.evidence_indices == (1,)
    assert call.adjudication.reviewer.answer is OracleAnswer.UNKNOWN
    assert call.adjudication.judge.answer is final_answer
    assert len(primary.requests) == len(reviewer.requests) == len(judge.requests) == 1
    assert call.metrics.recovery.retried_calls == 0
    for request in reviewer.requests + judge.requests:
        data = json.loads(request.messages[1]["content"].split("\n", 1)[1])
        assert set(data) == {"subject", "current_yes_no_question", "numbered_evidence_excerpts"}
        assert len(data["numbered_evidence_excerpts"]) == 1
        assert "PRIVATE_UNCERTAINTY" not in json.dumps(request.messages)
        assert "PRIVATE_JUDGE_DECISION" not in json.dumps(request.messages)
        assert "PRIVATE_ORACLE_SUPPORT" not in json.dumps(request.messages)
        assert request.max_web_search_requests is None
    assert EvidenceReviewResult.model_validate_json(
        call.adjudication.reviewer.model_dump_json()
    ) == call.adjudication.reviewer


@pytest.mark.parametrize("indices", ([0], [2], [1, 1]))
@pytest.mark.parametrize("role", (OracleRole.REVIEWER, OracleRole.JUDGE))
def test_unknown_context_still_rejects_invalid_references(
    audit_writer, oracle_request, indices, role,
) -> None:
    oracle, _, reviewer, judge = setup_oracle(
        audit_writer, research(evidence=True), reviewer_answer="NO",
    )
    invalid = reviewer if role is OracleRole.REVIEWER else judge
    invalid.raw_output = unknown_review("other", indices)
    with pytest.raises(OracleProtocolError) as caught:
        oracle.ask(oracle_request)
    assert caught.value.code == "invalid_structured_output"
    assert len(invalid.requests) == 2
    if role is OracleRole.REVIEWER:
        assert not judge.requests


@pytest.mark.parametrize("profile,policy", (
    (PromptProfile.STANDARD, AdjudicationPolicy.PROFILE_DEFAULT),
    (PromptProfile.CONCISE_V1, AdjudicationPolicy.PROFILE_DEFAULT),
    (PROFILE, AdjudicationPolicy.PROFILE_DEFAULT),
    (PROFILE, AdjudicationPolicy.JUDGE_STABLE_KNOWLEDGE_V1),
))
@pytest.mark.parametrize("with_statement", (False, True))
def test_legacy_policies_still_reject_unknown_context(profile, policy, with_statement) -> None:
    payload = json.loads(unknown_review("evidence", [1]))
    if not with_statement:
        payload.pop("supporting_statement")
    with pytest.raises(ValueError):
        result = EvidenceReviewResult.model_validate(payload)
        validate_protocol_result(result, profile, policy=policy, role=OracleRole.JUDGE)


@pytest.mark.parametrize("basis", ("evidence", "other"))
def test_unknown_context_keeps_the_original_token_and_audit_fields(basis) -> None:
    result = EvidenceReviewResult.model_validate_json(unknown_review(basis, [1]))
    validate_protocol_result(result, PROFILE, policy=POLICY, role=OracleRole.REVIEWER)
    assert result.answer is OracleAnswer.UNKNOWN
    assert result.basis.value == basis
    assert result.evidence_indices == (1,)
