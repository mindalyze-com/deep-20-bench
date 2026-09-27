"""Typed released profiles and reporting-only execution provenance."""

from typing import Annotated, Literal

from deep20_game.config import ModelConfig
from deep20_oracle.config import OracleConfig, PromptProfile
from deep20_oracle.models import OracleAnswer, StrictModel
from pydantic import Field, model_validator

Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Target = Annotated[str, Field(pattern=r"^T-[0-9]{4}$")]


class ReleasePrompts(StrictModel):
    guesser: str
    oracle: str
    recovery: str
    reviewer: str
    judge: str
    validator: str


class ReleaseRules(StrictModel):
    max_consecutive_contract_violations: int = Field(ge=1, le=100)
    reveal_entity_type: Literal[True]
    final_guess_after_limit: Literal[True]


class SubjectIdentity(StrictModel):
    target_id: Target
    identity_hash: Hash


class ReleaseContract(StrictModel):
    prompts: ReleasePrompts
    game_rules: ReleaseRules
    subject_identities: tuple[SubjectIdentity, ...]
    oracle_configuration_hash: Hash
    oracle_contract_hash: Hash
    validator_configuration_hash: Hash
    additional_prompt_versions: tuple[ReleasePrompts, ...] = ()


class AcceptedRevision(ReleaseContract):
    revision_id: str


class QualifiedRelease(ReleaseContract):
    kind: Literal["qualified_release"]
    accepted_revisions: tuple[AcceptedRevision, ...] = ()


class HistoricalRelease(StrictModel):
    kind: Literal["historical_standard"]


class ProfileCohort(StrictModel):
    cohort_id: str
    display_name: str
    edition_id: str = Field(pattern=r"^[0-9]+\.[0-9]+$")
    edition_label: str
    edition_status: Literal["current", "previous"]
    benchmark_id: str = Field(pattern=r"^B-[0-9]{4}$")
    benchmark_version: Literal[9]
    target_ids: tuple[Target, ...] = Field(min_length=1)
    iterations: int = Field(ge=1, le=100)
    base_seed: int = Field(ge=0, le=2**31 - 1)
    max_questions: int = Field(ge=1, le=100)
    model_ids: tuple[str, ...]
    eligibility: Annotated[QualifiedRelease | HistoricalRelease, Field(discriminator="kind")]

    @model_validator(mode="after")
    def unique_targets(self) -> ProfileCohort:
        if len(set(self.target_ids)) != len(self.target_ids):
            raise ValueError("edition targets must be unique")
        if isinstance(self.eligibility, QualifiedRelease):
            ids = tuple(s.target_id for s in self.eligibility.subject_identities)
            if len(set(ids)) != len(ids) or set(ids) != set(self.target_ids):
                raise ValueError("edition identity pins must cover its targets")
        return self


class EditionScore(StrictModel):
    version: Literal["average-then-average-v1"]
    failure_penalty_offset: int = Field(ge=1, le=100)


class EditionProfile(StrictModel):
    version: Literal[1]
    revision: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,63}$")
    launchable: bool
    prompt_profile: PromptProfile
    score: EditionScore
    cohort: ProfileCohort
    oracle_configuration: OracleConfig | None = None
    validator_configuration: ModelConfig | None = None

    @model_validator(mode="after")
    def executable_profile(self) -> EditionProfile:
        if self.launchable and (self.oracle_configuration is None
                                or self.validator_configuration is None
                                or not isinstance(self.cohort.eligibility, QualifiedRelease)):
            raise ValueError("launchable releases require complete configurations and pins")
        if (self.oracle_configuration is not None
                and self.oracle_configuration.prompt_profile is not self.prompt_profile):
            raise ValueError("edition requires paired answer profiles")
        return self


class EditionOverrides(StrictModel):
    iterations: int | None = Field(default=None, ge=1, le=100)
    target_ids: tuple[Target, ...] | None = None
    base_seed: int | None = Field(default=None, ge=0, le=2**31 - 1)
    variant_name: str | None = Field(default=None, pattern=r"^[a-z0-9][a-z0-9-]{0,63}$")


class EditionExecution(StrictModel):
    """Never passed to model messages, sessions, or prompt-cache namespaces."""

    schema_version: Literal[1] = 1
    edition_id: str = Field(pattern=r"^[0-9]+\.[0-9]+$")
    revision: str
    profile_hash: Hash
    comparison_hash: Hash
    classification: Literal["standard", "variant"]
    overrides: EditionOverrides
    differences: tuple[str, ...] = ()
    answer_tokens: tuple[OracleAnswer, ...]
    prompts: ReleasePrompts
    subject_identities: tuple[SubjectIdentity, ...]
    score: EditionScore

    @model_validator(mode="after")
    def classification_matches(self) -> EditionExecution:
        if (self.classification == "variant") != bool(
            self.differences or self.overrides.variant_name
        ):
            raise ValueError("edition classification differs from recorded overrides")
        return self
