"""The maintained v9 serialization boundary, independent of the current GUI default."""

from __future__ import annotations

import json
from typing import Annotated, Literal

from pydantic import Field

from .models import (
    DatasetProvenance,
    FrozenModel,
    HistoricalEligibility,
    IdentityAnswer,
    LeaderboardRow,
    LegacyCohortConfig,
    PublicActionTurn,
    PublicContractViolationTurn,
    PublicEpisodeDetail,
    PublicModel,
    PublicRunSummary,
    PublicSubjectSummary,
    PublicTrialSummary,
    PublishedDataset,
    ScorePolicy,
    SiteMetadata,
    Winner,
)


class LegacyPublicActionTurn(PublicActionTurn):
    answer: IdentityAnswer


class LegacyPublicEpisodeDetail(PublicEpisodeDetail):
    turns: tuple[
        Annotated[
            LegacyPublicActionTurn | PublicContractViolationTurn,
            Field(discriminator="turn_type"),
        ], ...
    ]


class LegacyPublicTrial(PublicTrialSummary):
    episode: LegacyPublicEpisodeDetail | None = None


class LegacyPublicSubject(PublicSubjectSummary):
    trials: tuple[LegacyPublicTrial, ...]


class LegacyPublicRun(PublicRunSummary):
    subjects: tuple[LegacyPublicSubject, ...]


class LegacyPublishedDataset(FrozenModel):
    schema_version: Literal[9] = 9
    site: SiteMetadata
    score_policy: ScorePolicy
    active_cohort: LegacyCohortConfig
    provenance: DatasetProvenance
    winner: Winner | None
    leaderboard: tuple[LeaderboardRow, ...]
    models: tuple[PublicModel, ...]
    official_runs: tuple[LegacyPublicRun, ...]
    lab_runs: tuple[LegacyPublicRun, ...]


def legacy_dataset(dataset: PublishedDataset) -> LegacyPublishedDataset:
    if not isinstance(dataset.active_cohort.eligibility, HistoricalEligibility):
        raise TypeError("v9 cannot represent a qualified-answer edition")
    value = dataset.model_dump(mode="json")
    value["schema_version"] = 9
    value["active_cohort"] = dataset.active_cohort.model_dump(
        mode="json",
        exclude={"edition_id", "edition_label", "edition_status", "eligibility"},
    )
    # This flag describes the single cohort in v9, not the current GUI edition.
    value["active_cohort"]["active"] = True
    return LegacyPublishedDataset.model_validate(value)


def legacy_dataset_schema_json() -> str:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **LegacyPublishedDataset.model_json_schema(mode="serialization"),
    }
    # Preserve v9's definition names as well as their unchanged wire contracts.
    return json.dumps(schema, indent=2, sort_keys=True).replace("Legacy", "") + "\n"
