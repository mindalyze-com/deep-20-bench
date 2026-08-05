from __future__ import annotations

import json
from collections.abc import Iterable
from decimal import Decimal
from types import SimpleNamespace

import pytest
import yaml
from deep20_game.audit import GameRunAuditWriter
from deep20_game.config import BenchmarkMode, CachePolicy, ModelConfig
from deep20_game.engine import GameEngine
from deep20_game.errors import GameAuditError, GameProviderError
from deep20_game.guesser import Guesser
from deep20_game.models import (
    ContractViolationKind,
    GameProviderRequest,
    GameRequest,
    TerminalReason,
)
from deep20_game.sampling import derive_guesser_prompt_nonce, derive_guesser_seed
from deep20_game.validator import GuessValidator
from deep20_oracle.config import OracleConfig
from deep20_oracle.models import (
    Evidence,
    EvidenceDecisionBasis,
    EvidenceReviewResult,
    OracleAdjudication,
    OracleAnswer,
    OracleDecisionPath,
    OracleMetrics,
    OracleRoleMetrics,
)

from .conftest import FakeGameProvider, official_policy


def ask(question: str) -> str:
    return json.dumps(
        {
            "result": {
                "action": "ASK",
                "question": question,
                "name": None,
                "description": None,
            }
        }
    )


def guess(name: str, description: str) -> str:
    return json.dumps(
        {
            "result": {
                "action": "GUESS",
                "question": None,
                "name": name,
                "description": description,
            }
        }
    )


def validation(answer: str, explanation: str = "Audit-only adjudication.") -> str:
    return json.dumps({"answer": answer, "explanation": explanation})


class FakeOracle:
    def __init__(self, answers: Iterable[OracleAnswer]):
        self.answers = list(answers)
        self.requests = []

    def ask(self, request):
        self.requests.append(request)
        answer = self.answers.pop(0)
        evidence = (
            ()
            if answer is OracleAnswer.UNKNOWN
            else (
                Evidence(
                    source_url="https://example.test/source",
                    excerpt=f"Evidence for: {request.question}",
                    validation="model_reported",
                ),
            )
        )
        role_metrics = OracleRoleMetrics(
            cost_usd=Decimal("0.01"),
            latency_ms=1_000,
            input_tokens=100,
            cached_input_tokens=50,
            cache_write_tokens=0,
            output_tokens=15,
            reasoning_tokens=5,
            search_count=0,
        )
        adjudication = (
            OracleAdjudication(
                oracle_answer=answer,
                disagreement=False,
                judge_invoked=False,
                final_answer=OracleAnswer.UNKNOWN,
                decision_path=OracleDecisionPath.ORACLE_UNKNOWN,
            )
            if answer is OracleAnswer.UNKNOWN
            else OracleAdjudication(
                oracle_answer=answer,
                reviewer=EvidenceReviewResult(
                    answer=answer,
                    basis=EvidenceDecisionBasis.EVIDENCE,
                    evidence_indices=(1,),
                ),
                disagreement=False,
                judge_invoked=False,
                final_answer=answer,
                decision_path=OracleDecisionPath.REVIEWER_AGREEMENT,
            )
        )
        return SimpleNamespace(
            call_id=f"OC-{len(self.requests):032x}",
            result=SimpleNamespace(evidence=evidence),
            adjudication=adjudication,
            audit=SimpleNamespace(
                provider=SimpleNamespace(
                    resolved_model="openai/test-oracle",
                    resolved_provider="openai",
                )
            ),
            metrics=OracleMetrics(
                cost_usd=Decimal("0.02"),
                latency_ms=2_000,
                input_tokens=200,
                cached_input_tokens=100,
                cache_write_tokens=0,
                output_tokens=30,
                reasoning_tokens=10,
                search_count=1,
                oracle=role_metrics.model_copy(
                    update={
                        "cost_usd": (
                            Decimal("0.02")
                            if answer is OracleAnswer.UNKNOWN
                            else Decimal("0.01")
                        ),
                        "search_count": 1,
                    }
                ),
                reviewer=(
                    None if answer is OracleAnswer.UNKNOWN else role_metrics
                ),
            ),
            guesser_answer=lambda: answer,
        )


class FailingGameProvider(FakeGameProvider):
    def complete(self, request: GameProviderRequest):
        self.requests.append(request)
        raise GameProviderError(
            "provider request failed",
            code="provider_request_failed",
        )


def make_engine(
    *,
    guesser_provider,
    validator_provider,
    oracle,
    audit_writer,
    policy,
    model_config,
    validator_config,
) -> GameEngine:
    return GameEngine(
        guesser=Guesser(guesser_provider, audit_writer, model_config, policy),
        oracle=oracle,
        validator=GuessValidator(
            validator_provider,
            audit_writer,
            validator_config,
        ),
        audit_writer=audit_writer,
        policy=policy,
        guesser_config=model_config,
        oracle_config=audit_writer.oracle_config,
        validator_config=audit_writer.validator_config,
    )


