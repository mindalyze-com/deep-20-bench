"""Versioned benchmark-owned history inventory. Contains no model-visible state."""

from __future__ import annotations

from typing import Literal, Protocol

from deep20_oracle.models import StrictModel, Subject
from pydantic import Field, field_validator


class HistoryFile(StrictModel):
    relative_path: str
    size: int = Field(ge=0)
    modified_ns: int = Field(ge=0)
    changed_ns: int = Field(ge=0)
    inode: int = Field(ge=0)

    @field_validator("relative_path")
    @classmethod
    def safe_path(cls, value: str) -> str:
        if value.startswith("/") or ".." in value.split("/") or "\\" in value:
            raise ValueError("history paths must be repository-relative")
        return value


class HistoryExecution(StrictModel):
    manifest: HistoryFile
    manifest_integrity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    trials: tuple[HistoryFile, ...]


class OracleHistorySnapshot(StrictModel):
    discovery_policy: Literal["per_subject_history_v1"] | None = Field(
        default=None, exclude_if=lambda v: v is None,
    )
    execution_reuse_policy: Literal["same_execution_ask_v1"] | None = Field(
        default=None, exclude_if=lambda v: v is None,
    )
    episode_reuse_policy: Literal["same_episode_ask_v1"] | None = Field(
        default=None, exclude_if=lambda v: v is None,
    )
    policy: Literal["historical_ask_v1"] = "historical_ask_v1"
    normalization: Literal["casefold-ascii-spaces-v1"] = "casefold-ascii-spaces-v1"
    context_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    cutoff: str
    sources: tuple[HistoryExecution, ...]
    snapshot_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class OracleHistoryLoad(StrictModel):
    snapshot: OracleHistorySnapshot | None = Field(default=None, exclude_if=lambda v: v is None)
    target_id: str = Field(pattern=r"^T-[0-9]{4}$")
    subject_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    files: int = Field(ge=0)
    bytes_read: int = Field(ge=0)
    records_found: int = Field(ge=0)
    eligible_records: int = Field(ge=0)
    entries: int = Field(ge=0)
    conflicts: int = Field(ge=0)
    skipped_files: int = Field(ge=0)
    duration_ms: float = Field(ge=0)


class OracleSubjectHistoryCheckpoint(StrictModel):
    parent_snapshot_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    subject_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    snapshot: OracleHistorySnapshot


class OracleSubjectHistoryStore(Protocol):
    """Execution-owned inventory persistence, acknowledged before any answer is reused."""

    def load(self, subject: Subject, parent: OracleHistorySnapshot) -> OracleHistorySnapshot | None: ...

    def save(
        self, subject: Subject, parent: OracleHistorySnapshot, snapshot: OracleHistorySnapshot,
    ) -> None: ...
