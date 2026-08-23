from __future__ import annotations

import json
import threading
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from deep20_game.audit import GameRunAuditWriter
from deep20_game.cache_probe import (
    load_cache_probe,
    run_cache_probe,
    write_cache_probe,
)
from deep20_game.config import (
    CacheControl,
    CachePolicy,
    ReasoningControl,
    StructuredOutputMode,
)
from deep20_game.errors import GameAuditError, GameProviderError
from deep20_game.models import (
    GameProviderRequest,
    guesser_action_output_schema,
)
from deep20_game.openrouter_provider import (
    OpenRouterGameProvider,
    _provider_failure_code,
)
from deep20_game.service_util import validate_game_trace
from deep20_oracle.models import RecoveryReason
from openrouter.errors import ResponseValidationError

from .conftest import FakeGameProvider, official_policy


def action_payload(question: str) -> str:
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


def test_cache_probe_proves_append_only_fresh_cache_read(
    tmp_path: Path,
    model_config,
    policy,
) -> None:
    provider = FakeGameProvider(
        model_config,
        [action_payload("First generated action?"), action_payload("Second generated action?")],
        traces=[
            {"input_tokens": 200, "cache_write_tokens": 200},
            {"input_tokens": 240, "cached_input_tokens": 200},
        ],
    )

    artifact = run_cache_probe(provider, model_config, policy)
    path = tmp_path / "probe.json"
    write_cache_probe(path, artifact)
    loaded = load_cache_probe(path, model_config)

    assert loaded.success is True
    assert loaded.second_trace is not None
    assert loaded.second_trace.usage.cached_input_tokens == 200
    assert provider.requests[1].messages[: len(provider.requests[0].messages)] == (
        provider.requests[0].messages
    )
    assert provider.requests[0].session_id == provider.requests[1].session_id
    assert provider.requests[0].prompt_cache_key == provider.requests[1].prompt_cache_key


def test_response_cache_replay_is_rejected(model_config) -> None:
    raw = action_payload("Question?")
    provider = FakeGameProvider(
        model_config,
        [raw],
        traces=[{"response_cache_status": "HIT", "output_tokens": 0}],
    )
    exchange = provider.complete(
        GameProviderRequest(
            messages=({"role": "user", "content": "BEGIN"},),
            output_schema=guesser_action_output_schema(),
            schema_name="guesser_action",
            session_id="probe",
            prompt_cache_key="cache-key",
        )
    )

    with pytest.raises(GameProviderError) as failure:
        validate_game_trace(exchange.trace, model_config)

    assert failure.value.code == "response_cache_replay"


def test_provider_slug_matches_resolved_provider_display_name(model_config) -> None:
    provider = FakeGameProvider(
        model_config,
        [action_payload("Question?")],
    )
    exchange = provider.complete(
        GameProviderRequest(
            messages=({"role": "user", "content": "BEGIN"},),
            output_schema=guesser_action_output_schema(),
            schema_name="guesser_action",
            session_id="probe",
            prompt_cache_key="cache-key",
        )
    )
    trace = exchange.trace.model_copy(
        update={
            "requested_provider": "google-ai-studio",
            "resolved_provider": "Google AI Studio",
        }
    )

    validate_game_trace(trace, model_config)


def test_google_vertex_slug_matches_google_display_name(model_config) -> None:
    provider = FakeGameProvider(
        model_config,
        [action_payload("Question?")],
    )
    exchange = provider.complete(
        GameProviderRequest(
            messages=({"role": "user", "content": "BEGIN"},),
            output_schema=guesser_action_output_schema(),
            schema_name="guesser_action",
            session_id="probe",
            prompt_cache_key="cache-key",
        )
    )
    trace = exchange.trace.model_copy(
        update={
            "requested_provider": "google-vertex",
            "resolved_provider": "Google",
        }
    )

    validate_game_trace(trace, model_config)


def test_different_resolved_provider_is_rejected(model_config) -> None:
    provider = FakeGameProvider(
        model_config,
        [action_payload("Question?")],
    )
    exchange = provider.complete(
        GameProviderRequest(
            messages=({"role": "user", "content": "BEGIN"},),
            output_schema=guesser_action_output_schema(),
            schema_name="guesser_action",
            session_id="probe",
            prompt_cache_key="cache-key",
        )
    )
    trace = exchange.trace.model_copy(
        update={
            "requested_provider": "google-ai-studio",
            "resolved_provider": "Anthropic",
        }
    )

    with pytest.raises(GameProviderError) as failure:
        validate_game_trace(trace, model_config)

    assert failure.value.code == "resolved_provider_mismatch"


