"""Opt-in paired Judge checks with controlled evidence, outside benchmark runs."""
from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest
from deep20_oracle.config import AdjudicationPolicy, PromptProfile, load_oracle_config
from deep20_oracle.credentials import load_openrouter_api_key
from deep20_oracle.models import (
    Evidence,
    EvidenceDecisionBasis,
    EvidenceReviewRequest,
    EvidenceReviewResult,
    OracleAnswer,
    OracleRole,
    ProviderUsage,
    StrictModel,
    Subject,
)
from deep20_oracle.openrouter_provider import OpenRouterProvider
from deep20_oracle.prompt import (
    evidence_review_prompt_version,
    prompt_hash,
    render_evidence_review_messages,
)
from deep20_oracle.protocol import answer_output_schema, validate_protocol_result
from deep20_oracle.provider import ProviderRequest
from deep20_oracle.service import validate_oracle_provider_trace
from deep20_oracle.util import sha256_text
from pydantic import HttpUrl


class JudgeCase(StrictModel):
    case_id: str
    subject_name: str
    subject_description: str
    question: str
    excerpts: tuple[str, ...]
    evidence_answer: OracleAnswer
    knowledge_answer: OracleAnswer
    knowledge_basis: EvidenceDecisionBasis = EvidenceDecisionBasis.EVIDENCE


BOOK = "Frankenstein; or, The Modern Prometheus"
BOOK_DESCRIPTION = "The English-language novel first published in 1818."
CASES = (
    JudgeCase(case_id="missing-author-yes", subject_name=BOOK,
              subject_description=BOOK_DESCRIPTION, question="Was this novel written by Mary Shelley?",
              excerpts=("The novel was first published in 1818.",),
              evidence_answer=OracleAnswer.UNKNOWN, knowledge_answer=OracleAnswer.YES,
              knowledge_basis=EvidenceDecisionBasis.MODEL_KNOWLEDGE),
    JudgeCase(case_id="missing-author-no", subject_name=BOOK,
              subject_description=BOOK_DESCRIPTION, question="Was this novel written by Jane Austen?",
              excerpts=("The novel was first published in 1818.",),
              evidence_answer=OracleAnswer.UNKNOWN, knowledge_answer=OracleAnswer.NO,
              knowledge_basis=EvidenceDecisionBasis.MODEL_KNOWLEDGE),
    JudgeCase(case_id="direct-counterevidence", subject_name=BOOK,
              subject_description=BOOK_DESCRIPTION, question="Was this novel written by Jane Austen?",
              excerpts=("Mary Shelley was the novel's sole author.",),
              evidence_answer=OracleAnswer.NO, knowledge_answer=OracleAnswer.NO),
    JudgeCase(case_id="qualified-evidence-before-memory", subject_name="Copper",
              subject_description="The chemical element Cu, considered as a bulk solid.",
              question="Does it conduct electricity?",
              excerpts=(("The measurements favor electrical conduction, but substantial measurement "
                         "uncertainty prevents the report from establishing it conclusively."),),
              evidence_answer=OracleAnswer.RATHER_YES, knowledge_answer=OracleAnswer.RATHER_YES),
    JudgeCase(case_id="conflict-is-not-a-memory-fallback", subject_name=BOOK,
              subject_description=BOOK_DESCRIPTION, question="Was this novel written by Mary Shelley?",
              excerpts=("Mary Shelley was the novel's sole author.",
                        "Jane Austen was the novel's sole author."),
              evidence_answer=OracleAnswer.UNKNOWN, knowledge_answer=OracleAnswer.UNKNOWN),
    JudgeCase(case_id="exact-count-remains-evidence-only", subject_name="Marie Curie",
              subject_description="The physicist and chemist born Maria Sklodowska in 1867.",
              question="Did she win exactly one Nobel Prize?",
              excerpts=("Marie Curie received the Nobel Prize in Physics in 1903.",),
              evidence_answer=OracleAnswer.UNKNOWN, knowledge_answer=OracleAnswer.UNKNOWN),
    JudgeCase(case_id="open-world-absence", subject_name="Mary Shelley",
              subject_description="The English novelist born Mary Wollstonecraft Godwin in 1797.",
              question="Did she never visit Iceland?",
              excerpts=("She traveled in France and Switzerland.",),
              evidence_answer=OracleAnswer.UNKNOWN, knowledge_answer=OracleAnswer.UNKNOWN),
    JudgeCase(case_id="subjective-claim", subject_name=BOOK,
              subject_description=BOOK_DESCRIPTION, question="Is it the greatest novel ever written?",
              excerpts=("The novel was first published in 1818.",),
              evidence_answer=OracleAnswer.UNKNOWN, knowledge_answer=OracleAnswer.UNKNOWN),
)


