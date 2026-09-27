"""Separate Parallel credentials loaded only by the benchmark composition roots."""

import os
from collections.abc import Mapping
from pathlib import Path

from deep20_oracle.credentials import CredentialLoadError
from deep20_oracle.util import load_yaml_unique
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class _Api(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True, str_strip_whitespace=True)
    api_key: str = Field(min_length=1)


class _Secrets(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)
    api: _Api


def load_parallel_api_key(repository: Path, *, environ: Mapping[str, str] | None = None) -> str:
    environment = os.environ if environ is None else environ
    value = environment.get("PARALLEL_API_KEY", "").strip()
    if value:
        return value
    for name in ("parallel.yml", "parallel.yaml"):
        path = repository / "private" / name
        if not path.is_file():
            continue
        try:
            return _Secrets.model_validate(load_yaml_unique(path)).api.api_key
        except (OSError, ValueError, ValidationError):
            raise CredentialLoadError("Invalid private Parallel credential file; expected api.api_key",
                                      code="invalid_parallel_key_file") from None
    raise CredentialLoadError("Parallel key missing; set PARALLEL_API_KEY or private/parallel.yml api.api_key",
                              code="missing_parallel_key")
