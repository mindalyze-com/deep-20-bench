from __future__ import annotations

from collections.abc import Callable
from contextlib import ExitStack
from typing import Protocol

from deep20_backends.config import ApprovePrimarySettings
from deep20_backends.models import Role
from deep20_game.config import ModelConfig
from deep20_game.engine import GameEngine
from deep20_game.guesser import Guesser
from deep20_game.models import EpisodeResult, GameRequest, GuesserSamplingContext
from deep20_game.sinks import ExecutionObserver
from deep20_game.validator import GuessValidator
from deep20_oracle.config import ModelRouteConfig
from deep20_oracle.models import StrictModel, Subject
from deep20_oracle.roles import ApprovePrimaryReviewer
from deep20_oracle.service import Oracle
from pydantic import Field

from .artifacts import BenchmarkTrialSink
from .backend_adapters import GameBackendAdapter, OracleBackendAdapter
from .backend_config import RuntimeSnapshot
from .backend_factory import BackendFactory
from .edition_models import EditionExecution
from .history_cache import LazyOracleHistoryCache
from .models import (
    BenchmarkDefinitionSnapshot,
    BenchmarkModelSnapshot,
    TrialIdentity,
)


class TrialExecutionContext(StrictModel):
    edition: EditionExecution | None = None
    identity: TrialIdentity
    definition: BenchmarkDefinitionSnapshot
    model: BenchmarkModelSnapshot
    subject: Subject
    subject_catalog_hash: str
    base_seed: int
    runtime: RuntimeSnapshot | None = None
    attempt_number: int = Field(default=1, ge=1)


class EpisodeExecutor(Protocol):
    def execute(
        self,
        context: TrialExecutionContext,
        sink: BenchmarkTrialSink,
        observer: ExecutionObserver,
    ) -> EpisodeResult: ...


class LiveEpisodeExecutor:
    """Compose one paid episode while the benchmark owns persistence and observation."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        oracle_cache: LazyOracleHistoryCache | None = None,
        judge_ignored_providers: tuple[str, ...] = (),
        backend_factory: BackendFactory | None = None,
        factory_provider: Callable[[TrialExecutionContext], BackendFactory] | None = None,
    ):
        self.api_key = api_key
        self.oracle_cache = oracle_cache
        self.judge_ignored_providers = judge_ignored_providers
        self.backend_factory = backend_factory
        self.factory_provider = factory_provider

    def execute(
        self,
        context: TrialExecutionContext,
        sink: BenchmarkTrialSink,
        observer: ExecutionObserver,
    ) -> EpisodeResult:
        definition = context.definition
        if context.runtime is None and context.edition is None:
            raise ValueError("live benchmarks require an edition preflight")
        factory = (self.factory_provider(context) if self.factory_provider is not None else None)
        factory = factory or self.backend_factory or BackendFactory(
            api_key=self.api_key, runtime=context.runtime,
            judge_ignored_providers=self.judge_ignored_providers,
        )
        with ExitStack() as resources:
            def game_provider(role: Role, config: ModelConfig) -> GameBackendAdapter:
                backend = factory.create(role, config)
                resources.callback(backend.close)
                return GameBackendAdapter(backend, role, config, record_backend=context.runtime is not None)

            def oracle_provider(role: Role, config: ModelRouteConfig) -> OracleBackendAdapter:
                backend = factory.create(role, config)
                resources.callback(backend.close)
                return OracleBackendAdapter(backend, role, config, record_backend=context.runtime is not None)

            guesser_provider = game_provider(Role.GUESSER, context.model.configuration)
            validator_provider = game_provider(Role.VALIDATOR, definition.validator_configuration)
            researcher = oracle_provider(Role.ORACLE, definition.oracle_configuration)
            reviewer = oracle_provider(Role.REVIEWER, definition.oracle_configuration.reviewer)
            judge = oracle_provider(Role.JUDGE, definition.oracle_configuration.judge)
            engine = GameEngine(
                oracle_cache=self.oracle_cache,
                reuse_episode_answers=(self.oracle_cache is not None
                    and self.oracle_cache.snapshot is not None
                    and self.oracle_cache.snapshot.episode_reuse_policy == "same_episode_ask_v1"),
                guesser=Guesser(
                    guesser_provider,
                    sink,
                    context.model.configuration,
                    definition.game_policy,
                ),
                oracle=Oracle(
                    researcher,
                    reviewer,
                    judge,
                    sink,
                    definition.oracle_configuration,
                    reviewer_client=(ApprovePrimaryReviewer() if context.runtime is not None
                                     and isinstance(context.runtime.roles.reviewer, ApprovePrimarySettings)
                                     else None),
                ),
                validator=GuessValidator(
                    validator_provider,
                    sink,
                    definition.validator_configuration,
                ),
                audit_writer=sink,
                policy=definition.game_policy,
                guesser_config=context.model.configuration,
                oracle_config=definition.oracle_configuration,
                validator_config=definition.validator_configuration,
                observer=observer,
            )
            result = engine.play(
                GameRequest(
                    run_id=str(context.identity.episode_run_id),
                    subject=context.subject,
                    guesser_sampling=GuesserSamplingContext(
                        base_seed=context.base_seed,
                        trial_number=context.identity.trial_number,
                    ),
                )
            )
            factory.episode_committed()
        return result
