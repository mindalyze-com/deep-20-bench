from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import JsonValue, ValidationError

from deep20_publication.cli import _edition_route_manifest, read_publication_config
from deep20_publication.model_pages import build_model_pages, model_slug
from deep20_publication.models import (
    ModelSlugPin,
    PublicationDataBundle,
    PublicationModelDocument,
    PublicSupersededRun,
    PublishedDataset,
)
from deep20_publication.split import edition_index, split_publication

REPOSITORY = Path(__file__).resolve().parents[4]
FORBIDDEN_FIELDS = {
    "call_id", "guesser_conversation", "system_instructions", "variation_token",
    "raw_response", "reviewer_answer", "judge_answer", "provider_trace", "response_id",
    "session_id", "cache_key", "error_outputs", "recorded_output", "evidence", "turns",
}


def _datasets() -> tuple[PublishedDataset, ...]:
    config = read_publication_config(REPOSITORY / "config/publication.yml")
    return tuple(
        PublishedDataset.model_validate_json(
            (REPOSITORY / "docs/data/editions" / cohort.edition_id / "deep20bench-v10.json")
            .read_text(encoding="utf-8")
        )
        for cohort in config.cohorts
    )


def _bundles() -> tuple[PublicationDataBundle, ...]:
    return tuple(split_publication(dataset) for dataset in _datasets())


def _keys(value: JsonValue) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {key for item in value.values() for key in _keys(item)}
    if isinstance(value, list):
        return {key for item in value for key in _keys(item)}
    return set()


@pytest.mark.parametrize(("name", "slug"), [
    ("GPT-6 Astra (high)", "gpt-6-astra-high"),
    ("Claude Opus 5.5 (high)", "claude-opus-5-5-high"),
    ("Llama 4 Maverick (non-thinking)", "llama-4-maverick-non-thinking"),
    ("GLM-5.3-Flash (high)", "glm-5-3-flash-high"),
    ("  Señor Model ++ (medium) ", "senor-model-medium"),
])
def test_model_slug_is_derived_from_the_display_name(name: str, slug: str) -> None:
    assert model_slug(name) == slug


def test_model_slug_rejects_names_without_url_characters() -> None:
    with pytest.raises(ValueError):
        model_slug("(+)")


def test_every_published_model_gets_one_page_per_edition() -> None:
    bundles = _bundles()
    pages = build_model_pages(bundles, (), {})

    assert tuple(item.edition_id for item in pages) == tuple(
        bundle.manifest.edition_id for bundle in bundles
    )
    for bundle, edition in zip(bundles, pages, strict=True):
        selected = {
            row.model.model_id: row.execution_id
            for row in bundle.leaderboard.leaderboard
            if row.execution_id is not None
        }
        assert {model.result.model.model_id: model.result.execution_id
                for model in edition.models} == selected
        assert len({model.slug for model in edition.models}) == len(edition.models)
        assert {entry.slug for entry in edition.index.models} == {
            model.slug for model in edition.models
        }
        names = [entry.model.display_name.casefold() for entry in edition.index.models]
        assert names == sorted(names)
        for model in edition.models:
            assert model.slug == model_slug(model.result.model.display_name)
            assert model.iterations == bundle.manifest.active_cohort.iterations
            assert model.max_questions == bundle.manifest.active_cohort.max_questions


def test_subject_ranks_compare_every_model_with_shared_competition_ranks() -> None:
    bundles = _bundles()
    for bundle, edition in zip(bundles, build_model_pages(bundles, (), {}), strict=True):
        averages: dict[str, list[Decimal]] = {}
        for run in bundle.runs:
            for summary in run.subjects:
                if summary.average_questions is not None:
                    averages.setdefault(summary.target_id, []).append(summary.average_questions)
        for model in edition.models:
            for subject in model.subjects:
                assert subject.average_questions is not None
                values = averages[subject.target_id]
                assert subject.ranked_models == len(values)
                assert subject.rank == 1 + sum(value < subject.average_questions for value in values)
                assert [item.trial_number for item in subject.rounds] == sorted(
                    item.trial_number for item in subject.rounds
                )


def test_observations_follow_fixed_rules_and_cite_their_rounds() -> None:
    bundles = _bundles()
    for edition in build_model_pages(bundles, (), {}):
        for model in edition.models:
            kinds = [observation.kind for observation in model.observations]
            order = [
                "strongest_subject", "hardest_subject", "fewest_questions", "most_questions",
                "uneven_subject", "wrong_guesses", "model_failure", "format_errors",
            ]
            assert kinds == sorted(kinds, key=order.index)
            assert kinds.count("strongest_subject") == min(2, len(model.subjects))
            assert kinds.count("hardest_subject") <= 2
            subjects = {subject.target_id: subject for subject in model.subjects}
            strongest = [item for item in model.observations if item.kind == "strongest_subject"]
            hardest = [item for item in model.observations if item.kind == "hardest_subject"]
            assert {item.target_id for item in strongest}.isdisjoint(
                {item.target_id for item in hardest}
            )
            best_rank = min(subject.rank for subject in subjects.values() if subject.rank)
            assert strongest[0].count == best_rank

            rounds = [item for subject in model.subjects for item in subject.rounds]
            failed = [item for item in rounds if item.status == "model_failure"]
            assert kinds.count("model_failure") == len(failed)
            format_errors = [item for item in model.observations if item.kind == "format_errors"]
            assert sum(item.format_errors for item in rounds) == (
                format_errors[0].count if format_errors else 0
            )
            assert model.result.contract is not None
            assert sum(item.format_errors for item in rounds) == model.result.contract.violations
            solved = [item.counted_questions for item in rounds if item.status == "success"]
            fewest = next(item for item in model.observations if item.kind == "fewest_questions")
            assert fewest.count == min(solved)


