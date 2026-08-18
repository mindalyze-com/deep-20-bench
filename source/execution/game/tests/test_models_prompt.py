from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from deep20_benchmark.catalog import load_model_catalog
from deep20_benchmark.models import BenchmarkModelId
from deep20_game.config import (
    GamePolicy,
    ReasoningControl,
    load_game_policy,
    load_model_config,
)
from deep20_game.models import (
    GuesserAction,
    GuesserSuccessRecord,
    guesser_action_output_schema,
    guesser_action_required_formats,
    parse_guesser_action_output,
)
from deep20_game.prompt import (
    GUESSER_PROMPT_VERSION,
    append_visible_action,
    append_visible_format_error,
    append_visible_turn,
    format_error_message,
    guesser_system_prompt,
    initial_guesser_messages,
)
from pydantic import ValidationError


def test_action_schema_is_stable_and_fields_are_mutually_exclusive() -> None:
    ask = GuesserAction(
        action="ASK",
        question="Was this subject born before 1900?",
        name=None,
        description=None,
    )
    guess = GuesserAction(
        action="GUESS",
        question=None,
        name="Albert Einstein",
        description="The theoretical physicist associated with relativity.",
    )

    assert ask.model_dump(mode="json") == {
        "action": "ASK",
        "question": "Was this subject born before 1900?",
        "name": None,
        "description": None,
    }
    assert guess.action == "GUESS"
    with pytest.raises(ValidationError):
        GuesserAction(
            action="GUESS",
            question=None,
            name="Einstein",
            description=None,
        )


def test_game_contract_rejects_retired_versions() -> None:
    with pytest.raises(ValidationError, match="Input should be 9"):
        GamePolicy(version=8)
    with pytest.raises(ValidationError, match="Input should be 2"):
        GuesserSuccessRecord.model_validate({"schema_version": 1})


def test_action_output_schema_discriminates_inactive_null_fields() -> None:
    schema = guesser_action_output_schema()
    assert schema["type"] == "object"
    assert schema["required"] == ["result"]
    assert schema["additionalProperties"] is False
    branches = schema["properties"]["result"]["anyOf"]
    assert len(branches) == 2
    assert branches[0]["properties"]["action"]["const"] == "ASK"
    assert branches[0]["properties"]["name"] == {"type": "null"}
    assert branches[0]["properties"]["description"] == {"type": "null"}
    assert branches[1]["properties"]["action"]["const"] == "GUESS"
    assert branches[1]["properties"]["question"] == {"type": "null"}
    assert all(branch["additionalProperties"] is False for branch in branches)
    assert "oneOf" not in schema
    assert schema == guesser_action_output_schema()
    serialized_schema = json.dumps(schema).casefold()
    assert all(
        private_name not in serialized_schema
        for private_name in (
            "canonical_name",
            "aliases",
            "reference_url",
            "trusted_subject",
            "oracle",
            "validator",
            "evidence",
        )
    )


def test_enveloped_action_output_parses_to_the_visible_domain_action() -> None:
    action = parse_guesser_action_output(
        json.dumps(
            {
                "result": {
                    "action": "ASK",
                    "question": "Is the subject human?",
                    "name": None,
                    "description": None,
                }
            }
        )
    )

    assert action == GuesserAction(
        action="ASK",
        question="Is the subject human?",
        name=None,
        description=None,
    )
    with pytest.raises(ValidationError):
        parse_guesser_action_output(
            json.dumps(
                {
                    "result": {
                        "action": "ASK",
                        "question": "Is the subject human?",
                        "name": "",
                        "description": "",
                    }
                }
            )
        )


def test_visible_history_is_append_only_and_canonical() -> None:
    initial = initial_guesser_messages(50, "person", "ASF23XSA")
    action = GuesserAction(
        action="ASK",
        question="Is the subject a person?",
        name=None,
        description=None,
    )
    next_messages = append_visible_turn(initial, action, "YES")

    assert next_messages[: len(initial)] == initial
    assert next_messages[-2] == {
        "role": "assistant",
        "content": (
            '{"result":{"action":"ASK","description":null,"name":null,'
            '"question":"Is the subject a person?"}}'
        ),
    }
    assert next_messages[-1] == {"role": "user", "content": "YES"}
    assert initial[-1] == {
        "role": "user",
        "content": (
            '{"category":"person","event":"BEGIN","variation_token":"ASF23XSA"}'
        ),
    }
    assert "Albert Einstein" not in str(next_messages)