def test_failed_probe_is_still_auditable(model_config, policy) -> None:
    provider = FakeGameProvider(
        model_config,
        [action_payload("First?"), action_payload("Second?")],
        traces=[
            {"input_tokens": 200, "cache_write_tokens": 200},
            {
                "input_tokens": 240,
                "cached_input_tokens": 0,
                "response_cache_status": "HIT",
                "output_tokens": 0,
            },
        ],
    )

    artifact = run_cache_probe(provider, model_config, policy)

    assert artifact.success is False
    assert artifact.first_trace is not None
    assert artifact.second_trace is not None
    assert "second probe request failed" in artifact.failure_reason
    assert artifact.failure_diagnostics is not None
    assert artifact.failure_diagnostics.causes[0].exception_type == "GameProviderError"
    assert artifact.failure_diagnostics.provider is not None
    assert artifact.failure_diagnostics.provider.response_cache_status == "HIT"
    assert "request" not in artifact.failure_diagnostics.provider.model_dump(mode="json")
    assert "response" not in artifact.failure_diagnostics.provider.model_dump(mode="json")


def test_official_writer_requires_required_policy_and_probe(
    tmp_path,
    monkeypatch,
    oracle_config,
    model_config,
    validator_config,
) -> None:
    writer = GameRunAuditWriter(
        tmp_path / "runs",
        game_policy=official_policy(),
        oracle_config=oracle_config,
        guesser_config=model_config,
        validator_config=validator_config,
        subject_catalog_hash="a" * 64,
        repository=tmp_path,
    )
    monkeypatch.setattr(writer, "_git", lambda arguments: "abc123")

    with pytest.raises(GameAuditError) as failure:
        writer.prepare_run("official")

    assert failure.value.code == "official_cache_policy_required"
    assert not (tmp_path / "runs" / "official").exists()


def test_openrouter_payload_has_sticky_keys_no_tools_or_response_cache(
    model_config,
) -> None:
    provider = OpenRouterGameProvider.__new__(OpenRouterGameProvider)
    provider.config = model_config
    request = GameProviderRequest(
        messages=({"role": "user", "content": "BEGIN"},),
        output_schema=guesser_action_output_schema(),
        schema_name="guesser_action",
        session_id="episode-session",
        prompt_cache_key="guesser-config-prompt-v1",
    )

    payload = provider._request_payload(request)

    assert set(payload) == {
        "model",
        "messages",
        "reasoning_effort",
        "max_tokens",
        "response_format",
        "provider",
        "session_id",
        "prompt_cache_key",
        "x_open_router_metadata",
        "stream",
    }
    assert payload["messages"] == [{"role": "user", "content": "BEGIN"}]
    assert payload["session_id"] == "episode-session"
    assert payload["prompt_cache_key"] == "guesser-config-prompt-v1"
    assert "tools" not in payload
    assert not {"subject", "oracle", "validator", "evidence"} & payload.keys()
    assert "cache_control" not in payload
    assert "http_headers" not in payload
    assert "seed" not in payload
    assert payload["provider"]["require_parameters"] is True
    assert payload["max_tokens"] == model_config.max_output_tokens
    assert "max_completion_tokens" not in payload
    assert payload["response_format"]["json_schema"]["strict"] is True
    strict_schema = payload["response_format"]["json_schema"]["schema"]
    assert strict_schema["type"] == "object"
    assert strict_schema["additionalProperties"] is False
    assert strict_schema["required"] == ["result"]
    branches = strict_schema["properties"]["result"]["anyOf"]
    assert branches[0]["properties"]["action"]["const"] == "ASK"
    assert branches[1]["properties"]["action"]["const"] == "GUESS"
    serialized_payload = json.dumps(payload)
    assert "transient_retry_max_seconds" not in serialized_payload

    provider.config = model_config.model_copy(
        update={
            "prompt_cache": model_config.prompt_cache.model_copy(
                update={
                    "policy": CachePolicy.BEST_EFFORT,
                    "control": CacheControl.EPHEMERAL_1H,
                }
            )
        }
    )
    assert provider._request_payload(request)["cache_control"] == {
        "type": "ephemeral",
        "ttl": "1h",
    }

    without_retries = provider.config.model_copy(
        update={
            "recovery": provider.config.recovery.model_copy(
                update={
                    "max_elapsed_seconds": 0,
                    "no_result_retries": 0,
                }
            )
        }
    )
    provider.config = without_retries
    assert provider._request_payload(request) == {
        **payload,
        "cache_control": {"type": "ephemeral", "ttl": "1h"},
    }


