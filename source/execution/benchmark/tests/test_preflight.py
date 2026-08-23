from pathlib import Path
from urllib.error import URLError

import pytest
from deep20_benchmark.canary import run_guesser_canary
from deep20_benchmark.catalog import load_benchmark_catalog, load_model_catalog
from deep20_benchmark.models import BenchmarkId, BenchmarkLlmRole, BenchmarkModelId
from deep20_benchmark.preflight import (
    OpenRouterEndpoint,
    OpenRouterEndpointData,
    validate_catalog_routes,
    validate_catalog_routes_with_retry,
    validate_execution_routes,
)
from deep20_game.errors import GameProviderError
from deep20_game.models import GameProviderExchange, GameProviderRequest
from deep20_oracle.config import ProviderRouting, TokenLimitParameter
from deep20_oracle.models import ProviderTrace
from deep20_oracle.util import canonical_json


class FakeRouteMetadata:
    def __init__(self, providers: dict[str, str], limits: dict[str, int]) -> None:
        self.providers = providers
        self.limits = limits

    def endpoints(self, model: str) -> OpenRouterEndpointData:
        return OpenRouterEndpointData(
            id=model,
            endpoints=(
                OpenRouterEndpoint(
                    provider_name=self.providers[model],
                    tag=self.providers[model],
                    max_completion_tokens=self.limits[model],
                    supported_parameters=(
                        "max_tokens",
                        "response_format",
                        "seed",
                        "structured_outputs",
                    ),
                    status=0,
                ),
            ),
        )


def test_catalog_route_preflight_accepts_exact_active_routes() -> None:
    root = Path(__file__).parents[4]
    catalog = load_model_catalog(root / "config" / "models.yaml")
    providers = {
        entry.configuration.model: entry.configuration.provider
        for entry in catalog.models.values()
    }
    limits = {
        entry.configuration.model: entry.configuration.max_output_tokens
        for entry in catalog.models.values()
    }

    result = validate_catalog_routes(
        catalog,
        FakeRouteMetadata(providers, limits),
    )

    assert result.valid is True
    assert len(result.routes) == len(catalog.models)
    assert all(route.valid for route in result.routes)


def test_catalog_route_preflight_can_check_only_the_execution_model() -> None:
    root = Path(__file__).parents[4]
    catalog = load_model_catalog(root / "config" / "models.yaml")
    selected = catalog.models["M-0001"].configuration

    result = validate_catalog_routes(
        catalog,
        FakeRouteMetadata(
            {selected.model: selected.provider},
            {selected.model: selected.max_output_tokens},
        ),
        model_ids=(BenchmarkModelId("M-0001"),),
    )

    assert result.valid is True
    assert tuple(str(route.model_id) for route in result.routes) == ("M-0001",)


def test_catalog_route_preflight_matches_provider_slug_to_endpoint_tag() -> None:
    root = Path(__file__).parents[4]
    catalog = load_model_catalog(root / "config" / "models.yaml")
    selected = catalog.models["M-0004"].configuration

    class GoogleVertexRouteMetadata:
        def endpoints(self, model: str) -> OpenRouterEndpointData:
            return OpenRouterEndpointData(
                id=model,
                endpoints=(
                    OpenRouterEndpoint(
                        provider_name="Google",
                        tag="google-vertex/global",
                        max_completion_tokens=65_536,
                        supported_parameters=(
                            "max_tokens",
                            "response_format",
                            "seed",
                            "structured_outputs",
                        ),
                        status=0,
                    ),
                ),
            )

    result = validate_catalog_routes(
        catalog,
        GoogleVertexRouteMetadata(),
        model_ids=(BenchmarkModelId("M-0004"),),
    )

    assert selected.provider == "google-vertex"
    assert result.valid is True
    assert result.routes[0].active_endpoint_count == 1


def test_catalog_route_preflight_omits_capability_issues_for_inactive_route() -> None:
    root = Path(__file__).parents[4]
    catalog = load_model_catalog(root / "config" / "models.yaml")

    class InactiveGoogleVertexRouteMetadata:
        def endpoints(self, model: str) -> OpenRouterEndpointData:
            return OpenRouterEndpointData(
                id=model,
                endpoints=(
                    OpenRouterEndpoint(
                        provider_name="Google",
                        tag="google-vertex/global",
                        max_completion_tokens=65_536,
                        supported_parameters=(
                            "max_tokens",
                            "response_format",
                            "seed",
                            "structured_outputs",
                        ),
                        status=-2,
                    ),
                ),
            )

    result = validate_catalog_routes(
        catalog,
        InactiveGoogleVertexRouteMetadata(),
        model_ids=(BenchmarkModelId("M-0004"),),
    )

    assert result.valid is False
    assert result.routes[0].issues == (
        "configured exact provider has no active endpoint",
    )


