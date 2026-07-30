from __future__ import annotations

from typing import Literal, Protocol

from pydantic import Field

from .models import (
    CALL_ID_PATTERN,
    FailureDiagnostics,
    JsonObject,
    OracleAdjudication,
    OracleAuditTrace,
    OracleCall,
    OracleMetrics,
    OracleProviderRoleTrace,
    OracleRequest,
    OracleResult,
    OracleRole,
    PersistedRecord,
    ProviderTrace,
    StrictModel,
)


class AuditFailure(StrictModel):
    code: str = Field(min_length=1, max_length=160)
    type: str = Field(min_length=1, max_length=160)
    message: str = Field(max_length=2_000)
    details: JsonObject
    diagnostics: FailureDiagnostics | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )


class OracleSuccessRecord(StrictModel):
    schema_version: Literal[5] = 5
    status: Literal["success"] = "success"
    call_id: str = Field(pattern=CALL_ID_PATTERN)
    request: OracleRequest
    result: OracleResult
    adjudication: OracleAdjudication
    metrics: OracleMetrics
    audit: OracleAuditTrace
    recorded_at: str


class OracleFailureRecord(StrictModel):
    schema_version: Literal[5] = 5
    status: Literal["failure"] = "failure"
    call_id: str = Field(pattern=CALL_ID_PATTERN)
    request: OracleRequest
    component: OracleRole
    prompt_version: str
    prompt_hash: str
    messages: tuple[dict[str, str], ...]
    failure: AuditFailure
    provider_trace: ProviderTrace | None
    recorded_at: str
    role_traces: tuple[OracleProviderRoleTrace, ...] = ()


class OracleAuditSink(Protocol):
    """Synchronous persistence boundary used by the Oracle service."""

    def prepare_run(self, run_id: str) -> None: ...

    def persist_oracle_success(self, record: OracleSuccessRecord) -> OracleCall: ...

    def persist_oracle_failure(self, record: OracleFailureRecord) -> PersistedRecord: ...
