from __future__ import annotations

import json

import pytest
from deep20_game.models import EpisodeResult, GameRequest
from deep20_oracle.audit import RunAuditWriter
from deep20_oracle.config import AdjudicationPolicy, PromptProfile
from deep20_oracle.models import OracleAnswer
from deep20_oracle.provider import ProviderExchange
from deep20_oracle.service import Oracle

from .conftest import FakeGameProvider, provider_trace
from .test_engine import ask, guess, make_engine, validation


@pytest.mark.parametrize("scenario", (
    "directional", "oracle_unknown", "reviewer_unknown", "judge_unknown",
))
def test_real_concise_oracle_support_is_saved_but_never_enters_guesser_requests(
    scenario, tmp_path, audit_writer, model_config, validator_config, policy, subject,
) -> None:
    oracle_unknown = scenario == "oracle_unknown"
    unknown = oracle_unknown or scenario == "judge_unknown"
    review_context = scenario in {"reviewer_unknown", "judge_unknown"}
    policy = policy.model_copy(update={"prompt_profile": PromptProfile.QUALIFIED_V1})
    audit_writer.game_policy = policy
    config = audit_writer.oracle_config.model_copy(update={
        "prompt_profile": PromptProfile.QUALIFIED_V1,
        "adjudication_policy": AdjudicationPolicy.CONCISE_KNOWLEDGE_V1,
    })
    audit_writer.oracle_config = config

    class Provider:
        def __init__(self, route, answer, research=False):
            self.requests = []
            self.answer = answer
            self.research = research
            self.route = route

        def complete(self, request):
            self.requests.append(request)
            payload = {"answer": self.answer, "basis": "other",
                       "supporting_statement": "PRIVATE_DECISION_SUPPORT remembered fact or gap."}
            if self.research:
                payload.update(evidence=([{
                    "source_url": "https://example.test/context", "excerpt": "PRIVATE_CONTEXT",
                    "validation": "model_reported",
                }] if review_context else []), attempted_queries=["PRIVATE_SEARCH"],
                    research_outcome=("insufficient_coverage" if oracle_unknown else "answered"))
            else:
                payload["evidence_indices"] = [1] if review_context else []
            output = json.dumps(payload)
            trace = provider_trace(model_config.model_copy(update={
                "model": self.route.model, "provider": self.route.provider,
            }), output)
            trace = trace.model_copy(update={"usage": trace.usage.model_copy(
                update={"search_count": int(self.research)},
            )})
            return ProviderExchange(raw_output=output, trace=trace)

    primary = Provider(config, "UNKNOWN" if oracle_unknown else "YES", research=True)
    reviewer = Provider(config.reviewer, "UNKNOWN" if review_context else "NO")
    judge = Provider(config.judge, "UNKNOWN" if scenario == "judge_unknown" else "RATHER_YES")
    oracle = Oracle(primary, reviewer, judge, RunAuditWriter(
        tmp_path / "oracle", config=config, subject_catalog_hash="a" * 64, repository=tmp_path,
    ), config)
    question = "Was this person born before 1900?"
    guesser = FakeGameProvider(model_config, [ask(question), ask(question),
        guess("Albert Einstein", "The physicist known for relativity.")])
    engine = make_engine(
        guesser_provider=guesser,
        validator_provider=FakeGameProvider(validator_config, [validation("YES")]),
        oracle=oracle, audit_writer=audit_writer, policy=policy,
        model_config=model_config, validator_config=validator_config,
    )
    engine.reuse_episode_answers = True
    result = engine.play(GameRequest(run_id="concise-support", subject=subject))
    assert result.success
    assert EpisodeResult.model_validate_json(result.model_dump_json()) == result
    assert "PRIVATE_DECISION_SUPPORT" in result.model_dump_json()
    # Bounded Oracle UNKNOWN is excluded; a fully adjudicated Judge decision keeps
    # the existing same-episode reuse policy, including a genuine final UNKNOWN.
    assert len(primary.requests) == (2 if oracle_unknown else 1)
    assert result.summary.oracle_cache_hits == (0 if oracle_unknown else 1)
    expected = OracleAnswer.UNKNOWN if unknown else OracleAnswer.RATHER_YES
    assert result.turns[0].adjudication.answer is expected
    if review_context:
        assert len(reviewer.requests) == len(judge.requests) == len(primary.requests)
        assert result.turns[0].adjudication.oracle_quality.reviewer.answer is OracleAnswer.UNKNOWN
        assert result.turns[0].adjudication.oracle_quality.reviewer.evidence_indices == (1,)
    for request in guesser.requests:
        visible = json.dumps(request.messages)
        assert "PRIVATE_DECISION_SUPPORT" not in visible
        assert "PRIVATE_SEARCH" not in visible
        assert "PRIVATE_CONTEXT" not in visible
        assert "supporting_statement" not in visible
        assert "concise_knowledge_v1" not in visible
    assert guesser.requests[1].messages[-1] == {"role": "user", "content": expected.value}
    for request in reviewer.requests + judge.requests:
        assert "PRIVATE_DECISION_SUPPORT" not in json.dumps(request.messages)
