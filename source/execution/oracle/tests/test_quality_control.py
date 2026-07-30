from __future__ import annotations

import json

import pytest
from conftest import FakeProvider, make_oracle, provider_trace, review_payload
from deep20_oracle.audit import RunAuditWriter
from deep20_oracle.errors import OracleProviderError
from deep20_oracle.models import (
    EvidenceDecisionBasis,
    OracleAnswer,
    OracleDecisionPath,
    OracleQuestionType,
    OracleRequest,
)
from deep20_oracle.provider import ProviderRequest
from deep20_oracle.question_type import classify_oracle_question


def oracle_payload(answer: OracleAnswer, excerpt: str = "The supported fact.") -> str:
    return json.dumps(
        {
            "answer": answer,
            "evidence": (
                []
                if answer is OracleAnswer.UNKNOWN
                else [
                    {
                        "source_url": "https://example.test/source",
                        "excerpt": excerpt,
                        "validation": "model_reported",
                    }
                ]
            ),
        }
    )


def decoded_review_payload(request: ProviderRequest) -> dict[str, object]:
    return json.loads(request.messages[1]["content"].split("\n", 1)[1])


def test_agreement_returns_shared_answer_without_calling_judge(
    oracle_request: OracleRequest,
    audit_writer: RunAuditWriter,
) -> None:
    oracle_provider = FakeProvider(oracle_payload(OracleAnswer.YES))
    reviewer_provider = FakeProvider(
        review_payload(OracleAnswer.YES),
        search_count=0,
        model=audit_writer.config.reviewer.model,
    )
    judge_provider = FakeProvider(
        review_payload(OracleAnswer.NO),
        search_count=0,
        model=audit_writer.config.judge.model,
    )

    call = make_oracle(
        oracle_provider,
        audit_writer,
        audit_writer.config,
        reviewer_provider=reviewer_provider,
        judge_provider=judge_provider,
    ).ask(oracle_request)

    assert call.guesser_answer() is OracleAnswer.YES
    assert call.adjudication.decision_path is OracleDecisionPath.REVIEWER_AGREEMENT
    assert call.adjudication.disagreement is False
    assert call.adjudication.judge_invoked is False
    assert len(oracle_provider.requests) == 1
    assert len(reviewer_provider.requests) == 1
    assert judge_provider.requests == []
    assert call.metrics.oracle is not None
    assert call.metrics.reviewer is not None
    assert call.metrics.judge is None


def test_einstein_date_polarity_disagreement_still_uses_judge_final_answer(
    oracle_request: OracleRequest,
    audit_writer: RunAuditWriter,
) -> None:
    request = oracle_request.model_copy(
        update={"question": "Was this person born before the year 1800?"}
    )
    oracle_provider = FakeProvider(
        oracle_payload(
            OracleAnswer.YES,
            "Albert Einstein was born 14 March 1879.",
        )
    )
    reviewer_provider = FakeProvider(
        review_payload(OracleAnswer.NO),
        search_count=0,
        model=audit_writer.config.reviewer.model,
    )
    judge_provider = FakeProvider(
        review_payload(OracleAnswer.NO),
        search_count=0,
        model=audit_writer.config.judge.model,
    )

    call = make_oracle(
        oracle_provider,
        audit_writer,
        audit_writer.config,
        reviewer_provider=reviewer_provider,
        judge_provider=judge_provider,
    ).ask(request)

    assert call.result.answer is OracleAnswer.YES
    assert call.adjudication.reviewer is not None
    assert call.adjudication.reviewer.answer is OracleAnswer.NO
    assert call.adjudication.judge is not None
    assert call.adjudication.judge.answer is OracleAnswer.NO
    assert call.adjudication.decision_path is OracleDecisionPath.JUDGE_DISAGREEMENT
    assert (
        call.adjudication.question_type
        is OracleQuestionType.TEMPORAL_COMPARISON
    )
    assert call.adjudication.oracle_answer_changed is True
    assert call.guesser_answer() is OracleAnswer.NO
    assert call.metrics.judge is not None


def test_judge_can_label_stable_closed_fact_as_model_knowledge(
    oracle_request: OracleRequest,
    audit_writer: RunAuditWriter,
) -> None:
    schweitzer = oracle_request.subject.model_copy(
        update={
            "target_id": "T-0002",
            "canonical_name": "Albert Schweitzer",
            "aliases": ("Schweitzer",),
            "description": "The physician and philosopher identified by Wikidata Q49325.",
        }
    )
    request = oracle_request.model_copy(
        update={
            "subject": schweitzer,
            "question": "Did this person write Being and Time?",
        }
    )
    reviewer_provider = FakeProvider(
        review_payload(OracleAnswer.UNKNOWN),
        search_count=0,
        model=audit_writer.config.reviewer.model,
    )
    judge_provider = FakeProvider(
        json.dumps(
            {
                "answer": "NO",
                "basis": "model_knowledge",
                "evidence_indices": [],
            }
        ),
        search_count=0,
        model=audit_writer.config.judge.model,
    )

    call = make_oracle(
        FakeProvider(
            oracle_payload(
                OracleAnswer.YES,
                "Albert Schweitzer wrote works about ethics and civilization.",
            )
        ),
        audit_writer,
        audit_writer.config,
        reviewer_provider=reviewer_provider,
        judge_provider=judge_provider,
    ).ask(request)

    assert call.adjudication.reviewer is not None
    assert call.adjudication.reviewer.answer is OracleAnswer.UNKNOWN
    assert call.adjudication.judge is not None
    assert (
        call.adjudication.judge.basis
        is EvidenceDecisionBasis.MODEL_KNOWLEDGE
    )
    assert call.adjudication.judge.evidence_indices == ()
    assert call.guesser_answer() is OracleAnswer.NO