def test_visible_action_appends_assistant_output_without_unseen_answer() -> None:
    initial = initial_guesser_messages(50, "person", "ASF23XSA")
    action = GuesserAction(
        action="GUESS",
        question=None,
        name="Albert Einstein",
        description="The theoretical physicist associated with relativity.",
    )

    conversation = append_visible_action(initial, action)

    assert conversation[: len(initial)] == initial
    assert conversation[-1] == {
        "role": "assistant",
        "content": (
            '{"result":{"action":"GUESS","description":"The theoretical physicist associated '
            'with relativity.","name":"Albert Einstein","question":null}}'
        ),
    }


def test_format_error_feedback_is_fixed_and_contains_no_attempt_content() -> None:
    initial = initial_guesser_messages(50, "person", "ASF23XSA")
    messages = append_visible_format_error(initial)
    event = json.loads(messages[-1]["content"])

    assert messages[:-1] == initial
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == format_error_message()
    assert event["event"] == "FORMAT_ERROR"
    assert event["required_formats"] == guesser_action_required_formats()
    serialized = messages[-1]["content"]
    assert "Albert Einstein" not in serialized
    assert "validation" not in serialized.casefold()
    assert "right or wrong" not in serialized.casefold()


def test_initial_messages_include_prompt_nonce_only_in_begin_event() -> None:
    messages = initial_guesser_messages(50, "person", "ASF23XSA")

    assert "ASF23XSA" not in messages[0]["content"]
    assert json.loads(messages[1]["content"]) == {
        "category": "person",
        "event": "BEGIN",
        "variation_token": "ASF23XSA",
    }


def test_guesser_prompt_uses_guess_for_named_identity_confirmation() -> None:
    prompt = guesser_system_prompt(50)
    normalized_prompt = " ".join(prompt.split())

    assert (
        GUESSER_PROMPT_VERSION
        == "stateful-category-guesser-v10-unknown-evidence-guidance"
    )
    assert "Never use ASK to confirm a named candidate" in normalized_prompt
    assert (
        "When you are ready to name a candidate, use GUESS immediately."
        in normalized_prompt
    )
    assert "A correct GUESS costs zero counted questions" in normalized_prompt
    assert "an incorrect GUESS costs exactly one, the same as ASK" in normalized_prompt
    assert "initial BEGIN event includes an opaque variation_token" in normalized_prompt
    assert "FORMAT_ERROR" in normalized_prompt


def test_guesser_prompt_explains_unknown_without_private_adjudicator_state() -> None:
    normalized_prompt = " ".join(guesser_system_prompt(50).split())

    assert (
        "UNKNOWN is a valid answer meaning the factual adjudication system could not "
        "determine the proposition under its evidence policy."
        in normalized_prompt
    )
    assert (
        "Questions requiring proof of absence, exclusivity, completeness, exact counts, "
        "or subjective classification are more likely to return UNKNOWN."
        in normalized_prompt
    )
    assert "Prefer direct, positively verifiable properties when possible." in normalized_prompt
    assert all(
        private_term not in normalized_prompt.casefold()
        for private_term in (
            "oracle",
            "reviewer",
            "judge",
            "evidence excerpt",
            "search result",
            "trusted subject",
            "source_url",
        )
    )


def test_fixed_game_rules_require_category_disclosure_and_final_guess() -> None:
    with pytest.raises(ValidationError):
        GamePolicy(reveal_entity_type=False)
    with pytest.raises(ValidationError):
        GamePolicy(final_guess_after_limit=False)


def test_repository_game_and_model_configurations_are_valid() -> None:
    root = Path(__file__).parents[4]

    game_policy = load_game_policy(root / "config/game.yaml")
    assert game_policy.max_questions == 50
    assert game_policy.include_oracle_evidence is True
    assert game_policy.include_guesser_conversation is True
    guesser = load_model_config(root / "config/guesser.yaml")
    assert guesser.configuration_id == "gpt-5.6-luna-medium"
    assert guesser.seed_capability == "unsupported"
    assert (
        load_model_config(root / "config/guess-validator.yaml").configuration_id
        == "gpt-5.6-luna-validator"
    )


def test_repository_model_catalog_has_expected_active_ids() -> None:
    root = Path(__file__).parents[4]
    catalog = load_model_catalog(root / "config/models.yaml")

    assert tuple(catalog.models) == (
        *(f"M-{number:04d}" for number in range(1, 17)),
        "M-0101",
        "M-0104",
    )


