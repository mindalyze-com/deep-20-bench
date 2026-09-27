"""Edition registry contract, usable without importing benchmark execution."""

from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from .models import FrozenModel


class EditionStatus(StrEnum):
    PREVIOUS = "previous"
    CURRENT = "current"
    DRAFT = "draft"


class Edition(FrozenModel):
    edition_id: str = Field(pattern=r"^[0-9]+\.[0-9]+$")
    label: str = Field(min_length=1, max_length=30)
    status: EditionStatus
    benchmark_id: str = Field(pattern=r"^B-[0-9]{4}$")
    runtime_overrides: bool = False
    profile_path: str | None = None


class EditionRegistry(FrozenModel):
    version: Literal[1] = 1
    default_edition_id: str
    editions: tuple[Edition, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def current_is_default(self) -> EditionRegistry:
        if len({entry.edition_id for entry in self.editions}) != len(self.editions):
            raise ValueError("edition IDs must be unique")
        current = tuple(entry for entry in self.editions if entry.status is EditionStatus.CURRENT)
        if len(current) != 1 or current[0].edition_id != self.default_edition_id:
            raise ValueError("exactly one current edition must be the default")
        if any(e.runtime_overrides and e.status is not EditionStatus.DRAFT for e in self.editions):
            raise ValueError("runtime overrides are restricted to draft editions")
        return self

    def edition(self, edition_id: str | None = None) -> Edition:
        requested = edition_id or self.default_edition_id
        for entry in self.editions:
            if entry.edition_id == requested:
                return entry
        raise ValueError("unknown edition")