def test_immediate_correct_guess_reveals_only_category(
    audit_writer,
    model_config,
    validator_config,
    policy,
    subject,
) -> None:
    guesser_provider = FakeGameProvider(
        model_config,
        [guess("Albert Einstein", "The theoretical physicist known for relativity.")],
    )
    validator_provider = FakeGameProvider(
        validator_config,
        [validation("YES", "The proposal identifies the exact target.")],
    )
    engine = make_engine(
        guesser_provider=guesser_provider,
        validator_provider=validator_provider,
        oracle=FakeOracle([]),
        audit_writer=audit_writer,
        policy=policy,
        model_config=model_config,
        validator_config=validator_config,
    )

    result = engine.play(GameRequest(run_id="immediate", subject=subject))

    assert result.schema_version == 9
    assert result.success is True
    assert result.counted_questions == 0
    assert result.guesser_call_count == 1
    assert result.total_turns == 1
    assert result.duration_ms >= 0
    assert result.models.under_test.requested_model == "openai/test-model"
    assert result.models.under_test.resolved_models == ("openai/test-model",)
    assert (
        result.models.under_test.prompt_version
        == "stateful-category-guesser-v10-unknown-evidence-guidance"
    )
    assert result.models.oracle.requested_model == "openai/test-oracle"
    assert result.models.oracle.resolved_models == ()
    assert (
        result.models.oracle.prompt_version
        == "live-web-oracle-v7-direct-negative-evidence"
    )
    assert result.costs_usd.guesser == Decimal("0.01")
    assert result.costs_usd.oracle == Decimal(0)
    assert result.costs_usd.validator == Decimal("0.01")
    assert result.costs_usd.total == Decimal("0.02")
    assert result.tokens.guesser == 100
    assert result.tokens.oracle == 0
    assert result.tokens.validator == 100
    assert result.tokens.total == 200
    assert result.guess_count == 1
    assert result.cache_status == "not_applicable"
    assert len(result.turns) == 1
    assert result.turns[0].turn_number == 1
    assert result.turns[0].action.name == "Albert Einstein"
    assert result.turns[0].adjudication.answer is OracleAnswer.YES
    assert result.turns[0].adjudication.explanation == "The proposal identifies the exact target."
    assert [message.role for message in result.guesser_conversation] == [
        "system",
        "user",
        "assistant",
    ]
    assert json.loads(result.guesser_conversation[1].content) == {
        "category": "person",
        "event": "BEGIN",
        "variation_token": derive_guesser_prompt_nonce(
            base_seed=0,
            trial_number=1,
        ),
    }
    assert [message.turn_number for message in result.guesser_conversation] == [
        None,
        None,
        1,
    ]
    final_message = json.loads(result.guesser_conversation[-1].content)
    assert final_message["result"]["action"] == "GUESS"
    assert final_message["result"]["name"] == "Albert Einstein"
    assert all(message.content != "YES" for message in result.guesser_conversation)
    assert result.llm.guesser.configuration.model == "openai/test-model"
    assert result.llm.oracle.configuration.model == "openai/test-oracle"
    assert isinstance(result.llm.guesser.configuration, ModelConfig)
    assert isinstance(result.llm.oracle.configuration, OracleConfig)
    assert result.llm.oracle.metrics.calls == 0
    guesser_provider_usage = result.llm.guesser.provider_usage
    assert guesser_provider_usage.unreported_calls == 0
    assert guesser_provider_usage.fallback_calls == 0
    assert len(guesser_provider_usage.providers) == 1
    assert guesser_provider_usage.providers[0].provider == "openai"
    assert guesser_provider_usage.providers[0].calls == 1
    assert guesser_provider_usage.providers[0].cost_usd == Decimal("0.01")
    assert guesser_provider_usage.providers[0].latency_ms == 1_000
    validator_provider_usage = result.llm.validator.provider_usage
    assert len(validator_provider_usage.providers) == 1
    assert validator_provider_usage.providers[0].provider == "openai"
    visible_conversation = json.dumps(
        [message.model_dump(mode="json") for message in result.guesser_conversation]
    )
    assert "provider_usage" not in visible_conversation
    assert "resolved_provider" not in visible_conversation
    stored_result = yaml.safe_load(
        (audit_writer.runs_root / "immediate" / "result.yml").read_text()
    )
    assert stored_result["summary"]["total_turns"] == 1
    assert stored_result["models"]["under_test"]["requested_model"] == "openai/test-model"
    assert stored_result["models"]["under_test"]["resolved_models"] == ["openai/test-model"]
    assert stored_result["llm_details"]["guesser"]["provider_usage"]["providers"] == [
        {
            "provider": "openai",
            "calls": 1,
            "cost_usd": "0.01",
            "latency_ms": 1_000,
        }
    ]
    assert (
        stored_result["models"]["oracle"]["prompt_version"]
        == "live-web-oracle-v7-direct-negative-evidence"
    )
    assert stored_result["summary"]["costs_usd"] == {
        "guesser": "0.01",
        "oracle": "0",
        "validator": "0.01",
        "total": "0.02",
    }
    assert stored_result["summary"]["tokens"] == {
        "guesser": 100,
        "oracle": 0,
        "validator": 100,
        "total": 200,
    }
    assert stored_result["turns"][0]["action"]["name"] == "Albert Einstein"
    assert "turn_number" not in stored_result["guesser_conversation"][0]
    assert "turn_number" not in stored_result["guesser_conversation"][1]
    assert stored_result["guesser_conversation"][-1]["role"] == "assistant"
    assert stored_result["guesser_conversation"][-1]["turn_number"] == 1
    assert (
        json.loads(stored_result["guesser_conversation"][-1]["content"])["result"][
            "action"
        ]
        == "GUESS"
    )
    assert len(stored_result["integrity_hash"]) == 64
    with pytest.raises(GameAuditError) as duplicate:
        audit_writer.prepare_run("immediate")
    assert duplicate.value.code == "game_result_exists"
    guesser_messages = guesser_provider.requests[0].messages
    assert guesser_messages[1] == {
        "role": "user",
        "content": (
            '{"category":"person","event":"BEGIN",'
            f'"variation_token":"{derive_guesser_prompt_nonce(base_seed=0, trial_number=1)}"'
            "}"
        ),
    }
    assert subject.canonical_name not in str(guesser_messages)
    assert subject.description not in str(guesser_messages)
    assert str(subject.reference_url) not in str(guesser_messages)
    assert "model_id" not in str(guesser_messages)
    assert "execution_id" not in str(guesser_messages)
    assert "total_cost_usd" not in str(guesser_messages)
    assert guesser_provider.requests[0].seed == derive_guesser_seed(
        base_seed=0,
        trial_number=1,
        turn_number=1,
    )
    assert (
        validator_provider.requests[0].session_id.replace("validator", "guesser")
        == guesser_provider.requests[0].session_id
    )


