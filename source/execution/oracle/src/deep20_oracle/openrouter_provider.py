from __future__ import annotations

import copy
import threading
import time
from decimal import Decimal
from typing import Any, Self

import httpx
from openrouter import OpenRouter

from .config import ModelRouteConfig, OracleConfig
from .diagnostics import provider_failure_code
from .errors import OracleProviderError
from .models import (
    ProviderOutputCapture,
    ProviderTrace,
    ProviderUsage,
    RecoveryMetrics,
    RecoveryReason,
)
from .openrouter_retry import (
    ProviderDeadlineExceeded,
    embedded_status_code,
    hard_deadline,
    is_malformed_response_error,
    is_transport_error,
    no_sdk_retry_config,
    parse_retry_after_ms,
    recovery_reason,
    retry_delay_ms,
)
from .provider import ProviderExchange, ProviderRequest
from .provider_output import capture_provider_output, raw_provider_output
from .recovery import (
    RecoveryAttemptLimitExceeded,
    combine_usage,
    current_recovery_budget,
    logical_recovery_budget,
    recovery_reason_counts,
)
from .util import timestamp

_NO_RESULT_RETRY_DELAY_MS = 1_000


class _RecordingClient:
    """Capture the raw response because the generated SDK omits citation annotations."""

    def __init__(self, timeout_seconds: int):
        self._client = httpx.Client(timeout=timeout_seconds)
        self.last_json: dict[str, Any] | None = None
        self.last_status_code: int | None = None
        self.last_response_cache_status: str | None = None
        self.request_attempts = 0
        self.last_retry_after_ms: int | None = None
        self.retry_after_ms: int | None = None

    def build_request(self, *args: Any, **kwargs: Any) -> httpx.Request:
        return self._client.build_request(*args, **kwargs)

    def send(self, *args: Any, **kwargs: Any) -> httpx.Response:
        budget = current_recovery_budget()
        if budget is not None:
            budget.reserve_request_attempt()
        self.request_attempts += 1
        self.last_json = None
        self.last_status_code = None
        self.last_response_cache_status = None
        self.last_retry_after_ms = None
        response = self._client.send(*args, **kwargs)
        self.last_status_code = response.status_code
        self.last_response_cache_status = response.headers.get("x-openrouter-cache-status")
        retry_after_ms = parse_retry_after_ms(response.headers)
        if retry_after_ms is not None:
            self.last_retry_after_ms = retry_after_ms
            self.retry_after_ms = retry_after_ms
        try:
            parsed = response.json()
            self.last_json = parsed if isinstance(parsed, dict) else None
        except (ValueError, RuntimeError):
            self.last_json = None
        return response

    def close(self) -> None:
        self._client.close()