def test_openrouter_seeded_payload_requires_parameter_support(model_config) -> None:
    provider = OpenRouterGameProvider.__new__(OpenRouterGameProvider)
    provider.config = model_config
    request = GameProviderRequest(
        messages=({"role": "user", "content": "BEGIN"},),
        output_schema=guesser_action_output_schema(),
        schema_name="guesser_action",
        session_id="episode-session",
        prompt_cache_key="guesser-config-prompt-v1",
        seed=1_234_567,
    )

    payload = provider._request_payload(request)

    assert payload["seed"] == 1_234_567
    assert payload["provider"]["require_parameters"] is True
    assert payload["max_tokens"] == model_config.max_output_tokens
    assert "max_completion_tokens" not in payload


def test_openrouter_json_object_payload_keeps_local_contract_boundary(
    model_config,
) -> None:
    provider = OpenRouterGameProvider.__new__(OpenRouterGameProvider)
    provider.config = model_config.model_copy(
        update={"structured_output_mode": StructuredOutputMode.JSON_OBJECT}
    )
    request = GameProviderRequest(
        messages=({"role": "user", "content": "BEGIN"},),
        output_schema=guesser_action_output_schema(),
        schema_name="guesser_action",
        session_id="episode-session",
        prompt_cache_key="guesser-config-prompt-v1",
    )

    payload = provider._request_payload(request)

    assert payload["response_format"] == {"type": "json_object"}
    assert payload["provider"]["require_parameters"] is True
    assert payload["messages"] == [{"role": "user", "content": "BEGIN"}]
    assert "json_schema" not in json.dumps(payload)


def test_openrouter_non_reasoning_payload_omits_unsupported_effort(
    model_config,
) -> None:
    provider = OpenRouterGameProvider.__new__(OpenRouterGameProvider)
    provider.config = model_config.model_copy(update={"reasoning_effort": "none"})
    request = GameProviderRequest(
        messages=({"role": "user", "content": "BEGIN"},),
        output_schema=guesser_action_output_schema(),
        schema_name="guesser_action",
        session_id="episode-session",
        prompt_cache_key="guesser-config-prompt-v1",
        seed=1_234_567,
    )

    payload = provider._request_payload(request)

    assert "reasoning_effort" not in payload
    assert payload["seed"] == 1_234_567
    assert payload["provider"] == {
        "only": [model_config.provider],
        "allow_fallbacks": False,
        "require_parameters": True,
    }
    assert payload["messages"] == [{"role": "user", "content": "BEGIN"}]
    assert not {"subject", "oracle", "validator", "evidence"} & payload.keys()


def test_openrouter_generic_reasoning_payload_preserves_isolation_and_seed(
    model_config,
) -> None:
    provider = OpenRouterGameProvider.__new__(OpenRouterGameProvider)
    provider.config = model_config.model_copy(
        update={
            "reasoning_effort": "medium",
            "reasoning_control": ReasoningControl.GENERIC,
        }
    )
    request = GameProviderRequest(
        messages=({"role": "user", "content": "BEGIN"},),
        output_schema=guesser_action_output_schema(),
        schema_name="guesser_action",
        session_id="episode-session",
        prompt_cache_key="guesser-config-prompt-v1",
        seed=1_234_567,
    )

    payload = provider._request_payload(request)

    assert payload["reasoning"] == {"effort": "medium"}
    assert "reasoning_effort" not in payload
    assert payload["seed"] == 1_234_567
    assert payload["provider"] == {
        "only": [model_config.provider],
        "allow_fallbacks": False,
        "require_parameters": True,
    }
    assert payload["messages"] == [{"role": "user", "content": "BEGIN"}]
    assert not {"subject", "oracle", "validator", "evidence"} & payload.keys()
    assert "reasoning_control" in provider.config.model_dump(mode="json")
    assert "reasoning_control" not in model_config.model_dump(mode="json")


