"""Parallel v1 transport. No sessions, response reuse, implicit retries, or credential audits."""

from __future__ import annotations

from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, HttpUrl, ValidationError

from .budget import SpendingLedger
from .models import BackendError, BackendUsage, JsonObject
from .research import (
    ExtractInput,
    ResearchJournal,
    ResearchResult,
    ResearchScope,
    ResearchSource,
    SearchInput,
)


class _Source(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)
    url: HttpUrl
    title: str | None = None
    excerpts: tuple[str, ...] | None = None


class _ExtractError(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)
    url: HttpUrl


class _Result(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)
    results: tuple[_Source, ...]
    errors: tuple[_ExtractError, ...] = ()


class ParallelResearchTools:
    def __init__(self, api_key: str, scope: ResearchScope, ledger: SpendingLedger,
                 journal: ResearchJournal, *, client: httpx.Client | None = None):
        self._api_key = api_key
        self.scope = scope
        self.ledger = ledger
        self.journal = journal
        self._client = client or httpx.Client(trust_env=False, follow_redirects=False)
        self._owns_client = client is None

    def _call(self, kind: Literal["search", "extract"], body: JsonObject) -> ResearchResult:
        ticket = self.journal.begin(self.scope, kind)
        policy = self.scope.policy
        succeeded = False
        try:
            reservation = self.ledger.reserve(
                "parallel_search" if kind == "search" else "parallel_extract",
                policy.search_reservation_usd if kind == "search" else policy.extract_reservation_usd,
            )
            response = self._client.post(
                f"https://api.parallel.ai/v1/{kind}", json=body,
                headers={"x-api-key": self._api_key},
                timeout=min(policy.request_timeout_seconds, ticket.remaining_seconds),
            )
            # Parallel's response does not provide a verified USD charge. Retain the
            # reservation even on failure. Never turn missing billing into zero.
            self.ledger.settle(reservation, None)
            response.raise_for_status()
            result = _Result.model_validate_json(response.content)
            if sum(len(e) for source in result.results for e in source.excerpts or ()) > policy.max_chars_total:
                raise BackendError("research_response_limit", "research response exceeds the excerpt limit")
            if len(result.results) > 100:
                raise BackendError("research_response_limit", "research response exceeds the source limit")
            succeeded = True
            return ResearchResult(
                sources=tuple(ResearchSource(url=s.url, title=s.title, excerpts=s.excerpts or ()) for s in result.results),
                failed_urls=tuple(error.url for error in result.errors),
            )
        except (httpx.HTTPError, ValidationError):
            raise BackendError("parallel_request_failed", "Parallel research request failed") from None
        finally:
            self.journal.finish(ticket, succeeded=succeeded)

    def search(self, request: SearchInput) -> ResearchResult:
        return self._call("search", {
            "objective": request.objective, "search_queries": list(request.search_queries),
            "mode": self.scope.policy.search_mode, "max_chars_total": self.scope.policy.max_chars_total,
        })

    def extract(self, request: ExtractInput) -> ResearchResult:
        return self._call("extract", {
            "urls": [str(request.url)], "objective": request.objective,
            "max_chars_total": self.scope.policy.max_chars_total,
        })

    def usage(self) -> BackendUsage:
        return self.journal.usage(self.scope.scope_id)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
