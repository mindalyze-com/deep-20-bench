from __future__ import annotations

import json

import pytest
from deep20_oracle.audit import RunAuditWriter
from deep20_oracle.config import AdjudicationPolicy, OracleConfig, PromptProfile
from deep20_oracle.errors import OracleProtocolError
from deep20_oracle.models import (
    EvidenceDecisionBasis,
    EvidenceReviewRequest,
    EvidenceReviewResult,
    OracleAnswer,
    OracleDecisionPath,
    OracleRequest,
    OracleRole,
)
from deep20_oracle.prompt import evidence_review_prompt_version, render_evidence_review_messages
from deep20_oracle.protocol import answer_output_schema, validate_protocol_result
from deep20_oracle.qualified_prompts import JUDGE_KNOWLEDGE_PROMPT_VERSION
from pydantic import ValidationError
from test_quality_control import decoded_review_payload, oracle_payload

from conftest import FakeProvider, make_oracle, review_payload

PROFILE = PromptProfile.QUALIFIED_V1
POLICY = AdjudicationPolicy.JUDGE_STABLE_KNOWLEDGE_V1


@pytest.mark.parametrize("profile", tuple(PromptProfile))
def test_historical_configuration_serialization_keeps_original_policy(
    config: OracleConfig, profile: PromptProfile,
) -> None:
    payload = config.model_dump(mode="json")
    payload["prompt_profile"] = profile.value
    original = OracleConfig.model_validate(payload)
    assert original.adjudication_policy is AdjudicationPolicy.PROFILE_DEFAULT
    assert "adjudication_policy" not in original.model_dump(mode="json")
    payload["adjudication_policy"] = POLICY.value
    if profile is PROFILE:
        revised = OracleConfig.model_validate(payload)
        assert revised.model_dump(mode="json")["adjudication_policy"] == POLICY.value
        assert OracleConfig.model_validate_json(revised.model_dump_json()) == revised
    else:
        with pytest.raises(ValidationError, match="require.*qualified_v1"):
            OracleConfig.model_validate(payload)


@pytest.mark.parametrize("role", (OracleRole.REVIEWER, OracleRole.JUDGE, None))
@pytest.mark.parametrize("policy", (AdjudicationPolicy.PROFILE_DEFAULT, POLICY))
@pytest.mark.parametrize("answer", (OracleAnswer.YES, OracleAnswer.NO,
                                    OracleAnswer.RATHER_YES, OracleAnswer.RATHER_NO))
def test_only_revised_judge_can_return_directional_knowledge_decisions(
    role: OracleRole | None, policy: AdjudicationPolicy, answer: OracleAnswer,
) -> None:
    result = EvidenceReviewResult(answer=answer, basis=EvidenceDecisionBasis.MODEL_KNOWLEDGE)
    schema = answer_output_schema(EvidenceReviewResult, PROFILE, role=role, policy=policy)
    knowledge_allowed = role is OracleRole.JUDGE and policy is POLICY
    expected = ["evidence", "model_knowledge"] if knowledge_allowed else ["evidence"]
    definitions = schema["$defs"]
    assert isinstance(definitions, dict)
    basis = definitions["EvidenceDecisionBasis"]
    assert isinstance(basis, dict)
    assert basis["enum"] == expected
    if knowledge_allowed:
        validate_protocol_result(result, PROFILE, role=role, policy=policy)
    else:
        with pytest.raises(ValueError):
            validate_protocol_result(result, PROFILE, role=role, policy=policy)


@pytest.mark.parametrize("answer", tuple(OracleAnswer))
def test_evidence_decisions_keep_all_five_answers(answer: OracleAnswer) -> None:
    result = EvidenceReviewResult(
        answer=answer, basis=EvidenceDecisionBasis.EVIDENCE,
        evidence_indices=() if answer is OracleAnswer.UNKNOWN else (1,),
    )
    for role in (OracleRole.REVIEWER, OracleRole.JUDGE):
        validate_protocol_result(result, PROFILE, role=role, policy=POLICY)


@pytest.mark.parametrize("answer", (OracleAnswer.YES, OracleAnswer.NO,
                                    OracleAnswer.RATHER_YES, OracleAnswer.RATHER_NO))
