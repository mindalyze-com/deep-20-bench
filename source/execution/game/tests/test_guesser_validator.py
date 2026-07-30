from __future__ import annotations

import json

import pytest
from deep20_game.config import BenchmarkMode, SeedCapability
from deep20_game.errors import GameConfigurationError, GuesserProtocolError
from deep20_game.guesser import Guesser
from deep20_game.models import (
    guesser_action_output_schema,
    parse_guesser_action_output,
)
from deep20_game.prompt import append_visible_turn, initial_guesser_messages
from deep20_game.sampling import derive_guesser_prompt_nonce, guesser_sampling_decision
from deep20_game.validator import GuessValidator
from deep20_oracle.models import OracleAnswer, RecoveryReason

from .conftest import FakeGameProvider


def ask_payload(question: str) -> str:
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


def guess_payload(name: str = "Albert Einstein") -> str:
    return json.dumps(
        {
            "result": {
                "action": "GUESS",
                "question": None,
                "name": name,
                "description": "The theoretical physicist associated with relativity.",
            }
        }
    )


def sampling(model_config, turn_number: int):
    return guesser_sampling_decision(
        capability=model_config.seed_capability,
        base_seed=0,
        trial_number=1,
        turn_number=turn_number,
    )


def initial_messages(*, base_seed: int = 0, trial_number: int = 1):
    return initial_guesser_messages(
        50,
        "person",
        derive_guesser_prompt_nonce(
            base_seed=base_seed,
            trial_number=trial_number,
        ),
    )


def test_guesser_reuses_session_cache_key_and_full_history(
    audit_writer, model_config, policy
) -> None:
    provider = FakeGameProvider(
        model_config,
        [ask_payload("Is it a person?"), guess_payload()],
    )
    guesser = Guesser(provider, audit_writer, model_config, policy)
    audit_writer.prepare_run("session-test")
    initial = initial_messages()

    first = guesser.next_action(
        run_id="session-test",
        episode_id="EP-" + "1" * 32,
        messages=initial,
        sampling=sampling(model_config, 1),
    )
    history = append_visible_turn(first.audit.messages, first.action, "YES")
    second = guesser.next_action(
        run_id="session-test",
        episode_id="EP-" + "1" * 32,
        messages=history,
        sampling=sampling(model_config, 2),
    )

    assert first.audit.session_id == second.audit.session_id
    assert first.audit.prompt_cache_key == second.audit.prompt_cache_key
    assert provider.requests[0].messages == first.audit.messages
    assert json.loads(provider.requests[0].messages[-1]["content"]) == {
        "category": "person",
        "event": "BEGIN",
        "variation_token": derive_guesser_prompt_nonce(base_seed=0, trial_number=1),
    }
    assert provider.requests[1].messages[: len(first.audit.messages)] == (
        first.audit.messages
    )
    assert provider.requests[0].output_schema == provider.requests[1].output_schema
    assert provider.requests[0].output_schema == guesser_action_output_schema()
    serialized_request = provider.requests[0].model_dump_json()
    assert "Albert Einstein" not in serialized_request
    assert "theoretical physicist" not in serialized_request
    stored = (audit_writer.runs_root / "session-test" / "guesser-calls.jsonl").read_text()
    assert '"session_id":"deep20-guesser-EP-' in stored


def test_guesser_surfaces_invalid_output_without_hidden_retry(
    audit_writer,
    model_config,
    policy,
) -> None:
    marker = "PRIVATE_RETRY_MARKER"
    invalid = json.dumps(
        {
            "result": {
                "action": "ASK",
                "question": "Is it a person?",
                "name": None,
                "description": None,
                "diagnostic": marker,
            }
        }
    )
    provider = FakeGameProvider(model_config, [invalid])
    audit_writer.prepare_run("invalid-output-recovery")
    with pytest.raises(GuesserProtocolError) as failure:
        Guesser(provider, audit_writer, model_config, policy).next_action(
            run_id="invalid-output-recovery",
            episode_id="EP-" + "9" * 32,
            messages=initial_messages(),
            sampling=sampling(model_config, 1),
        )

    assert len(provider.requests) == 1
    assert failure.value.code == "invalid_guesser_output"
    assert failure.value.details["violation_kind"] == "invalid_action"
    stored = (
        audit_writer.runs_root
        / "invalid-output-recovery"
        / "guesser-calls.jsonl"
    ).read_text()
    assert '"code":"invalid_guesser_output"' in stored
    assert marker in stored  # Standalone verbose audits may retain the original provider trace.


