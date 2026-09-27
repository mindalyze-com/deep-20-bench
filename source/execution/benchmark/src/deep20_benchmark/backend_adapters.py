"""Translate existing role requests at the backend boundary, preserving OpenRouter records."""

from __future__ import annotations

from deep20_backends.models import (
    BackendCapabilities,
    BackendError,
    BackendKind,
    BackendObservation,
    BackendUsage,
    Message,
    ModelRequest,
    ModelResponse,
    Role,
)
from deep20_backends.ports import ModelBackend
from deep20_game.config import ModelConfig, SeedCapability
from deep20_game.errors import GameProviderError
from deep20_game.models import GameProviderExchange, GameProviderRequest
from deep20_game.openrouter_provider import OpenRouterGameProvider
from deep20_oracle.config import ModelRouteConfig
from deep20_oracle.errors import OracleProviderError
from deep20_oracle.models import ProviderTrace, ProviderUsage, RecoveryMetrics
from deep20_oracle.openrouter_provider import OpenRouterProvider
from deep20_oracle.provider import ProviderExchange, ProviderRequest


def _model_request(role: Role, request: GameProviderRequest | ProviderRequest) -> ModelRequest:
    return ModelRequest(
        role=role,
        messages=tuple(Message.model_validate(message) for message in request.messages),
        output_schema=request.output_schema,
        schema_name=(request.schema_name if isinstance(request, GameProviderRequest)
                     else request.response_schema_name),
        session_id=request.session_id,
        prompt_cache_key=request.prompt_cache_key,
        seed=request.seed if isinstance(request, GameProviderRequest) else None,
        max_search_requests=(request.max_web_search_requests
                             if isinstance(request, ProviderRequest) else None),
    )


def _response(content: str, trace: ProviderTrace) -> ModelResponse:
    usage = trace.usage
    return ModelResponse(
        content=content,
        finish_reason=trace.finish_reason,
        requested_at=trace.requested_at,
        completed_at=trace.completed_at,
        latency_ms=trace.latency_ms,
        observation=BackendObservation(
            kind=BackendKind.OPENROUTER,
            model=trace.requested_model,
            resolved_model=trace.resolved_model,
            resolved_provider=trace.resolved_provider,
            inference_requests=trace.request_attempts,
            usage=BackendUsage(
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                cached_input_tokens=usage.cached_input_tokens,
                cache_write_tokens=usage.cache_write_tokens,
                reasoning_tokens=usage.reasoning_tokens,
                search_requests=usage.search_count,
                cost_usd=usage.cost_usd,
            ),
        ),
        native_record=trace.model_dump(mode="json"),
    )


class OpenRouterGameBackend:
    def __init__(self, provider: OpenRouterGameProvider):
        self.provider = provider

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            seed=self.provider.config.seed_capability is SeedCapability.SUPPORTED,
            prompt_cache="provider",
        )

    def complete(self, request: ModelRequest) -> ModelResponse:
        if request.tools:
            raise BackendError("unexpected_tools", "game roles cannot use tools")
        if request.session_id is None or request.prompt_cache_key is None:
            raise BackendError("missing_game_identity", "game request lacks its session or cache key")
        exchange = self.provider.complete(GameProviderRequest(
            messages=tuple({"role": m.role.value, "content": m.content} for m in request.messages),
            output_schema=request.output_schema,
            schema_name=request.schema_name,
            session_id=request.session_id,
            prompt_cache_key=request.prompt_cache_key,
            seed=request.seed,
        ))
        return _response(exchange.raw_output, exchange.trace)

    def close(self) -> None:
        self.provider.close()


