from __future__ import annotations

from typing import Protocol

from deep20_game.engine import GameEngine
from deep20_game.guesser import Guesser
from deep20_game.models import EpisodeResult, GameRequest, GuesserSamplingContext
from deep20_game.openrouter_provider import OpenRouterGameProvider
from deep20_game.sinks import ExecutionObserver
from deep20_game.validator import GuessValidator
from deep20_oracle.models import StrictModel, Subject
from deep20_oracle.openrouter_provider import OpenRouterOracleProviderSet
from deep20_oracle.service import Oracle

from .artifacts import BenchmarkTrialSink
from .models import (
    BenchmarkDefinitionSnapshot,
    BenchmarkModelSnapshot,
    TrialIdentity,
)


class TrialExecutionContext(StrictModel):
    identity: TrialIdentity
    definition: BenchmarkDefinitionSnapshot
    model: BenchmarkModelSnapshot
    subject: Subject
    subject_catalog_hash: str
    base_seed: int


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
        api_key: str,
        judge_ignored_providers: tuple[str, ...] = (),
    ):
        self.api_key = api_key
        self.judge_ignored_providers = judge_ignored_providers

    def execute(
        self,
        context: TrialExecutionContext,
        sink: BenchmarkTrialSink,
        observer: ExecutionObserver,
    ) -> EpisodeResult:
        definition = context.definition
        guesser_provider = OpenRouterGameProvider(
            self.api_key,
            context.model.configuration,
            title="Deep20Bench Benchmark Guesser",
        )
        validator_provider = OpenRouterGameProvider(
            self.api_key,
            definition.validator_configuration,
            title="Deep20Bench Benchmark Guess Validator",
        )
        oracle_providers = OpenRouterOracleProviderSet(
            self.api_key,
            definition.oracle_configuration,
            judge_ignored_providers=self.judge_ignored_providers,
        )
        try:
            engine = GameEngine(
                guesser=Guesser(
                    guesser_provider,
                    sink,
                    context.model.configuration,
                    definition.game_policy,
                ),
                oracle=Oracle(
                    oracle_providers.oracle,
                    oracle_providers.reviewer,
                    oracle_providers.judge,
                    sink,
                    definition.oracle_configuration,
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
        finally:
            guesser_provider.close()
            validator_provider.close()
            oracle_providers.close()
        return result
