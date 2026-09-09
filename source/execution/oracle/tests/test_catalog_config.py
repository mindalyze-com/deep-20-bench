from __future__ import annotations

from pathlib import Path

import pytest
from deep20_oracle.catalog import SubjectCatalog, SubjectStatus, load_subject_catalog
from deep20_oracle.config import (
    OPENROUTER_AUTO_PROVIDER,
    EvidenceReviewConfig,
    OracleConfig,
    ParallelSearchMode,
    ProviderRouting,
    TokenLimitParameter,
    load_oracle_config,
)
from deep20_oracle.models import Subject
from deep20_oracle.sinks import OracleSuccessRecord
from pydantic import ValidationError
from yaml.constructor import ConstructorError


def test_repository_configuration_and_catalog_are_valid() -> None:
    root = Path(__file__).parents[4]
    config = load_oracle_config(root / "config" / "oracle.yaml")
    catalog = load_subject_catalog(root / "config" / "subjects.yaml")

    assert config.gateway == "openrouter"
    assert config.parallel_search is True
    assert config.parallel_search_mode is ParallelSearchMode.FAST
    assert config.reviewer.model == "google/gemini-3.5-flash-lite"
    assert config.reviewer.provider == "google-ai-studio"
    assert config.reviewer.reasoning_effort == "medium"
    assert (
        config.reviewer.token_limit_parameter
        is TokenLimitParameter.MAX_TOKENS
    )
    assert config.judge.model == "anthropic/claude-opus-5"
    assert config.judge.provider == "openrouter-auto"
    assert config.judge.provider_routing is ProviderRouting.AUTOMATIC
    assert config.judge.reasoning_effort == "medium"
    assert config.judge.allow_fallbacks is True
    assert config.judge.token_limit_parameter is TokenLimitParameter.MAX_TOKENS
    assert len({config.provider, config.reviewer.provider, config.judge.provider}) == 3
    assert catalog.subject("T-0001").canonical_name == "Albert Einstein"
    schweitzer = catalog.subject("T-0002")
    assert schweitzer.canonical_name == "Albert Schweitzer"
    assert schweitzer.aliases == ("Schweitzer", "Dr. Albert Schweitzer")
    assert "Q49325" in schweitzer.description
    king = catalog.subject("T-0003")
    assert king.canonical_name == "Stephen King"
    assert king.aliases == ("Stephen Edwin King", "Steven King", "Richard Bachman")
    assert "Q39829" in king.description
    garfield = catalog.subject("T-0004")
    assert garfield.canonical_name == "Garfield"
    assert garfield.aliases == ("Garfield the Cat",)
    assert garfield.entity_type == "fictional_character"
    assert "Q767120" in garfield.description
    achilles = catalog.subject("T-0005")
    assert achilles.canonical_name == "Achilles"
    assert achilles.aliases == ("Achilleus",)
    assert achilles.entity_type == "mythological_figure"
    assert "Q41746" in achilles.description
    genghis_khan = catalog.subject("T-0006")
    assert genghis_khan.canonical_name == "Genghis Khan"
    assert genghis_khan.aliases == ("Chinggis Khan", "Temüjin", "Temujin")
    assert genghis_khan.entity_type == "person"
    assert "Q720" in genghis_khan.description
    mario = catalog.subject("T-0007")
    assert mario.canonical_name == "Mario"
    assert mario.aliases == ("Super Mario", "Jumpman")
    assert mario.entity_type == "video_game_character"
    assert "Q12379" in mario.description
    assert len(catalog.content_hash()) == 64


def test_configuration_rejects_dynamic_model_selector() -> None:
    with pytest.raises(ValidationError, match="exact provider/model slug"):
        OracleConfig(model="auto", provider="openai")


def test_inactive_subjects_remain_registered_but_leave_the_active_set() -> None:
    root = Path(__file__).parents[4]
    catalog = load_subject_catalog(root / "config" / "subjects.yaml")

    assert len(catalog.subjects) == 12
    assert tuple(subject.target_id for subject in catalog.active_subjects()) == (
        "T-0001", "T-0002", "T-0004", "T-0005", "T-0006",
        "T-0008", "T-0009", "T-0010", "T-0011", "T-0012",
    )
    assert catalog.entry("T-0001").status is SubjectStatus.ACTIVE
    for target_id in ("T-0003", "T-0007"):
        assert catalog.entry(target_id).status is SubjectStatus.INACTIVE
        assert type(catalog.subject(target_id)) is Subject
        assert "status" not in catalog.subject(target_id).model_dump()


