from pathlib import Path

import pytest
from deep20_benchmark.catalog import load_benchmark_catalog, load_model_catalog
from deep20_benchmark.models import BenchmarkId, SubjectId
from deep20_game.config import BenchmarkMode
from deep20_oracle import cache_contract
from deep20_oracle.config import (
    ParallelSearchMode,
    PromptProfile,
    ProviderRouting,
    TokenLimitParameter,
)
from pydantic import ValidationError


def test_oracle_service_contract_changes_definition_without_changing_model_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    catalog = load_benchmark_catalog(Path(__file__).parents[4] / "config/benchmarks.yaml")
    arguments = {
        "benchmark_mode": BenchmarkMode.EXPERIMENTAL,
        "subject_ids": (SubjectId("T-0001"),),
    }
    current = catalog.benchmark(BenchmarkId("B-0003"), **arguments)
    monkeypatch.setattr(cache_contract, "ORACLE_FACTUAL_CONTRACT_VERSION", "historical_ask_v1")
    previous = catalog.benchmark(BenchmarkId("B-0003"), **arguments)
    assert current.definition_hash != previous.definition_hash
    assert current.oracle_configuration == previous.oracle_configuration
    assert current.game_policy == previous.game_policy


@pytest.mark.parametrize("benchmark_id", ["B-0001", "B-0002", "B-0003"])
def test_repository_benchmarks_use_40_questions_with_a_new_definition_hash(
    benchmark_id: str,
) -> None:
    catalog = load_benchmark_catalog(Path(__file__).parents[4] / "config/benchmarks.yaml")
    identifier = BenchmarkId(benchmark_id)
    definition = catalog.benchmark(
        identifier,
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        subject_ids=(SubjectId("T-0001"),),
    )
    assert definition.game_policy.max_questions == 40
    assert definition.game_policy.final_guess_after_limit is True

    entry = catalog.entry(identifier)
    historical_entry = entry.model_copy(update={
        "game_policy": entry.game_policy.model_copy(update={"max_questions": 50}),
    })
    historical_catalog = catalog.model_copy(update={
        "benchmarks": {**catalog.benchmarks, benchmark_id: historical_entry},
    })
    historical = historical_catalog.benchmark(
        identifier,
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        subject_ids=(SubjectId("T-0001"),),
    )
    assert definition.definition_hash != historical.definition_hash


@pytest.mark.parametrize("benchmark_id", ["B-0001", "B-0002", "B-0003"])
def test_repository_search_mode_is_fast_and_changes_definition_hash(benchmark_id: str) -> None:
    catalog = load_benchmark_catalog(Path(__file__).parents[4] / "config/benchmarks.yaml")
    entry = catalog.entry(BenchmarkId(benchmark_id))
    assert entry.oracle_configuration.parallel_search_mode is ParallelSearchMode.FAST
    assert entry.oracle_configuration.model_dump(mode="json")["parallel_search_mode"] == "fast"
    legacy = entry.model_copy(update={
        "oracle_configuration": entry.oracle_configuration.model_copy(update={
            "parallel_search_mode": ParallelSearchMode.BASIC,
        }),
    })
    historical_catalog = catalog.model_copy(update={
        "benchmarks": {**catalog.benchmarks, benchmark_id: legacy},
    })
    definition = catalog.benchmark(
        BenchmarkId(benchmark_id), benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        subject_ids=(SubjectId("T-0001"),),
    )
    historical = historical_catalog.benchmark(
        BenchmarkId(benchmark_id), benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        subject_ids=(SubjectId("T-0001"),),
    )
    assert definition.definition_hash != historical.definition_hash


def test_repository_benchmark_enables_parallel_oracle_search() -> None:
    root = Path(__file__).parents[4]
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
        definition.oracle_configuration.reviewer.token_limit_parameter
        is TokenLimitParameter.MAX_TOKENS
    )
    assert (
        definition.oracle_configuration.judge.model == "anthropic/claude-opus-5"
    )
    assert definition.oracle_configuration.judge.provider == "openrouter-auto"
    assert (
        definition.oracle_configuration.judge.provider_routing
        is ProviderRouting.AUTOMATIC
    )
    assert definition.oracle_configuration.judge.allow_fallbacks is True
    assert (
        definition.oracle_configuration.judge.token_limit_parameter
        is TokenLimitParameter.MAX_TOKENS
    )
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
    root = Path(__file__).parents[4]
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
    root = Path(__file__).parents[4]
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


def test_concise_experiment_preserves_routes_and_requires_experimental_mode() -> None:
    catalog = load_benchmark_catalog(Path(__file__).parents[4] / "config/benchmarks.yaml")
    standard = catalog.entry(BenchmarkId("B-0001"))
    revised = catalog.benchmark(
        BenchmarkId("B-0002"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        subject_ids=(SubjectId("T-0003"),),
    )
    assert revised.iterations == 5
    assert revised.game_policy.prompt_profile is PromptProfile.CONCISE_V1
    assert revised.oracle_configuration.prompt_profile is PromptProfile.CONCISE_V1
    assert revised.oracle_configuration.model_dump(exclude={"prompt_profile"}) == (
        standard.oracle_configuration.model_dump()
    )
    assert revised.validator_configuration == standard.validator_configuration
    assert "prompt_profile" not in standard.game_policy.model_dump()
    assert "prompt_profile" not in standard.oracle_configuration.model_dump()
    with pytest.raises(ValidationError, match="require experimental"):
        catalog.benchmark(
            BenchmarkId("B-0002"),
            benchmark_mode=BenchmarkMode.OFFICIAL,
            subject_ids=(SubjectId("T-0003"),),
        )


def test_five_answer_experiment_keeps_models_and_limits_default_repetitions() -> None:
    catalog = load_benchmark_catalog(Path(__file__).parents[4] / "config/benchmarks.yaml")
    original = catalog.entry(BenchmarkId("B-0001"))
    variant = catalog.entry(BenchmarkId("B-0003"))
    assert variant.default_iterations == 3
    assert variant.game_policy.prompt_profile is PromptProfile.QUALIFIED_V1
    assert variant.oracle_configuration.prompt_profile is PromptProfile.QUALIFIED_V1
    assert variant.oracle_configuration.adjudication_policy.value == "concise_knowledge_v1"
    assert variant.oracle_configuration.model_dump(
        exclude={"prompt_profile", "adjudication_policy"},
    ) == (
        original.oracle_configuration.model_dump()
    )
    assert variant.validator_configuration == original.validator_configuration
    with pytest.raises(ValidationError, match="selected together"):
        type(variant).model_validate({
            **variant.model_dump(), "game_policy": original.game_policy,
        })
    with pytest.raises(ValidationError, match="require experimental"):
        catalog.benchmark(BenchmarkId("B-0003"), benchmark_mode=BenchmarkMode.OFFICIAL,
            subject_ids=(SubjectId("T-0003"),))
