from __future__ import annotations

import json
import threading
from types import SimpleNamespace

import httpx
import pytest
from deep20_oracle.config import EvidenceReviewConfig, OracleConfig
from deep20_oracle.errors import OracleProviderError
from deep20_oracle.models import OracleResult, RecoveryReason
from deep20_oracle.openrouter_provider import OpenRouterProvider
from deep20_oracle.provider import ProviderRequest
from openrouter.errors import ResponseValidationError


class FakeChoice:
    finish_reason = "stop"


class FakeResponse:
    def __init__(self) -> None:
        self.choices = [FakeChoice()]


class FakeHttpClient:
    def __init__(self, response: dict):
        self.last_json = response


class FakeChat:
    def __init__(self, http_client: FakeHttpClient, response: dict):
        self.http_client = http_client
        self.response = response
        self.calls: list[dict] = []

    def send(self, **kwargs):
        self.calls.append(kwargs)
        self.http_client.last_json = self.response
        return FakeResponse()


class FakeClient:
    def __init__(self, chat: FakeChat):
        self.chat = chat


class FailingChat:
    def __init__(self, http_client: FakeHttpClient):
        self.http_client = http_client

    def send(self, **kwargs):
        self.http_client.last_json = {
            "error": {
                "code": 404,
                "message": "No endpoints found that can handle the requested parameters.",
            }
        }
        self.http_client.last_status_code = 404
        raise RuntimeError("SDK HTTP error")


def test_openrouter_adapter_makes_one_search_and_schema_request() -> None:
    raw_output = json.dumps(
        {
            "answer": "UNKNOWN",
            "evidence": [],
        }
    )
    response = {
        "id": "response-1",
        "model": "openai/test-model",
        "provider": "openai",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "content": raw_output,
                    "annotations": [{"type": "url_citation", "url": "https://example.test"}],
                },
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "cost": 0.001,
            "prompt_tokens_details": {
                "cached_tokens": 8,
                "cache_write_tokens": 2,
            },
            "server_tool_use_details": {"web_search_requests": 1},
        },
    }
    config = OracleConfig(model="openai/test-model", provider="openai")
    provider = OpenRouterProvider.__new__(OpenRouterProvider)
    provider.config = config
    provider.http_client = FakeHttpClient(response)
    chat = FakeChat(provider.http_client, response)
    provider.client = FakeClient(chat)
    provider._lock = threading.Lock()

    exchange = provider.complete(
        ProviderRequest(
            messages=(
                {"role": "system", "content": "policy"},
                {"role": "user", "content": "data"},
            ),
            output_schema=OracleResult.model_json_schema(),
            session_id="oracle-session",
            prompt_cache_key="oracle-cache-key",
        )
    )

    assert len(chat.calls) == 1
    sent = chat.calls[0]
    assert sent["tools"] == [
        {
            "type": "openrouter:web_search",
            "parameters": {"max_results": 5, "engine": "parallel"},
        }
    ]
    assert sent["response_format"]["type"] == "json_schema"
    assert sent["response_format"]["json_schema"]["strict"] is True
    assert sent["provider"]["only"] == ["openai"]
    assert sent["provider"]["allow_fallbacks"] is False
    assert sent["session_id"] == "oracle-session"
    assert sent["prompt_cache_key"] == "oracle-cache-key-parallel"
    assert "require_parameters" not in sent["provider"]
    assert sent["retries"].strategy == "none"
    evidence_schema = sent["response_format"]["json_schema"]["schema"]["$defs"]["Evidence"]
    assert "format" not in evidence_schema["properties"]["source_url"]
    assert "maxLength" not in evidence_schema["properties"]["excerpt"]
    assert exchange.trace.usage.search_count == 1
    assert exchange.trace.usage.cached_input_tokens == 8
    assert exchange.trace.usage.cache_write_tokens == 2
    assert exchange.trace.http_status_code is None
    assert exchange.trace.finish_reason == "stop"
    assert exchange.trace.request_attempts == 1
    assert exchange.trace.annotations
    assert "api_key" not in json.dumps(exchange.trace.request)


def test_openrouter_adapter_omits_engine_for_automatic_search() -> None:
    config = OracleConfig(
        model="openai/test-model",
        provider="openai",
        parallel_search=False,
    )
    provider = OpenRouterProvider.__new__(OpenRouterProvider)
    provider.config = config

    sent = provider._request_payload(
        ProviderRequest(
            messages=({"role": "user", "content": "data"},),
            output_schema=OracleResult.model_json_schema(),
            prompt_cache_key="oracle-cache-key",
        )
    )

    assert sent["tools"] == [
        {
            "type": "openrouter:web_search",
            "parameters": {"max_results": 5},
        }
    ]
    assert sent["prompt_cache_key"] == "oracle-cache-key-auto"


