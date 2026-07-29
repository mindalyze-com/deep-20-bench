from pathlib import Path

import pytest
from deep20_benchmark.catalog import load_benchmark_catalog, load_model_catalog
from deep20_benchmark.models import BenchmarkId, SubjectId
from deep20_game.config import BenchmarkMode
from pydantic import ValidationError


def test_repository_benchmark_enables_parallel_oracle_search() -> None:
    root = Path(__file__).parents[2]
    catalog = load_benchmark_catalog(root / "config" / "benchmarks.yaml")

    definition = catalog.benchmark(
        BenchmarkId("B-0001"),
        benchmark_mode=BenchmarkMode.OFFICIAL,
        subject_ids=(SubjectId("T-0001"),),
    )

    assert definition.oracle_configuration.parallel_search is True
    assert (
        definition.oracle_configuration.reviewer.model
        == "google/gemini-3.5-flash-lite"
    )
    assert definition.oracle_configuration.reviewer.provider == "google-ai-studio"
    assert definition.oracle_configuration.reviewer.reasoning_effort == "medium"
    assert (
        definition.oracle_configuration.judge.model == "anthropic/claude-opus-5"
    )
    assert definition.oracle_configuration.judge.provider == "anthropic"
    assert definition.oracle_configuration.judge.reasoning_effort == "medium"
    assert (
        len(
            {
                definition.oracle_configuration.provider,
                definition.oracle_configuration.reviewer.provider,
                definition.oracle_configuration.judge.provider,
            }
        )
        == 3
    )
    assert definition.iterations == 3
    assert definition.game_policy.benchmark_mode is BenchmarkMode.OFFICIAL


def test_request_mode_overrides_catalog_template_and_changes_definition_hash() -> None:
    root = Path(__file__).parents[2]
    catalog = load_benchmark_catalog(root / "config" / "benchmarks.yaml")
    subject_ids = (SubjectId("T-0001"),)

    official = catalog.benchmark(
        BenchmarkId("B-0001"),
        benchmark_mode=BenchmarkMode.OFFICIAL,
        subject_ids=subject_ids,
    )
    experimental = catalog.benchmark(
        BenchmarkId("B-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        subject_ids=subject_ids,
    )

    assert official.game_policy.benchmark_mode is BenchmarkMode.OFFICIAL
    assert experimental.game_policy.benchmark_mode is BenchmarkMode.EXPERIMENTAL
    assert official.definition_hash != experimental.definition_hash


def test_catalogs_reject_retired_versions() -> None:
    root = Path(__file__).parents[2]
    benchmarks = load_benchmark_catalog(root / "config" / "benchmarks.yaml")
    models = load_model_catalog(root / "config" / "models.yaml")

    with pytest.raises(ValidationError, match="Input should be 2"):
        benchmarks.__class__.model_validate(
            {**benchmarks.model_dump(mode="json"), "version": 1}
        )
    with pytest.raises(ValidationError, match="Input should be 3"):
        models.__class__.model_validate(
            {**models.model_dump(mode="json"), "version": 2}
        )