class JudgeCheckRecord(StrictModel):
    case: JudgeCase
    evidence_provenance: str = "synthetic controlled excerpts, not fetched source quotations"
    policy: AdjudicationPolicy
    prompt_version: str
    prompt_hash: str
    decision: EvidenceReviewResult
    expected_answer: OracleAnswer
    expected_basis: EvidenceDecisionBasis
    resolved_model: str | None
    resolved_provider: str | None
    latency_ms: int
    usage: ProviderUsage


@pytest.mark.integration
@pytest.mark.parametrize("policy", tuple(AdjudicationPolicy))
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.case_id)
def test_live_judge_evidence_priority_and_bounded_fallback(
    tmp_path: Path, case: JudgeCase, policy: AdjudicationPolicy,
) -> None:
    if os.environ.get("DEEP20_RUN_LIVE_JUDGE") != "1":
        pytest.skip("set DEEP20_RUN_LIVE_JUDGE=1 for 16 paid paired Judge checks")
    repository = Path(__file__).resolve().parents[4]
    configuration = load_oracle_config(repository / "config/oracle.yaml").judge
    profile = PromptProfile.QUALIFIED_V1
    request = EvidenceReviewRequest(
        subject=Subject(target_id="T-9999", canonical_name=case.subject_name, aliases=(),
                        entity_type="thing", description=case.subject_description),
        question=case.question,
        evidence=tuple(Evidence(source_url=HttpUrl(f"https://example.test/judge-audit/{number}"),
                                excerpt=excerpt, validation="model_reported")
                       for number, excerpt in enumerate(case.excerpts, start=1)),
    )
    messages = render_evidence_review_messages(request, role=OracleRole.JUDGE,
                                              profile=profile, policy=policy)
    version = evidence_review_prompt_version(OracleRole.JUDGE, profile, policy=policy)
    with OpenRouterProvider(load_openrouter_api_key(repository), configuration,
                            enable_web_search=False, title="Deep20Bench Judge Policy Audit") as provider:
        exchange = provider.complete(ProviderRequest(
            messages=messages,
            output_schema=answer_output_schema(EvidenceReviewResult, profile,
                                               role=OracleRole.JUDGE, policy=policy),
            response_schema_name="judge_result",
            session_id=f"judge-policy-audit-{uuid4().hex}",
            prompt_cache_key="deep20-judge-audit-" + sha256_text(
                version + request.subject.model_dump_json())[:32],
        ))
    validate_oracle_provider_trace(exchange.trace, config=configuration, role=OracleRole.JUDGE)
    decision = EvidenceReviewResult.model_validate_json(exchange.raw_output)
    validate_protocol_result(decision, profile, role=OracleRole.JUDGE, policy=policy)
    decision.validate_evidence_count(len(request.evidence))
    new_policy = policy is AdjudicationPolicy.JUDGE_STABLE_KNOWLEDGE_V1
    record = JudgeCheckRecord(
        case=case, policy=policy, prompt_version=version, prompt_hash=prompt_hash(messages),
        decision=decision, expected_answer=case.knowledge_answer if new_policy else case.evidence_answer,
        expected_basis=case.knowledge_basis if new_policy else EvidenceDecisionBasis.EVIDENCE,
        resolved_model=exchange.trace.resolved_model, resolved_provider=exchange.trace.resolved_provider,
        latency_ms=exchange.trace.latency_ms, usage=exchange.trace.usage,
    )
    (tmp_path / "result.json").write_text(record.model_dump_json(indent=2) + "\n", encoding="utf-8")
    assert decision.answer is record.expected_answer
    assert decision.basis is record.expected_basis
