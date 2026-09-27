"""Durable research counters shared by benchmark and operator command processes."""

import sqlite3
import time
import uuid
from collections.abc import Callable
from typing import Literal

from deep20_backends.models import BackendError, BackendUsage
from deep20_backends.research import ResearchScope, ResearchTicket

from .work_models import WorkClaim
from .work_queue import SqliteWorkQueue


class SqliteResearchJournal:
    def __init__(self, connection: sqlite3.Connection, *, claim: WorkClaim | None = None,
                 clock: Callable[[], float] = time.time):
        self.connection = connection
        self.claim = claim
        self.clock = clock
        self.queue = SqliteWorkQueue(connection) if claim is not None else None
        with connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS research_scopes (
                scope_id TEXT PRIMARY KEY, scope_json TEXT NOT NULL, started_at REAL NOT NULL
            )""")
            connection.execute("""CREATE TABLE IF NOT EXISTS research_calls (
                ticket_id TEXT PRIMARY KEY, scope_id TEXT NOT NULL, kind TEXT NOT NULL,
                status TEXT NOT NULL
            )""")

    def begin(self, scope: ResearchScope, kind: Literal["search", "extract"]) -> ResearchTicket:
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            if scope.scope_id.startswith("WQ-"):
                if self.claim is None or self.claim.request_id != scope.scope_id:
                    raise BackendError("research_claim_required", "interactive research requires its current Oracle claim")
                assert self.queue is not None
                work = self.queue.read(self.claim)
                if work.identity.role.value != "oracle" or work.inference.max_search_requests is None:
                    raise BackendError("research_role_required", "only Oracle work can request research")
                if scope.search_limit > work.inference.max_search_requests:
                    raise BackendError("research_limit_changed", "research exceeds its request allowance")
            now = self.clock()
            self.connection.execute("INSERT OR IGNORE INTO research_scopes VALUES (?, ?, ?)",
                                    (scope.scope_id, scope.model_dump_json(), now))
            row = self.connection.execute("SELECT scope_json,started_at FROM research_scopes WHERE scope_id=?",
                                          (scope.scope_id,)).fetchone()
            assert row is not None
            if ResearchScope.model_validate_json(row[0]) != scope:
                raise BackendError("research_scope_changed", "research settings differ from the saved request")
            remaining = scope.policy.deadline_seconds - (now - row[1])
            if remaining <= 0:
                raise BackendError("research_deadline", "research deadline elapsed")
            pending = self.connection.execute("SELECT COUNT(*) FROM research_calls WHERE scope_id=? AND status='pending'",
                                              (scope.scope_id,)).fetchone()
            if pending and pending[0]:
                raise BackendError("research_in_progress", "a research request is already in progress or unresolved")
            row = self.connection.execute("SELECT COUNT(*) FROM research_calls WHERE scope_id=? AND kind=?",
                                          (scope.scope_id, kind)).fetchone()
            limit = min(scope.search_limit, scope.policy.max_search_requests) if kind == "search" else scope.policy.max_extract_requests
            if row and row[0] >= limit:
                raise BackendError("research_call_limit", "research request allowance is exhausted")
            ticket = ResearchTicket(ticket_id=f"RT-{uuid.uuid4().hex}", scope_id=scope.scope_id,
                                    kind=kind, remaining_seconds=remaining)
            self.connection.execute("INSERT INTO research_calls VALUES (?, ?, ?, 'pending')",
                                    (ticket.ticket_id, ticket.scope_id, kind))
        return ticket

    def finish(self, ticket: ResearchTicket, *, succeeded: bool) -> None:
        with self.connection:
            cursor = self.connection.execute("""UPDATE research_calls SET status=?
                WHERE ticket_id=? AND scope_id=? AND kind=? AND status='pending'""",
                ("succeeded" if succeeded else "failed", ticket.ticket_id, ticket.scope_id, ticket.kind))
            if cursor.rowcount != 1:
                raise BackendError("research_ticket_mismatch", "research ticket is stale or already completed")

    def usage(self, scope_id: str) -> BackendUsage:
        rows = self.connection.execute("SELECT kind,status FROM research_calls WHERE scope_id=?", (scope_id,)).fetchall()
        if any(row[1] != "succeeded" for row in rows):
            raise BackendError("research_incomplete", "research includes a failed or unresolved request")
        return BackendUsage(search_requests=sum(r[0] == "search" for r in rows),
                            extract_requests=sum(r[0] == "extract" for r in rows))