def test_revised_judge_fallback_is_audited_and_keeps_blind_requests(
    oracle_request: OracleRequest, audit_writer: RunAuditWriter, answer: OracleAnswer,
) -> None:
    audit_writer.config = audit_writer.config.model_copy(update={
        "prompt_profile": PROFILE, "adjudication_policy": POLICY,
    })
    oracle = FakeProvider(oracle_payload(OracleAnswer.RATHER_YES))
    reviewer = FakeProvider(review_payload(OracleAnswer.UNKNOWN), search_count=0,
                            model=audit_writer.config.reviewer.model)
    judge = FakeProvider(json.dumps({"answer": answer.value, "basis": "model_knowledge",
                                    "evidence_indices": []}), search_count=0,
                         model=audit_writer.config.judge.model)
    call = make_oracle(oracle, audit_writer, audit_writer.config,
                       reviewer_provider=reviewer, judge_provider=judge).ask(oracle_request)
    assert call.guesser_answer() is answer
    assert call.adjudication.decision_path is OracleDecisionPath.JUDGE_DISAGREEMENT
    assert call.adjudication.judge == EvidenceReviewResult(
        answer=answer, basis=EvidenceDecisionBasis.MODEL_KNOWLEDGE,
    )
    assert call.audit.judge is not None
    assert call.audit.judge.prompt_version == JUDGE_KNOWLEDGE_PROMPT_VERSION
    assert len(oracle.requests) == len(reviewer.requests) == len(judge.requests) == 1
    factual_input = decoded_review_payload(judge.requests[0])
    assert factual_input == decoded_review_payload(reviewer.requests[0])
    assert set(factual_input) == {"subject", "current_yes_no_question", "numbered_evidence_excerpts"}
    assert judge.requests[0].session_id != reviewer.requests[0].session_id
    assert judge.requests[0].prompt_cache_key != reviewer.requests[0].prompt_cache_key
    request = EvidenceReviewRequest(subject=oracle_request.subject,
                                    question=oracle_request.question, evidence=call.result.evidence)
    baseline = render_evidence_review_messages(request, role=OracleRole.REVIEWER, profile=PROFILE)
    assert reviewer.requests[0].messages[:-1] == baseline
    old_judge = render_evidence_review_messages(request, role=OracleRole.JUDGE, profile=PROFILE)
    assert judge.requests[0].messages[1] == old_judge[1]
    assert judge.requests[0].messages[0] != old_judge[0]
    assert evidence_review_prompt_version(OracleRole.JUDGE, PROFILE) != JUDGE_KNOWLEDGE_PROMPT_VERSION


@pytest.mark.parametrize(("policy", "answer"), (
    (AdjudicationPolicy.PROFILE_DEFAULT, OracleAnswer.YES),
    (AdjudicationPolicy.PROFILE_DEFAULT, OracleAnswer.RATHER_YES),
    (AdjudicationPolicy.PROFILE_DEFAULT, OracleAnswer.RATHER_NO),
    (POLICY, OracleAnswer.UNKNOWN),
))
def test_invalid_judge_knowledge_remains_infrastructure_failure(
    oracle_request: OracleRequest, audit_writer: RunAuditWriter,
    policy: AdjudicationPolicy, answer: OracleAnswer,
) -> None:
    audit_writer.config = audit_writer.config.model_copy(update={
        "prompt_profile": PROFILE, "adjudication_policy": policy,
    })
    reviewer = FakeProvider(review_payload(OracleAnswer.UNKNOWN), search_count=0,
                            model=audit_writer.config.reviewer.model)
    judge = FakeProvider(json.dumps({"answer": answer.value, "basis": "model_knowledge",
                                    "evidence_indices": []}), search_count=0,
                         model=audit_writer.config.judge.model)
    with pytest.raises(OracleProtocolError, match="schema"):
        make_oracle(FakeProvider(oracle_payload(OracleAnswer.YES)), audit_writer, audit_writer.config,
                    reviewer_provider=reviewer, judge_provider=judge).ask(oracle_request)
    assert len(judge.requests) == 2
    assert judge.requests[0] == judge.requests[1]


@pytest.mark.parametrize("oracle_answer", (OracleAnswer.UNKNOWN, OracleAnswer.YES))
def test_new_policy_does_not_add_calls_after_unknown_or_agreement(
    oracle_request: OracleRequest, audit_writer: RunAuditWriter, oracle_answer: OracleAnswer,
) -> None:
    audit_writer.config = audit_writer.config.model_copy(update={
        "prompt_profile": PROFILE, "adjudication_policy": POLICY,
    })
    reviewer = FakeProvider(review_payload(OracleAnswer.YES), search_count=0,
                            model=audit_writer.config.reviewer.model)
    judge = FakeProvider(review_payload(OracleAnswer.NO), search_count=0,
                         model=audit_writer.config.judge.model)
    call = make_oracle(FakeProvider(oracle_payload(oracle_answer)), audit_writer, audit_writer.config,
                       reviewer_provider=reviewer, judge_provider=judge).ask(oracle_request)
    assert call.guesser_answer() is oracle_answer
    assert len(reviewer.requests) == (0 if oracle_answer is OracleAnswer.UNKNOWN else 1)
    assert not judge.requests