def test_model_pages_link_the_same_model_in_other_editions() -> None:
    bundles = _bundles()
    pages = build_model_pages(bundles, (), {})
    slugs = {
        (edition.edition_id, model.result.model.model_id): model.slug
        for edition in pages
        for model in edition.models
    }
    shared = 0
    for edition in pages:
        for model in edition.models:
            for link in model.other_editions:
                assert link.edition_id != edition.edition_id
                assert slugs[(link.edition_id, model.result.model.model_id)] == link.slug
                shared += 1
    assert shared > 0


def test_slug_pins_keep_previous_addresses_and_reject_conflicts() -> None:
    bundles = _bundles()
    model = bundles[0].leaderboard.leaderboard[0].model
    current = model_slug(model.display_name)
    pin = ModelSlugPin(model_id=model.model_id, slug="pinned-name", previous_slugs=(current,))
    pages = build_model_pages(bundles, (pin,), {})
    edition = pages[0]
    assert next(
        item for item in edition.models if item.result.model.model_id == model.model_id
    ).slug == "pinned-name"
    assert edition.slug_aliases == {current: "pinned-name"}

    with pytest.raises(ValueError, match="unpublished"):
        build_model_pages(bundles, (ModelSlugPin(model_id="M-9999", slug="ghost"),), {})
    other = bundles[0].leaderboard.leaderboard[1].model
    with pytest.raises(ValueError, match="not unique"):
        build_model_pages(bundles, (ModelSlugPin(
            model_id=model.model_id, slug=model_slug(other.display_name),
        ),), {})
    with pytest.raises(ValueError, match="still in use"):
        build_model_pages(bundles, (ModelSlugPin(
            model_id=model.model_id, previous_slugs=(model_slug(other.display_name),),
        ),), {})
    with pytest.raises(ValidationError):
        ModelSlugPin(model_id=model.model_id, slug="Not A Slug")


def test_model_routes_are_canonical_and_replaced_runs_alias_the_model_page() -> None:
    config = read_publication_config(REPOSITORY / "config/publication.yml")
    datasets = _datasets()
    bundles = tuple(split_publication(dataset) for dataset in datasets)
    edition_id = config.default_edition_id
    bundle = next(item for item in bundles if item.manifest.edition_id == edition_id)
    model_id = bundle.leaderboard.leaderboard[0].model.model_id
    replaced = PublicSupersededRun(
        execution_id="BX-20260101-B-0003-official-M9999-001",
        completed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    pages = build_model_pages(bundles, (), {edition_id: {model_id: (replaced,)}})
    routes = {entry.route: entry for entry in _edition_route_manifest(config, datasets, pages).routes}
    edition = next(item for item in pages if item.edition_id == edition_id)
    document = next(item for item in edition.models if item.result.model.model_id == model_id)
    canonical = f"editions/{edition_id}/models/{document.slug}"

    labels = {item.manifest.edition_id: item.manifest.active_cohort.edition_label for item in bundles}
    for item in pages:
        prefix = f"editions/{item.edition_id}/models"
        assert routes[prefix].kind == "model-index"
        assert routes[prefix].sitemap_included
        for model in item.models:
            entry = routes[f"{prefix}/{model.slug}"]
            assert entry.kind == "model"
            assert entry.sitemap_included
            assert entry.canonical_route == entry.route
            assert entry.model_id == model.result.model.model_id
            assert entry.browser_title == (
                f"{model.result.model.display_name} Twenty Questions Results | "
                f"Deep20Bench {labels[item.edition_id]}"
            )
            assert model.result.model.display_name in entry.description
    assert routes[f"models/{document.slug}"].canonical_route == canonical
    assert not routes[f"models/{document.slug}"].sitemap_included
    alias = routes[f"runs/{replaced.execution_id}"]
    assert alias.kind == "alias"
    assert alias.canonical_route == canonical
    assert not alias.sitemap_included
    assert alias.model_id == model_id
    assert alias.edition_id == edition_id
    assert len([entry for entry in routes.values() if entry.kind == "model"
                and entry.sitemap_included]) == sum(len(item.models) for item in pages)


def test_edition_index_lists_model_slugs_and_documents_stay_public() -> None:
    config = read_publication_config(REPOSITORY / "config/publication.yml")
    datasets = _datasets()
    pages = build_model_pages(tuple(split_publication(item) for item in datasets), (), {})
    index = edition_index(config, datasets, pages)
    assert index.schema_version == 2
    for reference, edition in zip(index.editions, pages, strict=True):
        assert {(item.model_id, item.slug) for item in reference.models} == {
            (model.result.model.model_id, model.slug) for model in edition.models
        }
        for model in edition.models:
            serialized = json.loads(model.model_dump_json())
            assert not _keys(serialized) & FORBIDDEN_FIELDS
            assert PublicationModelDocument.model_validate(serialized) == model


def test_model_documents_reject_observations_without_published_rounds() -> None:
    bundles = _bundles()
    model = build_model_pages(bundles, (), {})[0].models[0]
    observation = model.observations[0].model_copy(update={
        "rounds": (model.observations[0].rounds[0].model_copy(update={"trial_id": "trial-999"}),),
    })
    with pytest.raises(ValidationError, match="published rounds"):
        PublicationModelDocument.model_validate({
            **model.model_dump(), "observations": (observation.model_dump(),),
        })
