from __future__ import annotations

import time
from collections.abc import Callable
from typing import Literal, Protocol
from urllib.parse import quote
from urllib.request import Request, urlopen

from deep20_game.config import ModelConfig, ReasoningControl
from deep20_oracle.models import JsonObject, StrictModel
from deep20_oracle.util import timestamp
from pydantic import Field, TypeAdapter

from .catalog import BenchmarkCatalogEntry, ModelCatalog
from .models import BenchmarkLlmRole, BenchmarkModelId, BenchmarkModelSnapshot


class OpenRouterEndpoint(StrictModel):
    provider_name: str = Field(min_length=1)
    tag: str = Field(min_length=1)
    max_completion_tokens: int | None = Field(default=None, ge=1)
    supported_parameters: tuple[str, ...] = ()
    status: int


class OpenRouterEndpointData(StrictModel):
    id: str = Field(min_length=1)
    endpoints: tuple[OpenRouterEndpoint, ...]


class RouteMetadataSource(Protocol):
    def endpoints(self, model: str) -> OpenRouterEndpointData: ...


class OpenRouterRouteMetadata:
    """Read current public route capabilities without entering benchmark state."""

    def endpoints(self, model: str) -> OpenRouterEndpointData:
        url = (
            "https://openrouter.ai/api/v1/models/"
            f"{quote(model, safe='/')}/endpoints"
        )
        request = Request(
            url,
            headers={"User-Agent": "Deep20Bench route preflight"},
        )
        with urlopen(request, timeout=30) as response:
            payload: JsonObject = TypeAdapter(JsonObject).validate_json(
                response.read()
            )
        data = payload.get("data")
        if not isinstance(data, dict):
            raise TypeError("OpenRouter endpoint metadata has no data object")
        endpoints = data.get("endpoints")
        if not isinstance(endpoints, list):
            raise TypeError("OpenRouter endpoint metadata has no endpoint list")
        projected_endpoints = tuple(
            OpenRouterEndpoint.model_validate(
                {
                    "provider_name": endpoint.get("provider_name"),
                    "tag": endpoint.get("tag"),
                    "max_completion_tokens": endpoint.get("max_completion_tokens"),
                    "supported_parameters": endpoint.get("supported_parameters", []),
                    "status": endpoint.get("status"),
                }
            )
            for endpoint in endpoints
            if isinstance(endpoint, dict)
        )
        parsed = OpenRouterEndpointData.model_validate(
            {
                "id": data.get("id"),
                "endpoints": projected_endpoints,
            }
        )
        if parsed.id != model:
            raise ValueError(
                f"OpenRouter returned metadata for {parsed.id!r}, expected {model!r}"
            )
        return parsed


class RouteCapabilityCheck(StrictModel):
    model_id: BenchmarkModelId
    model: str
    provider: str
    valid: bool
    active_endpoint_count: int = Field(ge=0)
    max_completion_tokens: int | None = Field(default=None, ge=1)
    supported_parameters: tuple[str, ...] = ()
    issues: tuple[str, ...] = ()


class CatalogRoutePreflight(StrictModel):
    schema_version: Literal[1] = 1
    valid: bool
    checked_at: str
    routes: tuple[RouteCapabilityCheck, ...]


class ExecutionRouteRequirement(StrictModel):
    role: BenchmarkLlmRole
    model: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    max_output_tokens: int = Field(ge=1)
    required_parameters: tuple[str, ...] = ()


class ExecutionRouteCapabilityCheck(StrictModel):
    role: BenchmarkLlmRole
    model: str
    provider: str
    valid: bool
    active_endpoint_count: int = Field(ge=0)
    max_completion_tokens: int | None = Field(default=None, ge=1)
    supported_parameters: tuple[str, ...] = ()
    missing_parameters: tuple[str, ...] = ()
    issues: tuple[str, ...] = ()


class ExecutionRoutePreflight(StrictModel):
    schema_version: Literal[1] = 1
    valid: bool
    checked_at: str
    routes: tuple[ExecutionRouteCapabilityCheck, ...]


class _RouteAssessment(StrictModel):
    active_endpoint_count: int = Field(ge=0)
    max_completion_tokens: int | None = Field(default=None, ge=1)
    supported_parameters: tuple[str, ...] = ()
    missing_parameters: tuple[str, ...] = ()
    output_limit_exceeded: bool = False


class _PreflightResult(Protocol):
    valid: bool


def _endpoint_matches_provider(endpoint: OpenRouterEndpoint, provider: str) -> bool:
    endpoint_tag = endpoint.tag.casefold()
    provider_slug = provider.casefold()
    return endpoint_tag == provider_slug or endpoint_tag.startswith(f"{provider_slug}/")