def test_wrong_guess_oracle_unknown_then_success_preserves_visible_history(
    audit_writer,
    model_config,
    validator_config,
    policy,
    subject,
) -> None:
    guesser_provider = FakeGameProvider(
        model_config,
        [
            guess("Isaac Newton", "The English scientist associated with gravity."),
            ask("Was this person born before 1900?"),
            guess("Albert Einstein", "The physicist known for relativity."),
        ],
    )
    validator_provider = FakeGameProvider(
        validator_config,
        [validation("NO"), validation("YES")],
    )
    oracle = FakeOracle([OracleAnswer.UNKNOWN])
    engine = make_engine(
        guesser_provider=guesser_provider,
        validator_provider=validator_provider,
        oracle=oracle,
        audit_writer=audit_writer,
        policy=policy,
        model_config=model_config,
        validator_config=validator_config,
    )

    result = engine.play(GameRequest(run_id="multi-turn", subject=subject))

    assert result.success is True
    assert result.counted_questions == 2
    assert result.guesser_call_count == 3
    assert result.ask_count == 1
    assert result.guess_count == 2
    assert result.rejected_guess_count == 1
    assert result.oracle_unknown_count == 1
    assert result.total_turns == 3
    assert result.costs_usd.total == Decimal("0.07")
    assert [turn.adjudication.answer for turn in result.turns] == [
        OracleAnswer.NO,
        OracleAnswer.UNKNOWN,
        OracleAnswer.YES,
    ]
    assert result.turns[1].action.question == "Was this person born before 1900?"
    assert result.turns[1].adjudication.component == "oracle"
    assert result.turns[1].adjudication.evidence == ()
    assert result.llm.guesser.metrics.calls == 3
    assert result.llm.oracle.metrics.calls == 1
    assert result.llm.validator.metrics.calls == 2
    second_messages = guesser_provider.requests[1].messages
    third_messages = guesser_provider.requests[2].messages
    assert second_messages[-1] == {"role": "user", "content": "NO"}
    assert third_messages[: len(second_messages)] == second_messages
    assert third_messages[-1] == {"role": "user", "content": "UNKNOWN"}
    assert "Audit-only adjudication" not in str(third_messages)
    reported_messages = tuple(
        message.model_dump(mode="json") for message in result.guesser_conversation
    )
    assert (
        tuple(
            {"role": message["role"], "content": message["content"]}
            for message in reported_messages[:-1]
        )
        == third_messages
    )
    assert [message.get("turn_number") for message in reported_messages] == [
        None,
        None,
        1,
        1,
        2,
        2,
        3,
    ]
    assert (
        json.loads(reported_messages[-1]["content"])["result"]["name"]
        == "Albert Einstein"
    )
    assert reported_messages[-1]["role"] == "assistant"
    assert "Audit-only adjudication" not in str(reported_messages)
    assert all(
        set(message) == {"role", "content"}
        for request in guesser_provider.requests
        for message in request.messages
    )
    expected_begin = {
        "category": "person",
        "event": "BEGIN",
        "variation_token": derive_guesser_prompt_nonce(
            base_seed=0,
            trial_number=1,
        ),
    }
    assert [
        json.loads(request.messages[1]["content"])
        for request in guesser_provider.requests
    ] == [expected_begin, expected_begin, expected_begin]
    assert all(
        sum(
            message["content"].count('"variation_token":')
            for message in request.messages
        )
        == 1
        for request in guesser_provider.requests
    )
    assert all(
        message["content"] in {"YES", "NO", "UNKNOWN"}
        for message in third_messages[2:]
        if message["role"] == "user"
    )
    assert [request.seed for request in guesser_provider.requests] == [
        derive_guesser_seed(base_seed=0, trial_number=1, turn_number=turn_number)
        for turn_number in (1, 2, 3)
    ]


