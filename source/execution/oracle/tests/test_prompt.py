from __future__ import annotations

import json

import pytest
from deep20_oracle.config import AdjudicationPolicy, PromptProfile
from deep20_oracle.knowledge_prompts import FACTUAL_POLICY as KNOWLEDGE_POLICY
from deep20_oracle.models import (
    Evidence,
    EvidenceReviewRequest,
    OracleRequest,
    OracleResearchStrategy,
    OracleRole,
    Subject,
)
from deep20_oracle.prompt import (
    JUDGE_PROMPT_VERSION,
    PROMPT_VERSION,
    RECOVERY_PROMPT_VERSION,
    REVIEWER_PROMPT_VERSION,
    render_evidence_review_messages,
    render_messages,
)
from deep20_oracle.qualified_prompts import FACTUAL_POLICY


@pytest.mark.parametrize("adjudication_policy", tuple(AdjudicationPolicy))
@pytest.mark.parametrize("excerpt", (
    "PRIVATE_EVIDENCE_EXCERPT",
    "PRIVATE_EVIDENCE_EXCERPT " + "Relevant surrounding source context. " * 50,
))
@pytest.mark.parametrize(
    ("entity_type", "canonical_name", "description"),
    [
        ("person", "Albert Einstein", "The physicist known for relativity."),
        ("object", "Hairbrush", "A brush used to groom hair."),
        ("object", "Computer keyboard", "A physical keyboard for entering computer input."),
    ],
)
def test_generic_factual_roles_share_policy_and_keep_subject_data_private(
    entity_type: str, canonical_name: str, description: str,
    adjudication_policy: AdjudicationPolicy,
    excerpt: str,
) -> None:
    subject = Subject(
        target_id="T-9999",
        canonical_name=canonical_name,
        entity_type=entity_type,
        description=description,
        aliases=("PRIVATE_ALIAS",),
    )
    question = "Is it widely known?"
    evidence = Evidence(
        source_url="https://example.test/private-source",
        excerpt=excerpt,
        validation="model_reported",
    )
    expected_subject = subject.model_dump(mode="json")
    expected_research = {"subject": expected_subject, "current_yes_no_question": question}
    concise_knowledge = adjudication_policy is AdjudicationPolicy.CONCISE_KNOWLEDGE_V1
    factual_policy = KNOWLEDGE_POLICY if concise_knowledge else FACTUAL_POLICY
    for strategy in OracleResearchStrategy:
        if concise_knowledge and strategy is not OracleResearchStrategy.PRIMARY:
            continue
        messages = render_messages(
            OracleRequest(run_id="PRIVATE_RUN_ID", subject=subject, question=question),
            strategy=strategy,
            profile=PromptProfile.QUALIFIED_V1,
            policy=adjudication_policy,
        )
        assert factual_policy in messages[0]["content"]
        assert canonical_name not in messages[0]["content"]
        assert "PRIVATE_ALIAS" not in messages[0]["content"]
        assert json.loads(messages[1]["content"].split("\n", 1)[1]) == expected_research

    for role in (OracleRole.REVIEWER, OracleRole.JUDGE):
        messages = render_evidence_review_messages(
            EvidenceReviewRequest(subject=subject, question=question, evidence=(evidence,)),
            role=role,
            profile=PromptProfile.QUALIFIED_V1,
            policy=adjudication_policy,
        )
        assert factual_policy in messages[0]["content"]
        assert canonical_name not in messages[0]["content"]
        assert "PRIVATE_EVIDENCE_EXCERPT" not in messages[0]["content"]
        assert json.loads(messages[1]["content"].split("\n", 1)[1]) == {
            **expected_research,
            "numbered_evidence_excerpts": [{"number": 1, "excerpt": evidence.excerpt}],
        }


def test_oracle_prompt_uses_provider_default_source_ranking(subject) -> None:
    messages = render_messages(
        OracleRequest(
            run_id="prompt-test",
            subject=subject,
            question="Was this person born before 1900?",
        )
    )

    policy = " ".join(messages[0]["content"].split())
    assert PROMPT_VERSION == "live-web-oracle-v8-classified-research"
    assert "normal relevance ranking" in policy
    assert "silently verify polarity" in policy
    assert "an authoritative death date directly supports NO" in policy
    assert "documented professional or recognized biographical role" in policy
    assert (
        "Failure to find another example or counterexample is not evidence for an answer "
        "that asserts absence, exclusivity, or completeness" in policy
    )
    assert "that wire answer may be YES or NO" in policy
    assert "One positive instance does not establish that it is the only instance" in policy
    assert "an exact count, or an explicitly complete enumeration" in policy
    assert "a description of one role does not exclude another" in policy
    assert '"no other evidence was found" as an evidence item' in policy
    assert "Classify the research outcome exactly" in policy
    assert "attempted_queries" in policy
    assert "report the exact concise queries you submitted" in policy
    assert "wikipedia" not in policy.casefold()
    assert "prefer" not in policy.casefold()