def test_status_round_trips_without_changing_identity_or_its_hash() -> None:
    root = Path(__file__).parents[4]
    catalog = load_subject_catalog(root / "config" / "subjects.yaml")
    reactivated = SubjectCatalog(
        subjects={
            key: entry.model_copy(update={"status": SubjectStatus.ACTIVE})
            for key, entry in catalog.subjects.items()
        },
    )
    assert len(reactivated.active_subjects()) == 12
    assert reactivated.content_hash() == catalog.content_hash()
    for target_id in catalog.subjects:
        assert reactivated.subject(target_id) == catalog.subject(target_id)
    assert SubjectCatalog.model_validate(catalog.model_dump(mode="json")) == catalog

    changed_identity = SubjectCatalog(
        subjects={
            **catalog.subjects,
            "T-0003": catalog.entry("T-0003").model_copy(update={"description": "Changed."}),
        },
    )
    assert changed_identity.content_hash() != catalog.content_hash()


@pytest.mark.parametrize("status", ["active", "inactive"])
def test_identity_hash_matches_the_publication_contract(status: str) -> None:
    catalog = SubjectCatalog.model_validate({
        "version": 1,
        "subjects": {"T-0001": {
            "target_id": "T-0001", "canonical_name": "Türfalle",
            "entity_type": "thing", "description": "Door handle.", "status": status,
        }},
    })
    assert catalog.content_hash() == (
        "24f8603c7790a366788e4840fbd3f3b8ce91dce2b16e75a6b58f6fb9c60a4345"
    )


@pytest.mark.parametrize("status", ["disabled", "retired", True, None])
def test_catalog_rejects_invalid_subject_status(status: str | bool | None) -> None:
    root = Path(__file__).parents[4]
    catalog = load_subject_catalog(root / "config" / "subjects.yaml")
    with pytest.raises(ValidationError, match="status"):
        type(catalog.entry("T-0001")).model_validate({
            **catalog.entry("T-0001").model_dump(), "status": status,
        })


def test_parallel_search_defaults_true_and_serializes_explicit_false() -> None:
    default_config = OracleConfig(model="openai/test-model", provider="openai")
    native_config = default_config.model_copy(update={"parallel_search": False})

    assert default_config.parallel_search is True
    assert native_config.model_dump(mode="json")["parallel_search"] is False


def test_search_mode_preserves_old_serialization_and_records_fast() -> None:
    legacy = OracleConfig(model="openai/test-model", provider="openai")
    assert legacy.parallel_search_mode is ParallelSearchMode.BASIC
    assert "parallel_search_mode" not in legacy.model_dump(mode="json")
    fast = OracleConfig.model_validate({
        **legacy.model_dump(mode="json"), "parallel_search_mode": "fast",
    })
    assert fast.parallel_search_mode is ParallelSearchMode.FAST
    assert fast.model_dump(mode="json")["parallel_search_mode"] == "fast"
    assert OracleConfig.model_validate(fast.model_dump(mode="json")) == fast
    with pytest.raises(ValidationError, match="requires parallel_search"):
        OracleConfig.model_validate({
            **fast.model_dump(mode="json"), "parallel_search": False,
        })
    with pytest.raises(ValidationError, match="parallel_search_mode"):
        OracleConfig.model_validate({
            **legacy.model_dump(mode="json"), "parallel_search_mode": "invalid",
        })


def test_exact_route_serialization_is_legacy_compatible() -> None:
    config = EvidenceReviewConfig(
        model="anthropic/claude-opus-5",
        provider="anthropic",
    )

    assert "provider_routing" not in config.model_dump(mode="json")
    assert "token_limit_parameter" not in config.model_dump(mode="json")


def test_automatic_route_requires_explicit_auto_provider_and_fallbacks() -> None:
    config = EvidenceReviewConfig(
        model="anthropic/claude-opus-5",
        provider=OPENROUTER_AUTO_PROVIDER,
        provider_routing=ProviderRouting.AUTOMATIC,
        allow_fallbacks=True,
    )

    assert config.model_dump(mode="json")["provider_routing"] == "automatic"
    with pytest.raises(ValidationError, match="requires provider fallbacks"):
        EvidenceReviewConfig.model_validate(
            {
                **config.model_dump(mode="json"),
                "allow_fallbacks": False,
            }
        )


def test_oracle_contract_rejects_retired_versions() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        OracleConfig.model_validate(
            {
                "model": "openai/test-model",
                "provider": "openai",
                "transient_retry_max_seconds": 75,
            }
        )
    with pytest.raises(ValidationError, match="Input should be 5"):
        OracleSuccessRecord.model_validate({"schema_version": 4})

    root = Path(__file__).parents[4]
    catalog = load_subject_catalog(root / "config" / "subjects.yaml")
    with pytest.raises(ValidationError, match="Input should be 1"):
        catalog.__class__.model_validate(
            {**catalog.model_dump(mode="json"), "version": 0}
        )


def test_yaml_loaders_reject_duplicate_keys(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.yaml"
    path.write_text("model: openai/one\nmodel: openai/two\n")
    with pytest.raises(ConstructorError, match="duplicate key"):
        load_oracle_config(path)
