from __future__ import annotations

import json
from dataclasses import dataclass, field

import pytest
import yaml
from deep20_game.models import EpisodeOracleCacheSource, EpisodeResult, OracleResultCallAudit
from deep20_oracle.models import (
    EvidenceReviewAuditTrace,
    OracleAnswer,
    OracleAuditTrace,
    OracleCall,
    OracleRequest,
    OracleResearchAttemptAuditTrace,
    OracleResearchAttemptResult,
    OracleResearchAuditTrace,
    OracleResearchOutcome,
    OracleResearchQuestionClass,
    OracleResearchResolution,
    OracleResearchStrategy,
    OracleResult,
    OracleRole,
)

from .conftest import FakeGameProvider, provider_trace
from .test_engine import FakeOracle, GameRequest, ask, guess, make_engine, validation


class AuditedOracle(FakeOracle):
    def __init__(self, answers, model_config, *, retrieval_failure=False):
        super().__init__(answers)
        self.model_config = model_config
        self.retrieval_failure = retrieval_failure

    def ask(self, request: OracleRequest) -> OracleCall:
        fresh = super().ask(request)
        answer = fresh.guesser_answer()
        trace = provider_trace(self.model_config, "PRIVATE_ORACLE_RESPONSE")
        unknown = answer is OracleAnswer.UNKNOWN
        resolution = (OracleResearchResolution.RETRIEVAL_EXHAUSTED_UNKNOWN
            if self.retrieval_failure else OracleResearchResolution.GENUINE_UNKNOWN_PRIMARY
            if unknown else OracleResearchResolution.ANSWERED_PRIMARY)
        outcome = (OracleResearchOutcome.NO_RESULTS if self.retrieval_failure
            else OracleResearchOutcome.AMBIGUOUS_QUESTION if unknown
            else OracleResearchOutcome.ANSWERED)
        attempt = OracleResearchAttemptAuditTrace(
            attempt_number=1, strategy=OracleResearchStrategy.PRIMARY,
            prompt_version="test-oracle", prompt_hash="a" * 64,
            messages=({"role": "system", "content": "PRIVATE_PROMPT"},),
            result=OracleResearchAttemptResult(answer=answer, evidence=fresh.result.evidence,
                research_outcome=outcome, attempted_queries=("private query",)),
            provider=trace,
        )
        attempts = (attempt,)
        if self.retrieval_failure:
            attempts += (attempt.model_copy(update={"attempt_number": 2,
                "strategy": OracleResearchStrategy.DIVERSIFIED_RECOVERY}),)
        return OracleCall(
            call_id=fresh.call_id, request=request,
            result=OracleResult(answer=answer, evidence=fresh.result.evidence),
            adjudication=fresh.adjudication, metrics=fresh.metrics,
            audit=OracleAuditTrace(prompt_version="test-oracle", prompt_hash="a" * 64,
                messages=attempt.messages, evidence_validation="model_reported", provider=trace,
                research=OracleResearchAuditTrace(
                    question_class=OracleResearchQuestionClass.TEMPORAL_STATUS,
                    resolution=resolution, attempts=attempts),
                reviewer=None if unknown else EvidenceReviewAuditTrace(
                    role=OracleRole.REVIEWER, prompt_version="test-reviewer", prompt_hash="b" * 64,
                    messages=attempt.messages, provider=trace)),
            recorded_at="2026-09-07T00:00:00+00:00", integrity_hash="c" * 64,
        )


@dataclass
class Observer:
    events: list = field(default_factory=list)

    def observe(self, event):
        self.events.append(event)


