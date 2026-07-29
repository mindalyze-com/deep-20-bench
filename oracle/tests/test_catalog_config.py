from __future__ import annotations

from pathlib import Path

import pytest
from deep20_oracle.catalog import load_subject_catalog
from deep20_oracle.config import OracleConfig, load_oracle_config
from deep20_oracle.sinks import OracleSuccessRecord
from pydantic import ValidationError
from yaml.constructor import ConstructorError


def test_repository_configuration_and_catalog_are_valid() -> None:
    root = Path(__file__).parents[2]
    config = load_oracle_config(root / "config" / "oracle.yaml")
    catalog = load_subject_catalog(root / "config" / "subjects.yaml")

    assert config.gateway == "openrouter"
    assert config.parallel_search is True
    assert config.reviewer.model == "google/gemini-3.5-flash-lite"
    assert config.reviewer.provider == "google-ai-studio"
    assert config.reviewer.reasoning_effort == "medium"
    assert config.judge.model == "anthropic/claude-opus-5"
    assert config.judge.provider == "anthropic"
    assert config.judge.reasoning_effort == "medium"
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


def test_parallel_search_defaults_true_and_serializes_explicit_false() -> None:
    default_config = OracleConfig(model="openai/test-model", provider="openai")
    native_config = default_config.model_copy(update={"parallel_search": False})

    assert default_config.parallel_search is True
    assert native_config.model_dump(mode="json")["parallel_search"] is False


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

    root = Path(__file__).parents[2]
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
