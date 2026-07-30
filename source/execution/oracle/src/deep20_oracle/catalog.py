from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from .models import Subject
from .util import load_yaml_unique, sha256_text


class SubjectCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal[1] = 1
    subjects: dict[str, Subject]

    @field_validator("subjects")
    @classmethod
    def matching_ids(cls, subjects: dict[str, Subject]) -> dict[str, Subject]:
        for target_id, subject in subjects.items():
            if target_id != subject.target_id:
                raise ValueError(f"catalog key {target_id!r} differs from subject target_id")
        return subjects

    def subject(self, target_id: str) -> Subject:
        try:
            return self.subjects[target_id]
        except KeyError as error:
            raise ValueError(f"unknown subject {target_id!r}") from error

    def content_hash(self) -> str:
        payload = self.model_dump(mode="json")
        return sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def load_subject_catalog(path: Path) -> SubjectCatalog:
    return SubjectCatalog.model_validate(load_yaml_unique(path))