def test_disagreement_metadata_never_enters_guesser_visible_projection(
    audit_writer,
    model_config,
    validator_config,
    policy,
    subject,
) -> None:
    class DisagreementOracle(FakeOracle):
        def ask(self, request):
            call = super().ask(request)
            call.adjudication = OracleAdjudication(
                oracle_answer=OracleAnswer.YES,
                reviewer=EvidenceReviewResult(
                    answer=OracleAnswer.NO,
                    basis=EvidenceDecisionBasis.MODEL_KNOWLEDGE,
                ),
                judge=EvidenceReviewResult(
                    answer=OracleAnswer.NO,
                    basis=EvidenceDecisionBasis.MODEL_KNOWLEDGE,
                ),
                disagreement=True,
                judge_invoked=True,
                final_answer=OracleAnswer.NO,
                decision_path=OracleDecisionPath.JUDGE_DISAGREEMENT,
            )
            call.metrics = call.metrics.model_copy(
                update={"judge": call.metrics.reviewer}
            )
            call.audit.reviewer = SimpleNamespace(
                provider=SimpleNamespace(
                    resolved_model="google/gemini-3.5-flash-lite",
                    resolved_provider="Google AI Studio",
                    fallback_occurred=False,
                )
            )
            call.audit.judge = SimpleNamespace(
                provider=SimpleNamespace(
                    resolved_model="anthropic/claude-opus-5",
                    resolved_provider="Amazon Bedrock",
                    fallback_occurred=True,
                )
            )
            call.guesser_answer = lambda: OracleAnswer.NO
            return call

    guesser_provider = FakeGameProvider(
        model_config,
        [
            ask("Was this person born before the year 1300?"),
            guess("Albert Einstein", "The physicist known for relativity."),
        ],
    )
    engine = make_engine(
        guesser_provider=guesser_provider,
        validator_provider=FakeGameProvider(
            validator_config,
            [validation("YES")],
        ),
        oracle=DisagreementOracle([OracleAnswer.NO]),
        audit_writer=audit_writer,
        policy=policy,
        model_config=model_config,
        validator_config=validator_config,
    )

    result = engine.play(GameRequest(run_id="blind-disagreement", subject=subject))

    second_request = guesser_provider.requests[1]
    assert second_request.messages[-1] == {"role": "user", "content": "NO"}
    visible = json.dumps(second_request.messages)
    assert "Evidence for:" not in visible
    assert "judge_disagreement" not in visible
    assert "oracle_answer" not in visible
    assert "reviewer" not in visible
    assert "model_knowledge" not in visible
    assert "complete enumeration" not in visible
    assert "no other evidence was found" not in visible
    assert "Amazon Bedrock" not in visible
    assert result.turns[0].adjudication.answer is OracleAnswer.NO
    assert result.turns[0].adjudication.oracle_quality is not None
    assert result.turns[0].adjudication.oracle_quality.judge_invoked is True
    assert (
        result.turns[0].adjudication.oracle_quality.reviewer.basis
        is EvidenceDecisionBasis.MODEL_KNOWLEDGE
    )
    assert (
        result.turns[0].adjudication.oracle_quality.judge.basis
        is EvidenceDecisionBasis.MODEL_KNOWLEDGE
    )
    assert result.summary.oracle_quality.reviewed_questions == 1
    assert result.summary.oracle_quality.disagreements == 1
    assert result.summary.oracle_quality.judge_invocations == 1
    assert result.summary.oracle_quality.oracle_answers_changed == 1
    assert result.summary.oracle_quality.judge_no_answers == 1
    assert len(result.summary.oracle_quality.question_types) == 1
    assert result.summary.oracle_quality.question_types[0].reviewed_questions == 1
    assert result.summary.oracle_quality.question_types[0].disagreements == 1
    judge_usage = result.llm_details.oracle.provider_usage.judge
    assert judge_usage.fallback_calls == 1
    assert judge_usage.unreported_calls == 0
    assert len(judge_usage.providers) == 1
    assert judge_usage.providers[0].provider == "Amazon Bedrock"
    assert judge_usage.providers[0].calls == 1


def test_validator_unknown_is_scored_terminal_failure(
    audit_writer,
    model_config,
    validator_config,
    policy,
    subject,
) -> None:
    engine = make_engine(
        guesser_provider=FakeGameProvider(
            model_config,
            [guess("John Smith", "A person with an insufficiently precise identity.")],
        ),
        validator_provider=FakeGameProvider(
            validator_config,
            [validation("UNKNOWN", "The proposal is ambiguous.")],
        ),
        oracle=FakeOracle([]),
        audit_writer=audit_writer,
        policy=policy,
        model_config=model_config,
        validator_config=validator_config,
    )

    result = engine.play(GameRequest(run_id="unknown-guess", subject=subject))

    assert result.success is False
    assert result.terminal_reason is TerminalReason.VALIDATOR_UNKNOWN
    assert result.scoring_eligible is True
    assert result.counted_questions == 1


