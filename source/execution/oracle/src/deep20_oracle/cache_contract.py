"""Fingerprint the complete factual-answer contract without changing provider requests."""

from pydantic import HttpUrl

from .config import AdjudicationPolicy, OracleConfig
from .models import (
    Evidence,
    EvidenceReviewRequest,
    EvidenceReviewResult,
    OracleRequest,
    OracleResearchAttemptResult,
    OracleResearchStrategy,
    OracleRole,
    Subject,
)
from .prompt import (
    evidence_review_prompt_version,
    render_evidence_review_messages,
    render_messages,
    research_prompt_version,
)
from .protocol import answer_output_schema
from .request_variation import QUESTION_ID_VERSION, QuestionMetadata
from .util import canonical_json, sha256_text

# Includes service behavior and the versioned Oracle/Reviewer question-ID policy.
ORACLE_FACTUAL_CONTRACT_VERSION = "oracle-factual-answer-v4-bounded-format-retry"


def oracle_contract_hash(config: OracleConfig) -> str:
    subject = Subject(
        target_id="T-0000",
        canonical_name="Contract fixture",
        entity_type="thing",
        description="Fixed contract fixture, never sent to a provider.",
    )
    request = OracleRequest(
        run_id="contract-fixture", subject=subject, question="Contract fixture?"
    )
    review = EvidenceReviewRequest(
        subject=subject,
        question=request.question,
        evidence=(
            Evidence(
                source_url=HttpUrl("https://example.test/contract"),
                excerpt="Contract fixture.",
                validation="model_reported",
            ),
        ),
    )
    profile = config.prompt_profile
    policy = config.adjudication_policy
    payload = {
        "contract": ORACLE_FACTUAL_CONTRACT_VERSION,
        **({"search_budget": {
            "requested": config.research_query_target, "maximum": config.research_search_limit,
            "no_result_recovery": "known-usage-remaining-allowance-v1",
            "missing_search_recovery": "explicit-zero-bounded-format-retry-v1",
        }}
           if policy is AdjudicationPolicy.CONCISE_KNOWLEDGE_V1 else {}),
        "question_metadata": {
            "version": QUESTION_ID_VERSION,
            "roles": [OracleRole.ORACLE.value, OracleRole.REVIEWER.value],
            "message": QuestionMetadata(question_id="00000000").message(),
            "schema": QuestionMetadata.model_json_schema(),
        },
        "configuration": config.model_dump(mode="json"),
        "research": [
            {
                "version": research_prompt_version(strategy, profile, policy=policy),
                "messages": render_messages(
                    request, strategy=strategy, profile=profile, policy=policy,
                    research_query_target=config.research_query_target,
                ),
                "schema": answer_output_schema(
                    OracleResearchAttemptResult, profile, policy=policy,
                    research_query_target=config.research_query_target,
                ),
            }
            for strategy in OracleResearchStrategy
            if policy is not AdjudicationPolicy.CONCISE_KNOWLEDGE_V1
            or strategy is OracleResearchStrategy.PRIMARY
        ],
        "review": [
            {
                "version": evidence_review_prompt_version(role, profile, policy=policy),
                "messages": render_evidence_review_messages(
                    review, role=role, profile=profile, policy=policy
                ),
                "schema": answer_output_schema(
                    EvidenceReviewResult, profile, role=role, policy=policy
                ),
            }
            for role in (OracleRole.REVIEWER, OracleRole.JUDGE)
        ],
    }
    return sha256_text(canonical_json(payload))
