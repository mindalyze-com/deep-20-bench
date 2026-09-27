"""Local Ollama inference. Research tools are executed by the benchmark, never here."""

from __future__ import annotations

from datetime import UTC, datetime
from time import monotonic

import httpx
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from .config import OllamaSettings
from .models import (
    BackendCapabilities,
    BackendError,
    BackendKind,
    BackendObservation,
    BackendUsage,
    JsonObject,
    Message,
    ModelRequest,
    ModelResponse,
    ToolCall,
)


class _ExternalModel(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)


class _Function(_ExternalModel):
    name: str
    arguments: JsonObject


class _ToolCall(_ExternalModel):
    function: _Function


class _Message(_ExternalModel):
    role: str
    content: str = ""
    tool_calls: tuple[_ToolCall, ...] = ()


class _ChatResponse(_ExternalModel):
    model: str
    message: _Message
    done: bool
    done_reason: str | None = None
    prompt_eval_count: int | None = Field(default=None, ge=0)
    prompt_eval_cached_count: int | None = Field(default=None, ge=0)
    eval_count: int | None = Field(default=None, ge=0)


class _InstalledModel(_ExternalModel):
    name: str
    digest: str


class _Tags(_ExternalModel):
    models: tuple[_InstalledModel, ...]


class _Show(_ExternalModel):
    capabilities: tuple[str, ...] = ()
    model_info: JsonObject = Field(default_factory=dict)


_JSON: TypeAdapter[JsonObject] = TypeAdapter(JsonObject)


def _message(message: Message) -> JsonObject:
    value: JsonObject = {"role": message.role.value, "content": message.content}
    if message.tool_name is not None:
        value["tool_name"] = message.tool_name
    if message.tool_calls:
        value["tool_calls"] = [
            {"function": {"name": call.name, "arguments": call.arguments}}
            for call in message.tool_calls
        ]
    return value


class OllamaBackend:
    def __init__(self, settings: OllamaSettings, *, client: httpx.Client | None = None):
        self.settings = settings
        self._client = client or httpx.Client(timeout=settings.timeout_seconds, trust_env=False)
        self._owns_client = client is None
        self._capabilities = BackendCapabilities(prompt_cache="unmeasured")
        self._model_name: str | None = None
        self._digest: str | None = None

    @property
    def capabilities(self) -> BackendCapabilities:
        return self._capabilities

    def _json(self, method: str, endpoint: str, body: JsonObject | None = None) -> JsonObject:
        try:
            response = self._client.request(
                method, self.settings.base_url.rstrip("/") + endpoint, json=body,
                timeout=self.settings.timeout_seconds,
            )
            response.raise_for_status()
            return _JSON.validate_json(response.content)
        except (httpx.HTTPError, ValidationError, ValueError):
            # Provider bodies and URLs never become exception messages.
            raise BackendError("ollama_request_failed", "local Ollama request failed") from None

    def preflight(self) -> BackendObservation:
        try:
            tags = _Tags.model_validate(self._json("GET", "/api/tags"))
            requested = self.settings.model
            canonical = requested if ":" in requested.rsplit("/", 1)[-1] else requested + ":latest"
            installed = next((m for m in tags.models if m.name in {requested, canonical}), None)
            if installed is None:
                raise BackendError("ollama_model_not_installed", "configured Ollama model is absent")
            if self.settings.model_digest is not None and installed.digest != self.settings.model_digest:
                raise BackendError("ollama_digest_mismatch", "installed Ollama model differs from the configured digest")
            shown = _Show.model_validate(self._json("POST", "/api/show", {"model": installed.name}))
        except ValidationError:
            raise BackendError("ollama_invalid_metadata", "invalid local model metadata") from None
        context_limits = [
            value for key, value in shown.model_info.items()
            if key.endswith(".context_length") and isinstance(value, int) and not isinstance(value, bool)
        ]
        if not context_limits or self.settings.context_tokens > min(context_limits):
            raise BackendError(
                "ollama_context_unsupported", "configured context exceeds the verified model context"
            )
        self._model_name = installed.name
        self._digest = installed.digest
        self._capabilities = BackendCapabilities(
            tool_calls="tools" in shown.capabilities, seed=True, prompt_cache="unmeasured",
        )
        return self._observation(BackendUsage(), inference_requests=0)

    def _observation(self, usage: BackendUsage, *, inference_requests: int) -> BackendObservation:
        return BackendObservation(
            kind=BackendKind.OLLAMA,
            model=self.settings.model,
            resolved_model=self._model_name,
            resolved_provider="ollama",
            model_digest=self._digest,
            inference_requests=inference_requests,
            usage=usage,
        )

    def complete(self, request: ModelRequest) -> ModelResponse:
        if self._model_name is None:
            self.preflight()
        if request.tools and not self.capabilities.tool_calls:
            raise BackendError("ollama_tools_unsupported", "this local model does not support tools")
        messages = [_message(message) for message in request.messages]
        options: JsonObject = {
            "num_predict": self.settings.max_output_tokens,
            "num_ctx": self.settings.context_tokens,
            "temperature": self.settings.temperature,
        }
        if request.seed is not None:
            options["seed"] = request.seed
        body: JsonObject = {
            "model": self._model_name,
            "messages": list(messages),
            "stream": False,
            "think": self.settings.think,
            "options": options,
            "format": request.output_schema,
        }
        if request.tools:
            body["tools"] = [
                {"type": "function", "function": tool.model_dump(mode="json")}
                for tool in request.tools
            ]
            # Tool selection is a native tool-call turn; enforce the final schema once
            # the bounded research driver requests the final answer without tools.
            body.pop("format")
        # Conservative byte upper bound plus template overhead. Reject before inference
        # instead of allowing Ollama to trim the beginning of a long conversation.
        input_bound = len(_JSON.dump_json(body)) + 1024
        if input_bound + self.settings.max_output_tokens > self.settings.context_tokens:
            raise BackendError("ollama_context_limit", "request exceeds the safe local context bound")
        requested_at = datetime.now(UTC).isoformat()
        start = monotonic()
        native_response = self._json("POST", "/api/chat", body)
        try:
            result = _ChatResponse.model_validate(native_response)
        except ValidationError:
            raise BackendError("ollama_invalid_response", "invalid local inference response") from None
        if result.model != self._model_name or result.message.role != "assistant":
            raise BackendError("ollama_route_mismatch", "local inference returned an unexpected model")
        if not result.done:
            raise BackendError("ollama_incomplete_response", "local inference did not finish")
        return ModelResponse(
            content=result.message.content,
            tool_calls=tuple(
                ToolCall(name=call.function.name, arguments=call.function.arguments)
                for call in result.message.tool_calls
            ),
            finish_reason=result.done_reason,
            requested_at=requested_at,
            completed_at=datetime.now(UTC).isoformat(),
            latency_ms=max(0, round((monotonic() - start) * 1000)),
            observation=self._observation(BackendUsage(
                input_tokens=result.prompt_eval_count,
                cached_input_tokens=result.prompt_eval_cached_count,
                output_tokens=result.eval_count,
                # Local hardware cost is unmeasured, not zero USD.
            ), inference_requests=1),
            native_record={"request": body, "response": native_response},
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