def test_game_adapter_disables_sdk_retry_for_project_policy(model_config) -> None:
    raw_output = action_payload("Is this subject human?")
    response = {
        "id": "response-1",
        "model": model_config.model,
        "provider": model_config.provider,
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": raw_output},
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.001},
    }
    http_client = SimpleNamespace(
        last_json=response,
        last_status_code=200,
        last_response_cache_status=None,
        request_attempts=1,
        last_retry_after_ms=None,
        retry_after_ms=None,
    )
    calls = []

    def send(**kwargs):
        calls.append(kwargs)
        http_client.last_json = response
        http_client.last_status_code = 200
        http_client.request_attempts = 1
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop")])

    provider = OpenRouterGameProvider.__new__(OpenRouterGameProvider)
    provider.config = model_config
    provider.http_client = http_client
    provider.client = SimpleNamespace(chat=SimpleNamespace(send=send))
    provider._lock = threading.Lock()

    exchange = provider.complete(
        GameProviderRequest(
            messages=({"role": "user", "content": "BEGIN"},),
            output_schema=guesser_action_output_schema(),
            schema_name="guesser_action",
            session_id="episode-session",
            prompt_cache_key="guesser-config-prompt-v1",
            seed=123,
        )
    )

    assert len(calls) == 1
    retry = calls[0]["retries"]
    assert retry.strategy == "none"
    assert exchange.trace.finish_reason == "stop"
    assert exchange.trace.request_attempts == 1


def test_game_adapter_retries_429_without_changing_request(
    model_config,
    monkeypatch,
) -> None:
    raw_output = action_payload("Is this subject human?")
    response = {
        "id": "response-1",
        "model": model_config.model,
        "provider": model_config.provider,
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": raw_output},
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.001},
    }
    http_client = SimpleNamespace(
        last_json=None,
        last_status_code=None,
        last_response_cache_status=None,
        request_attempts=0,
        last_retry_after_ms=None,
        retry_after_ms=None,
    )
    calls = []

    def send(**kwargs):
        calls.append(kwargs)
        http_client.request_attempts += 1
        if http_client.request_attempts == 1:
            http_client.last_status_code = 429
            http_client.last_json = {
                "error": {
                    "code": 429,
                    "message": "Provider returned error",
                }
            }
            http_client.last_retry_after_ms = 1_000
            http_client.retry_after_ms = 1_000
            raise RuntimeError("SDK HTTP error")
        http_client.last_json = response
        http_client.last_status_code = 200
        http_client.last_retry_after_ms = None
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop")])

    sleeps = []
    monkeypatch.setattr(
        "deep20_game.openrouter_provider.time.sleep",
        sleeps.append,
    )
    provider = OpenRouterGameProvider.__new__(OpenRouterGameProvider)
    provider.config = model_config
    provider.http_client = http_client
    provider.client = SimpleNamespace(chat=SimpleNamespace(send=send))
    provider._lock = threading.Lock()
    request = GameProviderRequest(
        messages=({"role": "user", "content": "BEGIN"},),
        output_schema=guesser_action_output_schema(),
        schema_name="guesser_action",
        session_id="episode-session",
        prompt_cache_key="guesser-config-prompt-v1",
        seed=123,
    )

    exchange = provider.complete(request)

    assert len(calls) == 2
    assert len(sleeps) == 1
    assert 1.0 <= sleeps[0] <= 2.0
    first_payload = {key: value for key, value in calls[0].items() if key != "retries"}
    second_payload = {key: value for key, value in calls[1].items() if key != "retries"}
    assert first_payload == second_payload
    assert exchange.trace.request_attempts == 2
    assert exchange.trace.retry_after_ms == 1_000