def test_reviewer_model_knowledge_agreement_skips_judge(
    oracle_request: OracleRequest,
    audit_writer: RunAuditWriter,
) -> None:
    schweitzer = oracle_request.subject.model_copy(
        update={
            "target_id": "T-0002",
            "canonical_name": "Albert Schweitzer",
            "aliases": ("Schweitzer",),
            "description": "The physician and philosopher identified by Wikidata Q49325.",
        }
    )
    request = oracle_request.model_copy(
        update={
            "subject": schweitzer,
            "question": "Did this person write Being and Time?",
        }
    )
    reviewer_provider = FakeProvider(
        json.dumps(
            {
                "answer": "NO",
                "basis": "model_knowledge",
                "evidence_indices": [],
            }
        ),
        search_count=0,
        model=audit_writer.config.reviewer.model,
    )
    judge_provider = FakeProvider(
        review_payload(OracleAnswer.YES),
        search_count=0,
        model=audit_writer.config.judge.model,
    )

    call = make_oracle(
        FakeProvider(
            oracle_payload(
                OracleAnswer.NO,
                "Albert Schweitzer wrote works about ethics and civilization.",
            )
        ),
        audit_writer,
        audit_writer.config,
        reviewer_provider=reviewer_provider,
        judge_provider=judge_provider,
    ).ask(request)

    assert call.adjudication.reviewer is not None
    assert (
        call.adjudication.reviewer.basis
        is EvidenceDecisionBasis.MODEL_KNOWLEDGE
    )
    assert call.adjudication.reviewer.evidence_indices == ()
    assert call.adjudication.decision_path is OracleDecisionPath.REVIEWER_AGREEMENT
    assert call.adjudication.judge_invoked is False
    assert judge_provider.requests == []
    assert call.guesser_answer() is OracleAnswer.NO


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        (
            "Was this person born before the year 1300?",
            OracleQuestionType.TEMPORAL_COMPARISON,
        ),
        (
            "Did the city have more than 12 million residents?",
            OracleQuestionType.QUANTITATIVE_COMPARISON,
        ),
        (
            "Was the subject never elected to office?",
            OracleQuestionType.NEGATION,
        ),
        ("Was the subject a physician?", OracleQuestionType.OTHER),
    ],
)
def test_question_type_classification_is_deterministic(
    question: str,
    expected: OracleQuestionType,
) -> None:
    assert classify_oracle_question(question) is expected


def test_reviewer_and_judge_are_blind_and_role_isolated(
    oracle_request: OracleRequest,
    audit_writer: RunAuditWriter,
) -> None:
    reviewer_provider = FakeProvider(
        review_payload(OracleAnswer.NO),
        search_count=0,
        model=audit_writer.config.reviewer.model,
    )
    judge_provider = FakeProvider(
        review_payload(OracleAnswer.NO),
        search_count=0,
        model=audit_writer.config.judge.model,
    )
    call = make_oracle(
        FakeProvider(oracle_payload(OracleAnswer.YES, "Born in 1875.")),
        audit_writer,
        audit_writer.config,
        reviewer_provider=reviewer_provider,
        judge_provider=judge_provider,
    ).ask(oracle_request)

    reviewer_request = reviewer_provider.requests[0]
    judge_request = judge_provider.requests[0]
    reviewer_payload = decoded_review_payload(reviewer_request)
    judge_payload = decoded_review_payload(judge_request)
    for payload in (reviewer_payload, judge_payload):
        assert set(payload) == {
            "subject",
            "current_yes_no_question",
            "numbered_evidence_excerpts",
        }
        assert "answer" not in payload
        assert "oracle" not in payload
        assert "reviewer" not in payload
    assert reviewer_payload == judge_payload
    assert reviewer_request.session_id != judge_request.session_id
    assert reviewer_request.prompt_cache_key != judge_request.prompt_cache_key
    assert reviewer_request.session_id is not None
    assert reviewer_request.session_id.startswith("deep20-oracle-reviewer-")
    assert judge_request.session_id is not None
    assert judge_request.session_id.startswith("deep20-oracle-judge-")
    assert "basis" in reviewer_request.output_schema["required"]
    assert "basis" in judge_request.output_schema["required"]
    assert reviewer_request.output_schema["$defs"]["EvidenceDecisionBasis"]["enum"] == [
        "evidence",
        "model_knowledge",
    ]
    assert (
        judge_request.output_schema["$defs"]["EvidenceDecisionBasis"]["enum"]
        == reviewer_request.output_schema["$defs"]["EvidenceDecisionBasis"]["enum"]
    )
    assert call.audit.reviewer is not None
    assert call.audit.judge is not None
    assert call.audit.reviewer.provider.usage.search_count == 0
    assert call.audit.judge.provider.usage.search_count == 0


