from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .util import load_yaml_unique

OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"
OPENROUTER_SECRET_PATHS = (
    Path("private/openrouter.yml"),
    Path("private/openrouter.yaml"),
)


class CredentialLoadError(ValueError):
    """A required credential is absent or its private file is malformed."""

    def __init__(self, message: str, *, code: str):
        super().__init__(message)
        self.code = code


class _OpenRouterApiSecrets(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True, str_strip_whitespace=True)

    api_key: str = Field(min_length=1)


class _OpenRouterSecretFile(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    api: _OpenRouterApiSecrets


def load_openrouter_api_key(
    repository: Path,
    *,
    environ: Mapping[str, str] | None = None,
) -> str:
    """Load the OpenRouter key without exposing it through config or logs.

    Environment variables take precedence for CI and one-off overrides. Local development uses
    the ignored private YAML file, preferring the project's canonical ``.yml`` spelling while
    accepting the existing ``.yaml`` spelling.
    """

    environment = os.environ if environ is None else environ
    environment_value = environment.get(OPENROUTER_API_KEY_ENV, "").strip()
    if environment_value:
        return environment_value

    for relative_path in OPENROUTER_SECRET_PATHS:
        path = repository / relative_path
        if not path.is_file():
            continue
        try:
            secrets = _OpenRouterSecretFile.model_validate(load_yaml_unique(path))
        except (OSError, ValidationError, ValueError) as error:
            raise CredentialLoadError(
                f"Invalid OpenRouter credential file {relative_path}: "
                "expected a non-empty api.api_key",
                code="invalid_api_key_file",
            ) from error
        return secrets.api.api_key

    checked = ", ".join(str(path) for path in OPENROUTER_SECRET_PATHS)
    raise CredentialLoadError(
        f"OpenRouter API key not found; set {OPENROUTER_API_KEY_ENV} "
        f"or create one of: {checked}",
        code="missing_api_key",
    )
