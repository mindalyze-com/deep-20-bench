import json
from decimal import Decimal

import httpx
import pytest
from deep20_backends.config import FixedMockSettings, OllamaSettings, ScriptedMockSettings
from deep20_backends.mock import MockBackend
from deep20_backends.models import BackendError, Message, MessageRole, ModelRequest, Role
from deep20_backends.ollama import OllamaBackend
from pydantic import ValidationError


def request(role=Role.VALIDATOR):
    return ModelRequest(
        role=role, messages=(Message(role=MessageRole.USER, content="fixture"),),
        output_schema={"type": "object"}, schema_name="fixture",
    )


@pytest.mark.parametrize("role", list(Role))
def test_fixed_mock_never_reports_provider_activity(role):
    backend = MockBackend(FixedMockSettings(response={"answer": "UNKNOWN"}))
    for _ in range(2):
        result = backend.complete(request(role))
        assert json.loads(result.content) == {"answer": "UNKNOWN"}
        assert result.observation.inference_requests == 0
        assert result.observation.usage.cost_usd == Decimal(0)
        assert result.observation.usage.search_requests == 0
        assert result.observation.resolved_provider is None


def test_script_exhaustion_has_no_fallback():
    backend = MockBackend(ScriptedMockSettings(responses=({"answer": "YES"}, {"answer": "NO"})))
    assert json.loads(backend.complete(request()).content)["answer"] == "YES"
    assert json.loads(backend.complete(request()).content)["answer"] == "NO"
    with pytest.raises(BackendError, match="exhausted") as raised:
        backend.complete(request())
    assert raised.value.code == "mock_script_exhausted"


def test_non_oracle_request_cannot_enable_research():
    with pytest.raises(ValidationError, match="only Oracle"):
        request().model_copy()  # The checked boundary below must use validation, not model_copy.
        ModelRequest.model_validate({**request().model_dump(), "max_search_requests": 1})


def ollama_client(*, model="fixture:latest", capabilities=("completion", "tools"), done=True):
    requests = []

    def respond(incoming):
        requests.append(incoming)
        if incoming.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "fixture:latest", "digest": "abc"}]})
        if incoming.url.path == "/api/show":
            return httpx.Response(200, json={
                "capabilities": list(capabilities), "model_info": {"fixture.context_length": 32768},
            })
        assert incoming.url.path == "/api/chat"
        return httpx.Response(200, json={
            "model": model, "message": {"role": "assistant", "content": '{"answer":"YES"}'},
            "done": done, "done_reason": "stop", "prompt_eval_count": 100, "eval_count": 10,
        })

    return httpx.Client(transport=httpx.MockTransport(respond)), requests


def test_ollama_uses_native_schema_without_sessions_or_private_metadata():
    client, requests = ollama_client()
    backend = OllamaBackend(OllamaSettings(model="fixture"), client=client)
    result = backend.complete(request())
    sent = json.loads(requests[-1].content)
    assert sent["format"] == {"type": "object"}
    assert sent["stream"] is False
    assert sent["messages"] == [{"role": "user", "content": "fixture"}]
    assert result.observation.model_digest == "abc"
    assert result.observation.usage.input_tokens == 100
    assert result.observation.usage.cached_input_tokens is None
    assert result.observation.usage.cost_usd is None
    assert "session_id" not in sent


def test_ollama_rejects_model_substitution():
    client, _ = ollama_client(model="different:latest")
    backend = OllamaBackend(OllamaSettings(model="fixture"), client=client)
    with pytest.raises(BackendError) as raised:
        backend.complete(request())
    assert raised.value.code == "ollama_route_mismatch"


def test_ollama_never_pulls_a_missing_model():
    client, requests = ollama_client()
    backend = OllamaBackend(OllamaSettings(model="absent"), client=client)
    with pytest.raises(BackendError) as raised:
        backend.complete(request())
    assert raised.value.code == "ollama_model_not_installed"
    assert [r.url.path for r in requests] == ["/api/tags"]


def test_ollama_rejects_large_input_before_generation():
    client, requests = ollama_client()
    backend = OllamaBackend(OllamaSettings(model="fixture"), client=client)
    large = request().model_copy(update={
        "messages": (Message(role=MessageRole.USER, content="a" * 33000),),
    })
    with pytest.raises(BackendError) as raised:
        backend.complete(large)
    assert raised.value.code == "ollama_context_limit"
    assert all(r.url.path != "/api/chat" for r in requests)


@pytest.mark.parametrize("url", ["https://ollama.com", "http://user:secret@localhost:11434"])
def test_ollama_settings_reject_remote_or_credential_endpoints(url):
    with pytest.raises(ValidationError):
        OllamaSettings(model="fixture", base_url=url)
