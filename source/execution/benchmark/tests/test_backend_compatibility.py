import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from deep20_backends.models import BackendError, Role
from deep20_benchmark.backend_adapters import (
    GameBackendAdapter,
    OpenRouterGameBackend,
    OpenRouterOracleBackend,
    OracleBackendAdapter,
)
from deep20_benchmark.catalog import load_benchmark_catalog, load_model_catalog
from deep20_benchmark.models import BenchmarkId, BenchmarkModelId
from deep20_game.errors import GameProviderError
from deep20_game.models import GameProviderRequest
from deep20_game.openrouter_provider import OpenRouterGameProvider
from deep20_oracle.config import RecoveryPolicy
from deep20_oracle.errors import OracleProviderError
from deep20_oracle.openrouter_provider import OpenRouterProvider
from deep20_oracle.provider import ProviderRequest

ROOT = Path(__file__).parents[4]


def configuration(game):
    recovery = RecoveryPolicy(max_request_attempts=1, max_elapsed_seconds=0,
        no_result_retries=0, invalid_output_retries=0, rate_limit_max_elapsed_seconds=0,
        rate_limit_max_request_attempts=1)
    if game:
        config = load_model_catalog(ROOT / "config/models.yaml").model(BenchmarkModelId("M-0003")).configuration
    else:
        config = load_benchmark_catalog(ROOT / "config/benchmarks.yaml").entry(BenchmarkId("B-0003")).oracle_configuration
    return config.model_copy(update={"recovery": recovery})


@pytest.mark.parametrize("game", [True, False])
def test_legacy_adapter_keeps_exact_provider_http_payload_and_audit_shape(game):
    config = configuration(game)
    requests = []
    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={
            "id": "recorded-completion", "created": 1, "object": "chat.completion", "system_fingerprint": None,
            "model": config.model, "provider": config.provider,
            "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": '{"answer":"UNKNOWN"}'}}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 5, "total_tokens": 25, "cost": 0.0001,
                      "server_tool_use_details": {"web_search_requests": 1 if not game else 0}},
        })
    provider = (OpenRouterGameProvider("offline-key", config, title="offline parity") if game else
                OpenRouterProvider("offline-key", config, title="offline parity"))
    provider.http_client._client.close()
    provider.http_client._client = httpx.Client(transport=httpx.MockTransport(handler))
    values = {"messages": ({"role": "user", "content": "same private input"},),
              "output_schema": {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"]},
              "session_id": "unchanged-session", "prompt_cache_key": "unchanged-key"}
    if game:
        request = GameProviderRequest(**values, schema_name="parity")
        adapter = GameBackendAdapter(OpenRouterGameBackend(provider), Role.GUESSER, config, record_backend=False)
    else:
        request = ProviderRequest(**values, max_web_search_requests=5, response_schema_name="parity")
        adapter = OracleBackendAdapter(OpenRouterOracleBackend(provider), Role.ORACLE, config, record_backend=False)
    try:
        direct = provider.complete(request)
        wrapped = adapter.complete(request)
    finally:
        provider.close()
    assert requests[0] == requests[1]
    assert direct.raw_output == wrapped.raw_output
    assert direct.trace.usage == wrapped.trace.usage
    assert direct.trace.model_dump().keys() == wrapped.trace.model_dump().keys()
    assert "backend" not in wrapped.trace.model_dump()
    assert wrapped.trace.request == direct.trace.request


@pytest.mark.parametrize("game", [True, False])
def test_wrapped_spending_rejection_keeps_its_code_and_is_never_retried(game):
    config = configuration(game)
    provider = (OpenRouterGameProvider("offline-key", config, title="offline budget") if game else
                OpenRouterProvider("offline-key", config, title="offline budget"))
    calls = []
    def rejected(**kwargs):
        calls.append(kwargs)
        try:
            raise BackendError("spending_cap_reached", "allowance exhausted")
        except BackendError as error:
            raise RuntimeError("SDK wrapped hook error") from error
    provider.client = SimpleNamespace(chat=SimpleNamespace(send=rejected))
    values = {"messages": ({"role": "user", "content": "fixture"},), "output_schema": {"type": "object"},
              "session_id": "session", "prompt_cache_key": "key"}
    request = GameProviderRequest(**values, schema_name="fixture") if game else ProviderRequest(**values)
    try:
        with pytest.raises(GameProviderError if game else OracleProviderError) as error:
            provider.complete(request)
    finally:
        provider.close()
    assert error.value.code == "spending_cap_reached"
    assert len(calls) == 1