def test_game_adapter_retries_opaque_400_without_changing_visible_history(
    model_config,
    monkeypatch,
) -> None:
    raw_output = action_payload("Is this subject human?")
    response = {
        "id": "response-1",
        "model": model_config.model,
        "provider": model_config.provider,
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": raw_output},
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.001},
    }
    http_client = SimpleNamespace(
        last_json=None,
        last_status_code=None,
        last_response_cache_status=None,
        request_attempts=0,
        last_retry_after_ms=None,
        retry_after_ms=None,
    )
    calls = []

    def send(**kwargs):
        calls.append(kwargs)
        http_client.request_attempts += 1
        if http_client.request_attempts == 1:
            http_client.last_status_code = 400
            http_client.last_json = {
                "error": {
                    "code": "400",
                    "message": "Provider returned error",
                }
            }
            raise RuntimeError("SDK HTTP error")
        http_client.last_json = response
        http_client.last_status_code = 200
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop")])

    sleeps = []
    monkeypatch.setattr(
        "deep20_game.openrouter_provider.time.sleep",
        sleeps.append,
    )
    provider = OpenRouterGameProvider.__new__(OpenRouterGameProvider)
    provider.config = model_config
    provider.http_client = http_client
    provider.client = SimpleNamespace(chat=SimpleNamespace(send=send))
    provider._lock = threading.Lock()
    request = GameProviderRequest(
        messages=(
            {"role": "user", "content": "BEGIN opaque-variation-token"},
        ),
        output_schema=guesser_action_output_schema(),
        schema_name="guesser_action",
        session_id="episode-session",
        prompt_cache_key="guesser-config-prompt-v1",
        seed=123,
    )

    exchange = provider.complete(request)

    assert len(calls) == 2
    assert len(sleeps) == 1
    assert 5.0 <= sleeps[0] <= 6.0
    first_payload = {key: value for key, value in calls[0].items() if key != "retries"}
    second_payload = {key: value for key, value in calls[1].items() if key != "retries"}
    assert first_payload == second_payload
    assert first_payload["messages"] == list(request.messages)
    assert exchange.raw_output == raw_output
    assert exchange.trace.request_attempts == 2
    assert exchange.trace.recovery.recovered_calls == 1
    assert exchange.trace.recovery.reasons[0].reason is RecoveryReason.HTTP_400
    assert "Provider returned error" not in json.dumps(
        exchange.trace.model_dump(mode="json")
    )


def test_game_adapter_retries_transport_disconnect_without_changing_request(
    model_config,
    monkeypatch,
) -> None:
    raw_output = action_payload("Is this subject human?")
    response = {
        "id": "response-1",
        "model": model_config.model,
        "provider": model_config.provider,
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": raw_output},
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.001},
    }
    http_client = SimpleNamespace(
        last_json=None,
        last_status_code=None,
        last_response_cache_status=None,
        request_attempts=0,
        last_retry_after_ms=None,
        retry_after_ms=None,
    )
    calls = []

    def send(**kwargs):
        calls.append(kwargs)
        http_client.request_attempts += 1
        if http_client.request_attempts == 1:
            raise httpx.RemoteProtocolError("peer closed response")
        http_client.last_json = response
        http_client.last_status_code = 200
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop")])

    sleeps = []
    monkeypatch.setattr(
        "deep20_game.openrouter_provider.time.sleep",
        sleeps.append,
    )
    provider = OpenRouterGameProvider.__new__(OpenRouterGameProvider)
    provider.config = model_config
    provider.http_client = http_client
    provider.client = SimpleNamespace(chat=SimpleNamespace(send=send))
    provider._lock = threading.Lock()
    request = GameProviderRequest(
        messages=({"role": "user", "content": "BEGIN"},),
        output_schema=guesser_action_output_schema(),
        schema_name="guesser_action",
        session_id="episode-session",
        prompt_cache_key="guesser-config-prompt-v1",
        seed=123,
    )

    exchange = provider.complete(request)

    assert len(calls) == 2
    assert len(sleeps) == 1
    assert 5.0 <= sleeps[0] <= 6.0
    first_payload = {key: value for key, value in calls[0].items() if key != "retries"}
    second_payload = {key: value for key, value in calls[1].items() if key != "retries"}
    assert first_payload == second_payload
    assert exchange.trace.request_attempts == 2