def test_limit_allows_one_final_guess_without_changing_schema(
    tmp_path,
    monkeypatch,
    oracle_config,
    model_config,
    validator_config,
    subject,
) -> None:
    policy = official_policy(max_questions=2).model_copy(
        update={
            "benchmark_mode": BenchmarkMode.EXPERIMENTAL,
            "include_oracle_evidence": False,
            "include_guesser_conversation": False,
        }
    )
    writer = GameRunAuditWriter(
        tmp_path / "runs",
        game_policy=policy,
        oracle_config=oracle_config,
        guesser_config=model_config,
        validator_config=validator_config,
        subject_catalog_hash="a" * 64,
        repository=tmp_path,
    )
    monkeypatch.setattr(writer, "_git", lambda arguments: "abc123")
    guesser_provider = FakeGameProvider(
        model_config,
        [
            ask("Question one?"),
            ask("Question two?"),
            guess("Isaac Newton", "The English scientist associated with gravity."),
        ],
    )
    engine = make_engine(
        guesser_provider=guesser_provider,
        validator_provider=FakeGameProvider(
            validator_config,
            [validation("NO")],
        ),
        oracle=FakeOracle([OracleAnswer.YES, OracleAnswer.NO]),
        audit_writer=writer,
        policy=policy,
        model_config=model_config,
        validator_config=validator_config,
    )

    result = engine.play(GameRequest(run_id="final-guess", subject=subject))

    assert result.terminal_reason is TerminalReason.LIMIT_EXHAUSTED
    assert result.counted_questions == 2
    assert result.guesser_call_count == 3
    assert result.rejected_guess_count == 1
    assert result.guesser_conversation == ()
    stored_result = yaml.safe_load((writer.runs_root / "final-guess" / "result.yml").read_text())
    assert stored_result["guesser_conversation"] == []
    assert all(
        not turn.adjudication.evidence
        for turn in result.turns
        if turn.adjudication.component == "oracle"
    )
    assert all(
        request.output_schema == guesser_provider.requests[0].output_schema
        for request in guesser_provider.requests
    )


def test_ask_on_final_opportunity_is_protocol_failure(
    tmp_path,
    monkeypatch,
    oracle_config,
    model_config,
    validator_config,
    subject,
) -> None:
    from deep20_game.config import GamePolicy

    policy = GamePolicy(max_questions=1)
    writer = GameRunAuditWriter(
        tmp_path / "runs",
        game_policy=policy,
        oracle_config=oracle_config,
        guesser_config=model_config,
        validator_config=validator_config,
        subject_catalog_hash="a" * 64,
        repository=tmp_path,
    )
    monkeypatch.setattr(writer, "_git", lambda arguments: "abc123")
    engine = make_engine(
        guesser_provider=FakeGameProvider(
            model_config,
            [ask("First?"), ask("Illegal final ask?")],
        ),
        validator_provider=FakeGameProvider(validator_config, []),
        oracle=FakeOracle([OracleAnswer.NO]),
        audit_writer=writer,
        policy=policy,
        model_config=model_config,
        validator_config=validator_config,
    )

    result = engine.play(GameRequest(run_id="illegal-final", subject=subject))

    assert result.terminal_reason is TerminalReason.GUESSER_PROTOCOL_FAILURE
    assert result.scoring_eligible is True
    assert result.counted_questions == 1