def test_oracle_unknown_bypasses_both_quality_control_models(
    oracle_request: OracleRequest,
    audit_writer: RunAuditWriter,
) -> None:
    reviewer_provider = FakeProvider(
        review_payload(OracleAnswer.YES),
        search_count=0,
        model=audit_writer.config.reviewer.model,
    )
    judge_provider = FakeProvider(
        review_payload(OracleAnswer.YES),
        search_count=0,
        model=audit_writer.config.judge.model,
    )
    call = make_oracle(
        FakeProvider(oracle_payload(OracleAnswer.UNKNOWN)),
        audit_writer,
        audit_writer.config,
        reviewer_provider=reviewer_provider,
        judge_provider=judge_provider,
    ).ask(oracle_request)

    assert call.guesser_answer() is OracleAnswer.UNKNOWN
    assert call.adjudication.decision_path is OracleDecisionPath.ORACLE_UNKNOWN
    assert reviewer_provider.requests == []
    assert judge_provider.requests == []


@pytest.mark.parametrize(
    ("reviewer_answer", "judge_answer", "expected"),
    [
        (OracleAnswer.UNKNOWN, OracleAnswer.YES, OracleAnswer.YES),
        (OracleAnswer.NO, OracleAnswer.UNKNOWN, OracleAnswer.UNKNOWN),
    ],
)
def test_reviewer_unknown_is_a_disagreement_and_judge_unknown_is_final(
    reviewer_answer: OracleAnswer,
    judge_answer: OracleAnswer,
    expected: OracleAnswer,
    oracle_request: OracleRequest,
    audit_writer: RunAuditWriter,
) -> None:
    call = make_oracle(
        FakeProvider(oracle_payload(OracleAnswer.YES)),
        audit_writer,
        audit_writer.config,
        reviewer_answer=reviewer_answer,
        judge_answer=judge_answer,
    ).ask(oracle_request)

    assert call.adjudication.disagreement is True
    assert call.adjudication.judge_invoked is True
    assert call.guesser_answer() is expected


class FailingQualityProvider:
    def __init__(self, *, model: str):
        self.model = model
        self.requests: list[ProviderRequest] = []

    def complete(self, request: ProviderRequest):
        self.requests.append(request)
        trace = provider_trace(
            raw_output="",
            search_count=0,
            model=self.model,
        )
        raise OracleProviderError(
            "quality-control provider unavailable",
            code="provider_request_failed",
            details={"provider_trace": trace.model_dump(mode="json")},
        )


def test_required_reviewer_failure_does_not_fall_back_to_oracle_answer(
    oracle_request: OracleRequest,
    audit_writer: RunAuditWriter,
) -> None:
    reviewer = FailingQualityProvider(model=audit_writer.config.reviewer.model)
    with pytest.raises(OracleProviderError, match="unavailable"):
        make_oracle(
            FakeProvider(oracle_payload(OracleAnswer.YES)),
            audit_writer,
            audit_writer.config,
            reviewer_provider=reviewer,
        ).ask(oracle_request)

    record = json.loads(
        (
            audit_writer.runs_root
            / oracle_request.run_id
            / "oracle-calls.jsonl"
        ).read_text()
    )
    assert record["status"] == "failure"
    assert record["audit"]["component"] == "reviewer"
    assert [item["role"] for item in record["audit"]["role_traces"]] == [
        "oracle",
        "reviewer",
    ]
    assert record["result"] is None
    assert record["adjudication"] is None


def test_required_judge_failure_does_not_fall_back_to_oracle_answer(
    oracle_request: OracleRequest,
    audit_writer: RunAuditWriter,
) -> None:
    judge = FailingQualityProvider(model=audit_writer.config.judge.model)
    with pytest.raises(OracleProviderError, match="unavailable"):
        make_oracle(
            FakeProvider(oracle_payload(OracleAnswer.YES)),
            audit_writer,
            audit_writer.config,
            reviewer_answer=OracleAnswer.NO,
            judge_provider=judge,
        ).ask(oracle_request)

    record = json.loads(
        (
            audit_writer.runs_root
            / oracle_request.run_id
            / "oracle-calls.jsonl"
        ).read_text()
    )
    assert record["status"] == "failure"
    assert record["audit"]["component"] == "judge"
    assert [item["role"] for item in record["audit"]["role_traces"]] == [
        "oracle",
        "reviewer",
        "judge",
    ]
    assert record["result"] is None
    assert record["adjudication"] is None
