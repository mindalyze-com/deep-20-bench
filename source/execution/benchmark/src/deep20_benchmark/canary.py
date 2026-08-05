from __future__ import annotations

import time
from decimal import Decimal, InvalidOperation
from typing import Literal, Protocol
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

from deep20_game.config import GamePolicy
from deep20_game.errors import GameError
from deep20_game.models import (
    GUESSER_ACTION_SCHEMA_NAME,
    GameProviderExchange,
    GameProviderRequest,
    guesser_action_output_schema,
    parse_guesser_action_output,
)
from deep20_game.openrouter_provider import OpenRouterGameProvider
from deep20_game.prompt import initial_guesser_messages
from deep20_game.service_util import validate_game_trace
from deep20_oracle.config import EvidenceReviewConfig, ProviderRouting
from deep20_oracle.errors import OracleError
from deep20_oracle.models import (
    Evidence,
    EvidenceDecisionBasis,
    EvidenceReviewRequest,
    EvidenceReviewResult,
    JsonObject,
    OracleAnswer,
    OracleRole,
    ProviderTrace,
    ProviderUsage,
    StrictModel,
    Subject,
)
from deep20_oracle.openrouter_provider import OpenRouterProvider
from deep20_oracle.prompt import render_evidence_review_messages
from deep20_oracle.provider import ProviderExchange, ProviderRequest
from deep20_oracle.service import validate_oracle_provider_trace
from deep20_oracle.util import (
    canonical_json,
    openrouter_provider_matches,
)
from pydantic import Field, HttpUrl, TypeAdapter, ValidationError

from .catalog import BenchmarkCatalogEntry
from .models import BenchmarkLlmRole, BenchmarkModelId, BenchmarkModelSnapshot
from .preflight import ExecutionRouteRequirement, execution_route_requirements

_ECHO_CANARY_VERSION = "startup-echo-canary-v1"
_ECHO_PROMPT = "Reply with exactly: Hi"
_ECHO_RESPONSE = "Hi"
_REVIEWER_CANARY_VERSION = "startup-reviewer-canary-v1"
_JUDGE_CANARY_VERSION = "startup-judge-canary-v1"
_GUESSER_CANARY_VARIATION_TOKEN = "Q7MV2KZA"
_STRUCTURED_CANARY_REVIEW = EvidenceReviewRequest(
    subject=Subject(
        target_id="T-0000",
        canonical_name="Ada Lovelace",
        aliases=("Augusta Ada King",),
        entity_type="person",
        description="The mathematician identified by Wikidata Q7259.",
        reference_url=HttpUrl("https://www.wikidata.org/wiki/Q7259"),
    ),
    question="Was this person born before 1900?",
    evidence=(
        Evidence(
            source_url=HttpUrl("https://www.britannica.com/biography/Ada-Lovelace"),
            excerpt="Ada Lovelace was born on December 10, 1815.",
            validation="model_reported",
        ),
    ),
)


class EchoCanaryRequest(StrictModel):
    role: BenchmarkLlmRole
    model: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    provider_routing: ProviderRouting = ProviderRouting.EXACT
    session_id: str = Field(min_length=1, max_length=256)
    prompt_cache_key: str = Field(min_length=1, max_length=256)


class EchoCanaryExchange(StrictModel):
    output: str
    requested_model: str
    resolved_model: str | None = None
    requested_provider: str
    resolved_provider: str | None = None
    finish_reason: str | None = None
    response_cache_status: str | None = None
    latency_ms: int = Field(ge=0)
    usage: ProviderUsage = Field(default_factory=ProviderUsage)


class EchoCanaryProvider(Protocol):
    def complete(self, request: EchoCanaryRequest) -> EchoCanaryExchange: ...

    def close(self) -> None: ...


class EvidenceReviewCanaryProvider(Protocol):
    def complete(self, request: ProviderRequest) -> ProviderExchange: ...

    def close(self) -> None: ...


class EchoCanaryProviderError(RuntimeError):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


