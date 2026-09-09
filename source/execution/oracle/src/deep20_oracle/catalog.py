from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from .models import Subject
from .util import load_yaml_unique, sha256_text


class SubjectStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class SubjectCatalogEntry(Subject):
    status: SubjectStatus = SubjectStatus.ACTIVE

    def to_subject(self) -> Subject:
        """Project identity only; catalog scheduling metadata never enters a call."""
        return Subject(
            target_id=self.target_id,
            canonical_name=self.canonical_name,
            aliases=self.aliases,
            entity_type=self.entity_type,
            description=self.description,
            reference_url=self.reference_url,
        )


class SubjectCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal[1] = 1
    subjects: dict[str, SubjectCatalogEntry]

    @field_validator("subjects")
    @classmethod
    def matching_ids(
        cls, subjects: dict[str, SubjectCatalogEntry],
    ) -> dict[str, SubjectCatalogEntry]:
        for target_id, subject in subjects.items():
            if target_id != subject.target_id:
                raise ValueError(f"catalog key {target_id!r} differs from subject target_id")
        return subjects

    def entry(self, target_id: str) -> SubjectCatalogEntry:
        try:
            return self.subjects[target_id]
        except KeyError as error:
            raise ValueError(f"unknown subject {target_id!r}") from error

    def subject(self, target_id: str) -> Subject:
        return self.entry(target_id).to_subject()

    def active_subjects(self) -> tuple[Subject, ...]:
        return tuple(
            entry.to_subject()
            for entry in self.subjects.values()
            if entry.status is SubjectStatus.ACTIVE
        )

    def content_hash(self) -> str:
        # The signed schedule records selection. Status changes must not invalidate
        # historical subject identities or alter an existing execution's context.
        payload = self.model_dump(
            mode="json", exclude={"subjects": {"__all__": {"status"}}},
        )
        return sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def load_subject_catalog(path: Path) -> SubjectCatalog:
    return SubjectCatalog.model_validate(load_yaml_unique(path))