def test_recovery_prompt_diversifies_without_prior_research_content(subject) -> None:
    marker = "PRIVATE_PREVIOUS_QUERY"
    request = OracleRequest(
        run_id="prompt-test",
        subject=subject,
        question="Is this person currently alive?",
    )

    messages = render_messages(
        request,
        strategy=OracleResearchStrategy.DIVERSIFIED_RECOVERY,
    )
    policy = " ".join(messages[0]["content"].split())

    assert RECOVERY_PROMPT_VERSION == "live-web-oracle-recovery-v1-diversified"
    assert "previous independent research attempt did not establish a usable answer" in policy
    assert "deliberately diversify the search direction" in policy
    assert "death date, obituary, institutional biography" in policy
    assert "do not turn failure to find an instance into NO" in policy
    assert marker not in json.dumps(messages)
    payload = json.loads(messages[1]["content"].split("\n", 1)[1])
    assert set(payload) == {"subject", "current_yes_no_question"}


def test_reviewer_and_judge_have_bounded_labelled_memory_fallback(
    subject,
) -> None:
    request = EvidenceReviewRequest(
        subject=subject,
        question="Did the person win prizes in more than one category?",
        evidence=(
            Evidence(
                source_url="https://example.test/one-prize",
                excerpt="The person won a prize in physics.",
                validation="model_reported",
            ),
        ),
    )

    reviewer_messages = render_evidence_review_messages(
        request,
        role=OracleRole.REVIEWER,
    )
    judge_messages = render_evidence_review_messages(
        request,
        role=OracleRole.JUDGE,
    )

    assert REVIEWER_PROMPT_VERSION == "oracle-evidence-reviewer-v4-explicit-wire-format"
    assert JUDGE_PROMPT_VERSION == "oracle-evidence-judge-v5-explicit-wire-format"
    for messages in (reviewer_messages, judge_messages):
        policy = " ".join(messages[0]["content"].split())
        assert "require direct support for the selected answer" in policy
        assert "that wire answer may be YES or NO" in policy
        assert (
            "Failure to supply another example or counterexample is not evidence for such an answer"
            in policy
        )
        assert "One positive instance does not establish that it is the only instance" in policy
        assert "a description of one role does not exclude another" in policy
        assert "Use an evidence-first decision process" in policy
        assert 'basis to "evidence"' in policy
        assert "Authoritative counter-attribution counts as evidence" in policy
        assert 'basis to "model_knowledge"' in policy
        assert "stable, widely established" in policy
        assert "sole authorship, birthplace, creator" in policy
        assert "affiliations, citizenships, awards, visits" in policy
        assert "Did Albert Schweitzer write Being and Time?" in policy
        assert "exactly these three keys and no others" in policy
        assert '"answer": "YES", "NO", or "UNKNOWN"' in policy
        assert '"basis": "evidence" or "model_knowledge"' in policy
        assert '"evidence_indices"' in policy
        assert 'Never return "decision", "evidence_numbers", "reasoning"' in policy

        payload = json.loads(messages[1]["content"].split("\n", 1)[1])
        assert set(payload) == {
            "subject",
            "current_yes_no_question",
            "numbered_evidence_excerpts",
        }
        assert payload["numbered_evidence_excerpts"] == [
            {
                "number": 1,
                "excerpt": "The person won a prize in physics.",
            }
        ]
        assert "https://example.test/one-prize" not in messages[1]["content"]
        assert "oracle_answer" not in messages[1]["content"]
        assert "reviewer" not in messages[1]["content"].casefold()

    reviewer_policy = " ".join(reviewer_messages[0]["content"].split())
    assert "agreement between you and the Oracle bypasses the Judge" in reviewer_policy
    assert "use this fallback conservatively" in reviewer_policy
    assert "Return UNKNOWN" in reviewer_policy
    assert "whenever you are uncertain" in reviewer_policy

    judge_policy = " ".join(judge_messages[0]["content"].split())
    assert "stable, widely established fact with a closed, specific relation" in judge_policy
    assert "Do not use it for current or recent facts" in judge_policy
    assert "complete lists, exact totals" in judge_policy
    assert "Did Albert Schweitzer write Being and Time?" in judge_policy
    assert "does not turn failure to find evidence into general evidence of absence" in judge_policy
