from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .search_budget import (
    DEFAULT_RESEARCH_QUERY_TARGET,
    MAX_SERVER_TOOL_CALLS,
    SEARCH_CALL_BONUS,
    research_search_limit,
)
from .util import load_yaml_unique

OPENROUTER_AUTO_PROVIDER = "openrouter-auto"


class PromptProfile(StrEnum):
    STANDARD = "standard"
    CONCISE_V1 = "concise_v1"
    QUALIFIED_V1 = "qualified_v1"


class AdjudicationPolicy(StrEnum):
    PROFILE_DEFAULT = "profile_default"
    JUDGE_STABLE_KNOWLEDGE_V1 = "judge_stable_knowledge_v1"
    CONCISE_KNOWLEDGE_V1 = "concise_knowledge_v1"


class ParallelSearchMode(StrEnum):
    BASIC = "basic"
    FAST = "fast"
    TURBO = "turbo"
    ADVANCED = "advanced"


def validate_prompt_profiles(guesser: PromptProfile, oracle: PromptProfile) -> None:
    if (guesser is PromptProfile.QUALIFIED_V1) != (oracle is PromptProfile.QUALIFIED_V1):
        raise ValueError("five-answer Guesser and Oracle profiles must be selected together")


class ProviderRouting(StrEnum):
    EXACT = "exact"
    AUTOMATIC = "automatic"


class TokenLimitParameter(StrEnum):
    MAX_COMPLETION_TOKENS = "max_completion_tokens"
    MAX_TOKENS = "max_tokens"


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
    provider_routing: ProviderRouting = Field(
        default=ProviderRouting.EXACT,
        exclude_if=lambda value: value is ProviderRouting.EXACT,
    )
    reasoning_effort: str = Field(default="high", min_length=1)
    allow_fallbacks: bool = False
    token_limit_parameter: TokenLimitParameter = Field(
        default=TokenLimitParameter.MAX_COMPLETION_TOKENS,
        exclude_if=lambda value: value is TokenLimitParameter.MAX_COMPLETION_TOKENS,
    )
    max_output_tokens: int = Field(default=4_096, ge=128, le=65_536)
    timeout_seconds: int = Field(default=120, ge=1, le=600)
    recovery: RecoveryPolicy = Field(default_factory=RecoveryPolicy)

    @model_validator(mode="after")
    def route_is_valid(self) -> Self:
        if "/" not in self.model:
            raise ValueError("model must be an exact provider/model slug")
        if self.provider_routing is ProviderRouting.AUTOMATIC:
            if self.provider != OPENROUTER_AUTO_PROVIDER:
                raise ValueError(
                    "automatic routing requires provider: openrouter-auto"
                )
            if not self.allow_fallbacks:
                raise ValueError("automatic routing requires provider fallbacks")
        elif self.provider == OPENROUTER_AUTO_PROVIDER:
            raise ValueError(
                "provider: openrouter-auto requires automatic routing"
            )
        return self


class EvidenceReviewConfig(ModelRouteConfig):
    """No-web model route for blind evidence review or final judgment."""


def _default_reviewer_config() -> EvidenceReviewConfig:
    return EvidenceReviewConfig(
        model="google/gemini-3.5-flash-lite",
        provider="google-ai-studio",
        reasoning_effort="medium",
        token_limit_parameter=TokenLimitParameter.MAX_TOKENS,
    )


def _default_judge_config() -> EvidenceReviewConfig:
    return EvidenceReviewConfig(
        model="anthropic/claude-opus-5",
        provider=OPENROUTER_AUTO_PROVIDER,
        provider_routing=ProviderRouting.AUTOMATIC,
        reasoning_effort="medium",
        allow_fallbacks=True,
        token_limit_parameter=TokenLimitParameter.MAX_TOKENS,
    )


class OracleConfig(ModelRouteConfig):
    prompt_profile: PromptProfile = Field(
        default=PromptProfile.STANDARD,
        exclude_if=lambda value: value is PromptProfile.STANDARD,
    )
    adjudication_policy: AdjudicationPolicy = Field(
        default=AdjudicationPolicy.PROFILE_DEFAULT,
        exclude_if=lambda value: value is AdjudicationPolicy.PROFILE_DEFAULT,
    )
    parallel_search: bool = True
    parallel_search_mode: ParallelSearchMode = Field(
        default=ParallelSearchMode.BASIC,
        exclude_if=lambda value: value is ParallelSearchMode.BASIC,
    )
    max_search_results: int = Field(default=5, ge=1, le=10)
    research_query_target: int = Field(
        default=DEFAULT_RESEARCH_QUERY_TARGET, strict=True,
        ge=1, le=MAX_SERVER_TOOL_CALLS - SEARCH_CALL_BONUS,
        exclude_if=lambda value: value == DEFAULT_RESEARCH_QUERY_TARGET,
    )
    reviewer: EvidenceReviewConfig = Field(default_factory=_default_reviewer_config)
    judge: EvidenceReviewConfig = Field(default_factory=_default_judge_config)

    @property
    def research_search_limit(self) -> int:
        return research_search_limit(self.research_query_target)

    @model_validator(mode="after")
    def adjudication_policy_matches_profile(self) -> Self:
        if (
            self.adjudication_policy is not AdjudicationPolicy.PROFILE_DEFAULT
            and self.prompt_profile is not PromptProfile.QUALIFIED_V1
        ):
            raise ValueError("non-default adjudication policies require qualified_v1")
        if (
            self.adjudication_policy is AdjudicationPolicy.CONCISE_KNOWLEDGE_V1
            and not self.parallel_search
        ):
            raise ValueError("concise_knowledge_v1 requires bounded Parallel search")
        if (self.research_query_target != DEFAULT_RESEARCH_QUERY_TARGET
            and self.adjudication_policy is not AdjudicationPolicy.CONCISE_KNOWLEDGE_V1):
            raise ValueError("research_query_target requires concise_knowledge_v1")
        return self

    @model_validator(mode="after")
    def search_mode_requires_parallel(self) -> Self:
        if not self.parallel_search and self.parallel_search_mode is not ParallelSearchMode.BASIC:
            raise ValueError("parallel_search_mode requires parallel_search: true")
        return self


def load_oracle_config(path: Path) -> OracleConfig:
    return OracleConfig.model_validate(load_yaml_unique(path))
