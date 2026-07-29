from __future__ import annotations

from .models import JsonObject


class OracleError(Exception):
    """Base class for typed Oracle failures."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        call_id: str | None = None,
        details: JsonObject | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.call_id = call_id
        self.details = details or {}


class OracleConfigurationError(OracleError):
    """The selected provider configuration cannot satisfy the Oracle contract."""


class OracleProviderError(OracleError):
    """The single provider request failed."""


class OracleProtocolError(OracleError):
    """The provider response violated the Oracle protocol."""


class AuditWriteError(OracleError):
    """An Oracle call could not be durably audited."""