def test_evidence_review_adapter_has_no_web_tool_and_uses_isolated_cache_suffix() -> None:
    config = EvidenceReviewConfig(
        model="openai/test-reviewer",
        provider="openai",
        reasoning_effort="medium",
    )
    provider = OpenRouterProvider.__new__(OpenRouterProvider)
    provider.config = config
    provider.enable_web_search = False

    sent = provider._request_payload(
        ProviderRequest(
            messages=({"role": "user", "content": "evidence data"},),
            output_schema={
                "type": "object",
                "properties": {"answer": {"type": "string"}},
            },
            response_schema_name="reviewer_result",
            prompt_cache_key="reviewer-cache-key",
        )
    )

    assert "tools" not in sent
    assert sent["reasoning_effort"] == "medium"
    assert sent["response_format"]["json_schema"]["name"] == "reviewer_result"
    assert sent["prompt_cache_key"] == "reviewer-cache-key-no-web"


def test_openrouter_adapter_preserves_http_error_response_in_trace() -> None:
    config = OracleConfig(model="openai/test-model", provider="openai")
    provider = OpenRouterProvider.__new__(OpenRouterProvider)
    provider.config = config
    provider.http_client = FakeHttpClient({})
    provider.http_client.last_status_code = None
    provider.http_client.request_attempts = 0
    provider.http_client.last_retry_after_ms = None
    provider.http_client.retry_after_ms = None
    provider.client = FakeClient(FailingChat(provider.http_client))
    provider._lock = threading.Lock()

    with pytest.raises(OracleProviderError) as failure:
        provider.complete(
            ProviderRequest(
                messages=({"role": "user", "content": "data"},),
                output_schema=OracleResult.model_json_schema(),
            )
        )

    trace = failure.value.details["provider_trace"]
    assert failure.value.code == "provider_not_found"
    assert trace["http_status_code"] == 404
    assert trace["response"]["error"]["code"] == 404
    assert trace["requested_model"] == "openai/test-model"
    assert trace["request_attempts"] == 1


