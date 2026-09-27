"""Durable, process-safe interactive work queue with no shared role conversations."""

from __future__ import annotations

import sqlite3
import time
import uuid
from collections.abc import Callable
from typing import Protocol

from deep20_backends.models import BackendError, ModelRequest, Role
from deep20_oracle.util import canonical_json, sha256_text

from .work_models import (
    WorkClaim,
    WorkClaimId,
    WorkIdentity,
    WorkReceipt,
    WorkReply,
    WorkRequest,
    WorkRequestId,
    WorkStatus,
    WorkSubmission,
)


class WorkQueue(Protocol):
    def enqueue(self, identity: WorkIdentity, operator: str, request: ModelRequest) -> WorkRequest: ...
    def receipts(self, *, role: Role | None = None) -> tuple[WorkReceipt, ...]: ...
    def claim(self, request_id: WorkRequestId, *, operator: str, role: Role, lease_seconds: int = 900) -> WorkClaim: ...
    def read(self, claim: WorkClaim) -> WorkRequest: ...
    def renew(self, claim: WorkClaim, *, lease_seconds: int = 900) -> WorkClaim: ...
    def submit(self, submission: WorkSubmission) -> WorkReceipt: ...
    def reply(self, request: WorkRequest) -> WorkReply | None: ...
    def cancel(self, request_id: WorkRequestId) -> None: ...


