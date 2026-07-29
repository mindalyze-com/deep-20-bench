from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

import pytest
from deep20_game.audit import GameRunAuditWriter
from deep20_game.config import (
    BenchmarkMode,
    CachePolicy,
    GamePolicy,
    ModelConfig,
    PromptCacheConfig,
    SeedCapability,
)
from deep20_game.models import GameProviderExchange, GameProviderRequest
from deep20_oracle.artifacts import RunArtifactPolicy
from deep20_oracle.config import OracleConfig
from deep20_oracle.models import (
    ProviderTrace,
    ProviderUsage,
    RecoveryMetrics,
    Subject,
)


@pytest.fixture
def subject() -> Subject:
    return Subject(
        target_id="T-0001",
        canonical_name="Albert Einstein",
        aliases=("Einstein",),
        entity_type="person",
        description="The theoretical physicist identified by Wikidata Q937.",
        reference_url="https://example.test/einstein",
    )


@pytest.fixture
def oracle_config() -> OracleConfig:
    return OracleConfig(model="openai/test-oracle", provider="openai")


@pytest.fixture
def model_config() -> ModelConfig:
    return ModelConfig(
        configuration_id="test-guesser",
        model="openai/test-model",
        provider="openai",
        reasoning_effort="medium",
        max_output_tokens=500,
        timeout_seconds=30,
        seed_capability=SeedCapability.SUPPORTED,
        prompt_cache=PromptCacheConfig(
            policy=CachePolicy.BEST_EFFORT,
            minimum_cacheable_tokens=100,
            ttl_seconds=300,
            input_usd_per_million=Decimal(1),
            cached_input_usd_per_million=Decimal("0.1"),
            cache_write_multiplier=Decimal("1.25"),
        ),
    )


@pytest.fixture
def validator_config(model_config: ModelConfig) -> ModelConfig:
    return model_config.model_copy(update={"configuration_id": "test-validator"})


@pytest.fixture
def policy() -> GamePolicy:
    return GamePolicy(max_questions=50)


def provider_trace(
    config: ModelConfig,
    raw_output: str,
    *,
    index: int = 0,
    input_tokens: int = 80,
    cached_input_tokens: int = 0,
    cache_write_tokens: int = 0,
    output_tokens: int = 20,
    response_cache_status: str | None = None,
    request_attempts: int = 1,
) -> ProviderTrace:
    return ProviderTrace(
        requested_at=f"2026-07-26T10:00:{index * 2:02d}+00:00",
        completed_at=f"2026-07-26T10:00:{index * 2 + 1:02d}+00:00",
        latency_ms=1_000,
        http_status_code=200,
        response_id=f"response-{index}",
        response_cache_status=response_cache_status,
        request_attempts=request_attempts,
        recovery=RecoveryMetrics(request_attempts=request_attempts),
        requested_model=config.model,
        resolved_model=config.model,
        requested_provider=config.provider,
        resolved_provider=config.provider,
        fallback_occurred=False,
        request={"model": config.model},
        response={"id": f"response-{index}"},
        raw_output=raw_output,
        annotations=(),
        usage=ProviderUsage(
            input_tokens=input_tokens,
            cached_input_tokens=cached_input_tokens,
            cache_write_tokens=cache_write_tokens,
            output_tokens=output_tokens,
            reasoning_tokens=5,
            search_count=0,
            cost_usd=Decimal("0.01"),
            cache_discount_usd=Decimal("0.001"),
        ),
    )


class FakeGameProvider:
    def __init__(
        self,
        config: ModelConfig,
        outputs: Iterable[str],
        *,
        traces: Iterable[dict] | None = None,
    ):
        self.config = config
        self.outputs = list(outputs)
        self.trace_options = list(traces or ())
        self.requests: list[GameProviderRequest] = []

    def complete(self, request: GameProviderRequest) -> GameProviderExchange:
        self.requests.append(request)
        raw_output = self.outputs.pop(0)
        index = len(self.requests) - 1
        options = self.trace_options[index] if index < len(self.trace_options) else {}
        return GameProviderExchange(
            raw_output=raw_output,
            trace=provider_trace(
                self.config,
                raw_output,
                index=index,
                **options,
            ),
        )


@pytest.fixture
def audit_writer(
    tmp_path: Path,
    policy: GamePolicy,
    oracle_config: OracleConfig,
    model_config: ModelConfig,
    validator_config: ModelConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> GameRunAuditWriter:
    writer = GameRunAuditWriter(
        tmp_path / "runs",
        game_policy=policy,
        oracle_config=oracle_config,
        guesser_config=model_config,
        validator_config=validator_config,
        subject_catalog_hash="a" * 64,
        repository=tmp_path,
        artifact_policy=RunArtifactPolicy(verbose=True),
    )
    monkeypatch.setattr(
        writer,
        "_git",
        lambda arguments: "abc123" if arguments == ["rev-parse", "HEAD"] else "",
    )
    return writer


def official_policy(max_questions: int = 50) -> GamePolicy:
    return GamePolicy(
        benchmark_mode=BenchmarkMode.OFFICIAL,
        max_questions=max_questions,
    )