def test_oracle_adapter_retries_503_without_changing_request(monkeypatch) -> None:
    raw_output = json.dumps({"answer": "UNKNOWN", "evidence": []})
    response = {
        "id": "response-1",
        "model": "openai/test-model",
        "provider": "openai",
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
            http_client.last_status_code = 503
            http_client.last_json = {
                "error": {
                    "code": 503,
                    "message": "No provider available",
                }
            }
            http_client.last_retry_after_ms = 500
            http_client.retry_after_ms = 500
            raise RuntimeError("SDK HTTP error")
        http_client.last_json = response
        http_client.last_status_code = 200
        http_client.last_retry_after_ms = None
        return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop")])

    sleeps = []
    monkeypatch.setattr(
        "deep20_oracle.openrouter_provider.time.sleep",
        sleeps.append,
    )
    provider = OpenRouterProvider.__new__(OpenRouterProvider)
    provider.config = OracleConfig(model="openai/test-model", provider="openai")
    provider.http_client = http_client
    provider.client = SimpleNamespace(chat=SimpleNamespace(send=send))
    provider._lock = threading.Lock()
    request = ProviderRequest(
        messages=({"role": "user", "content": "data"},),
        output_schema=OracleResult.model_json_schema(),
        session_id="oracle-session",
        prompt_cache_key="oracle-cache-key",
    )

    exchange = provider.complete(request)

    assert len(calls) == 2
    assert len(sleeps) == 1
    assert 0.5 <= sleeps[0] <= 1.5
    first_payload = {key: value for key, value in calls[0].items() if key != "retries"}
    second_payload = {key: value for key, value in calls[1].items() if key != "retries"}
    assert first_payload == second_payload
    assert exchange.trace.request_attempts == 2
    assert exchange.trace.retry_after_ms == 500


def test_oracle_adapter_retries_opaque_400_without_changing_request(
    monkeypatch,
) -> None:
    raw_output = json.dumps({"answer": "UNKNOWN", "evidence": []})
    response = {
        "id": "response-1",
        "model": "openai/test-model",
        "provider": "openai",
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
        "deep20_oracle.openrouter_provider.time.sleep",
        sleeps.append,
    )
    provider = OpenRouterProvider.__new__(OpenRouterProvider)
    provider.config = OracleConfig(model="openai/test-model", provider="openai")
    provider.http_client = http_client
    provider.client = SimpleNamespace(chat=SimpleNamespace(send=send))
    provider._lock = threading.Lock()
    request = ProviderRequest(
        messages=({"role": "user", "content": "data"},),
        output_schema=OracleResult.model_json_schema(),
        session_id="oracle-session",
        prompt_cache_key="oracle-cache-key",
    )

    exchange = provider.complete(request)

    assert len(calls) == 2
    assert len(sleeps) == 1
    assert 5.0 <= sleeps[0] <= 6.0
    first_payload = {key: value for key, value in calls[0].items() if key != "retries"}
    second_payload = {key: value for key, value in calls[1].items() if key != "retries"}
    assert first_payload == second_payload
    assert exchange.trace.request_attempts == 2
    assert exchange.trace.recovery.recovered_calls == 1
    assert exchange.trace.recovery.reasons[0].reason is RecoveryReason.HTTP_400


def test_oracle_adapter_retries_transport_disconnect_without_changing_request(
    monkeypatch,
) -> None:
    raw_output = json.dumps({"answer": "UNKNOWN", "evidence": []})
    response = {
        "id": "response-1",
        "model": "openai/test-model",
        "provider": "openai",
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
        "deep20_oracle.openrouter_provider.time.sleep",
        sleeps.append,
    )
    provider = OpenRouterProvider.__new__(OpenRouterProvider)
    provider.config = OracleConfig(model="openai/test-model", provider="openai")
    provider.http_client = http_client
    provider.client = SimpleNamespace(chat=SimpleNamespace(send=send))
    provider._lock = threading.Lock()
    request = ProviderRequest(
        messages=({"role": "user", "content": "data"},),
        output_schema=OracleResult.model_json_schema(),
        session_id="oracle-session",
        prompt_cache_key="oracle-cache-key",
    )

    exchange = provider.complete(request)

    assert len(calls) == 2
    assert len(sleeps) == 1
    assert 5.0 <= sleeps[0] <= 6.0
    first_payload = {key: value for key, value in calls[0].items() if key != "retries"}
    second_payload = {key: value for key, value in calls[1].items() if key != "retries"}
    assert first_payload == second_payload
    assert exchange.trace.request_attempts == 2


def test_oracle_adapter_retries_malformed_http_200_without_changing_request(
    monkeypatch,
) -> None:
    raw_output = json.dumps({"answer": "UNKNOWN", "evidence": []})
    completed = {
        "id": "response-1",
        "model": "openai/test-model",
        "provider": "openai",
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
    monkeypatch.setattr("deep20_oracle.openrouter_provider.time.sleep", sleeps.append)
    provider = OpenRouterProvider.__new__(OpenRouterProvider)
    provider.config = OracleConfig(model="openai/test-model", provider="openai")
    provider.http_client = http_client
    provider.client = SimpleNamespace(chat=SimpleNamespace(send=send))
    provider._lock = threading.Lock()
    request = ProviderRequest(
        messages=({"role": "user", "content": "trusted question"},),
        output_schema=OracleResult.model_json_schema(),
        session_id="oracle-session",
        prompt_cache_key="oracle-cache-key",
    )

    exchange = provider.complete(request)

    assert len(calls) == 2
    assert len(sleeps) == 1
    assert 5.0 <= sleeps[0] <= 6.0
    first_payload = {key: value for key, value in calls[0].items() if key != "retries"}
    second_payload = {key: value for key, value in calls[1].items() if key != "retries"}
    assert first_payload == second_payload
    assert exchange.raw_output == raw_output
    assert exchange.trace.request_attempts == 2
    assert exchange.trace.recovery.recovered_calls == 1
    assert exchange.trace.recovery.reasons[0].reason is RecoveryReason.MALFORMED_RESPONSE
    assert malformed_body not in json.dumps(exchange.trace.model_dump(mode="json"))


def test_oracle_adapter_retries_empty_response_and_sums_usage(monkeypatch) -> None:
    raw_output = json.dumps({"answer": "UNKNOWN", "evidence": []})
    empty = {
        "id": "response-empty",
        "model": "openai/test-model",
        "provider": "openai",
        "choices": [{"finish_reason": "stop", "message": {"content": ""}}],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 2,
            "cost": 0.0004,
            "server_tool_use_details": {"web_search_requests": 1},
        },
    }
    completed = {
        "id": "response-completed",
        "model": "openai/test-model",
        "provider": "openai",
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
            "server_tool_use_details": {"web_search_requests": 1},
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
    monkeypatch.setattr("deep20_oracle.openrouter_provider.time.sleep", sleeps.append)
    provider = OpenRouterProvider.__new__(OpenRouterProvider)
    provider.config = OracleConfig(model="openai/test-model", provider="openai")
    provider.http_client = http_client
    provider.client = SimpleNamespace(chat=SimpleNamespace(send=send))
    provider._lock = threading.Lock()
    request = ProviderRequest(
        messages=({"role": "user", "content": "data"},),
        output_schema=OracleResult.model_json_schema(),
        session_id="oracle-session",
        prompt_cache_key="oracle-cache-key",
    )

    exchange = provider.complete(request)

    assert len(calls) == 2
    assert sleeps == [1.0]
    first_payload = {key: value for key, value in calls[0].items() if key != "retries"}
    second_payload = {key: value for key, value in calls[1].items() if key != "retries"}
    assert first_payload == second_payload
    assert exchange.trace.usage.input_tokens == 21
    assert exchange.trace.usage.output_tokens == 7
    assert exchange.trace.usage.search_count == 2
    assert exchange.trace.recovery.retry_usage.input_tokens == 10
    assert exchange.trace.recovery.recovered_calls == 1
