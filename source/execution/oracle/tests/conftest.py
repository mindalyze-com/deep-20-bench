from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from deep20_oracle.artifacts import RunArtifactPolicy
from deep20_oracle.audit import RunAuditWriter
from deep20_oracle.config import EvidenceReviewConfig, OracleConfig
from deep20_oracle.models import (
    EvidenceDecisionBasis,
    OracleAnswer,
    OracleRequest,
    ProviderTrace,
    ProviderUsage,
    Subject,
)
from deep20_oracle.provider import ProviderExchange, ProviderRequest


@pytest.fixture
def config() -> OracleConfig:
    return OracleConfig(
        model="openai/test-model",
        provider="openai",
        reasoning_effort="high",
        allow_fallbacks=False,
        max_search_results=5,
        max_output_tokens=1_500,
        timeout_seconds=30,
        reviewer=EvidenceReviewConfig(
            model="openai/test-reviewer",
            provider="openai",
            reasoning_effort="medium",
            timeout_seconds=30,
        ),
        judge=EvidenceReviewConfig(
            model="openai/test-judge",
            provider="openai",
            reasoning_effort="medium",
            timeout_seconds=30,
        ),
    )


@pytest.fixture
def subject() -> Subject:
    return Subject(
        target_id="T-0001",
        canonical_name="Albert Einstein",
        aliases=("Einstein",),
        entity_type="person",
        description="The theoretical physicist identified by Wikidata Q937.",
        reference_url="https://en.wikipedia.org/wiki/Albert_Einstein",
    )


@pytest.fixture
def oracle_request(subject: Subject) -> OracleRequest:
    return OracleRequest(
        run_id="test-run",
        subject=subject,
        question="Was this person born before 1900?",
    )


def provider_trace(
    *,
    raw_output: str,
    search_count: int = 1,
    request: dict[str, Any] | None = None,
    model: str = "openai/test-model",
    provider: str = "openai",
) -> ProviderTrace:
    return ProviderTrace(
        requested_at="2026-07-26T10:00:00+00:00",
        completed_at="2026-07-26T10:00:01+00:00",
        latency_ms=1_000,
        response_id="response-1",
        requested_model=model,
        resolved_model=model,
        requested_provider=provider,
        resolved_provider=provider,
        fallback_occurred=False,
        request=request or {"model": "openai/test-model"},
        response={"id": "response-1", "safe": True},
        raw_output=raw_output,
        annotations=(
            {
                "type": "url_citation",
                "url_citation": {"url": "https://example.test/source"},
            },
        ),
        usage=ProviderUsage(
            input_tokens=100,
            output_tokens=40,
            reasoning_tokens=10,
            search_count=search_count,
            cost_usd=Decimal("0.01"),
        ),
    )


class FakeProvider:
    def __init__(
        self,
        raw_output: str,
        *,
        search_count: int = 1,
        model: str = "openai/test-model",
    ):
        self.raw_output = raw_output
        self.search_count = search_count
        self.model = model
        self.requests: list[ProviderRequest] = []

    def complete(self, request: ProviderRequest) -> ProviderExchange:
        self.requests.append(request)
        return ProviderExchange(
            raw_output=self.raw_output,
            trace=provider_trace(
                raw_output=self.raw_output,
                search_count=self.search_count,
                model=self.model,
                request={
                    "messages": request.messages,
                    "response_format": request.output_schema,
                },
            ),
        )


def review_payload(answer: OracleAnswer | str) -> str:
    value = OracleAnswer(answer)
    return json.dumps(
        {
            "answer": value.value,
            "basis": EvidenceDecisionBasis.EVIDENCE.value,
            "evidence_indices": [] if value is OracleAnswer.UNKNOWN else [1],
        },
        separators=(",", ":"),
    )


def make_oracle(
    provider: object,
    audit_writer: RunAuditWriter,
    config: OracleConfig,
    *,
    reviewer_answer: OracleAnswer = OracleAnswer.YES,
    judge_answer: OracleAnswer = OracleAnswer.YES,
    reviewer_provider: object | None = None,
    judge_provider: object | None = None,
) -> object:
    from deep20_oracle.service import Oracle

    reviewer = reviewer_provider or FakeProvider(
        review_payload(reviewer_answer),
        search_count=0,
        model=config.reviewer.model,
    )
    judge = judge_provider or FakeProvider(
        review_payload(judge_answer),
        search_count=0,
        model=config.judge.model,
    )
    return Oracle(
        provider,  # type: ignore[arg-type]
        reviewer,  # type: ignore[arg-type]
        judge,  # type: ignore[arg-type]
        audit_writer,
        config,
    )


@pytest.fixture
def audit_writer(
    tmp_path: Path, config: OracleConfig, monkeypatch: pytest.MonkeyPatch
) -> RunAuditWriter:
    def fake_git(self: RunAuditWriter, arguments: list[str]) -> str:
        return "abc123" if arguments == ["rev-parse", "HEAD"] else ""

    monkeypatch.setattr(RunAuditWriter, "_git", fake_git)
    return RunAuditWriter(
        tmp_path / "runs",
        config=config,
        subject_catalog_hash="a" * 64,
        repository=tmp_path,
        artifact_policy=RunArtifactPolicy(verbose=True),
    )
