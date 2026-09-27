"""Backend-neutral wire contracts. No role can discover another role through these types."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

type JsonObject = dict[str, JsonValue]


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Role(StrEnum):
    GUESSER = "guesser"
    ORACLE = "oracle"
    REVIEWER = "reviewer"
    JUDGE = "judge"
    VALIDATOR = "validator"


class BackendKind(StrEnum):
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    INTERACTIVE = "interactive"
    MOCK = "mock"


class MessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCall(FrozenModel):
    name: str = Field(min_length=1, max_length=80)
    arguments: JsonObject
    call_id: str | None = None


class Message(FrozenModel):
    role: MessageRole
    content: str
    tool_calls: tuple[ToolCall, ...] = ()
    tool_name: str | None = None


class ToolDefinition(FrozenModel):
    name: str = Field(min_length=1, max_length=80)
    description: str
    parameters: JsonObject


class BackendCapabilities(FrozenModel):
    structured_output: bool = True
    tool_calls: bool = False
    seed: bool = False
    prompt_cache: Literal["provider", "unmeasured", "none"] = "none"


class ModelRequest(FrozenModel):
    role: Role
    messages: tuple[Message, ...] = Field(min_length=1)
    output_schema: JsonObject
    schema_name: str = Field(min_length=1, max_length=80)
    session_id: str | None = None
    prompt_cache_key: str | None = None
    seed: int | None = Field(default=None, ge=0, le=(2**31) - 1)
    max_search_requests: int | None = Field(default=None, ge=1)
    tools: tuple[ToolDefinition, ...] = ()

    @model_validator(mode="after")
    def research_is_oracle_only(self) -> ModelRequest:
        if self.role is not Role.ORACLE and (self.tools or self.max_search_requests is not None):
            raise ValueError("only Oracle requests may expose research tools")
        return self


class BackendUsage(FrozenModel):
    """None means unavailable; zero means explicitly measured zero activity."""

    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    cached_input_tokens: int | None = Field(default=None, ge=0)
    cache_write_tokens: int | None = Field(default=None, ge=0)
    reasoning_tokens: int | None = Field(default=None, ge=0)
    search_requests: int = Field(default=0, ge=0)
    extract_requests: int = Field(default=0, ge=0)
    cost_usd: Decimal | None = Field(default=None, ge=0)


class BackendObservation(FrozenModel):
    schema_version: Literal[1] = 1
    kind: BackendKind
    model: str = Field(min_length=1)
    resolved_model: str | None = None
    resolved_provider: str | None = None
    model_digest: str | None = None
    operator: str | None = None
    inference_requests: int = Field(ge=0)
    usage: BackendUsage
    research_workflow: str | None = None


class ModelResponse(FrozenModel):
    content: str
    tool_calls: tuple[ToolCall, ...] = ()
    finish_reason: str | None = None
    requested_at: str
    completed_at: str
    latency_ms: int = Field(ge=0)
    observation: BackendObservation
    # Adapter-owned external provider records. Never fed into a subsequent request.
    native_record: JsonObject | None = None


class BackendError(RuntimeError):
    """Stable, credential-free error surfaced by an adapter."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)