def test_game_adapter_retries_malformed_http_200_without_changing_visible_history(
    model_config,
    monkeypatch,
) -> None:
    raw_output = action_payload("Is this subject human?")
    completed = {
        "id": "response-1",
        "model": model_config.model,
        "provider": model_config.provider,
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": raw_output},
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.001},
    }
    malformed_body = '{"malformed-output-marker":'
    malformed_response = httpx.Response(
        200,
        text=malformed_body,
        request=httpx.Request("POST", "https://openrouter.example.test"),
    )
    http_client = SimpleNamespace(
        last_json=None,
        last_status_code=None,
        last_response_cache_status=None,
        request_attempts=0,
        last_retry_after_ms=None,
        retry_after_ms=None,
    )
    calls = []

    def send(**kwargs):
        calls.append(kwargs)
        http_client.request_attempts += 1
        http_client.last_status_code = 200
        if http_client.request_attempts == 1:
            http_client.last_json = None
            raise ResponseValidationError(
                "Response validation failed",
                malformed_response,
                ValueError("EOF while parsing a value"),
            )
        http_client.last_json = completed
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop")])

    sleeps = []
    monkeypatch.setattr("deep20_game.openrouter_provider.time.sleep", sleeps.append)
    provider = OpenRouterGameProvider.__new__(OpenRouterGameProvider)
    provider.config = model_config
    provider.http_client = http_client
    provider.client = SimpleNamespace(chat=SimpleNamespace(send=send))
    provider._lock = threading.Lock()
    request = GameProviderRequest(
        messages=({"role": "user", "content": "BEGIN opaque-variation-token"},),
        output_schema=guesser_action_output_schema(),
        schema_name="guesser_action",
        session_id="episode-session",
        prompt_cache_key="guesser-config-prompt-v1",
        seed=123,
    )

    exchange = provider.complete(request)

    assert len(calls) == 2
    assert len(sleeps) == 1
    assert 5.0 <= sleeps[0] <= 6.0
    first_payload = {key: value for key, value in calls[0].items() if key != "retries"}
    second_payload = {key: value for key, value in calls[1].items() if key != "retries"}
    assert first_payload == second_payload
    assert first_payload["messages"] == list(request.messages)
    assert exchange.raw_output == raw_output
    assert exchange.trace.request_attempts == 2
    assert exchange.trace.recovery.recovered_calls == 1
    assert exchange.trace.recovery.reasons[0].reason is RecoveryReason.MALFORMED_RESPONSE
    assert malformed_body not in json.dumps(exchange.trace.model_dump(mode="json"))


def test_game_adapter_retries_empty_stop_response_and_sums_usage(
    model_config,
    monkeypatch,
) -> None:
    raw_output = action_payload("Is this subject human?")
    empty = {
        "id": "response-empty",
        "model": model_config.model,
        "provider": model_config.provider,
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": ""},
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 2,
            "cost": 0.0004,
            "prompt_tokens_details": {"cached_tokens": 2},
            "completion_tokens_details": {"reasoning_tokens": 2},
        },
    }
    completed = {
        "id": "response-completed",
        "model": model_config.model,
        "provider": model_config.provider,
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": raw_output},
            }
        ],
        "usage": {
            "prompt_tokens": 11,
            "completion_tokens": 5,
            "cost": 0.001,
            "prompt_tokens_details": {"cached_tokens": 3},
        },
    }
    http_client = SimpleNamespace(
        last_json=None,
        last_status_code=None,
        last_response_cache_status=None,
        request_attempts=0,
        last_retry_after_ms=None,
        retry_after_ms=None,
    )
    calls = []

    def send(**kwargs):
        calls.append(kwargs)
        http_client.request_attempts += 1
        response = empty if http_client.request_attempts == 1 else completed
        http_client.last_json = response
        http_client.last_status_code = 200
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop")])

    sleeps = []
    monkeypatch.setattr(
        "deep20_game.openrouter_provider.time.sleep",
        sleeps.append,
    )
    provider = OpenRouterGameProvider.__new__(OpenRouterGameProvider)
    provider.config = model_config
    provider.http_client = http_client
    provider.client = SimpleNamespace(chat=SimpleNamespace(send=send))
    provider._lock = threading.Lock()
    request = GameProviderRequest(
        messages=({"role": "user", "content": "BEGIN"},),
        output_schema=guesser_action_output_schema(),
        schema_name="guesser_action",
        session_id="episode-session",
        prompt_cache_key="guesser-config-prompt-v1",
        seed=123,
    )

    exchange = provider.complete(request)

    assert len(calls) == 2
    assert sleeps == [1.0]
    first_payload = {key: value for key, value in calls[0].items() if key != "retries"}
    second_payload = {key: value for key, value in calls[1].items() if key != "retries"}
    assert first_payload == second_payload
    assert exchange.trace.request_attempts == 2
    assert exchange.trace.usage.input_tokens == 21
    assert exchange.trace.usage.cached_input_tokens == 5
    assert exchange.trace.usage.output_tokens == 7
    assert exchange.trace.usage.reasoning_tokens == 2
    assert exchange.trace.usage.cost_usd == Decimal("0.0014")


