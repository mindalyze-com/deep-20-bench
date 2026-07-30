from __future__ import annotations

from pathlib import Path

import pytest
from deep20_oracle.credentials import CredentialLoadError, load_openrouter_api_key


def test_loads_key_from_preferred_private_yml(tmp_path: Path) -> None:
    private = tmp_path / "private"
    private.mkdir()
    (private / "openrouter.yml").write_text(
        "api:\n  api_key: from-yml\n  base_url: https://openrouter.ai/api/v1\n"
    )
    (private / "openrouter.yaml").write_text("api:\n  api_key: from-yaml\n")

    assert load_openrouter_api_key(tmp_path, environ={}) == "from-yml"


def test_accepts_existing_private_yaml_spelling(tmp_path: Path) -> None:
    private = tmp_path / "private"
    private.mkdir()
    (private / "openrouter.yaml").write_text("api:\n  api_key: from-yaml\n")

    assert load_openrouter_api_key(tmp_path, environ={}) == "from-yaml"


def test_environment_overrides_private_file(tmp_path: Path) -> None:
    private = tmp_path / "private"
    private.mkdir()
    (private / "openrouter.yml").write_text("api:\n  api_key: from-file\n")

    assert (
        load_openrouter_api_key(
            tmp_path,
            environ={"OPENROUTER_API_KEY": "from-environment"},
        )
        == "from-environment"
    )


def test_missing_and_invalid_credentials_do_not_expose_values(tmp_path: Path) -> None:
    with pytest.raises(CredentialLoadError, match="OpenRouter API key not found") as missing:
        load_openrouter_api_key(tmp_path, environ={})
    assert missing.value.code == "missing_api_key"

    private = tmp_path / "private"
    private.mkdir()
    secret = "must-not-appear-in-errors"
    (private / "openrouter.yml").write_text(f"api:\n  wrong_field: {secret}\n")

    with pytest.raises(CredentialLoadError) as invalid:
        load_openrouter_api_key(tmp_path, environ={})
    assert invalid.value.code == "invalid_api_key_file"
    assert secret not in str(invalid.value)