@pytest.mark.parametrize("answer", [OracleAnswer.YES, OracleAnswer.NO, OracleAnswer.UNKNOWN])
def test_live_repeats_keep_question_cost_provenance_and_isolation(
    answer, audit_writer, model_config, validator_config, policy, subject,
):
    policy = policy.model_copy(update={"max_questions": 3})
    audit_writer.game_policy = policy
    actions = [ask("Was this person born before 1900?"),
               ask("WAS  this person born before 1900?"),
               ask("Was this person born before 1900?!"),
               guess("Albert Einstein", "The physicist associated with relativity.")]
    results = []
    providers = []
    for enabled in (True, False):
        oracle = AuditedOracle([answer] * (2 if enabled else 3), model_config)
        provider = FakeGameProvider(model_config, actions.copy())
        observer = Observer()
        engine = make_engine(guesser_provider=provider,
            validator_provider=FakeGameProvider(validator_config, [validation("YES")]),
            oracle=oracle, audit_writer=audit_writer, policy=policy,
            model_config=model_config, validator_config=validator_config)
        engine.reuse_episode_answers = enabled
        engine.observer = observer
        result = engine.play(GameRequest(run_id=f"repeat-{enabled}", subject=subject))
        assert result.success and result.summary.counted_questions == 3
        assert result.summary.ask_count == 3 and result.summary.total_turns == 4
        assert len(oracle.requests) == (2 if enabled else 3)
        assert result.summary.oracle_cache_hits == int(enabled)
        assert EpisodeResult.model_validate_json(result.model_dump_json()) == result
        results.append(result)
        providers.append(provider)
        if enabled:
            original, repeated, distinct = result.turns[:3]
            source = repeated.adjudication.cache_source
            assert isinstance(source, EpisodeOracleCacheSource)
            assert source.episode_id == result.episode_id and source.run_id == result.run_id
            assert source.turn_number == 1 and source.oracle_call_id == original.adjudication.call_id
            assert source.question == original.action.question
            assert original.adjudication.cache_source is None
            assert distinct.adjudication.cache_source is None
            assert repeated.adjudication.evidence == original.adjudication.evidence
            assert repeated.adjudication.oracle_quality == original.adjudication.oracle_quality
            audits = [call for call in result.audit.calls if isinstance(call, OracleResultCallAudit)]
            assert audits[1].oracle == audits[0].oracle and audits[1].reviewer == audits[0].reviewer
            stored = yaml.safe_load((audit_writer.runs_root / result.run_id / "result.yml").read_text())
            assert stored["turns"][1]["adjudication"]["cache_source"]["policy"] == "same_episode_ask_v1"
            assert "source_file" not in source.model_dump()  # No file exists at lookup time.
            for field_name, bad in (("episode_id", "EP-" + "0" * 32), ("turn_number", 2),
                                    ("question", "A different question?")):
                value = result.model_dump(mode="json")
                value["turns"][1]["adjudication"]["cache_source"][field_name] = bad
                value["audit"]["calls"][3]["cache_source"][field_name] = bad
                with pytest.raises(ValueError, match="same-episode cache"):
                    EpisodeResult.model_validate_json(json.dumps(value))
            # Reusing the engine for another episode starts with empty memory.
            oracle.answers = [answer]
            engine.guesser.provider = FakeGameProvider(model_config, [actions[0], actions[-1]])
            engine.validator.provider = FakeGameProvider(validator_config, [validation("YES")])
            next_result = engine.play(GameRequest(run_id="next-game", subject=subject))
            assert next_result.success and next_result.summary.oracle_cache_hits == 0
            assert len(oracle.requests) == 3
    cached, fresh = results
    assert cached.costs_usd.oracle * 3 == fresh.costs_usd.oracle * 2
    assert cached.llm.oracle.metrics.calls * 3 == fresh.llm.oracle.metrics.calls * 2
    assert cached.llm.oracle.metrics.total_tokens * 3 == fresh.llm.oracle.metrics.total_tokens * 2
    assert [request.messages for request in providers[0].requests] == [
        request.messages for request in providers[1].requests]
    visible = json.dumps([request.messages for request in providers[0].requests])
    for marker in ("PRIVATE_", "cache_source", "same_episode", "private query", cached.episode_id):
        assert marker not in visible


def test_failed_retrieval_is_not_remembered(audit_writer, model_config, validator_config, policy, subject):
    oracle = AuditedOracle([OracleAnswer.UNKNOWN] * 2, model_config, retrieval_failure=True)
    engine = make_engine(guesser_provider=FakeGameProvider(model_config,
        [ask("Is it alive?"), ask("Is it alive?"), guess("Albert Einstein", "Physicist.")]),
        validator_provider=FakeGameProvider(validator_config, [validation("YES")]),
        oracle=oracle, audit_writer=audit_writer, policy=policy,
        model_config=model_config, validator_config=validator_config)
    engine.reuse_episode_answers = True
    result = engine.play(GameRequest(run_id="retrieval-repeat", subject=subject))
    assert result.success and len(oracle.requests) == 2
    assert result.summary.oracle_cache_hits == 0 and result.summary.counted_questions == 2
