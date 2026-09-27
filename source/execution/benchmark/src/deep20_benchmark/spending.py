"""Atomic durable reservations shared by inference, research, and operator processes."""

from __future__ import annotations

import sqlite3
import uuid
from decimal import Decimal
from typing import Literal

from deep20_backends.budget import BudgetSnapshot, Reservation, ReservationId
from deep20_backends.models import BackendError


class SqliteSpendingLedger:
    """The composition root supplies the connection and owns its artifact path/lifetime."""

    def __init__(self, connection: sqlite3.Connection, limit_usd: Decimal):
        BudgetSnapshot(limit_usd=limit_usd)
        self.connection = connection
        with connection:
            connection.execute("CREATE TABLE IF NOT EXISTS spending_config (id INTEGER PRIMARY KEY, limit_usd TEXT NOT NULL)")
            connection.execute("""CREATE TABLE IF NOT EXISTS spending_reservations (
                reservation_id TEXT PRIMARY KEY, service TEXT NOT NULL,
                reserved_usd TEXT NOT NULL, actual_usd TEXT
            )""")
            connection.execute("INSERT OR IGNORE INTO spending_config VALUES (1, ?)", (str(limit_usd),))
            row = connection.execute("SELECT limit_usd FROM spending_config WHERE id=1").fetchone()
            if row is None or Decimal(row[0]) != limit_usd:
                raise BackendError("spending_limit_changed", "saved spending limit differs from this execution")
        self.limit_usd = limit_usd

    def snapshot(self) -> BudgetSnapshot:
        rows = self.connection.execute("SELECT reserved_usd, actual_usd FROM spending_reservations").fetchall()
        reported = sum((Decimal(row[1]) for row in rows if row[1] is not None), Decimal(0))
        reserved = sum((Decimal(row[0]) for row in rows if row[1] is None), Decimal(0))
        return BudgetSnapshot(
            limit_usd=self.limit_usd, reported_usd=reported, reserved_usd=reserved,
            requests=len(rows), unmetered_requests=sum(row[1] is None for row in rows),
        )

    def reserve(
        self, service: Literal["openrouter", "parallel_search", "parallel_extract"], amount: Decimal,
    ) -> Reservation:
        reservation = Reservation(reservation_id=ReservationId(f"RS-{uuid.uuid4().hex}"), service=service, amount_usd=amount)
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            if amount > self.snapshot().remaining_usd:
                raise BackendError("spending_cap_reached", "execution spending allowance is exhausted")
            self.connection.execute(
                "INSERT INTO spending_reservations VALUES (?, ?, ?, NULL)",
                (reservation.reservation_id, service, str(amount)),
            )
        return reservation

    def settle(self, reservation: Reservation, actual_usd: Decimal | None) -> None:
        if actual_usd is None:
            return  # Unknown and failed billing keep their entire durable reservation.
        if not actual_usd.is_finite() or actual_usd < 0:
            raise BackendError("invalid_billing", "provider billing is invalid")
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            row = self.connection.execute(
                "SELECT service, reserved_usd, actual_usd FROM spending_reservations WHERE reservation_id=?",
                (reservation.reservation_id,),
            ).fetchone()
            if row is None or row[0] != reservation.service or Decimal(row[1]) != reservation.amount_usd:
                raise BackendError("reservation_mismatch", "billing does not match a saved reservation")
            if row[2] is not None:
                if Decimal(row[2]) != actual_usd:
                    raise BackendError("conflicting_billing", "billing was already settled differently")
                return
            self.connection.execute(
                "UPDATE spending_reservations SET actual_usd=? WHERE reservation_id=?",
                (str(actual_usd), reservation.reservation_id),
            )
        if actual_usd > reservation.amount_usd:
            raise BackendError("billing_exceeded_reservation", "provider billing exceeded its reserved bound")
