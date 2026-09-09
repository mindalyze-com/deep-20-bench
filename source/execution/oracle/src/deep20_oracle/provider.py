from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from .models import JsonObject, ProviderTrace
from .search_budget import MAX_SERVER_TOOL_CALLS


class ProviderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    messages: tuple[dict[str, str], ...]
    output_schema: JsonObject
    response_schema_name: str = Field(
        default="oracle_result",
        pattern=r"^[a-z][a-z0-9_]{0,63}$",
    )
    max_web_search_requests: int | None = Field(
        default=None, ge=1, le=MAX_SERVER_TOOL_CALLS, exclude_if=lambda v: v is None,
    )
    session_id: str | None = None
    prompt_cache_key: str | None = Field(default=None, max_length=55)


class ProviderExchange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    raw_output: str
    trace: ProviderTrace


class OracleProvider(Protocol):
    def complete(self, request: ProviderRequest) -> ProviderExchange: ...
