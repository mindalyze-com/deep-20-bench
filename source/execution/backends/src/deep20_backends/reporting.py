"""Versioned, post-run draft projection. This contains no role prompts or private evidence."""

from decimal import Decimal
from typing import Literal

from pydantic import Field

from .models import BackendKind, FrozenModel, Role


class RoleActivity(FrozenModel):
    role: Role
    backend: BackendKind
    model: str
    logical_calls: int = Field(ge=0)
    inference_requests: int = Field(ge=0)
    control_bypasses: int = Field(default=0, ge=0)
    search_requests: int = Field(ge=0)
    extract_requests: int = Field(ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    reported_cost_usd: Decimal = Field(ge=0)
    unmetered_calls: int = Field(ge=0)
    model_digests: tuple[str, ...] = ()


class DraftRunReport(FrozenModel):
    schema_version: Literal[1] = 1
    edition_id: str = Field(pattern=r"^[0-9]+\.[0-9]+$")
    status: Literal["draft"] = "draft"
    execution_id: str = Field(pattern=r"^BX-[A-Za-z0-9._-]+$")
    model_id: str = Field(pattern=r"^M-[0-9]{4}$")
    runtime_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    manifest_integrity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    synthetic: bool
    publication_eligible: Literal[False] = False
    scheduled_trials: int = Field(ge=0)
    scoring_eligible_trials: int = Field(ge=0)
    infrastructure_failed_trials: int = Field(ge=0)
    # Shared spending-summary.json is the authority for canaries, failed requests,
    # superseded attempts and tools; role activity covers retained episode audits.
    accounting_scope: Literal["retained_episode_audits"] = "retained_episode_audits"
    roles: tuple[RoleActivity, ...] = Field(min_length=5, max_length=5)
    integrity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
