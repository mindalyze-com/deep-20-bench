from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from deep20_benchmark.canary import (
    EchoCanaryExchange,
    EchoCanaryProviderError,
    EchoCanaryRequest,
    OpenRouterEchoCanaryProvider,
    run_startup_canaries,
)
from deep20_benchmark.catalog import (
    BenchmarkCatalogEntry,
    load_benchmark_catalog,
    load_model_catalog,
)
from deep20_benchmark.models import (
    BenchmarkId,
    BenchmarkLlmRole,
    BenchmarkModelId,
    BenchmarkModelSnapshot,
)
from deep20_oracle.models import ProviderUsage


class RecordingEchoProvider:
    def __init__(
        self,
        *,
        outputs: dict[BenchmarkLlmRole, str] | None = None,
        failures: dict[BenchmarkLlmRole, str] | None = None,
    ) -> None:
        self.outputs = outputs or {}
        self.failures = failures or {}
        self.requests: list[EchoCanaryRequest] = []
        self.closed = False

    def complete(self, request: EchoCanaryRequest) -> EchoCanaryExchange:
        self.requests.append(request)
        failure = self.failures.get(request.role)
        if failure is not None:
            raise EchoCanaryProviderError(
                "synthetic provider failure",
                code=failure,
            )
        return EchoCanaryExchange(
            output=self.outputs.get(request.role, "Hi"),
            requested_model=request.model,
            resolved_model=request.model,
            requested_provider=request.provider,
            resolved_provider=(
                "Google" if request.provider == "google-vertex" else request.provider
            ),
            finish_reason="stop",
            latency_ms=12,
            usage=ProviderUsage(
                input_tokens=8,
                output_tokens=1,
                cost_usd=Decimal("0.000001"),
            ),
        )

    def close(self) -> None:
        self.closed = True


def _configuration() -> tuple[BenchmarkModelSnapshot, BenchmarkCatalogEntry]:
    root = Path(__file__).parents[4]
    model = load_model_catalog(root / "config" / "models.yaml").model(BenchmarkModelId("M-0004"))
    benchmark = load_benchmark_catalog(root / "config" / "benchmarks.yaml").entry(
        BenchmarkId("B-0001")
    )
    return model, benchmark


def test_echo_payload_contains_only_plain_request_and_route_controls() -> None:
    request = EchoCanaryRequest(
        role=BenchmarkLlmRole.GUESSER,
        model="google/gemini-3.6-flash",
        provider="google-vertex",
        session_id="isolated-session",
        prompt_cache_key="isolated-cache",
    )

    payload = OpenRouterEchoCanaryProvider._request_payload(request)

    assert payload == {
        "model": "google/gemini-3.6-flash",
        "messages": [{"role": "user", "content": "Reply with exactly: Hi"}],
        "max_tokens": 512,
        "provider": {
            "only": ["google-vertex"],
            "allow_fallbacks": False,
            "require_parameters": True,
        },
        "session_id": "isolated-session",
        "prompt_cache_key": "isolated-cache",
        "x_open_router_metadata": "enabled",
        "stream": False,
    }


def test_startup_canaries_make_one_isolated_echo_call_per_role() -> None:
    model, benchmark = _configuration()
    provider = RecordingEchoProvider()

    result = run_startup_canaries(
        model,
        benchmark,
        api_key="unused",
        provider=provider,
    )

    assert result.valid is True
    assert tuple(role.role for role in result.roles) == tuple(BenchmarkLlmRole)
    assert all(role.valid and role.answer == "Hi" for role in result.roles)
    assert provider.closed is True
    assert len(provider.requests) == 5
    assert len({request.session_id for request in provider.requests}) == 5
    assert len({request.prompt_cache_key for request in provider.requests}) == 5
    assert all("startup-echo-canary-v1" in request.session_id for request in provider.requests)
    assert all(
        "startup-echo-canary-v1" in request.prompt_cache_key for request in provider.requests
    )
    serialized_result = result.model_dump_json()
    assert "Reply with exactly" not in serialized_result
    assert "synthetic_entity" not in serialized_result
    assert "Example Domain" not in serialized_result


def test_startup_canaries_report_failures_without_retaining_bad_output() -> None:
    model, benchmark = _configuration()
    provider = RecordingEchoProvider(
        outputs={BenchmarkLlmRole.JUDGE: "Hello"},
        failures={BenchmarkLlmRole.REVIEWER: "provider_http_503"},
    )

    result = run_startup_canaries(
        model,
        benchmark,
        api_key="unused",
        provider=provider,
    )

    failures = {role.role: role for role in result.roles if not role.valid}
    assert result.valid is False
    assert failures[BenchmarkLlmRole.REVIEWER].error_code == "provider_http_503"
    assert failures[BenchmarkLlmRole.JUDGE].error_code == "invalid_echo_output"
    assert failures[BenchmarkLlmRole.JUDGE].answer is None
    assert "Hello" not in result.model_dump_json()
    assert len(provider.requests) == 5
    assert provider.closed is True


def test_echo_exchange_reads_openrouter_provider_metadata() -> None:
    request = EchoCanaryRequest(
        role=BenchmarkLlmRole.GUESSER,
        model="google/gemini-3.6-flash",
        provider="google-vertex",
        session_id="isolated-session",
        prompt_cache_key="isolated-cache",
    )

    exchange = OpenRouterEchoCanaryProvider._exchange(
        request,
        {
            "model": request.model,
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"content": "Hi"},
                }
            ],
            "openrouter_metadata": {
                "attempts": [{"provider_name": "Google"}],
            },
            "usage": {
                "prompt_tokens": 8,
                "completion_tokens": 1,
                "cost": 0.000001,
            },
        },
        response_cache_status=None,
        latency_ms=12,
    )

    assert exchange.output == "Hi"
    assert exchange.resolved_provider == "Google"
    assert exchange.usage.input_tokens == 8
    assert exchange.usage.output_tokens == 1