def test_catalog_route_preflight_accepts_json_object_route_without_strict_schema() -> None:
    root = Path(__file__).parents[4]
    catalog = load_model_catalog(root / "config" / "models.yaml")

    class JsonObjectRouteMetadata:
        def endpoints(self, model: str) -> OpenRouterEndpointData:
            return OpenRouterEndpointData(
                id=model,
                endpoints=(
                    OpenRouterEndpoint(
                        provider_name="Stealth",
                        tag="stealth",
                        max_completion_tokens=131_072,
                        supported_parameters=(
                            "max_tokens",
                            "reasoning_effort",
                            "response_format",
                        ),
                        status=0,
                    ),
                ),
            )

    result = validate_catalog_routes(
        catalog,
        JsonObjectRouteMetadata(),
        model_ids=(BenchmarkModelId("M-0017"),),
    )

    assert result.valid is True
    assert result.routes[0].issues == ()


def test_catalog_route_preflight_still_requires_schema_support_for_strict_route() -> None:
    root = Path(__file__).parents[4]
    catalog = load_model_catalog(root / "config" / "models.yaml")

    class NonStrictRouteMetadata:
        def endpoints(self, model: str) -> OpenRouterEndpointData:
            return OpenRouterEndpointData(
                id=model,
                endpoints=(
                    OpenRouterEndpoint(
                        provider_name="OpenAI",
                        tag="openai",
                        max_completion_tokens=65_536,
                        supported_parameters=(
                            "max_tokens",
                            "reasoning_effort",
                            "response_format",
                        ),
                        status=0,
                    ),
                ),
            )

    result = validate_catalog_routes(
        catalog,
        NonStrictRouteMetadata(),
        model_ids=(BenchmarkModelId("M-0001"),),
    )

    assert result.valid is False
    assert result.routes[0].issues == (
        "exact route does not advertise strict structured output",
    )


def test_catalog_route_preflight_rejects_provider_or_limit_mismatch() -> None:
    root = Path(__file__).parents[4]
    catalog = load_model_catalog(root / "config" / "models.yaml")
    providers = {
        entry.configuration.model: entry.configuration.provider
        for entry in catalog.models.values()
    }
    limits = {
        entry.configuration.model: entry.configuration.max_output_tokens
        for entry in catalog.models.values()
    }
    selected = catalog.models["M-0001"].configuration
    providers[selected.model] = "different-provider"
    limits[selected.model] = 128

    result = validate_catalog_routes(
        catalog,
        FakeRouteMetadata(providers, limits),
    )

    failed = next(route for route in result.routes if str(route.model_id) == "M-0001")
    assert result.valid is False
    assert failed.active_endpoint_count == 0
    assert "configured exact provider has no active endpoint" in failed.issues


def test_catalog_route_preflight_rejects_an_advertised_output_cap() -> None:
    root = Path(__file__).parents[4]
    catalog = load_model_catalog(root / "config" / "models.yaml")
    providers = {
        entry.configuration.model: entry.configuration.provider for entry in catalog.models.values()
    }
    limits = {
        entry.configuration.model: entry.configuration.max_output_tokens
        for entry in catalog.models.values()
    }
    selected = catalog.models["M-0001"].configuration
    limits[selected.model] = selected.max_output_tokens - 1

    result = validate_catalog_routes(
        catalog,
        FakeRouteMetadata(providers, limits),
    )

    failed = next(route for route in result.routes if str(route.model_id) == "M-0001")
    assert failed.valid is False
    assert (
        "configured max_output_tokens exceeds the exact route capability"
        in failed.issues
    )


class FlakyRouteMetadata:
    def __init__(self, inner: FakeRouteMetadata, failures: int) -> None:
        self.inner = inner
        self.failures = failures
        self.calls = 0

    def endpoints(self, model: str) -> OpenRouterEndpointData:
        self.calls += 1
        if self.calls <= self.failures:
            raise URLError("temporary metadata outage")
        return self.inner.endpoints(model)


def test_route_preflight_retries_transient_metadata_outages() -> None:
    root = Path(__file__).parents[4]
    catalog = load_model_catalog(root / "config" / "models.yaml")
    selected = catalog.models["M-0001"].configuration
    source = FlakyRouteMetadata(
        FakeRouteMetadata(
            {selected.model: selected.provider},
            {selected.model: selected.max_output_tokens},
        ),
        failures=2,
    )
    sleeps: list[float] = []

    result = validate_catalog_routes_with_retry(
        catalog,
        source,
        model_ids=(BenchmarkModelId("M-0001"),),
        attempts=3,
        wait_seconds=30.0,
        sleep=sleeps.append,
    )

    assert result.valid is True
    assert source.calls == 3
    assert sleeps == [30.0, 30.0]