def test_invalid_final_guesser_output_is_scored_protocol_failure(
    audit_writer,
    model_config,
    validator_config,
    policy,
    subject,
) -> None:
    provider = FakeGameProvider(model_config, ["not-json", "still-not-json"])
    limited_policy = policy.model_copy(update={"max_questions": 1})
    engine = make_engine(
        guesser_provider=provider,
        validator_provider=FakeGameProvider(validator_config, []),
        oracle=FakeOracle([]),
        audit_writer=audit_writer,
        policy=limited_policy,
        model_config=model_config,
        validator_config=validator_config,
    )

    result = engine.play(GameRequest(run_id="bad-output", subject=subject))

    assert result.terminal_reason is TerminalReason.GUESSER_PROTOCOL_FAILURE
    assert result.scoring_eligible is True
    assert result.failure is not None
    assert result.failure.code == "invalid_guesser_output"
    assert result.failure.diagnostics is not None
    assert result.counted_questions == 1
    assert result.summary.contract.violations == 2
    assert result.summary.contract.counted_penalties == 1
    assert result.summary.contract.status == "breached"
    assert result.turns[0].turn_type == "contract_violation"
    assert result.turns[0].feedback_event == "FORMAT_ERROR"
    assert result.turns[1].turn_type == "contract_violation"
    assert result.turns[1].feedback_event is None
    expected_begin = {
        "category": "person",
        "event": "BEGIN",
        "variation_token": derive_guesser_prompt_nonce(
            base_seed=0,
            trial_number=1,
        ),
    }
    assert json.loads(result.guesser_conversation[1].content) == expected_begin
    assert json.loads(provider.requests[0].messages[1]["content"]) == expected_begin
    serialized_guesser_request = json.dumps(provider.requests[0].messages)
    visible_conversation = json.dumps(
        [message.model_dump(mode="json") for message in result.guesser_conversation]
    )
    for forbidden in (
        subject.target_id,
        subject.canonical_name,
        subject.description,
        str(subject.reference_url),
        "benchmark.trial_context",
        "trial-001",
        "model_id",
        "execution_id",
        "total_cost_usd",
    ):
        assert forbidden not in serialized_guesser_request
        assert forbidden not in visible_conversation
    for forbidden_field in (
        "base_seed",
        "trial_number",
        "seed_capability",
        "provider_seed",
    ):
        assert f'"{forbidden_field}"' not in visible_conversation
    failures = [
        json.loads(line)
        for line in (
            audit_writer.runs_root / "bad-output" / "guesser-calls.jsonl"
        ).read_text().splitlines()
    ]
    assert len(failures) == 2
    assert all(failure["status"] == "failure" for failure in failures)
    assert all(
        failure["error"]["code"] == "invalid_guesser_output"
        for failure in failures
    )
    events = [
        json.loads(line)
        for line in (audit_writer.runs_root / "bad-output" / "episode-events.jsonl")
        .read_text()
        .splitlines()
    ]
    terminal = next(event for event in events if event["event_type"] == "episode_finished")
    violations = [
        event for event in events if event["event_type"] == "contract_violation"
    ]
    assert len(violations) == 2
    diagnostics = terminal["payload"]["failure"]["diagnostics"]
    assert [cause["exception_type"] for cause in diagnostics["causes"]] == [
        "GuesserProtocolError",
        "ValidationError",
    ]
    assert diagnostics["causes"][1]["message"] == "validation failed"
    assert diagnostics["provider"]["requested_model"] == model_config.model
    serialized_diagnostics = json.dumps(diagnostics)
    assert "not-json" not in serialized_diagnostics
    assert subject.canonical_name not in serialized_diagnostics
    assert subject.description not in serialized_diagnostics
    persisted_result = yaml.safe_load(
        (audit_writer.runs_root / "bad-output" / "result.yml").read_text()
    )
    assert persisted_result["failure"]["code"] == "invalid_guesser_output"
    assert persisted_result["failure"]["diagnostics"] == diagnostics


def test_contract_violation_costs_one_turn_then_success_remains_marked_breached(
    audit_writer,
    model_config,
    validator_config,
    policy,
    subject,
) -> None:
    invalid = json.dumps(
        {
            "result": {
                "action": "GUESS",
                "question": None,
                "name": "Albert Einstein",
                "description": "The physicist associated with relativity.",
                "unexpected": "PRIVATE_INVALID_MARKER",
            }
        }
    )
    provider = FakeGameProvider(
        model_config,
        [
            invalid,
            guess(
                "Albert Einstein",
                "The physicist associated with relativity.",
            ),
        ],
    )
    engine = make_engine(
        guesser_provider=provider,
        validator_provider=FakeGameProvider(
            validator_config,
            [validation("YES")],
        ),
        oracle=FakeOracle([]),
        audit_writer=audit_writer,
        policy=policy,
        model_config=model_config,
        validator_config=validator_config,
    )

    result = engine.play(GameRequest(run_id="recovered-output", subject=subject))

    assert result.success is True
    assert result.counted_questions == 1
    assert result.summary.contract.evaluated_outputs == 2
    assert result.summary.contract.valid_outputs == 1
    assert result.summary.contract.violations == 1
    assert result.summary.contract.counted_penalties == 1
    assert result.summary.contract.affected_trials == 1
    assert result.summary.contract.compliance_rate == Decimal("0.5")
    assert result.summary.contract.status == "breached"
    assert [turn.turn_type for turn in result.turns] == [
        "contract_violation",
        "action",
    ]
    assert len(provider.requests) == 2
    retry_messages = json.dumps(provider.requests[1].messages)
    assert "FORMAT_ERROR" in retry_messages
    assert "PRIVATE_INVALID_MARKER" not in retry_messages
    assert not engine.oracle.requests
    recovery = result.llm.guesser.metrics.recovery
    assert recovery.request_attempts == 2
    assert recovery.retried_calls == 0
    assert recovery.recovered_calls == 0
    assert recovery.exhausted_retries == 0
    assert result.llm.guesser.metrics.input_tokens == 160


def test_first_guesser_provider_failure_preserves_prompt_nonce_in_report(
    audit_writer,
    model_config,
    validator_config,
    policy,
    subject,
) -> None:
    provider = FailingGameProvider(model_config, [])
    engine = make_engine(
        guesser_provider=provider,
        validator_provider=FakeGameProvider(validator_config, []),
        oracle=FakeOracle([]),
        audit_writer=audit_writer,
        policy=policy,
        model_config=model_config,
        validator_config=validator_config,
    )

    result = engine.play(GameRequest(run_id="provider-failure", subject=subject))

    assert result.terminal_reason is TerminalReason.INFRASTRUCTURE_FAILURE
    assert result.scoring_eligible is False
    expected_begin = {
        "category": "person",
        "event": "BEGIN",
        "variation_token": derive_guesser_prompt_nonce(
            base_seed=0,
            trial_number=1,
        ),
    }
    assert json.loads(result.guesser_conversation[1].content) == expected_begin
    assert json.loads(provider.requests[0].messages[1]["content"]) == expected_begin


