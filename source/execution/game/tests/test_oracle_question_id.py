from __future__ import annotations

import json

import pytest
from deep20_game.models import TerminalReason
from deep20_oracle.audit import RunAuditWriter
from deep20_oracle.config import PromptProfile
from deep20_oracle.models import OracleRole
from deep20_oracle.provider import ProviderExchange
from deep20_oracle.request_variation import QuestionMetadata
from deep20_oracle.service import Oracle

from .conftest import FakeGameProvider, provider_trace
from .test_engine import GameRequest, ask, guess, make_engine, validation


@pytest.mark.parametrize("profile", tuple(PromptProfile))
@pytest.mark.parametrize("failed_role", (None, OracleRole.ORACLE, OracleRole.REVIEWER))
def test_question_ids_and_format_failures_never_enter_guesser_requests(
    profile, failed_role, tmp_path, audit_writer,
    model_config, validator_config, policy, subject,
):
    policy = policy.model_copy(update={"prompt_profile": profile, "max_questions": 1})
    audit_writer.game_policy = policy
    config = audit_writer.oracle_config.model_copy(update={"prompt_profile": profile})
    audit_writer.oracle_config = config
    research_output = json.dumps({
        "answer": "YES", "research_outcome": "answered",
        "attempted_queries": ["PRIVATE_SEARCH_QUERY"],
        "evidence": [{"source_url": "https://example.test/private",
                      "excerpt": "PRIVATE_EVIDENCE", "validation": "model_reported"}],
    })
    review_output = '{"answer":"YES","basis":"evidence","evidence_indices":[1]}'

    class RoleProvider:
        def __init__(self, role, route, output):
            self.role = role
            self.route = route
            self.output = output
            self.requests = []

        def complete(self, request):
            self.requests.append(request)
            raw = ("PRIVATE_INVALID_OUTPUT" if len(self.requests) == 1 or failed_role is self.role
                   else self.output)
            trace = provider_trace(model_config, raw).model_copy(update={
                "requested_model": self.route.model, "resolved_model": self.route.model,
                "requested_provider": self.route.provider, "resolved_provider": self.route.provider,
                "request": {"messages": list(request.messages), "schema": request.output_schema},
            })
            trace = trace.model_copy(update={"usage": trace.usage.model_copy(update={
                "search_count": int(self.role is OracleRole.ORACLE),
            })})
            return ProviderExchange(raw_output=raw, trace=trace)

    class UnusedJudge:
        def complete(self, request):
            pytest.fail("Agreement or required-role failure must not invoke the Judge")

    research = RoleProvider(OracleRole.ORACLE, config, research_output)
    reviewer = RoleProvider(OracleRole.REVIEWER, config.reviewer, review_output)
    sink = RunAuditWriter(tmp_path / "oracle", config=config,
                          subject_catalog_hash="a" * 64, repository=tmp_path)
    oracle = Oracle(research, reviewer, UnusedJudge(), sink, config)
    guesser = FakeGameProvider(model_config, [
        ask("Was this person born before 1900?"),
        guess("Albert Einstein", "The physicist known for relativity."),
    ])
    validator = FakeGameProvider(validator_config, [validation("YES")])
    engine = make_engine(guesser_provider=guesser, validator_provider=validator, oracle=oracle,
                         audit_writer=audit_writer, policy=policy, model_config=model_config,
                         validator_config=validator_config)

    result = engine.play(GameRequest(run_id="question-id-isolation", subject=subject))

    visible = json.dumps([request.messages for request in guesser.requests])
    validator_visible = json.dumps([request.messages for request in validator.requests])
    for marker in ("question_id", "metadata only", "PRIVATE_INVALID_OUTPUT",
                   "PRIVATE_SEARCH_QUERY", "PRIVATE_EVIDENCE"):
        assert marker not in visible
        assert marker not in validator_visible
    for provider in (research, reviewer):
        for request in provider.requests:
            metadata = QuestionMetadata.model_validate_json(request.messages[-1]["content"])
            assert metadata.question_id not in visible
            assert metadata.question_id not in validator_visible
    assert len(research.requests) == 2
    if failed_role is None:
        assert result.success and result.scoring_eligible
        assert len(reviewer.requests) == 2
        assert len(guesser.requests) == 2
        assert guesser.requests[1].messages[-1] == {"role": "user", "content": "YES"}
        assert len(guesser.requests[1].messages) == 4
        assert result.counted_questions == 1
    else:
        assert result.terminal_reason is TerminalReason.INFRASTRUCTURE_FAILURE
        assert not result.scoring_eligible
        assert len(guesser.requests) == 1
        assert len(reviewer.requests) == (2 if failed_role is OracleRole.REVIEWER else 0)