def test_game_adapter_retries_error_finish_without_changing_request(
    model_config,
    monkeypatch,
) -> None:
    raw_output = action_payload("Is this subject human?")
    failed = {
        "id": "response-error",
        "model": model_config.model,
        "provider": model_config.provider,
        "choices": [
            {
                "finish_reason": "error",
                "message": {"content": ""},
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 3,
            "cost": 0,
            "completion_tokens_details": {"reasoning_tokens": 3},
        },
    }
    completed = {
        "id": "response-completed",
        "model": model_config.model,
        "provider": model_config.provider,
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": raw_output},
            }
        ],
        "usage": {"prompt_tokens": 11, "completion_tokens": 5, "cost": 0.001},
    }
    http_client = SimpleNamespace(
        last_json=None,
        last_status_code=None,
        last_response_cache_status=None,
        request_attempts=0,
        last_retry_after_ms=None,
        retry_after_ms=None,
    )
    calls = []

    def send(**kwargs):
        calls.append(kwargs)
        http_client.request_attempts += 1
        response = failed if http_client.request_attempts == 1 else completed
        http_client.last_json = response
        http_client.last_status_code = 200
        finish_reason = "error" if http_client.request_attempts == 1 else "stop"
        return SimpleNamespace(
            choices=[SimpleNamespace(finish_reason=finish_reason)]
        )

    sleeps = []
    monkeypatch.setattr(
        "deep20_game.openrouter_provider.time.sleep",
        sleeps.append,
    )
    provider = OpenRouterGameProvider.__new__(OpenRouterGameProvider)
    provider.config = model_config
    provider.http_client = http_client
    provider.client = SimpleNamespace(chat=SimpleNamespace(send=send))
    provider._lock = threading.Lock()
    request = GameProviderRequest(
        messages=({"role": "user", "content": "BEGIN"},),
        output_schema=guesser_action_output_schema(),
        schema_name="guesser_action",
        session_id="episode-session",
        prompt_cache_key="guesser-config-prompt-v1",
        seed=123,
    )

    exchange = provider.complete(request)

    assert len(calls) == 2
    assert sleeps == [1.0]
    first_payload = {key: value for key, value in calls[0].items() if key != "retries"}
    second_payload = {key: value for key, value in calls[1].items() if key != "retries"}
    assert first_payload == second_payload
    assert exchange.trace.request_attempts == 2
    assert exchange.trace.usage.input_tokens == 21
    assert exchange.trace.usage.output_tokens == 8
    assert exchange.trace.usage.reasoning_tokens == 3
    assert exchange.trace.usage.cost_usd == Decimal("0.001")


def test_game_adapter_fails_output_limit_fast_without_retry(
    model_config,
    monkeypatch,
) -> None:
    limited = {
        "id": "response-limited",
        "model": model_config.model,
        "provider": model_config.provider,
        "choices": [
            {
                "finish_reason": "length",
                "message": {"content": "runaway first attempt"},
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 4_096,
            "cost": 0.004,
            "completion_tokens_details": {"reasoning_tokens": 400},
        },
    }
    http_client = SimpleNamespace(
        last_json=None,
        last_status_code=None,
        last_response_cache_status=None,
        request_attempts=0,
        last_retry_after_ms=None,
        retry_after_ms=None,
    )
    calls = []

    def send(**kwargs):
        calls.append(kwargs)
        http_client.request_attempts += 1
        http_client.last_json = limited
        http_client.last_status_code = 200
        return SimpleNamespace(
            choices=[SimpleNamespace(finish_reason="length")]
        )

    sleeps = []
    monkeypatch.setattr(
        "deep20_game.openrouter_provider.time.sleep",
        sleeps.append,
    )
    provider = OpenRouterGameProvider.__new__(OpenRouterGameProvider)
    provider.config = model_config
    provider.http_client = http_client
    provider.client = SimpleNamespace(chat=SimpleNamespace(send=send))
    provider._lock = threading.Lock()
    request = GameProviderRequest(
        messages=({"role": "user", "content": "BEGIN"},),
        output_schema=guesser_action_output_schema(),
        schema_name="guesser_action",
        session_id="episode-session",
        prompt_cache_key="guesser-config-prompt-v1",
        seed=None,
    )

    with pytest.raises(GameProviderError) as excinfo:
        provider.complete(request)

    assert excinfo.value.code == "provider_output_limit_exceeded"
    assert len(calls) == 1
    assert sleeps == []
    trace = excinfo.value.details["provider_trace"]
    assert trace["recovery"]["exhausted_retries"] == 1
    reasons = [entry["reason"] for entry in trace["recovery"]["reasons"]]
    assert reasons == [RecoveryReason.OUTPUT_LIMIT_EXCEEDED.value]


def test_game_adapter_does_not_retry_empty_response_when_retries_are_disabled(
    model_config,
    monkeypatch,
) -> None:
    empty = {
        "id": "response-empty",
        "model": model_config.model,
        "provider": model_config.provider,
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": ""},
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 2, "cost": 0.0004},
    }
    http_client = SimpleNamespace(
        last_json=empty,
        last_status_code=200,
        last_response_cache_status=None,
        request_attempts=0,
        last_retry_after_ms=None,
        retry_after_ms=None,
    )
    calls = []

    def send(**kwargs):
        calls.append(kwargs)
        http_client.request_attempts += 1
        http_client.last_json = empty
        http_client.last_status_code = 200
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop")])

    sleeps = []
    monkeypatch.setattr(
        "deep20_game.openrouter_provider.time.sleep",
        sleeps.append,
    )
    provider = OpenRouterGameProvider.__new__(OpenRouterGameProvider)
    provider.config = model_config.model_copy(
        update={
            "recovery": model_config.recovery.model_copy(
                update={
                    "max_elapsed_seconds": 0,
                    "no_result_retries": 0,
                }
            )
        }
    )
    provider.http_client = http_client
    provider.client = SimpleNamespace(chat=SimpleNamespace(send=send))
    provider._lock = threading.Lock()

    with pytest.raises(GameProviderError) as failure:
        provider.complete(
            GameProviderRequest(
                messages=({"role": "user", "content": "BEGIN"},),
                output_schema=guesser_action_output_schema(),
                schema_name="guesser_action",
                session_id="episode-session",
                prompt_cache_key="guesser-config-prompt-v1",
            )
        )

    assert failure.value.code == "provider_empty_response"
    assert len(calls) == 1
    assert sleeps == []


