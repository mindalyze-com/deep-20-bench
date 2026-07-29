from __future__ import annotations

from deep20_oracle.models import JsonObject


class GameError(Exception):
    """Base class for typed game-component failures."""

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


class GameConfigurationError(GameError):
    """A game or model configuration cannot satisfy the benchmark contract."""


class GameProviderError(GameError):
    """A Guesser or Guess Validator provider request failed."""


class GuesserProtocolError(GameError):
    """The model under evaluation violated the structured Guesser protocol."""


class ValidatorProtocolError(GameError):
    """The fixed Guess Validator violated its adjudication protocol."""


class GameAuditError(GameError):
    """A game artifact could not be validated or durably persisted."""