def test_route_preflight_retry_raises_after_persistent_outage() -> None:
    root = Path(__file__).parents[4]
    catalog = load_model_catalog(root / "config" / "models.yaml")
    selected = catalog.models["M-0001"].configuration
    source = FlakyRouteMetadata(
        FakeRouteMetadata(
            {selected.model: selected.provider},
            {selected.model: selected.max_output_tokens},
        ),
        failures=10,
    )
    sleeps: list[float] = []

    with pytest.raises(URLError):
        validate_catalog_routes_with_retry(
            catalog,
            source,
            model_ids=(BenchmarkModelId("M-0001"),),
            attempts=3,
            wait_seconds=5.0,
            sleep=sleeps.append,
        )

    assert source.calls == 3
    assert sleeps == [5.0, 5.0]


class FakeCanaryProvider:
    def __init__(
        self,
        *,
        raw_output: str | None = None,
        error: GameProviderError | None = None,
        model: str = "openai/gpt-5.6-luna",
        provider: str = "openai",
    ) -> None:
        self.raw_output = raw_output
        self.error = error
        self.model = model
        self.provider = provider
        self.requests: list[GameProviderRequest] = []
        self.closed = False

    def complete(self, request: GameProviderRequest) -> GameProviderExchange:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        assert self.raw_output is not None
        return GameProviderExchange(
            raw_output=self.raw_output,
            trace=ProviderTrace(
                requested_at="2026-07-27T20:00:00+00:00",
                completed_at="2026-07-27T20:00:02+00:00",
                latency_ms=2_000,
                finish_reason="stop",
                requested_model=self.model,
                resolved_model=self.model,
                requested_provider=self.provider,
                resolved_provider=self.provider,
                request={},
            ),
        )

    def close(self) -> None:
        self.closed = True


def test_guesser_canary_accepts_a_valid_opening_action() -> None:
    root = Path(__file__).parents[4]
    catalog = load_model_catalog(root / "config" / "models.yaml")
    entry = catalog.model(BenchmarkModelId("M-0001"))
    provider = FakeCanaryProvider(
        raw_output=canonical_json(
            {
                "result": {
                    "action": "ASK",
                    "question": "Is the person alive today?",
                    "name": None,
                    "description": None,
                }
            }
        )
    )

    result = run_guesser_canary(entry, api_key="unused", provider=provider)

    assert result.valid is True
    assert result.action == "ASK"
    assert result.error_code is None
    assert provider.closed is True
    request = provider.requests[0]
    assert request.prompt_cache_key == "deep20-guesser-canary-v1"
    assert '"category":"synthetic_entity"' in request.messages[1]["content"]
    assert "PRIVATE" not in canonical_json(result.model_dump(mode="json"))


def test_guesser_canary_reports_provider_and_contract_failures() -> None:
    root = Path(__file__).parents[4]
    catalog = load_model_catalog(root / "config" / "models.yaml")
    entry = catalog.model(BenchmarkModelId("M-0001"))
    failing = FakeCanaryProvider(
        error=GameProviderError(
            "provider produced only whitespace output",
            code="provider_empty_response",
        )
    )
    malformed = FakeCanaryProvider(raw_output='{"result": {"action": "PONDER"}}')

    provider_failure = run_guesser_canary(entry, api_key="unused", provider=failing)
    contract_failure = run_guesser_canary(entry, api_key="unused", provider=malformed)

    assert provider_failure.valid is False
    assert provider_failure.error_code == "provider_empty_response"
    assert failing.closed is True
    assert contract_failure.valid is False
    assert contract_failure.error_code == "invalid_guesser_output"
    assert malformed.closed is True