def test_prompt_nonce_mismatch_is_an_infrastructure_failure_before_provider_call(
    audit_writer,
    model_config,
    validator_config,
    policy,
    subject,
    monkeypatch,
) -> None:
    provider = FakeGameProvider(model_config, [ask("Should not be called")])
    engine = make_engine(
        guesser_provider=provider,
        validator_provider=FakeGameProvider(validator_config, []),
        oracle=FakeOracle([]),
        audit_writer=audit_writer,
        policy=policy,
        model_config=model_config,
        validator_config=validator_config,
    )
    monkeypatch.setattr(
        "deep20_game.engine.derive_guesser_prompt_nonce",
        lambda *, base_seed, trial_number: "ASF23XSA",
    )

    result = engine.play(GameRequest(run_id="nonce-mismatch", subject=subject))

    assert result.terminal_reason is TerminalReason.INFRASTRUCTURE_FAILURE
    assert result.scoring_eligible is False
    assert result.failure is not None
    assert result.failure.code == "guesser_variation_token_mismatch"
    assert provider.requests == []


def test_official_runtime_cache_miss_is_publication_eligible_and_isolated(
    tmp_path,
    monkeypatch,
    oracle_config,
    model_config,
    validator_config,
    subject,
) -> None:
    policy = official_policy()
    required_config = model_config.model_copy(
        update={
            "prompt_cache": model_config.prompt_cache.model_copy(
                update={"policy": CachePolicy.REQUIRED}
            )
        }
    )
    writer = GameRunAuditWriter(
        tmp_path / "runs",
        game_policy=policy,
        oracle_config=oracle_config,
        guesser_config=required_config,
        validator_config=validator_config,
        subject_catalog_hash="a" * 64,
        repository=tmp_path,
        cache_probe_summary={"success": True, "probe_id": "CP-test"},
    )
    monkeypatch.setattr(writer, "_git", lambda arguments: "abc123")
    guesser_provider = FakeGameProvider(
        required_config,
        [
            ask("Was this person born before 1900?"),
            guess("Albert Einstein", "The physicist known for relativity."),
        ],
        traces=[
            {"input_tokens": 100, "cache_write_tokens": 100},
            {"input_tokens": 130, "cached_input_tokens": 0},
        ],
    )
    engine = make_engine(
        guesser_provider=guesser_provider,
        validator_provider=FakeGameProvider(
            validator_config,
            [validation("YES")],
        ),
        oracle=FakeOracle([OracleAnswer.YES]),
        audit_writer=writer,
        policy=policy,
        model_config=required_config,
        validator_config=validator_config,
    )

    result = engine.play(GameRequest(run_id="cache-miss", subject=subject))

    assert result.success is True
    assert result.cache_status == "noncompliant"
    assert result.publication_eligible is True
    assert guesser_provider.requests[1].messages[-1] == {
        "role": "user",
        "content": "YES",
    }
    visible_request = json.dumps(guesser_provider.requests[1].messages)
    for reporting_only_value in (
        "cache_status",
        "noncompliant",
        "publication_eligible",
    ):
        assert reporting_only_value not in visible_request
    evidence = result.turns[0].adjudication.evidence
    assert len(evidence) == 1
    assert str(evidence[0].source_url) == "https://example.test/source"
    assert evidence[0].excerpt == "Evidence for: Was this person born before 1900?"
    stored = yaml.safe_load((writer.runs_root / "cache-miss" / "result.yml").read_text())
    stored_evidence = stored["turns"][0]["adjudication"]["evidence"][0]
    assert stored_evidence["source_url"] == "https://example.test/source"
    assert stored_evidence["excerpt"] == "Evidence for: Was this person born before 1900?"


class ScriptedGameProvider(FakeGameProvider):
    """Interleaves provider-output failures with successful completions."""

    def __init__(self, config: ModelConfig, script: list[tuple[str, str]]):
        super().__init__(config, [value for kind, value in script if kind == "ok"])
        self.script = list(script)

    def complete(self, request: GameProviderRequest):
        kind, value = self.script.pop(0)
        if kind == "fail":
            self.requests.append(request)
            raise GameProviderError(
                "PRIVATE_PROVIDER_DETAIL the provider stopped before a structured action",
                code=value,
            )
        return super().complete(request)


