"""Shared paid-request accounting; persistence is an injected root-owned port."""

from decimal import Decimal
from typing import Literal, NewType, Protocol

import httpx
from pydantic import Field

from .models import BackendError, FrozenModel

ReservationId = NewType("ReservationId", str)


class BudgetSnapshot(FrozenModel):
    limit_usd: Decimal = Field(gt=0, allow_inf_nan=False)
    reported_usd: Decimal = Field(default=Decimal(0), ge=0, allow_inf_nan=False)
    reserved_usd: Decimal = Field(default=Decimal(0), ge=0, allow_inf_nan=False)
    requests: int = Field(default=0, ge=0)
    unmetered_requests: int = Field(default=0, ge=0)

    @property
    def remaining_usd(self) -> Decimal:
        return max(self.limit_usd - self.reported_usd - self.reserved_usd, Decimal(0))


class Reservation(FrozenModel):
    reservation_id: ReservationId = Field(pattern=r"^RS-[0-9a-f]{32}$")
    service: Literal["openrouter", "parallel_search", "parallel_extract"]
    amount_usd: Decimal = Field(ge=0, allow_inf_nan=False)


class SpendingLedger(Protocol):
    def snapshot(self) -> BudgetSnapshot: ...

    def reserve(
        self, service: Literal["openrouter", "parallel_search", "parallel_extract"], amount: Decimal,
    ) -> Reservation: ...

    def settle(self, reservation: Reservation, actual_usd: Decimal | None) -> None: ...


class HttpSpendingGuard(Protocol):
    def before(self, request: httpx.Request) -> None: ...
    def after(self, response: httpx.Response) -> None: ...


def backend_error_cause(error: BaseException) -> BackendError | None:
    """SDKs may wrap request-hook rejections; keep their stable code and do not retry."""
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, BackendError):
            return current
        current = current.__cause__ or current.__context__
    return None