def _assess_route(
    requirement: ExecutionRouteRequirement,
    data: OpenRouterEndpointData,
) -> _RouteAssessment:
    active = tuple(
        endpoint
        for endpoint in data.endpoints
        if endpoint.status == 0
        and _endpoint_matches_provider(endpoint, requirement.provider)
    )
    supported = tuple(
        sorted(
            {
                parameter
                for endpoint in active
                for parameter in endpoint.supported_parameters
            }
        )
    )
    completion_limits = tuple(
        endpoint.max_completion_tokens
        for endpoint in active
        if endpoint.max_completion_tokens is not None
    )
    max_completion_tokens = max(completion_limits) if completion_limits else None
    return _RouteAssessment(
        active_endpoint_count=len(active),
        max_completion_tokens=max_completion_tokens,
        supported_parameters=supported,
        missing_parameters=(
            tuple(
                parameter
                for parameter in requirement.required_parameters
                if parameter not in supported
            )
            if active
            else ()
        ),
        output_limit_exceeded=(
            max_completion_tokens is not None
            and requirement.max_output_tokens > max_completion_tokens
        ),
    )


def _game_required_parameters(
    config: ModelConfig,
    *,
    include_seed: bool,
) -> tuple[str, ...]:
    required = ["max_tokens", "response_format", "structured_outputs"]
    if config.reasoning_effort.casefold() != "none":
        required.append(
            "reasoning"
            if config.reasoning_control is ReasoningControl.GENERIC
            else "reasoning_effort"
        )
    if include_seed and config.seed_capability == "supported":
        required.append("seed")
    return tuple(required)


def execution_route_requirements(
    model: BenchmarkModelSnapshot,
    benchmark: BenchmarkCatalogEntry,
) -> tuple[ExecutionRouteRequirement, ...]:
    oracle = benchmark.oracle_configuration
    return (
        ExecutionRouteRequirement(
            role=BenchmarkLlmRole.GUESSER,
            model=model.configuration.model,
            provider=model.configuration.provider,
            max_output_tokens=model.configuration.max_output_tokens,
            required_parameters=_game_required_parameters(
                model.configuration,
                include_seed=True,
            ),
        ),
        ExecutionRouteRequirement(
            role=BenchmarkLlmRole.ORACLE,
            model=oracle.model,
            provider=oracle.provider,
            max_output_tokens=oracle.max_output_tokens,
            required_parameters=(
                "max_tokens",
                "reasoning_effort",
                "response_format",
                "structured_outputs",
                "tools",
            ),
        ),
        ExecutionRouteRequirement(
            role=BenchmarkLlmRole.REVIEWER,
            model=oracle.reviewer.model,
            provider=oracle.reviewer.provider,
            max_output_tokens=oracle.reviewer.max_output_tokens,
            required_parameters=(
                "max_tokens",
                "reasoning_effort",
                "response_format",
                "structured_outputs",
            ),
        ),
        ExecutionRouteRequirement(
            role=BenchmarkLlmRole.JUDGE,
            model=oracle.judge.model,
            provider=oracle.judge.provider,
            max_output_tokens=oracle.judge.max_output_tokens,
            required_parameters=(
                "max_tokens",
                "reasoning_effort",
                "response_format",
                "structured_outputs",
            ),
        ),
        ExecutionRouteRequirement(
            role=BenchmarkLlmRole.VALIDATOR,
            model=benchmark.validator_configuration.model,
            provider=benchmark.validator_configuration.provider,
            max_output_tokens=benchmark.validator_configuration.max_output_tokens,
            required_parameters=_game_required_parameters(
                benchmark.validator_configuration,
                include_seed=False,
            ),
        ),
    )


def validate_execution_routes(
    model: BenchmarkModelSnapshot,
    benchmark: BenchmarkCatalogEntry,
    source: RouteMetadataSource,
) -> ExecutionRoutePreflight:
    checks: list[ExecutionRouteCapabilityCheck] = []
    metadata: list[OpenRouterEndpointData] = []
    for requirement in execution_route_requirements(model, benchmark):
        data = next(
            (item for item in metadata if item.id == requirement.model),
            None,
        )
        if data is None:
            data = source.endpoints(requirement.model)
            metadata.append(data)
        assessment = _assess_route(requirement, data)
        issues: list[str] = []
        if assessment.active_endpoint_count == 0:
            issues.append("configured exact provider has no active endpoint")
        if assessment.missing_parameters:
            issues.append(
                "exact route does not advertise required parameters: "
                + ", ".join(assessment.missing_parameters)
            )
        if assessment.output_limit_exceeded:
            issues.append(
                "configured max_output_tokens exceeds the exact route capability"
            )
        checks.append(
            ExecutionRouteCapabilityCheck(
                role=requirement.role,
                model=requirement.model,
                provider=requirement.provider,
                valid=not issues,
                active_endpoint_count=assessment.active_endpoint_count,
                max_completion_tokens=assessment.max_completion_tokens,
                supported_parameters=assessment.supported_parameters,
                missing_parameters=assessment.missing_parameters,
                issues=tuple(issues),
            )
        )
    routes = tuple(checks)
    return ExecutionRoutePreflight(
        valid=all(route.valid for route in routes),
        checked_at=timestamp(),
        routes=routes,
    )