def test_game_adapter_classifies_output_ceiling_separately(model_config) -> None:
    response = {
        "id": "response-1",
        "model": model_config.model,
        "provider": model_config.provider,
        "choices": [
            {
                "finish_reason": "length",
                "message": {"content": "runaway final attempt"},
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": model_config.max_output_tokens,
            "cost": 0.001,
        },
    }
    http_client = SimpleNamespace(
        last_json=response,
        last_status_code=200,
        last_response_cache_status=None,
        request_attempts=1,
        last_retry_after_ms=None,
        retry_after_ms=None,
    )

    def send(**kwargs):
        del kwargs
        http_client.last_json = response
        http_client.last_status_code = 200
        http_client.request_attempts = 1
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="length")])

    provider = OpenRouterGameProvider.__new__(OpenRouterGameProvider)
    provider.config = model_config
    provider.http_client = http_client
    provider.client = SimpleNamespace(chat=SimpleNamespace(send=send))
    provider._lock = threading.Lock()

    with pytest.raises(GameProviderError) as failure:
        provider.complete(
            GameProviderRequest(
                messages=({"role": "user", "content": "BEGIN"},),
                output_schema=guesser_action_output_schema(),
                schema_name="guesser_action",
                session_id="episode-session",
                prompt_cache_key="guesser-config-prompt-v1",
            )
        )

    assert failure.value.code == "provider_output_limit_exceeded"
    trace = failure.value.details["provider_trace"]
    assert trace["finish_reason"] == "length"
    assert trace["request_attempts"] == 1
    assert trace["raw_output"] == "runaway final attempt"


@pytest.mark.parametrize(
    ("raw_response", "status_code", "expected"),
    [
        (
            {
                "error": {
                    "code": 429,
                    "message": "request text must not become the durable failure code",
                    "metadata": {"error_type": "rate_limit_exceeded"},
                }
            },
            429,
            "provider_rate_limited",
        ),
        (
            {"error_type": "provider_unavailable"},
            200,
            "provider_unavailable",
        ),
        (
            {"error": {"error_type": "invalid_prompt"}},
            400,
            "provider_invalid_request",
        ),
        (
            {"private_subject": "must remain private"},
            503,
            "provider_overloaded",
        ),
        (
            {"error": {"message": "unrecognized provider failure"}},
            520,
            "provider_request_failed",
        ),
    ],
)
def test_provider_failure_codes_are_stable_and_credential_free(
    raw_response,
    status_code,
    expected,
) -> None:
    code = _provider_failure_code(raw_response, status_code)

    assert code == expected
    assert "request text" not in code
    assert "private_subject" not in code