class OpenRouterEchoCanaryProvider:
    """Make minimal plain-text reachability calls without retaining responses."""

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("OpenRouter API key is required")
        self.api_key = api_key

    def complete(self, request: EchoCanaryRequest) -> EchoCanaryExchange:
        payload = self._request_payload(request)
        http_request = Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=canonical_json(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Deep20Bench startup echo canary",
                "X-Title": "Deep20Bench Startup Echo Canary",
            },
            method="POST",
        )
        started = time.monotonic()
        try:
            with urlopen(http_request, timeout=30) as response:
                response_cache_status = response.headers.get("x-openrouter-cache-status")
                body: JsonObject = TypeAdapter(JsonObject).validate_json(response.read())
            return self._exchange(
                request,
                body,
                response_cache_status=response_cache_status,
                latency_ms=int((time.monotonic() - started) * 1_000),
            )
        except HTTPError as error:
            raise EchoCanaryProviderError(
                "OpenRouter echo request failed",
                code=f"provider_http_{error.code}",
            ) from error
        except (OSError, ValidationError, ValueError) as error:
            raise EchoCanaryProviderError(
                "OpenRouter echo request failed",
                code="provider_request_failed",
            ) from error

    @staticmethod
    def _request_payload(request: EchoCanaryRequest) -> JsonObject:
        provider_preferences: JsonObject = {
            "allow_fallbacks": (
                request.provider_routing is ProviderRouting.AUTOMATIC
            ),
            "require_parameters": True,
        }
        if request.provider_routing is ProviderRouting.EXACT:
            provider_preferences["only"] = [request.provider]
        return {
            "model": request.model,
            "messages": [
                {
                    "role": "user",
                    "content": _ECHO_PROMPT,
                }
            ],
            "max_tokens": 512,
            "provider": provider_preferences,
            "session_id": request.session_id,
            "prompt_cache_key": request.prompt_cache_key,
            "x_open_router_metadata": "enabled",
            "stream": False,
        }

    def close(self) -> None:
        return None

    @staticmethod
    def _exchange(
        request: EchoCanaryRequest,
        body: JsonObject,
        *,
        response_cache_status: str | None,
        latency_ms: int,
    ) -> EchoCanaryExchange:
        choices = body.get("choices")
        first_choice = choices[0] if isinstance(choices, list) and choices else None
        message = first_choice.get("message") if isinstance(first_choice, dict) else None
        output = message.get("content") if isinstance(message, dict) else None
        visible_output = output.strip() if isinstance(output, str) else ""
        finish_reason = (
            first_choice.get("finish_reason") if isinstance(first_choice, dict) else None
        )
        usage_raw = body.get("usage")
        usage = usage_raw if isinstance(usage_raw, dict) else {}
        prompt_details_raw = usage.get("prompt_tokens_details")
        prompt_details = prompt_details_raw if isinstance(prompt_details_raw, dict) else {}
        cost = usage.get("cost")
        resolved_model = body.get("model")
        resolved_provider = body.get("provider")
        if not isinstance(resolved_provider, str):
            metadata = body.get("openrouter_metadata")
            attempts = metadata.get("attempts") if isinstance(metadata, dict) else None
            last_attempt = attempts[-1] if isinstance(attempts, list) and attempts else None
            if isinstance(last_attempt, dict):
                provider_name = last_attempt.get("provider_name")
                provider_slug = last_attempt.get("provider")
                resolved_provider = (
                    provider_name if isinstance(provider_name, str) else provider_slug
                )
        return EchoCanaryExchange(
            output=visible_output,
            requested_model=request.model,
            resolved_model=(resolved_model if isinstance(resolved_model, str) else None),
            requested_provider=request.provider,
            resolved_provider=(resolved_provider if isinstance(resolved_provider, str) else None),
            finish_reason=(finish_reason if isinstance(finish_reason, str) else None),
            response_cache_status=response_cache_status,
            latency_ms=latency_ms,
            usage=ProviderUsage(
                input_tokens=_non_negative_integer(usage.get("prompt_tokens")),
                cached_input_tokens=_non_negative_integer(prompt_details.get("cached_tokens")),
                cache_write_tokens=_non_negative_integer(prompt_details.get("cache_write_tokens")),
                output_tokens=_non_negative_integer(usage.get("completion_tokens")),
                cost_usd=_non_negative_decimal(cost),
            ),
        )


