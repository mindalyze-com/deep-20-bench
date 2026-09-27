"""Bounded, role-private research contracts shared by local and interactive Oracles."""

from decimal import Decimal
from typing import Literal, Protocol

from pydantic import Field, HttpUrl, field_validator

from .models import BackendUsage, FrozenModel, ToolDefinition


class ResearchPolicy(FrozenModel):
    workflow: Literal["parallel-tools-v1"] = "parallel-tools-v1"
    search_mode: Literal["basic", "advanced", "fast", "turbo"] = "basic"
    max_search_requests: int = Field(default=8, ge=1, le=20)
    max_extract_requests: int = Field(default=4, ge=0, le=20)
    max_model_rounds: int = Field(default=12, ge=2, le=40)
    deadline_seconds: int = Field(default=300, ge=1, le=1800)
    request_timeout_seconds: int = Field(default=60, ge=1, le=120)
    max_chars_total: int = Field(default=8000, ge=1000, le=16000)
    # Conservative versioned bounds, not measured billing or claimed cost savings.
    search_reservation_usd: Decimal = Field(default=Decimal("0.01"), ge=Decimal("0.01"), allow_inf_nan=False)
    extract_reservation_usd: Decimal = Field(default=Decimal("0.005"), ge=Decimal("0.005"), allow_inf_nan=False)


class SearchInput(FrozenModel):
    objective: str = Field(min_length=1, max_length=4000)
    search_queries: tuple[str, ...] = Field(min_length=1, max_length=3)

    @field_validator("search_queries")
    @classmethod
    def bounded_queries(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not query.strip() or len(query) > 500 for query in value):
            raise ValueError("search queries must be nonempty and at most 500 characters")
        return value


class ExtractInput(FrozenModel):
    url: HttpUrl
    objective: str = Field(min_length=1, max_length=4000)

    @field_validator("url")
    @classmethod
    def public_url(cls, value: HttpUrl) -> HttpUrl:
        import ipaddress
        host = value.host or ""
        if value.username or value.password or host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
            raise ValueError("fetch requires a public URL without credentials")
        try:
            address = ipaddress.ip_address(host.strip("[]"))
        except ValueError:
            return value
        if not address.is_global:
            raise ValueError("fetch requires a public URL")
        return value


class ResearchSource(FrozenModel):
    url: HttpUrl
    title: str | None = None
    excerpts: tuple[str, ...] = ()


class ResearchResult(FrozenModel):
    sources: tuple[ResearchSource, ...]
    failed_urls: tuple[HttpUrl, ...] = ()


class ResearchScope(FrozenModel):
    scope_id: str = Field(pattern=r"^(WQ|RR)-[0-9a-f]{32}$")
    search_limit: int = Field(ge=1, le=20)
    policy: ResearchPolicy


class ResearchTicket(FrozenModel):
    ticket_id: str = Field(pattern=r"^RT-[0-9a-f]{32}$")
    scope_id: str = Field(pattern=r"^(WQ|RR)-[0-9a-f]{32}$")
    kind: Literal["search", "extract"]
    remaining_seconds: float = Field(gt=0)


class ResearchJournal(Protocol):
    def begin(self, scope: ResearchScope, kind: Literal["search", "extract"]) -> ResearchTicket: ...
    def finish(self, ticket: ResearchTicket, *, succeeded: bool) -> None: ...
    def usage(self, scope_id: str) -> BackendUsage: ...


class ResearchTools(Protocol):
    def search(self, request: SearchInput) -> ResearchResult: ...
    def extract(self, request: ExtractInput) -> ResearchResult: ...
    def usage(self) -> BackendUsage: ...
    def close(self) -> None: ...


def tool_definitions() -> tuple[ToolDefinition, ...]:
    return (
        ToolDefinition(name="search", description="Search the public web for evidence about the current question.",
                       parameters=SearchInput.model_json_schema()),
        ToolDefinition(name="fetch", description="Extract evidence from one public web page.",
                       parameters=ExtractInput.model_json_schema()),
    )