def test_execution_route_preflight_checks_every_configured_role() -> None:
    root = Path(__file__).parents[4]
    models = load_model_catalog(root / "config" / "models.yaml")
    benchmarks = load_benchmark_catalog(root / "config" / "benchmarks.yaml")
    model = models.model(BenchmarkModelId("M-0004"))
    benchmark = benchmarks.entry(BenchmarkId("B-0001"))

    class ExecutionMetadata:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def endpoints(self, route_model: str) -> OpenRouterEndpointData:
            self.calls.append(route_model)
            providers = {
                model.configuration.model: model.configuration.provider,
                benchmark.oracle_configuration.model: (
                    benchmark.oracle_configuration.provider
                ),
                benchmark.oracle_configuration.reviewer.model: (
                    benchmark.oracle_configuration.reviewer.provider
                ),
                benchmark.oracle_configuration.judge.model: (
                    benchmark.oracle_configuration.judge.provider
                ),
                benchmark.validator_configuration.model: (
                    benchmark.validator_configuration.provider
                ),
            }
            return OpenRouterEndpointData(
                id=route_model,
                endpoints=(
                    OpenRouterEndpoint(
                        provider_name=providers[route_model],
                        tag=providers[route_model],
                        max_completion_tokens=65_536,
                        supported_parameters=(
                            "max_tokens",
                            "reasoning_effort",
                            "response_format",
                            "seed",
                            "structured_outputs",
                            "tools",
                        ),
                        status=0,
                    ),
                ),
            )

    source = ExecutionMetadata()
    result = validate_execution_routes(model, benchmark, source)

    assert result.valid is True
    assert tuple(route.role for route in result.routes) == tuple(BenchmarkLlmRole)
    assert len(source.calls) == 4
    assert source.calls.count(benchmark.oracle_configuration.model) == 1


def test_execution_route_preflight_checks_the_configured_reviewer_token_parameter() -> None:
    root = Path(__file__).parents[4]
    models = load_model_catalog(root / "config" / "models.yaml")
    benchmarks = load_benchmark_catalog(root / "config" / "benchmarks.yaml")
    model = models.model(BenchmarkModelId("M-0004"))
    benchmark = benchmarks.entry(BenchmarkId("B-0001"))
    reviewer = benchmark.oracle_configuration.reviewer.model_copy(
        update={
            "token_limit_parameter": TokenLimitParameter.MAX_COMPLETION_TOKENS,
        }
    )
    oracle = benchmark.oracle_configuration.model_copy(
        update={"reviewer": reviewer}
    )
    mismatched_benchmark = benchmark.model_copy(
        update={"oracle_configuration": oracle}
    )

    class MaxTokensOnlyMetadata:
        def endpoints(self, route_model: str) -> OpenRouterEndpointData:
            providers = {
                model.configuration.model: model.configuration.provider,
                oracle.model: oracle.provider,
                reviewer.model: reviewer.provider,
                oracle.judge.model: "anthropic",
            }
            return OpenRouterEndpointData(
                id=route_model,
                endpoints=(
                    OpenRouterEndpoint(
                        provider_name=providers[route_model],
                        tag=providers[route_model],
                        max_completion_tokens=65_536,
                        supported_parameters=(
                            "max_tokens",
                            "reasoning_effort",
                            "response_format",
                            "seed",
                            "structured_outputs",
                            "tools",
                        ),
                        status=0,
                    ),
                ),
            )

    result = validate_execution_routes(
        model,
        mismatched_benchmark,
        MaxTokensOnlyMetadata(),
    )

    failures = tuple(route for route in result.routes if not route.valid)
    assert len(failures) == 1
    assert failures[0].role is BenchmarkLlmRole.REVIEWER
    assert failures[0].missing_parameters == ("max_completion_tokens",)


def test_execution_route_preflight_reports_the_failed_role() -> None:
    root = Path(__file__).parents[4]
    models = load_model_catalog(root / "config" / "models.yaml")
    benchmarks = load_benchmark_catalog(root / "config" / "benchmarks.yaml")
    model = models.model(BenchmarkModelId("M-0004"))
    benchmark = benchmarks.entry(BenchmarkId("B-0001"))

    class MissingJudgeMetadata:
        def endpoints(self, route_model: str) -> OpenRouterEndpointData:
            judge_route = route_model == benchmark.oracle_configuration.judge.model
            provider = (
                "different-provider"
                if judge_route
                else {
                    model.configuration.model: model.configuration.provider,
                    benchmark.oracle_configuration.model: (
                        benchmark.oracle_configuration.provider
                    ),
                    benchmark.oracle_configuration.reviewer.model: (
                        benchmark.oracle_configuration.reviewer.provider
                    ),
                }[route_model]
            )
            return OpenRouterEndpointData(
                id=route_model,
                endpoints=(
                    OpenRouterEndpoint(
                        provider_name=provider,
                        tag=provider,
                        max_completion_tokens=65_536,
                        supported_parameters=(
                            "max_tokens",
                            "reasoning_effort",
                            "response_format",
                            "seed",
                            "structured_outputs",
                            "tools",
                        ),
                        status=-5 if judge_route else 0,
                    ),
                ),
            )

    result = validate_execution_routes(model, benchmark, MissingJudgeMetadata())

    failures = tuple(route for route in result.routes if not route.valid)
    assert len(failures) == 1
    assert failures[0].role is BenchmarkLlmRole.JUDGE
    assert failures[0].provider_routing is ProviderRouting.AUTOMATIC
    assert failures[0].issues == (
        "model has no active endpoint for automatic routing",
    )