@pytest.mark.parametrize(
    ("failure_code", "expected_kind"),
    [
        ("provider_output_limit_exceeded", ContractViolationKind.OUTPUT_LIMIT_EXCEEDED),
        ("provider_empty_response", ContractViolationKind.EMPTY_OUTPUT),
        ("provider_incomplete_response", ContractViolationKind.INCOMPLETE_OUTPUT),
    ],
)
def test_provider_output_failure_is_scored_contract_violation_then_recovery(
    audit_writer,
    model_config,
    validator_config,
    policy,
    subject,
    failure_code,
    expected_kind,
) -> None:
    provider = ScriptedGameProvider(
        model_config,
        [
            ("fail", failure_code),
            ("ok", guess("Albert Einstein", "The physicist associated with relativity.")),
        ],
    )
    engine = make_engine(
        guesser_provider=provider,
        validator_provider=FakeGameProvider(validator_config, [validation("YES")]),
        oracle=FakeOracle([]),
        audit_writer=audit_writer,
        policy=policy,
        model_config=model_config,
        validator_config=validator_config,
    )

    result = engine.play(GameRequest(run_id="provider-output-violation", subject=subject))

    assert result.success is True
    assert result.counted_questions == 1
    assert [turn.turn_type for turn in result.turns] == [
        "contract_violation",
        "action",
    ]
    assert result.turns[0].violation_kind is expected_kind
    assert result.turns[0].feedback_event == "FORMAT_ERROR"
    assert result.summary.contract.violations == 1
    assert result.summary.contract.counted_penalties == 1
    assert result.summary.contract.status == "breached"
    retry_messages = json.dumps(provider.requests[1].messages)
    assert "FORMAT_ERROR" in retry_messages
    assert "PRIVATE_PROVIDER_DETAIL" not in retry_messages
    assert failure_code not in retry_messages
    visible_conversation = json.dumps(
        [message.model_dump(mode="json") for message in result.guesser_conversation]
    )
    assert "PRIVATE_PROVIDER_DETAIL" not in visible_conversation
    assert failure_code not in visible_conversation


def test_consecutive_contract_violations_exhaust_as_scored_model_failure(
    audit_writer,
    model_config,
    validator_config,
    policy,
    subject,
) -> None:
    limited_policy = policy.model_copy(
        update={"max_consecutive_contract_violations": 3}
    )
    provider = ScriptedGameProvider(
        model_config,
        [("fail", "provider_output_limit_exceeded")] * 3,
    )
    engine = make_engine(
        guesser_provider=provider,
        validator_provider=FakeGameProvider(validator_config, []),
        oracle=FakeOracle([]),
        audit_writer=audit_writer,
        policy=limited_policy,
        model_config=model_config,
        validator_config=validator_config,
    )

    result = engine.play(GameRequest(run_id="violations-exhausted", subject=subject))

    assert result.terminal_reason is TerminalReason.GUESSER_PROTOCOL_FAILURE
    assert result.scoring_eligible is True
    assert result.failure is not None
    assert result.failure.code == "consecutive_contract_violations_exhausted"
    assert result.counted_questions == 3
    assert len(provider.requests) == 3
    assert [turn.turn_type for turn in result.turns] == ["contract_violation"] * 3
    assert all(turn.feedback_event == "FORMAT_ERROR" for turn in result.turns)
    assert all(
        turn.violation_kind is ContractViolationKind.OUTPUT_LIMIT_EXCEEDED
        for turn in result.turns
    )
    assert result.summary.contract.violations == 3
    assert result.summary.contract.counted_penalties == 3
    assert result.summary.contract.status == "breached"


def test_valid_action_resets_consecutive_violation_counter(
    audit_writer,
    model_config,
    validator_config,
    policy,
    subject,
) -> None:
    limited_policy = policy.model_copy(
        update={"max_consecutive_contract_violations": 2}
    )
    provider = ScriptedGameProvider(
        model_config,
        [
            ("fail", "provider_output_limit_exceeded"),
            ("ok", ask("Was this person a scientist?")),
            ("fail", "provider_empty_response"),
            ("ok", guess("Albert Einstein", "The physicist associated with relativity.")),
        ],
    )
    engine = make_engine(
        guesser_provider=provider,
        validator_provider=FakeGameProvider(validator_config, [validation("YES")]),
        oracle=FakeOracle([OracleAnswer.YES]),
        audit_writer=audit_writer,
        policy=limited_policy,
        model_config=model_config,
        validator_config=validator_config,
    )

    result = engine.play(GameRequest(run_id="violation-counter-reset", subject=subject))

    assert result.success is True
    assert result.counted_questions == 3
    assert [turn.turn_type for turn in result.turns] == [
        "contract_violation",
        "action",
        "contract_violation",
        "action",
    ]
    assert result.summary.contract.violations == 2
    assert result.summary.contract.counted_penalties == 2


def test_validator_output_limit_remains_infrastructure_failure(
    audit_writer,
    model_config,
    validator_config,
    policy,
    subject,
) -> None:
    engine = make_engine(
        guesser_provider=FakeGameProvider(
            model_config,
            [guess("Albert Einstein", "The physicist associated with relativity.")],
        ),
        validator_provider=ScriptedGameProvider(
            validator_config,
            [("fail", "provider_output_limit_exceeded")] * 4,
        ),
        oracle=FakeOracle([]),
        audit_writer=audit_writer,
        policy=policy,
        model_config=model_config,
        validator_config=validator_config,
    )

    result = engine.play(GameRequest(run_id="validator-output-limit", subject=subject))

    assert result.terminal_reason is TerminalReason.INFRASTRUCTURE_FAILURE
    assert result.scoring_eligible is False