def test_invalid_output_preserves_provider_request_attempt_accounting(
    audit_writer,
    model_config,
    policy,
) -> None:
    provider = FakeGameProvider(
        model_config,
        ['{"result":{"action":"ASK"}'],
        traces=({"request_attempts": 2},),
    )
    audit_writer.prepare_run("shared-attempt-budget")

    with pytest.raises(GuesserProtocolError) as failure:
        Guesser(provider, audit_writer, model_config, policy).next_action(
            run_id="shared-attempt-budget",
            episode_id="EP-" + "6" * 32,
            messages=initial_messages(),
            sampling=sampling(model_config, 1),
        )

    assert failure.value.code == "invalid_guesser_output"
    assert len(provider.requests) == 1
    trace = failure.value.details["provider_trace"]
    assert trace["request_attempts"] == 2


def test_benchmark_mode_never_changes_guesser_request_or_cache_namespace(
    audit_writer,
    model_config,
    policy,
) -> None:
    messages = initial_messages()
    decision = sampling(model_config, 1)
    episode_id = "EP-" + "2" * 32
    policies = (
        policy.model_copy(update={"benchmark_mode": BenchmarkMode.EXPERIMENTAL}),
        policy.model_copy(update={"benchmark_mode": BenchmarkMode.OFFICIAL}),
    )
    requests = []

    for index, selected_policy in enumerate(policies, start=1):
        provider = FakeGameProvider(model_config, [ask_payload("Is it a person?")])
        run_id = f"mode-isolation-{index}"
        audit_writer.prepare_run(run_id)
        Guesser(provider, audit_writer, model_config, selected_policy).next_action(
            run_id=run_id,
            episode_id=episode_id,
            messages=messages,
            sampling=decision,
        )
        requests.append(provider.requests[0])

    assert requests[0] == requests[1]
    assert requests[0].messages == messages
    assert "official" not in requests[0].model_dump_json()
    assert "experimental" not in requests[0].model_dump_json()


def test_guesser_emits_no_component_owned_info_log(
    audit_writer,
    model_config,
    policy,
    caplog,
) -> None:
    provider = FakeGameProvider(model_config, [guess_payload()])
    guesser = Guesser(provider, audit_writer, model_config, policy)
    audit_writer.prepare_run("feedback-log-test")
    first = parse_guesser_action_output(ask_payload("First line\nSecond line"))
    messages = append_visible_turn(initial_messages(), first, "NO")
    guesser.next_action(
        run_id="feedback-log-test",
        episode_id="EP-" + "3" * 32,
        messages=messages,
        sampling=sampling(model_config, 2),
    )

    assert caplog.records == []


def test_guesser_ask_emits_no_component_owned_info_log(
    audit_writer,
    model_config,
    policy,
    caplog,
) -> None:
    provider = FakeGameProvider(model_config, [ask_payload("Is it a person?")])
    guesser = Guesser(provider, audit_writer, model_config, policy)
    audit_writer.prepare_run("question-number-log-test")
    guesser.next_action(
        run_id="question-number-log-test",
        episode_id="EP-" + "4" * 32,
        messages=initial_messages(),
        sampling=sampling(model_config, 1),
    )

    assert caplog.records == []


def test_guesser_passes_controlled_seed_only_as_provider_metadata(
    audit_writer,
    model_config,
    policy,
) -> None:
    provider = FakeGameProvider(model_config, [ask_payload("Is it a person?")])
    guesser = Guesser(provider, audit_writer, model_config, policy)
    audit_writer.prepare_run("seeded-guesser-test")
    decision = guesser_sampling_decision(
        capability=model_config.seed_capability,
        base_seed=42,
        trial_number=2,
        turn_number=1,
    )
    messages = initial_messages(base_seed=42, trial_number=2)

    call = guesser.next_action(
        run_id="seeded-guesser-test",
        episode_id="EP-" + "5" * 32,
        messages=messages,
        sampling=decision,
    )

    assert provider.requests[0].seed == decision.seed
    rendered_begin = json.loads(provider.requests[0].messages[-1]["content"])
    assert rendered_begin == {
        "category": "person",
        "event": "BEGIN",
        "variation_token": decision.prompt_nonce,
    }
    assert call.audit.sampling == decision
    assert "seed" not in json.dumps(messages)
    stored = (
        audit_writer.runs_root / "seeded-guesser-test" / "guesser-calls.jsonl"
    ).read_text()
    assert '"mode":"prompt_nonce_plus_provider_seed"' in stored
    assert f'"prompt_nonce":"{decision.prompt_nonce}"' in stored
    assert f'"seed":{decision.seed}' in stored


