from __future__ import annotations

from pathlib import Path
from typing import Literal

from deep20_game.config import BenchmarkMode, GamePolicy, ModelConfig
from deep20_oracle.cache_contract import oracle_contract_hash
from deep20_oracle.config import OracleConfig, validate_prompt_profiles
from deep20_oracle.models import StrictModel
from deep20_oracle.util import canonical_json, load_yaml_unique, sha256_text
from pydantic import Field, field_validator, model_validator

from .models import (
    BenchmarkDefinitionSnapshot,
    BenchmarkId,
    BenchmarkModelId,
    BenchmarkModelSnapshot,
    SubjectId,
)


class ModelCatalogEntry(StrictModel):
    model_id: BenchmarkModelId
    display_name: str = Field(min_length=1, max_length=160)
    configuration: ModelConfig

    @field_validator("configuration")
    @classmethod
    def matching_configuration_id(cls, configuration: ModelConfig) -> ModelConfig:
        if configuration.configuration_id.startswith("M-") is False:
            raise ValueError("benchmark Guesser configuration_id must be an M- identifier")
        return configuration


class ModelCatalog(StrictModel):
    version: Literal[3] = 3
    models: dict[str, ModelCatalogEntry]

    @field_validator("models")
    @classmethod
    def matching_model_keys(
        cls, models: dict[str, ModelCatalogEntry]
    ) -> dict[str, ModelCatalogEntry]:
        for key, entry in models.items():
            if key != str(entry.model_id):
                raise ValueError(f"model key {key!r} does not match model_id")
            if entry.configuration.configuration_id != key:
                raise ValueError(f"configuration_id for {key!r} must match the model ID")
        return models

    def model(self, model_id: BenchmarkModelId) -> BenchmarkModelSnapshot:
        try:
            entry = self.models[str(model_id)]
        except KeyError as error:
            raise ValueError(f"unknown benchmark model {model_id!s}") from error
        configuration_hash = sha256_text(
            canonical_json(entry.configuration.model_dump(mode="json"))
        )
        return BenchmarkModelSnapshot(
            model_id=entry.model_id,
            display_name=entry.display_name,
            configuration=entry.configuration,
            configuration_hash=configuration_hash,
        )

    def registered_model_ids(self) -> tuple[BenchmarkModelId, ...]:
        return tuple(entry.model_id for entry in self.models.values())


class BenchmarkCatalogEntry(StrictModel):
    benchmark_id: BenchmarkId
    display_name: str = Field(min_length=1, max_length=160)
    default_iterations: int = Field(default=3, ge=1, le=100)
    game_policy: GamePolicy
    oracle_configuration: OracleConfig
    validator_configuration: ModelConfig

    @model_validator(mode="after")
    def matching_answer_protocols(self) -> BenchmarkCatalogEntry:
        validate_prompt_profiles(
            self.game_policy.prompt_profile, self.oracle_configuration.prompt_profile,
        )
        return self


class BenchmarkCatalog(StrictModel):
    version: Literal[2] = 2
    benchmarks: dict[str, BenchmarkCatalogEntry]

    @field_validator("benchmarks")
    @classmethod
    def matching_benchmark_keys(
        cls, benchmarks: dict[str, BenchmarkCatalogEntry]
    ) -> dict[str, BenchmarkCatalogEntry]:
        for key, entry in benchmarks.items():
            if key != str(entry.benchmark_id):
                raise ValueError(f"benchmark key {key!r} does not match benchmark_id")
        return benchmarks

    def benchmark(
        self,
        benchmark_id: BenchmarkId,
        *,
        benchmark_mode: BenchmarkMode,
        subject_ids: tuple[SubjectId, ...],
        iterations_override: int | None = None,
    ) -> BenchmarkDefinitionSnapshot:
        entry = self.entry(benchmark_id)
        if benchmark_mode is BenchmarkMode.OFFICIAL and any(
            route.gateway != "openrouter"
            for route in (
                entry.oracle_configuration,
                entry.oracle_configuration.reviewer,
                entry.oracle_configuration.judge,
                entry.validator_configuration,
            )
        ):
            raise ValueError("interactive adjudication requires experimental benchmark mode")
        iterations = iterations_override or entry.default_iterations
        game_policy = GamePolicy.model_validate(
            {**entry.game_policy.model_dump(), "benchmark_mode": benchmark_mode}
        )
        unsigned = {
            **entry.model_dump(mode="json"),
            "oracle_contract_hash": oracle_contract_hash(entry.oracle_configuration),
            "game_policy": game_policy.model_dump(mode="json"),
            "subject_ids": [str(subject_id) for subject_id in subject_ids],
            "iterations": iterations,
        }
        return BenchmarkDefinitionSnapshot(
            benchmark_id=entry.benchmark_id,
            display_name=entry.display_name,
            subject_ids=subject_ids,
            iterations=iterations,
            game_policy=game_policy,
            oracle_configuration=entry.oracle_configuration,
            validator_configuration=entry.validator_configuration,
            definition_hash=sha256_text(canonical_json(unsigned)),
        )

    def entry(self, benchmark_id: BenchmarkId) -> BenchmarkCatalogEntry:
        try:
            return self.benchmarks[str(benchmark_id)]
        except KeyError as error:
            raise ValueError(f"unknown benchmark {benchmark_id!s}") from error


def load_model_catalog(path: Path) -> ModelCatalog:
    return ModelCatalog.model_validate(load_yaml_unique(path))


def load_benchmark_catalog(path: Path) -> BenchmarkCatalog:
    from .edition_profiles import load_profile, profile_policy

    payload = load_yaml_unique(path)
    if not isinstance(payload, dict) or not isinstance(payload.get("benchmarks"), dict):
        raise TypeError("invalid benchmark catalog")
    for key, entry in payload["benchmarks"].items():
        if isinstance(entry, dict) and "edition_profile" in entry:
            if set(entry) != {"edition_profile"} or not isinstance(entry["edition_profile"], str):
                raise ValueError("edition-backed benchmarks cannot override profile fields")
            profile = load_profile(path.parent / entry["edition_profile"])
            payload["benchmarks"][key] = {
                "benchmark_id": profile.cohort.benchmark_id,
                "display_name": f"Deep20Bench Edition {profile.cohort.edition_label}",
                "default_iterations": profile.cohort.iterations,
                "game_policy": profile_policy(profile, BenchmarkMode.OFFICIAL).model_dump(),
                "oracle_configuration": profile.oracle_configuration,
                "validator_configuration": profile.validator_configuration,
            }
    return BenchmarkCatalog.model_validate(payload)