class OpenRouterOracleBackend:
    capabilities = BackendCapabilities(prompt_cache="provider")

    def __init__(self, provider: OpenRouterProvider):
        self.provider = provider

    def complete(self, request: ModelRequest) -> ModelResponse:
        if request.tools:
            raise BackendError("unexpected_tools", "OpenRouter uses its native research workflow")
        exchange = self.provider.complete(ProviderRequest(
            messages=tuple({"role": m.role.value, "content": m.content} for m in request.messages),
            output_schema=request.output_schema,
            response_schema_name=request.schema_name,
            max_web_search_requests=request.max_search_requests,
            session_id=request.session_id,
            prompt_cache_key=request.prompt_cache_key,
        ))
        return _response(exchange.raw_output, exchange.trace)

    def close(self) -> None:
        self.provider.close()


def _trace(
    response: ModelResponse,
    request: ModelRequest,
    config: ModelConfig | ModelRouteConfig,
    *,
    record_backend: bool,
) -> ProviderTrace:
    observed = response.observation
    if observed.kind.value != config.gateway or observed.model != config.model:
        raise BackendError("backend_route_mismatch", "backend observation differs from the configured model and implementation")
    if observed.kind is BackendKind.OPENROUTER:
        if response.native_record is None:
            raise BackendError("missing_provider_record", "OpenRouter response lacks its typed audit")
        trace = ProviderTrace.model_validate(response.native_record)
        return trace.model_copy(update={"backend": observed}) if record_backend else trace
    if response.tool_calls:
        raise BackendError("unresolved_tool_calls", "research must finish before returning a role reply")
    usage = observed.usage
    return ProviderTrace(
        requested_at=response.requested_at,
        completed_at=response.completed_at,
        latency_ms=response.latency_ms,
        finish_reason=response.finish_reason,
        request_attempts=observed.inference_requests,
        recovery=RecoveryMetrics(request_attempts=observed.inference_requests),
        requested_model=config.model,
        requested_provider=config.provider,
        resolved_model=observed.resolved_model,
        resolved_provider=observed.resolved_provider,
        request=request.model_dump(mode="json"),
        response=response.native_record,
        raw_output=response.content,
        usage=ProviderUsage(
            # Legacy totals carry observed amounts; the backend observation preserves
            # whether each measurement was unavailable rather than measured zero.
            input_tokens=usage.input_tokens or 0,
            output_tokens=usage.output_tokens or 0,
            cached_input_tokens=usage.cached_input_tokens or 0,
            cache_write_tokens=usage.cache_write_tokens or 0,
            reasoning_tokens=usage.reasoning_tokens or 0,
            search_count=usage.search_requests,
            cost_usd=usage.cost_usd,
        ),
        backend=observed,
    )


class GameBackendAdapter:
    def __init__(
        self, backend: ModelBackend, role: Role, config: ModelConfig, *, record_backend: bool = True,
    ):
        if role not in {Role.GUESSER, Role.VALIDATOR}:
            raise ValueError("game adapters require Guesser or Validator")
        self.backend = backend
        self.role = role
        self.config = config
        self.record_backend = record_backend

    def complete(self, request: GameProviderRequest) -> GameProviderExchange:
        try:
            projected = _model_request(self.role, request)
            response = self.backend.complete(projected)
            return GameProviderExchange(
                raw_output=response.content,
                trace=_trace(response, projected, self.config, record_backend=self.record_backend),
            )
        except BackendError as error:
            raise GameProviderError(str(error), code=error.code) from None


class OracleBackendAdapter:
    def __init__(
        self, backend: ModelBackend, role: Role, config: ModelRouteConfig,
        *, record_backend: bool = True,
    ):
        if role not in {Role.ORACLE, Role.REVIEWER, Role.JUDGE}:
            raise ValueError("Oracle adapters require Oracle, Reviewer or Judge")
        self.backend = backend
        self.role = role
        self.config = config
        self.record_backend = record_backend

    def complete(self, request: ProviderRequest) -> ProviderExchange:
        try:
            projected = _model_request(self.role, request)
            response = self.backend.complete(projected)
            return ProviderExchange(
                raw_output=response.content,
                trace=_trace(response, projected, self.config, record_backend=self.record_backend),
            )
        except BackendError as error:
            raise OracleProviderError(str(error), code=error.code) from None
