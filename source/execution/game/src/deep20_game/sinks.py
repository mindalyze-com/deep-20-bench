from __future__ import annotations

from typing import Protocol

from deep20_oracle.models import PersistedRecord

from .models import (
    EpisodeEvent,
    EpisodeResult,
    GameProgressEvent,
    GuesserCall,
    GuesserFailureRecord,
    GuesserSuccessRecord,
    GuessValidatorCall,
    ValidatorFailureRecord,
    ValidatorSuccessRecord,
)


class GameAuditSink(Protocol):
    """Synchronous persistence boundary for one game episode."""

    def prepare_run(self, run_id: str) -> None: ...

    def persist_guesser_success(self, record: GuesserSuccessRecord) -> GuesserCall: ...

    def persist_guesser_failure(self, record: GuesserFailureRecord) -> PersistedRecord: ...

    def persist_validator_success(self, record: ValidatorSuccessRecord) -> GuessValidatorCall: ...

    def persist_validator_failure(self, record: ValidatorFailureRecord) -> PersistedRecord: ...

    def persist_episode_event(self, event: EpisodeEvent) -> PersistedRecord: ...

    def persist_episode_result(self, result: EpisodeResult) -> PersistedRecord: ...


class ExecutionObserver(Protocol):
    def observe(self, event: GameProgressEvent) -> None: ...


class NullExecutionObserver:
    def observe(self, event: GameProgressEvent) -> None:
        del event