def test_gpt_oss_benchmark_route_uses_reliable_structured_output_provider() -> None:
    root = Path(__file__).parents[4]
    configuration = (
        load_model_catalog(root / "config/models.yaml")
        .model(BenchmarkModelId("M-0002"))
        .configuration
    )

    assert configuration.model == "openai/gpt-oss-120b"
    assert configuration.provider == "cerebras"
    assert configuration.reasoning_effort == "high"
    assert configuration.max_output_tokens == 32_768
    assert configuration.prompt_cache.input_usd_per_million == Decimal("0.35")
    assert configuration.prompt_cache.cached_input_usd_per_million == Decimal("0.35")


def test_gpt_5_nano_benchmark_route_has_reasoning_output_headroom() -> None:
    root = Path(__file__).parents[4]
    configuration = (
        load_model_catalog(root / "config/models.yaml")
        .model(BenchmarkModelId("M-0003"))
        .configuration
    )

    assert configuration.model == "openai/gpt-5-nano"
    assert configuration.reasoning_effort == "medium"
    assert configuration.max_output_tokens == 32_768


@pytest.mark.parametrize("model_id", ["M-0011", "M-0013"])
def test_qwen_benchmark_routes_use_generic_reasoning_control(model_id: str) -> None:
    root = Path(__file__).parents[4]
    configuration = (
        load_model_catalog(root / "config/models.yaml")
        .model(BenchmarkModelId(model_id))
        .configuration
    )

    assert configuration.reasoning_control is ReasoningControl.GENERIC


@pytest.mark.parametrize(
    (
        "model_id",
        "display_name",
        "model_slug",
        "provider",
        "reasoning_effort",
        "max_output_tokens",
        "recovery_max_elapsed_seconds",
        "seed_capability",
        "input_price",
        "cached_input_price",
        "minimum_cacheable_tokens",
    ),
    [
        (
            "M-0001",
            "GPT-5.6 Luna (high)",
            "openai/gpt-5.6-luna",
            "openai",
            "high",
            32_768,
            300,
            "unsupported",
            Decimal("1.00"),
            Decimal("0.10"),
            1_024,
        ),
        (
            "M-0004",
            "Gemini 3.6 Flash (high)",
            "google/gemini-3.6-flash",
            "google-vertex",
            "high",
            32_768,
            300,
            "supported",
            Decimal("1.50"),
            Decimal("0.15"),
            1_024,
        ),
        (
            "M-0005",
            "Claude Sonnet 5 (high)",
            "anthropic/claude-sonnet-5",
            "anthropic",
            "high",
            32_768,
            300,
            "unsupported",
            Decimal("2.00"),
            Decimal("0.20"),
            1_024,
        ),
        (
            "M-0006",
            "Claude Opus 5 (high)",
            "anthropic/claude-opus-5",
            "anthropic",
            "high",
            32_768,
            300,
            "unsupported",
            Decimal("5.00"),
            Decimal("0.50"),
            1_024,
        ),
        (
            "M-0007",
            "Kimi K3 (high)",
            "moonshotai/kimi-k3",
            "moonshotai",
            "high",
            32_768,
            300,
            "unsupported",
            Decimal("3.00"),
            Decimal("0.30"),
            1_024,
        ),
        (
            "M-0008",
            "Grok 4.5 (high)",
            "x-ai/grok-4.5",
            "xai",
            "high",
            32_768,
            300,
            "supported",
            Decimal("2.00"),
            Decimal("0.30"),
            1_024,
        ),
        (
            "M-0009",
            "Llama 4 Maverick (non-thinking)",
            "meta-llama/llama-4-maverick",
            "parasail",
            "none",
            4_096,
            300,
            "supported",
            Decimal("0.35"),
            Decimal("0.17"),
            1_024,
        ),
        (
            "M-0010",
            "GPT-5.6 Sol (high)",
            "openai/gpt-5.6-sol",
            "openai",
            "high",
            32_768,
            300,
            "supported",
            Decimal("5.00"),
            Decimal("0.50"),
            1_024,
        ),
        (
            "M-0011",
            "Qwen3.7 Plus (high)",
            "qwen/qwen3.7-plus",
            "alibaba",
            "high",
            32_768,
            300,
            "supported",
            Decimal("0.32"),
            Decimal("0.064"),
            1_024,
        ),
        (
            "M-0012",
            "Mistral Medium 3.5 (high)",
            "mistralai/mistral-medium-3-5",
            "mistral",
            "high",
            32_768,
            300,
            "supported",
            Decimal("1.50"),
            Decimal("1.50"),
            1_024,
        ),
        (
            "M-0013",
            "Qwen3.8 Max (high)",
            "qwen/qwen3.8-max",
            "alibaba",
            "high",
            32_768,
            300,
            "supported",
            Decimal("2.00"),
            Decimal("0.25"),
            1_024,
        ),
        (
            "M-0014",
            "Claude Fable 5 (high)",
            "anthropic/claude-fable-5",
            "anthropic",
            "high",
            32_768,
            300,
            "unsupported",
            Decimal("10.00"),
            Decimal("1.00"),
            512,
        ),
        (
            "M-0015",
            "Grok 4.6 (high)",
            "x-ai/grok-4.6",
            "xai",
            "high",
            32_768,
            300,
            "supported",
            Decimal("2.00"),
            Decimal("0.50"),
            1_024,
        ),
        (
            "M-0016",
            "Gemini 3.7 Flash (high)",
            "google/gemini-3.7-flash",
            "google-ai-studio",
            "high",
            32_768,
            300,
            "supported",
            Decimal("0.75"),
            Decimal("0.075"),
            1_024,
        ),
        (
            "M-0101",
            "GPT-5.6 Luna (medium)",
            "openai/gpt-5.6-luna",
            "openai",
            "medium",
            32_768,
            300,
            "unsupported",
            Decimal("1.00"),
            Decimal("0.10"),
            1_024,
        ),
        (
            "M-0104",
            "Gemini 3.6 Flash (medium)",
            "google/gemini-3.6-flash",
            "google-vertex",
            "medium",
            32_768,
            300,
            "supported",
            Decimal("1.50"),
            Decimal("0.15"),
            1_024,
        ),
    ],
)
def test_active_benchmark_model_routes_are_fully_pinned(
    model_id: str,
    display_name: str,
    model_slug: str,
    provider: str,
    reasoning_effort: str,
    max_output_tokens: int,
    recovery_max_elapsed_seconds: int,
    seed_capability: str,
    input_price: Decimal,
    cached_input_price: Decimal,
    minimum_cacheable_tokens: int,
) -> None:
    root = Path(__file__).parents[4]
    model = load_model_catalog(root / "config/models.yaml").model(
        BenchmarkModelId(model_id)
    )

    assert model.display_name == display_name
    assert model.configuration.configuration_id == model_id
    assert model.configuration.model == model_slug
    assert model.configuration.provider == provider
    assert model.configuration.reasoning_effort == reasoning_effort
    assert model.configuration.allow_fallbacks is False
    assert model.configuration.max_output_tokens == max_output_tokens
    assert (
        model.configuration.recovery.max_elapsed_seconds
        == recovery_max_elapsed_seconds
    )
    assert model.configuration.recovery.max_request_attempts == 8
    assert model.configuration.recovery.no_result_retries == 1
    assert model.configuration.recovery.invalid_output_retries == 1
    assert model.configuration.seed_capability == seed_capability
    assert model.configuration.prompt_cache.input_usd_per_million == input_price
    assert (
        model.configuration.prompt_cache.cached_input_usd_per_million
        == cached_input_price
    )
    assert (
        model.configuration.prompt_cache.minimum_cacheable_tokens
        == minimum_cacheable_tokens
    )
    expected_cache_control = (
        "ephemeral_5m"
        if model_id in {"M-0005", "M-0006", "M-0013", "M-0014"}
        else "automatic"
    )
    assert model.configuration.prompt_cache.control == expected_cache_control


