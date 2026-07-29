from __future__ import annotations

from pathlib import Path
from typing import Literal

from deep20_game.config import BenchmarkMode, GamePolicy, ModelConfig
from deep20_oracle.config import OracleConfig
from deep20_oracle.models import StrictModel
from deep20_oracle.util import canonical_json, load_yaml_unique, sha256_text
from pydantic import Field, field_validator

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
        iterations = iterations_override or entry.default_iterations
        game_policy = entry.game_policy.model_copy(update={"benchmark_mode": benchmark_mode})
        unsigned = {
            **entry.model_dump(mode="json"),
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
    return BenchmarkCatalog.model_validate(load_yaml_unique(path))
