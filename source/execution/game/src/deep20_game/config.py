from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Literal

from deep20_oracle.config import RecoveryPolicy
from deep20_oracle.util import load_yaml_unique
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CachePolicy(StrEnum):
    REQUIRED = "required"
    BEST_EFFORT = "best_effort"


class CacheControl(StrEnum):
    AUTOMATIC = "automatic"
    EPHEMERAL_5M = "ephemeral_5m"
    EPHEMERAL_1H = "ephemeral_1h"


class BenchmarkMode(StrEnum):
    OFFICIAL = "official"
    EXPERIMENTAL = "experimental"


class SeedCapability(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"


class ReasoningControl(StrEnum):
    EFFORT = "effort"
    GENERIC = "generic"


class StructuredOutputMode(StrEnum):
    STRICT_JSON_SCHEMA = "strict_json_schema"
    JSON_OBJECT = "json_object"


class PromptCacheConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    policy: CachePolicy = CachePolicy.BEST_EFFORT
    control: CacheControl = CacheControl.AUTOMATIC
    minimum_cacheable_tokens: int = Field(default=1_024, ge=1)
    ttl_seconds: int = Field(default=300, ge=1, le=3_600)
    input_usd_per_million: Decimal = Field(ge=0)
    cached_input_usd_per_million: Decimal = Field(ge=0)
    cache_write_multiplier: Decimal = Field(default=Decimal(1), ge=0)


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    configuration_id: str = Field(
        min_length=1,
        max_length=80,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
    )
    gateway: str = Field(default="openrouter", pattern=r"^openrouter$")
    model: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    reasoning_effort: str = Field(default="high", min_length=1)
    reasoning_control: ReasoningControl = Field(
        default=ReasoningControl.EFFORT,
        exclude_if=lambda value: value is ReasoningControl.EFFORT,
    )
    structured_output_mode: StructuredOutputMode = Field(
        default=StructuredOutputMode.STRICT_JSON_SCHEMA,
        exclude_if=lambda value: value is StructuredOutputMode.STRICT_JSON_SCHEMA,
    )
    allow_fallbacks: bool = False
    max_output_tokens: int = Field(default=4_096, ge=128, le=65_536)
    timeout_seconds: int = Field(default=120, ge=1, le=600)
    recovery: RecoveryPolicy = Field(default_factory=RecoveryPolicy)
    seed_capability: SeedCapability = SeedCapability.UNSUPPORTED
    prompt_cache: PromptCacheConfig

    @model_validator(mode="after")
    def exact_route(self) -> ModelConfig:
        if "/" not in self.model:
            raise ValueError("model must be an exact provider/model slug")
        if (
            self.reasoning_control is ReasoningControl.GENERIC
            and self.reasoning_effort.casefold() == "none"
        ):
            raise ValueError("generic reasoning control requires an enabled effort")
        return self


class GamePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal[9] = 9
    benchmark_mode: BenchmarkMode = BenchmarkMode.EXPERIMENTAL
    max_questions: int = Field(default=50, ge=1, le=100)
    max_consecutive_contract_violations: int = Field(default=5, ge=1, le=100)
    reveal_entity_type: Literal[True] = True
    final_guess_after_limit: Literal[True] = True
    include_oracle_evidence: bool = True
    include_guesser_conversation: bool = True


def load_model_config(path: Path) -> ModelConfig:
    return ModelConfig.model_validate(load_yaml_unique(path))


def load_game_policy(path: Path) -> GamePolicy:
    return GamePolicy.model_validate(load_yaml_unique(path))