def test_unsupported_seed_route_still_receives_prompt_nonce(
    audit_writer,
    model_config,
    policy,
) -> None:
    unsupported_config = model_config.model_copy(
        update={"seed_capability": SeedCapability.UNSUPPORTED}
    )
    provider = FakeGameProvider(
        unsupported_config,
        [ask_payload("Is it a person?")],
    )
    guesser = Guesser(provider, audit_writer, unsupported_config, policy)
    audit_writer.prepare_run("unsupported-seed-guesser-test")
    decision = guesser_sampling_decision(
        capability=unsupported_config.seed_capability,
        base_seed=42,
        trial_number=2,
        turn_number=1,
    )

    guesser.next_action(
        run_id="unsupported-seed-guesser-test",
        episode_id="EP-" + "6" * 32,
        messages=initial_messages(base_seed=42, trial_number=2),
        sampling=decision,
    )

    assert provider.requests[0].seed is None
    assert json.loads(provider.requests[0].messages[1]["content"]) == {
        "category": "person",
        "event": "BEGIN",
        "variation_token": decision.prompt_nonce,
    }


@pytest.mark.parametrize(
    ("run_id", "begin_content"),
    [
        (
            "missing-variation-token",
            '{"category":"person","event":"BEGIN"}',
        ),
        (
            "mismatched-variation-token",
            '{"category":"person","event":"BEGIN","variation_token":"ASF23XSA"}',
        ),
    ],
)
def test_guesser_rejects_missing_or_mismatched_prompt_nonce_before_provider_call(
    audit_writer,
    model_config,
    policy,
    run_id: str,
    begin_content: str,
) -> None:
    provider = FakeGameProvider(model_config, [ask_payload("Is it a person?")])
    guesser = Guesser(provider, audit_writer, model_config, policy)
    audit_writer.prepare_run(run_id)
    messages = initial_messages()
    messages = (
        messages[0],
        {"role": "user", "content": begin_content},
    )

    with pytest.raises(GameConfigurationError) as failure:
        guesser.next_action(
            run_id=run_id,
            episode_id="EP-" + "7" * 32,
            messages=messages,
            sampling=sampling(model_config, 1),
        )

    assert failure.value.code == "guesser_variation_token_mismatch"
    assert provider.requests == []


def test_validator_is_independent_and_keeps_explanation_out_of_guesser_history(
    audit_writer,
    validator_config,
    subject,
    caplog,
) -> None:
    raw = json.dumps(
        {
            "answer": "YES",
            "explanation": "The spelling variant and description uniquely identify the target.",
        }
    )
    provider = FakeGameProvider(validator_config, [raw])
    validator = GuessValidator(provider, audit_writer, validator_config)
    audit_writer.prepare_run("validator-test")
    guess = parse_guesser_action_output(guess_payload("Albert Einstien"))
    call = validator.validate(
        run_id="validator-test",
        episode_id="EP-" + "2" * 32,
        subject=subject,
        guess=guess,
    )

    assert call.result.answer is OracleAnswer.YES
    assert call.call_id.startswith("VC-")
    sent = provider.requests[0]
    assert "tools" not in sent.model_dump(mode="json")
    assert subject.description in sent.messages[-1]["content"]
    assert call.result.explanation not in guess.model_dump_json()
    assert sent.session_id.startswith("deep20-validator-")
    assert caplog.records == []


def test_validator_retries_invalid_schema_once_with_exact_request(
    audit_writer,
    validator_config,
    subject,
) -> None:
    invalid = json.dumps(
        {
            "answer": "YES",
            "explanation": "candidate",
            "unexpected": "discarded",
        }
    )
    valid = json.dumps(
        {
            "answer": "YES",
            "explanation": "The spelling variant identifies the target.",
        }
    )
    provider = FakeGameProvider(validator_config, [invalid, valid])
    audit_writer.prepare_run("validator-recovery")
    guess = parse_guesser_action_output(guess_payload("Albert Einstien"))

    call = GuessValidator(provider, audit_writer, validator_config).validate(
        run_id="validator-recovery",
        episode_id="EP-" + "8" * 32,
        subject=subject,
        guess=guess,
    )

    assert provider.requests[0] == provider.requests[1]
    assert call.result.answer is OracleAnswer.YES
    assert call.audit.provider.recovery.recovered_calls == 1
    assert call.audit.provider.recovery.reasons[0].reason is (
        RecoveryReason.INVALID_VALIDATOR_OUTPUT
    )
    assert call.audit.provider.discarded_error_outputs[0].output == invalid
