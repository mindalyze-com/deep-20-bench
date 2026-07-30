from __future__ import annotations

from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .util import load_yaml_unique


class RecoveryPolicy(BaseModel):
    """Bounded recovery for one logical model call."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    max_elapsed_seconds: int = Field(default=300, ge=0, le=300)
    max_request_attempts: int = Field(default=8, ge=1, le=8)
    no_result_retries: int = Field(default=1, ge=0, le=1)
    invalid_output_retries: int = Field(default=1, ge=0, le=1)
    rate_limit_max_elapsed_seconds: int = Field(default=900, ge=0, le=3_600)
    rate_limit_max_request_attempts: int = Field(default=20, ge=1, le=50)
    retry_jitter_ms: int = Field(default=1_000, ge=0, le=10_000)


class ModelRouteConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    gateway: str = Field(default="openrouter", pattern=r"^openrouter$")
    model: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    reasoning_effort: str = Field(default="high", min_length=1)
    allow_fallbacks: bool = False
    max_output_tokens: int = Field(default=4_096, ge=128, le=65_536)
    timeout_seconds: int = Field(default=120, ge=1, le=600)
    recovery: RecoveryPolicy = Field(default_factory=RecoveryPolicy)

    @model_validator(mode="after")
    def route_is_exact(self) -> Self:
        if "/" not in self.model:
            raise ValueError("model must be an exact provider/model slug")
        return self


class EvidenceReviewConfig(ModelRouteConfig):
    """No-web model route for blind evidence review or final judgment."""


def _default_reviewer_config() -> EvidenceReviewConfig:
    return EvidenceReviewConfig(
        model="google/gemini-3.5-flash-lite",
        provider="google-ai-studio",
        reasoning_effort="medium",
    )


def _default_judge_config() -> EvidenceReviewConfig:
    return EvidenceReviewConfig(
        model="anthropic/claude-opus-5",
        provider="anthropic",
        reasoning_effort="medium",
    )


class OracleConfig(ModelRouteConfig):
    parallel_search: bool = True
    max_search_results: int = Field(default=5, ge=1, le=10)
    reviewer: EvidenceReviewConfig = Field(default_factory=_default_reviewer_config)
    judge: EvidenceReviewConfig = Field(default_factory=_default_judge_config)


def load_oracle_config(path: Path) -> OracleConfig:
    return OracleConfig.model_validate(load_yaml_unique(path))