class OpenRouterProvider:
    """One-request OpenRouter adapter with explicit web capability and strict output."""

    def __init__(
        self,
        api_key: str,
        config: ModelRouteConfig,
        *,
        enable_web_search: bool = True,
        title: str = "Deep20Bench Oracle",
    ):
        if not api_key:
            raise ValueError("OpenRouter API key is required")
        if enable_web_search and not isinstance(config, OracleConfig):
            raise ValueError("web-enabled providers require an OracleConfig")
        self.config = config
        self.enable_web_search = enable_web_search
        self.http_client = _RecordingClient(config.timeout_seconds)
        self.client = OpenRouter(
            api_key=api_key,
            x_open_router_title=title,
            timeout_ms=config.timeout_seconds * 1_000,
            client=self.http_client,
        )
        self._lock = threading.Lock()

    def close(self) -> None:
        self.http_client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def complete(self, request: ProviderRequest) -> ProviderExchange:
        budget = current_recovery_budget()
        if budget is None:
            with logical_recovery_budget(
                self.config.recovery,
                self.config.timeout_seconds,
            ):
                return self.complete(request)
        provider_request = self._request_payload(request)
        requested_at = timestamp()
        started = time.monotonic()
        raw_response: dict[str, Any] | None = None
        prior_usage = ProviderUsage()
        discarded_error_outputs: list[ProviderOutputCapture] = []
        retry_reasons: list[RecoveryReason] = []
        no_result_retries = 0
        recovery_started: float | None = None
        recovery_exhausted = False
        with self._lock:
            self.http_client.last_json = None
            self.http_client.last_status_code = None
            self.http_client.last_response_cache_status = None
            self.http_client.request_attempts = 0
            self.http_client.last_retry_after_ms = None
            self.http_client.retry_after_ms = None
            try:
                with hard_deadline(
                    budget.remaining_seconds
                ):
                    while True:
                        try:
                            response = self.client.chat.send(
                                **provider_request,
                                retries=no_sdk_retry_config(),
                            )
                        except Exception as error:
                            transport_error = is_transport_error(error)
                            malformed_response = is_malformed_response_error(error)
                            raw_response = self.http_client.last_json
                            status_code = embedded_status_code(
                                raw_response,
                                self.http_client.last_status_code,
                            )
                            reason = recovery_reason(
                                status_code=status_code,
                                connection_error=transport_error,
                                malformed_response=malformed_response,
                            )
                            if reason is None:
                                raise
                            retry_reasons.append(reason)
                            recovery_started = recovery_started or time.monotonic()
                            delay_ms = retry_delay_ms(
                                status_code=status_code,
                                connection_error=transport_error,
                                malformed_response=malformed_response,
                                request_attempts=self.http_client.request_attempts,
                                logical_request_attempts=max(
                                    budget.request_attempts,
                                    self.http_client.request_attempts,
                                ),
                                retry_after_ms=self.http_client.last_retry_after_ms,
                                elapsed_ms=int(
                                    (time.monotonic() - recovery_started) * 1_000
                                ),
                                max_elapsed_seconds=(
                                    self.config.recovery.max_elapsed_seconds
                                ),
                                max_request_attempts=(
                                    self.config.recovery.max_request_attempts
                                ),
                                rate_limit_max_elapsed_seconds=(
                                    self.config.recovery.rate_limit_max_elapsed_seconds
                                ),
                                rate_limit_max_request_attempts=(
                                    self.config.recovery.rate_limit_max_request_attempts
                                ),
                                jitter_ms=self.config.recovery.retry_jitter_ms,
                            )
                            if delay_ms is None:
                                recovery_exhausted = True
                                raise
                            if reason is RecoveryReason.HTTP_429:
                                budget.extend_for_rate_limit()
                            captured = capture_provider_output(
                                raw_response,
                                attempt_number=self.http_client.request_attempts,
                            )
                            if captured is not None:
                                discarded_error_outputs.append(captured)
                            prior_usage = combine_usage(
                                prior_usage,
                                self._usage(raw_response),
                            )
                            time.sleep(delay_ms / 1_000)
                            continue
                        raw_response = self.http_client.last_json
                        if raw_response is None:
                            raw_response = response.model_dump(mode="json")
                        reason = self._no_result_reason(response, raw_response)
                        if reason is None:
                            break
                        retry_reasons.append(reason)
                        recovery_started = recovery_started or time.monotonic()
                        if not self._can_retry_no_result_response(
                            recovery_started,
                            no_result_retries,
                        ):
                            recovery_exhausted = True
                            break
                        captured = capture_provider_output(
                            raw_response,
                            attempt_number=self.http_client.request_attempts,
                        )
                        if captured is not None:
                            discarded_error_outputs.append(captured)
                        prior_usage = combine_usage(
                            prior_usage,
                            self._usage(raw_response),
                        )
                        no_result_retries += 1
                        time.sleep(_NO_RESULT_RETRY_DELAY_MS / 1_000)
            except Exception as error:
                raw_response = self.http_client.last_json
                if isinstance(error, ProviderDeadlineExceeded):
                    retry_reasons.append(RecoveryReason.HARD_DEADLINE_EXCEEDED)
                    recovery_exhausted = True
                elif isinstance(error, RecoveryAttemptLimitExceeded):
                    recovery_exhausted = True
                completed_at = timestamp()
                trace = self._trace(
                    provider_request,
                    raw_response,
                    requested_at,
                    completed_at,
                    int((time.monotonic() - started) * 1_000),
                    prior_usage=prior_usage,
                    retry_reasons=tuple(retry_reasons),
                    recovery_started=recovery_started,
                    recovery_exhausted=recovery_exhausted,
                    discarded_error_outputs=tuple(discarded_error_outputs),
                )
                raise OracleProviderError(
                    "OpenRouter request failed",
                    code=(
                        "provider_hard_deadline_exceeded"
                        if isinstance(error, ProviderDeadlineExceeded)
                        else (
                            "provider_recovery_attempts_exhausted"
                            if isinstance(error, RecoveryAttemptLimitExceeded)
                            else provider_failure_code(
                                raw_response,
                                self.http_client.last_status_code,
                            )
                        )
                    ),
                    details={
                        "exception_type": type(error).__name__,
                        "provider_trace": trace.model_dump(mode="json"),
                    },
                ) from error

        completed_at = timestamp()
        latency_ms = int((time.monotonic() - started) * 1_000)
        if raw_response is None:
            raw_response = response.model_dump(mode="json")
        trace = self._trace(
            provider_request,
            raw_response,
            requested_at,
            completed_at,
            latency_ms,
            prior_usage=prior_usage,
            retry_reasons=tuple(retry_reasons),
            recovery_started=recovery_started,
            recovery_exhausted=recovery_exhausted,
            discarded_error_outputs=tuple(discarded_error_outputs),
        )
        if not response.choices or str(response.choices[0].finish_reason) != "stop":
            finish_reason = trace.finish_reason
            raise OracleProviderError(
                "OpenRouter did not return a completed choice",
                code=(
                    "provider_output_limit_exceeded"
                    if finish_reason == "length"
                    else "provider_incomplete_response"
                ),
                details={"provider_trace": trace.model_dump(mode="json")},
            )
        raw_output = raw_provider_output(raw_response)
        if not raw_output:
            raise OracleProviderError(
                "OpenRouter returned no textual structured output",
                code="provider_empty_response",
                details={"provider_trace": trace.model_dump(mode="json")},
            )
        return ProviderExchange(raw_output=raw_output, trace=trace)

    def _request_payload(self, request: ProviderRequest) -> dict[str, Any]:
        schema = copy.deepcopy(request.output_schema)
        self._make_schema_strict(schema)
        enable_web_search = getattr(self, "enable_web_search", True)
        payload = {
            "model": self.config.model,
            "messages": list(request.messages),
            "reasoning_effort": self.config.reasoning_effort,
            "max_completion_tokens": self.config.max_output_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": request.response_schema_name,
                    "strict": True,
                    "schema": schema,
                },
            },
            "provider": {
                "only": [self.config.provider],
                "allow_fallbacks": self.config.allow_fallbacks,
            },
            "x_open_router_metadata": "enabled",
            "stream": False,
        }
        if enable_web_search:
            assert isinstance(self.config, OracleConfig)
            search_parameters: dict[str, Any] = {
                "max_results": self.config.max_search_results,
            }
            if self.config.parallel_search:
                search_parameters["engine"] = "parallel"
            payload["tools"] = [
                {
                    "type": "openrouter:web_search",
                    "parameters": search_parameters,
                }
            ]
        if request.session_id is not None:
            payload["session_id"] = request.session_id
        if request.prompt_cache_key is not None:
            capability = "no-web"
            if enable_web_search:
                assert isinstance(self.config, OracleConfig)
                capability = "parallel" if self.config.parallel_search else "auto"
            payload["prompt_cache_key"] = f"{request.prompt_cache_key}-{capability}"
        return payload

    def _trace(
        self,
        provider_request: dict[str, Any],
        raw_response: dict[str, Any] | None,
        requested_at: str,
        completed_at: str,
        latency_ms: int,
        *,
        prior_usage: ProviderUsage | None = None,
        retry_reasons: tuple[RecoveryReason, ...] = (),
        recovery_started: float | None = None,
        recovery_exhausted: bool = False,
        discarded_error_outputs: tuple[ProviderOutputCapture, ...] = (),
    ) -> ProviderTrace:
        metadata = (raw_response or {}).get("openrouter_metadata") or {}
        attempts = metadata.get("attempts") or []
        choices = (raw_response or {}).get("choices") or []
        finish_reason = choices[0].get("finish_reason") if choices else None
        resolved_provider = (raw_response or {}).get("provider")
        if resolved_provider is None and attempts:
            last_attempt = attempts[-1]
            resolved_provider = last_attempt.get("provider_name") or last_attempt.get("provider")
        fallback_occurred = False if not self.config.allow_fallbacks else len(attempts) > 1
        request_attempts = max(
            int(getattr(self.http_client, "request_attempts", 1)),
            1,
        )
        return ProviderTrace(
            requested_at=requested_at,
            completed_at=completed_at,
            latency_ms=latency_ms,
            http_status_code=getattr(self.http_client, "last_status_code", None),
            response_id=(raw_response or {}).get("id"),
            response_cache_status=getattr(
                self.http_client,
                "last_response_cache_status",
                None,
            ),
            finish_reason=(finish_reason if isinstance(finish_reason, str) else None),
            request_attempts=request_attempts,
            retry_after_ms=getattr(self.http_client, "retry_after_ms", None),
            recovery=RecoveryMetrics(
                request_attempts=request_attempts,
                retried_calls=int(request_attempts > 1),
                recovered_calls=int(bool(retry_reasons) and not recovery_exhausted),
                exhausted_retries=int(recovery_exhausted),
                reasons=recovery_reason_counts(retry_reasons),
                retry_usage=prior_usage or ProviderUsage(),
                retry_latency_ms=(
                    int((time.monotonic() - recovery_started) * 1_000)
                    if recovery_started is not None
                    else 0
                ),
            ),
            requested_model=self.config.model,
            resolved_model=(raw_response or {}).get("model"),
            requested_provider=self.config.provider,
            resolved_provider=resolved_provider,
            fallback_occurred=fallback_occurred,
            request=provider_request,
            response=raw_response,
            raw_output=raw_provider_output(raw_response),
            discarded_error_outputs=discarded_error_outputs,
            annotations=tuple(self._annotations(raw_response)),
            usage=combine_usage(
                prior_usage or ProviderUsage(),
                self._usage(raw_response),
            ),
        )

    def _can_retry_no_result_response(
        self,
        recovery_started: float,
        retries_used: int,
    ) -> bool:
        if (
            self.config.recovery.max_elapsed_seconds == 0
            or retries_used >= self.config.recovery.no_result_retries
            or self.http_client.request_attempts
            >= self.config.recovery.max_request_attempts
            or (
                (budget := current_recovery_budget()) is not None
                and budget.request_attempts_remaining == 0
            )
        ):
            return False
        elapsed_ms = int((time.monotonic() - recovery_started) * 1_000)
        return (
            elapsed_ms + _NO_RESULT_RETRY_DELAY_MS
            <= self.config.recovery.max_elapsed_seconds * 1_000
        )

    def _no_result_reason(
        self,
        response: object,
        raw_response: dict[str, Any],
    ) -> RecoveryReason | None:
        choices = getattr(response, "choices", ())
        finish_reason = str(choices[0].finish_reason) if choices else None
        response_cache_hit = (
            self.http_client.last_response_cache_status or ""
        ).casefold() == "hit"
        if response_cache_hit:
            return None
        if finish_reason == "length":
            return RecoveryReason.OUTPUT_LIMIT_EXCEEDED
        if finish_reason == "stop" and not raw_provider_output(raw_response):
            return RecoveryReason.EMPTY_RESPONSE
        if finish_reason != "stop":
            return RecoveryReason.INCOMPLETE_RESPONSE
        return None

    @staticmethod
    def _usage(raw_response: dict[str, Any] | None) -> ProviderUsage:
        usage_raw = (raw_response or {}).get("usage") or {}
        prompt_details = usage_raw.get("prompt_tokens_details") or {}
        completion_details = usage_raw.get("completion_tokens_details") or {}
        server_tools = usage_raw.get("server_tool_use_details") or {}
        cost = usage_raw.get("cost")
        cache_discount = usage_raw.get("cache_discount")
        if cache_discount is None:
            cache_discount = (raw_response or {}).get("cache_discount")
        return ProviderUsage(
            input_tokens=int(usage_raw.get("prompt_tokens") or 0),
            cached_input_tokens=int(prompt_details.get("cached_tokens") or 0),
            cache_write_tokens=int(prompt_details.get("cache_write_tokens") or 0),
            output_tokens=int(usage_raw.get("completion_tokens") or 0),
            reasoning_tokens=int(completion_details.get("reasoning_tokens") or 0),
            search_count=int(server_tools.get("web_search_requests") or 0),
            cost_usd=Decimal(str(cost)) if cost is not None else None,
            cache_discount_usd=(
                Decimal(str(cache_discount)) if cache_discount is not None else None
            ),
        )

    @staticmethod
    def _annotations(raw_response: dict[str, Any] | None) -> list[dict[str, Any]]:
        choices = (raw_response or {}).get("choices") or []
        if not choices:
            return []
        annotations = (choices[0].get("message") or {}).get("annotations") or []
        return [item for item in annotations if isinstance(item, dict)]

    @classmethod
    def _make_schema_strict(cls, node: dict[str, Any]) -> None:
        # Provider structured-output implementations support a smaller JSON Schema
        # vocabulary than Pydantic. Local Pydantic validation remains authoritative
        # for these bounds and URI syntax after the response arrives.
        for unsupported in (
            "format",
            "maxItems",
            "maxLength",
            "minItems",
            "minLength",
            "pattern",
        ):
            node.pop(unsupported, None)
        if node.get("type") == "object":
            properties = node.get("properties", {})
            node["additionalProperties"] = False
            node["required"] = list(properties)
            for child in properties.values():
                if isinstance(child, dict):
                    cls._make_schema_strict(child)
        if node.get("type") == "array" and isinstance(node.get("items"), dict):
            cls._make_schema_strict(node["items"])
        for key in ("$defs", "definitions"):
            for child in node.get(key, {}).values():
                if isinstance(child, dict):
                    cls._make_schema_strict(child)


class OpenRouterOracleProviderSet:
    """Role-isolated OpenRouter clients for one Oracle adjudication service."""

    def __init__(self, api_key: str, config: OracleConfig):
        self.oracle = OpenRouterProvider(
            api_key,
            config,
            enable_web_search=True,
            title="Deep20Bench Oracle",
        )
        self.reviewer = OpenRouterProvider(
            api_key,
            config.reviewer,
            enable_web_search=False,
            title="Deep20Bench Oracle Reviewer",
        )
        self.judge = OpenRouterProvider(
            api_key,
            config.judge,
            enable_web_search=False,
            title="Deep20Bench Oracle Judge",
        )

    def close(self) -> None:
        self.oracle.close()
        self.reviewer.close()
        self.judge.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