def _non_negative_integer(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, str | int | float):
        return 0
    try:
        parsed = int(value)
    except OverflowError, ValueError:
        return 0
    return max(parsed, 0)


def _non_negative_decimal(value: object) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, str | int | float):
        return None
    try:
        parsed = Decimal(str(value))
    except InvalidOperation:
        return None
    return parsed if parsed.is_finite() and parsed >= 0 else None


class LlmCanaryResult(StrictModel):
    role: BenchmarkLlmRole
    model: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    provider_routing: ProviderRouting = ProviderRouting.EXACT
    resolved_provider: str | None = None
    valid: bool
    answer: str | None = None
    finish_reason: str | None = None
    evidence_count: int = Field(default=0, ge=0)
    search_count: int = Field(default=0, ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    cache_write_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    latency_ms: int = Field(default=0, ge=0)
    cost_usd: Decimal | None = Field(default=None, ge=0)
    error_code: str | None = None


class StartupCanaryResult(StrictModel):
    schema_version: Literal[1] = 1
    valid: bool
    roles: tuple[LlmCanaryResult, ...]


def _validate_echo(
    request: EchoCanaryRequest,
    exchange: EchoCanaryExchange,
) -> str | None:
    if exchange.requested_model != request.model:
        return "requested_model_mismatch"
    if exchange.requested_provider != request.provider:
        return "requested_provider_mismatch"
    if exchange.resolved_model != request.model:
        return "resolved_model_mismatch"
    if exchange.resolved_provider is None:
        return "resolved_provider_missing"
    if (
        request.provider_routing is ProviderRouting.EXACT
        and not openrouter_provider_matches(
            request.provider,
            exchange.resolved_provider,
        )
    ):
        return "resolved_provider_mismatch"
    if exchange.finish_reason != "stop":
        return "provider_incomplete_response"
    if (exchange.response_cache_status or "").casefold() == "hit":
        return "response_cache_replay"
    if not exchange.output:
        return "provider_empty_response"
    if exchange.output != _ECHO_RESPONSE:
        return "invalid_echo_output"
    return None


def _evidence_review_canary_request(
    invocation_id: str,
    *,
    role: OracleRole,
) -> ProviderRequest:
    if role not in {OracleRole.REVIEWER, OracleRole.JUDGE}:
        raise ValueError("structured startup canary requires Reviewer or Judge role")
    version = (
        _REVIEWER_CANARY_VERSION
        if role is OracleRole.REVIEWER
        else _JUDGE_CANARY_VERSION
    )
    return ProviderRequest(
        messages=render_evidence_review_messages(
            _STRUCTURED_CANARY_REVIEW,
            role=role,
        ),
        output_schema=EvidenceReviewResult.model_json_schema(),
        response_schema_name=f"{role.value}_canary_result",
        session_id=f"deep20-{version}-{invocation_id}",
        prompt_cache_key=f"deep20-{version}",
    )


def _run_evidence_review_canary(
    requirement: ExecutionRouteRequirement,
    *,
    config: EvidenceReviewConfig,
    role: OracleRole,
    invocation_id: str,
    provider: EvidenceReviewCanaryProvider,
) -> LlmCanaryResult:
    try:
        exchange = provider.complete(
            _evidence_review_canary_request(invocation_id, role=role)
        )
        trace = exchange.trace
        validate_oracle_provider_trace(
            trace,
            config=config,
            role=role,
        )
        if trace.finish_reason != "stop":
            raise ValueError(
                f"{role.value.title()} canary response did not finish with stop"
            )
        decision = EvidenceReviewResult.model_validate_json(
            exchange.raw_output
        ).validate_evidence_count(len(_STRUCTURED_CANARY_REVIEW.evidence))
        if (
            decision.answer is not OracleAnswer.YES
            or decision.basis is not EvidenceDecisionBasis.EVIDENCE
            or decision.evidence_indices != (1,)
        ):
            raise ValueError(
                f"{role.value.title()} canary returned an unexpected decision"
            )
    except OracleError as error:
        return LlmCanaryResult(
            role=requirement.role,
            model=requirement.model,
            provider=requirement.provider,
            provider_routing=requirement.provider_routing,
            valid=False,
            error_code=error.code,
        )
    except (ValidationError, ValueError):
        return LlmCanaryResult(
            role=requirement.role,
            model=requirement.model,
            provider=requirement.provider,
            provider_routing=requirement.provider_routing,
            valid=False,
            error_code=f"invalid_{role.value}_canary_output",
        )

    usage = trace.usage
    return LlmCanaryResult(
        role=requirement.role,
        model=requirement.model,
        provider=requirement.provider,
        provider_routing=requirement.provider_routing,
        resolved_provider=trace.resolved_provider,
        valid=True,
        answer=decision.answer,
        finish_reason=trace.finish_reason,
        evidence_count=len(decision.evidence_indices),
        search_count=usage.search_count,
        cached_input_tokens=usage.cached_input_tokens,
        cache_write_tokens=usage.cache_write_tokens,
        output_tokens=usage.output_tokens,
        latency_ms=trace.latency_ms,
        cost_usd=usage.cost_usd,
    )


def run_startup_canaries(
    model: BenchmarkModelSnapshot,
    benchmark: BenchmarkCatalogEntry,
    *,
    api_key: str,
    provider: EchoCanaryProvider | None = None,
    reviewer_provider: EvidenceReviewCanaryProvider | None = None,
    judge_provider: EvidenceReviewCanaryProvider | None = None,
) -> StartupCanaryResult:
    """Probe route reachability and both structured evidence-review contracts."""

    injected = tuple(
        item is not None for item in (provider, reviewer_provider, judge_provider)
    )
    if any(injected) and not all(injected):
        raise ValueError(
            "inject echo, Reviewer, and Judge canary providers together"
        )

    echo_provider: EchoCanaryProvider = (
        OpenRouterEchoCanaryProvider(api_key) if provider is None else provider
    )
    structured_reviewer_provider: EvidenceReviewCanaryProvider = (
        OpenRouterProvider(
            api_key,
            benchmark.oracle_configuration.reviewer,
            enable_web_search=False,
            title="Deep20Bench Startup Reviewer Canary",
        )
        if reviewer_provider is None
        else reviewer_provider
    )
    structured_judge_provider: EvidenceReviewCanaryProvider = (
        OpenRouterProvider(
            api_key,
            benchmark.oracle_configuration.judge,
            enable_web_search=False,
            title="Deep20Bench Startup Judge Canary",
        )
        if judge_provider is None
        else judge_provider
    )
    results: list[LlmCanaryResult] = []
    invocation_id = uuid4().hex
    try:
        for requirement in execution_route_requirements(model, benchmark):
            if requirement.role in {
                BenchmarkLlmRole.REVIEWER,
                BenchmarkLlmRole.JUDGE,
            }:
                role = OracleRole(requirement.role.value)
                role_config = (
                    benchmark.oracle_configuration.reviewer
                    if role is OracleRole.REVIEWER
                    else benchmark.oracle_configuration.judge
                )
                role_provider = (
                    structured_reviewer_provider
                    if role is OracleRole.REVIEWER
                    else structured_judge_provider
                )
                results.append(
                    _run_evidence_review_canary(
                        requirement,
                        config=role_config,
                        role=role,
                        invocation_id=invocation_id,
                        provider=role_provider,
                    )
                )
                continue
            request = EchoCanaryRequest(
                role=requirement.role,
                model=requirement.model,
                provider=requirement.provider,
                provider_routing=requirement.provider_routing,
                session_id=(f"deep20-{_ECHO_CANARY_VERSION}-{invocation_id}-{requirement.role}"),
                prompt_cache_key=(f"deep20-{_ECHO_CANARY_VERSION}-{requirement.role}"),
            )
            try:
                exchange = echo_provider.complete(request)
                error_code = _validate_echo(request, exchange)
                usage = exchange.usage
                results.append(
                    LlmCanaryResult(
                        role=requirement.role,
                        model=requirement.model,
                        provider=requirement.provider,
                        provider_routing=requirement.provider_routing,
                        resolved_provider=exchange.resolved_provider,
                        valid=error_code is None,
                        answer=(_ECHO_RESPONSE if error_code is None else None),
                        finish_reason=exchange.finish_reason,
                        cached_input_tokens=usage.cached_input_tokens,
                        cache_write_tokens=usage.cache_write_tokens,
                        output_tokens=usage.output_tokens,
                        latency_ms=exchange.latency_ms,
                        cost_usd=usage.cost_usd,
                        error_code=error_code,
                    )
                )
            except EchoCanaryProviderError as error:
                results.append(
                    LlmCanaryResult(
                        role=requirement.role,
                        model=requirement.model,
                        provider=requirement.provider,
                        provider_routing=requirement.provider_routing,
                        valid=False,
                        error_code=error.code,
                    )
                )
    finally:
        echo_provider.close()
        structured_reviewer_provider.close()
        structured_judge_provider.close()
    roles = tuple(results)
    return StartupCanaryResult(
        valid=all(role.valid for role in roles),
        roles=roles,
    )


class GuesserCanaryProvider(Protocol):
    def complete(self, request: GameProviderRequest) -> GameProviderExchange: ...

    def close(self) -> None: ...


class GuesserCanaryResult(StrictModel):
    model_id: BenchmarkModelId
    model: str
    provider: str
    valid: bool
    action: str | None = None
    finish_reason: str | None = None
    output_tokens: int = Field(default=0, ge=0)
    latency_ms: int = Field(default=0, ge=0)
    error_code: str | None = None


def run_guesser_canary(
    model: BenchmarkModelSnapshot,
    *,
    api_key: str,
    provider: GuesserCanaryProvider | None = None,
) -> GuesserCanaryResult:
    """Probe one Guesser structured-action contract outside benchmark state."""

    canary_provider: GuesserCanaryProvider = (
        OpenRouterGameProvider(
            api_key,
            model.configuration,
            title="Deep20Bench Guesser Canary",
        )
        if provider is None
        else provider
    )
    trace: ProviderTrace | None = None
    action: str | None = None
    error_code: str | None = None
    try:
        exchange = canary_provider.complete(
            GameProviderRequest(
                messages=initial_guesser_messages(
                    GamePolicy().max_questions,
                    "synthetic_entity",
                    _GUESSER_CANARY_VARIATION_TOKEN,
                ),
                output_schema=guesser_action_output_schema(),
                schema_name=GUESSER_ACTION_SCHEMA_NAME,
                session_id=f"deep20-guesser-canary-{model.model_id}",
                prompt_cache_key="deep20-guesser-canary-v1",
            )
        )
        trace = exchange.trace
        validate_game_trace(trace, model.configuration)
        action = parse_guesser_action_output(exchange.raw_output).action.value
    except GameError as error:
        error_code = error.code
    except ValidationError, ValueError:
        error_code = "invalid_guesser_output"
    finally:
        canary_provider.close()
    return GuesserCanaryResult(
        model_id=model.model_id,
        model=model.configuration.model,
        provider=model.configuration.provider,
        valid=error_code is None,
        action=action,
        finish_reason=trace.finish_reason if trace is not None else None,
        output_tokens=trace.usage.output_tokens if trace is not None else 0,
        latency_ms=trace.latency_ms if trace is not None else 0,
        error_code=error_code,
    )