class SqliteWorkQueue:
    """Connection creation, filesystem permissions, and lifetime belong to the root."""

    def __init__(self, connection: sqlite3.Connection, *, clock: Callable[[], float] = time.time):
        self.connection = connection
        self.clock = clock
        with connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS role_work (
                request_id TEXT PRIMARY KEY, request_hash TEXT NOT NULL,
                identity_json TEXT NOT NULL, operator TEXT NOT NULL, role TEXT NOT NULL,
                status TEXT NOT NULL, created_at REAL NOT NULL, request_json TEXT,
                claim_id TEXT, expires_at REAL, response_text TEXT, response_hash TEXT,
                submitted_at REAL
            )""")

    def enqueue(self, identity: WorkIdentity, operator: str, request: ModelRequest) -> WorkRequest:
        if identity.role is not request.role:
            raise BackendError("work_role_mismatch", "work identity differs from the requested role")
        work = WorkRequest(
            request_id=WorkRequestId(f"WQ-{uuid.uuid4().hex}"),
            request_hash=sha256_text(canonical_json({
                "version": 1, "identity": identity.model_dump(mode="json"),
                "operator": operator, "inference": request.model_dump(mode="json"),
            })),
            identity=identity, operator=operator, inference=request, created_at=self.clock(),
        )
        with self.connection:
            self.connection.execute("""INSERT INTO role_work
                (request_id, request_hash, identity_json, operator, role, status, created_at, request_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (
                    work.request_id, work.request_hash, identity.model_dump_json(), operator,
                    identity.role.value, WorkStatus.PENDING.value, work.created_at, work.model_dump_json(),
                ))
        return work

    def receipts(self, *, role: Role | None = None) -> tuple[WorkReceipt, ...]:
        statement = "SELECT request_id,request_hash,identity_json,operator,status,created_at,response_hash FROM role_work"
        rows = self.connection.execute(statement + (" WHERE role=?" if role is not None else "") +
                                       " ORDER BY created_at,request_id", (role.value,) if role else ()).fetchall()
        return tuple(WorkReceipt(
            request_id=row[0], request_hash=row[1], identity=WorkIdentity.model_validate_json(row[2]),
            operator=row[3], status=WorkStatus(row[4]), created_at=row[5], response_hash=row[6],
        ) for row in rows)

    def _receipt(self, request_id: WorkRequestId) -> WorkReceipt:
        for item in self.receipts():
            if item.request_id == request_id:
                return item
        raise BackendError("work_not_found", "work item does not exist")

    def claim(self, request_id: WorkRequestId, *, operator: str, role: Role, lease_seconds: int = 900) -> WorkClaim:
        if not 1 <= lease_seconds <= 3600:
            raise ValueError("claim leases must be between 1 and 3600 seconds")
        now = self.clock()
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            row = self.connection.execute(
                "SELECT request_hash,operator,role,status,expires_at FROM role_work WHERE request_id=?",
                (request_id,),
            ).fetchone()
            if row is None or row[1] != operator or row[2] != role.value:
                raise BackendError("work_claim_denied", "work is not assigned to this operator and role")
            if row[3] != WorkStatus.PENDING.value and not (
                row[3] == WorkStatus.CLAIMED.value and row[4] <= now
            ):
                raise BackendError("work_unavailable", "work is already claimed or terminal")
            claim = WorkClaim(
                request_id=request_id, request_hash=row[0], claim_id=WorkClaimId(f"CL-{uuid.uuid4().hex}"),
                operator=operator, role=role, expires_at=now + lease_seconds,
            )
            self.connection.execute(
                "UPDATE role_work SET status=?,claim_id=?,expires_at=? WHERE request_id=?",
                (WorkStatus.CLAIMED.value, claim.claim_id, claim.expires_at, request_id),
            )
        return claim

    def read(self, claim: WorkClaim) -> WorkRequest:
        row = self.connection.execute("""SELECT request_hash,operator,role,status,claim_id,expires_at,request_json
            FROM role_work WHERE request_id=?""", (claim.request_id,)).fetchone()
        if (row is None or row[0] != claim.request_hash or row[1] != claim.operator
            or row[2] != claim.role.value or row[3] != WorkStatus.CLAIMED.value
            or row[4] != claim.claim_id or row[5] <= self.clock() or row[6] is None):
            raise BackendError("stale_work_claim", "claim is stale or does not match this work")
        return WorkRequest.model_validate_json(row[6])

    def renew(self, claim: WorkClaim, *, lease_seconds: int = 900) -> WorkClaim:
        if not 1 <= lease_seconds <= 3600:
            raise ValueError("claim leases must be between 1 and 3600 seconds")
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            self.read(claim)
            updated = claim.model_copy(update={"expires_at": self.clock() + lease_seconds})
            self.connection.execute("UPDATE role_work SET expires_at=? WHERE request_id=?",
                                    (updated.expires_at, claim.request_id))
        return updated

    def submit(self, submission: WorkSubmission) -> WorkReceipt:
        response_hash = sha256_text(submission.content)
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            row = self.connection.execute("""SELECT request_hash,status,claim_id,expires_at,response_hash
                FROM role_work WHERE request_id=?""", (submission.request_id,)).fetchone()
            if row is None or row[0] != submission.request_hash or row[2] != submission.claim_id:
                raise BackendError("work_submission_mismatch", "submission does not match its claimed request")
            if row[1] in {WorkStatus.SUBMITTED.value, WorkStatus.CONSUMED.value}:
                if row[4] != response_hash:
                    raise BackendError("conflicting_work_submission", "a different response was already submitted")
                return self._receipt(submission.request_id)
            if row[1] != WorkStatus.CLAIMED.value or row[3] <= self.clock():
                raise BackendError("stale_work_submission", "work is no longer available to this claim")
            if self.connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='research_calls'").fetchone():
                pending = self.connection.execute("SELECT 1 FROM research_calls WHERE scope_id=? AND status='pending'",
                                                  (submission.request_id,)).fetchone()
                if pending:
                    raise BackendError("research_in_progress", "complete research before submitting this role response")
            self.connection.execute("""UPDATE role_work SET status=?,response_text=?,response_hash=?,submitted_at=?
                WHERE request_id=?""", (WorkStatus.SUBMITTED.value, submission.content, response_hash,
                                         self.clock(), submission.request_id))
        return self._receipt(submission.request_id)

    def reply(self, request: WorkRequest) -> WorkReply | None:
        row = self.connection.execute("""SELECT request_hash,status,response_text,submitted_at
            FROM role_work WHERE request_id=?""", (request.request_id,)).fetchone()
        if row is None or row[0] != request.request_hash:
            raise BackendError("work_request_mismatch", "work request changed or is missing")
        if row[1] == WorkStatus.CANCELLED.value:
            raise BackendError("interactive_cancelled", "interactive work was cancelled")
        if row[1] == WorkStatus.CONSUMED.value:
            raise BackendError("work_already_consumed", "interactive work was already consumed")
        if row[1] == WorkStatus.SUBMITTED.value:
            return WorkReply(content=row[2], submitted_at=row[3])
        return None

    def cancel(self, request_id: WorkRequestId) -> None:
        with self.connection:
            self.connection.execute("""UPDATE role_work SET status=?,request_json=NULL,response_text=NULL
                WHERE request_id=? AND status IN (?,?,?)""", (WorkStatus.CANCELLED.value, request_id,
                    WorkStatus.PENDING.value, WorkStatus.CLAIMED.value, WorkStatus.SUBMITTED.value))

    def finish_attempt(self, identity: WorkIdentity) -> None:
        """Scrub delivered payloads only after the benchmark commits the episode result."""
        with self.connection:
            for receipt in self.receipts():
                if self._same_attempt(receipt.identity, identity) and receipt.status is WorkStatus.SUBMITTED:
                    self.connection.execute("""UPDATE role_work SET status=?,request_json=NULL,response_text=NULL
                        WHERE request_id=?""", (WorkStatus.CONSUMED.value, receipt.request_id))

    def invalidate_prior_attempts(self, identity: WorkIdentity) -> None:
        for receipt in self.receipts():
            if (receipt.identity.execution_id == identity.execution_id
                and receipt.identity.model_id == identity.model_id
                and receipt.identity.target_id == identity.target_id
                and receipt.identity.trial_id == identity.trial_id
                and receipt.identity.attempt_number < identity.attempt_number):
                self.cancel(receipt.request_id)

    @staticmethod
    def _same_attempt(left: WorkIdentity, right: WorkIdentity) -> bool:
        return left.model_dump(exclude={"role"}) == right.model_dump(exclude={"role"})


class MemoryWorkQueue(SqliteWorkQueue):
    """Use identical queue semantics with an in-memory, offline database."""

    def __init__(self, *, clock: Callable[[], float] = time.time):
        super().__init__(sqlite3.connect(":memory:"), clock=clock)

    def close(self) -> None:
        self.connection.close()