@pytest.mark.parametrize(
    "model_id",
    [
        "M-0001",
        "M-0002",
        "M-0003",
        "M-0004",
        "M-0005",
        "M-0006",
        "M-0007",
        "M-0008",
        "M-0009",
        "M-0010",
        "M-0011",
        "M-0012",
        "M-0013",
        "M-0014",
        "M-0015",
        "M-0016",
        "M-0101",
        "M-0104",
    ],
)
def test_active_model_configuration_stays_out_of_guesser_visible_projection(
    model_id: str,
) -> None:
    root = Path(__file__).parents[4]
    configuration = (
        load_model_catalog(root / "config/models.yaml")
        .model(BenchmarkModelId(model_id))
        .configuration
    )
    messages = initial_guesser_messages(50, "person", "ASF23XSA")
    serialized_messages = json.dumps(messages)

    assert json.loads(messages[1]["content"]) == {
        "category": "person",
        "event": "BEGIN",
        "variation_token": "ASF23XSA",
    }
    for private_control in (
        configuration.configuration_id,
        configuration.model,
        configuration.provider,
        str(configuration.max_output_tokens),
        str(configuration.timeout_seconds),
    ):
        assert private_control not in serialized_messages
    assert "reasoning_effort" not in serialized_messages
    assert "reasoning_control" not in serialized_messages
    if configuration.reasoning_effort != "none":
        assert configuration.reasoning_effort not in serialized_messages