def validate_catalog_routes(
    catalog: ModelCatalog,
    source: RouteMetadataSource,
    *,
    model_ids: tuple[BenchmarkModelId, ...] | None = None,
) -> CatalogRoutePreflight:
    checks: list[RouteCapabilityCheck] = []
    selected_model_ids = (
        catalog.registered_model_ids() if model_ids is None else model_ids
    )
    for model_id in selected_model_ids:
        snapshot = catalog.model(model_id)
        config = snapshot.configuration
        data = source.endpoints(config.model)
        requirement = ExecutionRouteRequirement(
            role=BenchmarkLlmRole.GUESSER,
            model=config.model,
            provider=config.provider,
            max_output_tokens=config.max_output_tokens,
            required_parameters=_game_required_parameters(
                config,
                include_seed=True,
            ),
        )
        assessment = _assess_route(requirement, data)
        issues: list[str] = []
        if assessment.active_endpoint_count == 0:
            issues.append("configured exact provider has no active endpoint")
        if assessment.active_endpoint_count and (
            "structured_outputs" in assessment.missing_parameters
            or "response_format" in assessment.missing_parameters
        ):
            issues.append("exact route does not advertise strict structured output")
        if (
            assessment.active_endpoint_count
            and config.seed_capability == "supported"
            and "seed" in assessment.missing_parameters
        ):
            issues.append("catalog declares seed support but the exact route does not")
        if assessment.output_limit_exceeded:
            issues.append(
                "configured max_output_tokens exceeds the exact route capability"
            )
        checks.append(
            RouteCapabilityCheck(
                model_id=model_id,
                model=config.model,
                provider=config.provider,
                valid=not issues,
                active_endpoint_count=assessment.active_endpoint_count,
                max_completion_tokens=assessment.max_completion_tokens,
                supported_parameters=assessment.supported_parameters,
                issues=tuple(issues),
            )
        )
    routes = tuple(checks)
    return CatalogRoutePreflight(
        valid=all(route.valid for route in routes),
        checked_at=timestamp(),
        routes=routes,
    )


def _validate_with_retry[PreflightResultT: _PreflightResult](
    operation: Callable[[], PreflightResultT],
    *,
    attempts: int = 3,
    wait_seconds: float = 30.0,
    sleep: Callable[[float], None] = time.sleep,
) -> PreflightResultT:
    """Retry transient metadata outages so preflight reflects steady-state routes."""
    if attempts < 1:
        raise ValueError("preflight retry needs at least one attempt")
    result: PreflightResultT | None = None
    for attempt in range(1, attempts + 1):
        try:
            result = operation()
        except OSError:
            if attempt == attempts:
                raise
            sleep(wait_seconds)
            continue
        if result.valid or attempt == attempts:
            return result
        sleep(wait_seconds)
    if result is None:
        raise RuntimeError("route preflight produced no result")
    return result


def validate_catalog_routes_with_retry(
    catalog: ModelCatalog,
    source: RouteMetadataSource,
    *,
    model_ids: tuple[BenchmarkModelId, ...] | None = None,
    attempts: int = 3,
    wait_seconds: float = 30.0,
    sleep: Callable[[float], None] = time.sleep,
) -> CatalogRoutePreflight:
    return _validate_with_retry(
        lambda: validate_catalog_routes(catalog, source, model_ids=model_ids),
        attempts=attempts,
        wait_seconds=wait_seconds,
        sleep=sleep,
    )


def validate_execution_routes_with_retry(
    model: BenchmarkModelSnapshot,
    benchmark: BenchmarkCatalogEntry,
    source: RouteMetadataSource,
    *,
    attempts: int = 3,
    wait_seconds: float = 30.0,
    sleep: Callable[[float], None] = time.sleep,
) -> ExecutionRoutePreflight:
    return _validate_with_retry(
        lambda: validate_execution_routes(model, benchmark, source),
        attempts=attempts,
        wait_seconds=wait_seconds,
        sleep=sleep,
    )
