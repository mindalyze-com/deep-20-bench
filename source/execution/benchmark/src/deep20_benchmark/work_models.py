"""Private work-control metadata is separate from the role's model-visible input."""

from enum import StrEnum
from typing import Literal, NewType

from deep20_backends.models import ModelRequest, Role
from deep20_oracle.models import StrictModel
from pydantic import ConfigDict, Field

from .models import BenchmarkExecutionId, BenchmarkModelId, SubjectId, TrialId

WorkRequestId = NewType("WorkRequestId", str)
WorkClaimId = NewType("WorkClaimId", str)


class WorkStatus(StrEnum):
    PENDING = "pending"
    CLAIMED = "claimed"
    SUBMITTED = "submitted"
    CONSUMED = "consumed"
    CANCELLED = "cancelled"


class WorkIdentity(StrictModel):
    execution_id: BenchmarkExecutionId
    model_id: BenchmarkModelId
    target_id: SubjectId
    trial_id: TrialId
    attempt_number: int = Field(ge=1)
    role: Role


class WorkRequest(StrictModel):
    version: Literal[1] = 1
    request_id: WorkRequestId = Field(pattern=r"^WQ-[0-9a-f]{32}$")
    request_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    identity: WorkIdentity
    operator: str = Field(min_length=1, max_length=80)
    inference: ModelRequest
    created_at: float


class WorkReceipt(StrictModel):
    request_id: WorkRequestId = Field(pattern=r"^WQ-[0-9a-f]{32}$")
    request_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    identity: WorkIdentity
    operator: str
    status: WorkStatus
    created_at: float
    response_hash: str | None = None


class WorkClaim(StrictModel):
    request_id: WorkRequestId = Field(pattern=r"^WQ-[0-9a-f]{32}$")
    request_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    claim_id: WorkClaimId = Field(pattern=r"^CL-[0-9a-f]{32}$")
    operator: str
    role: Role
    expires_at: float


class WorkSubmission(StrictModel):
    model_config = ConfigDict(str_strip_whitespace=False)
    request_id: WorkRequestId = Field(pattern=r"^WQ-[0-9a-f]{32}$")
    request_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    claim_id: WorkClaimId = Field(pattern=r"^CL-[0-9a-f]{32}$")
    # Transport accepts raw output. In particular, invalid Guesser output must reach
    # the engine's counted FORMAT_ERROR path instead of receiving a free correction.
    content: str = Field(max_length=1_000_000)


class WorkReply(StrictModel):
    model_config = ConfigDict(str_strip_whitespace=False)
    content: str
    submitted_at: float
