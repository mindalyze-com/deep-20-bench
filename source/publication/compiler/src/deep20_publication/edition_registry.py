"""Independent consumer of the shared edition registry; no execution dependency."""

from typing import Literal

from pydantic import Field, model_validator

from .models import FrozenModel, PublicationConfig


class RegisteredEdition(FrozenModel):
    edition_id: str = Field(pattern=r"^[0-9]+\.[0-9]+$")
    label: str
    status: Literal["previous", "current", "draft"]
    benchmark_id: str = Field(pattern=r"^B-[0-9]{4}$")
    runtime_overrides: bool = False
    profile_path: str | None = None


class EditionRegistry(FrozenModel):
    version: Literal[1] = 1
    default_edition_id: str
    editions: tuple[RegisteredEdition, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_default(self) -> "EditionRegistry":
        current = tuple(e for e in self.editions if e.status == "current")
        if len(current) != 1 or current[0].edition_id != self.default_edition_id:
            raise ValueError("edition registry must have one current default")
        if len({e.edition_id for e in self.editions}) != len(self.editions):
            raise ValueError("edition registry contains duplicate IDs")
        if any(e.runtime_overrides and e.status != "draft" for e in self.editions):
            raise ValueError("runtime overrides require a draft edition")
        return self

    def validate_publication(self, config: PublicationConfig) -> None:
        public = {e.edition_id: e for e in self.editions if e.status != "draft"}
        if config.default_edition_id != self.default_edition_id:
            raise ValueError("publication default differs from the shared edition registry")
        if set(public) != {c.edition_id for c in config.cohorts}:
            raise ValueError("publication must contain exactly the released editions")
        for cohort in config.cohorts:
            edition = public[cohort.edition_id]
            if (cohort.edition_status, cohort.edition_label, cohort.benchmark_id) != (
                edition.status, edition.label, edition.benchmark_id,
            ):
                raise ValueError("publication edition metadata differs from the shared registry")
