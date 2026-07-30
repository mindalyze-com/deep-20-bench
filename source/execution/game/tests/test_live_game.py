from __future__ import annotations

import os
from pathlib import Path

import pytest
from deep20_game.audit import GameRunAuditWriter
from deep20_game.config import load_game_policy, load_model_config
from deep20_game.engine import GameEngine
from deep20_game.guesser import Guesser
from deep20_game.models import GameRequest
from deep20_game.openrouter_provider import OpenRouterGameProvider
from deep20_game.validator import GuessValidator
from deep20_oracle.audit import RunAuditWriter
from deep20_oracle.catalog import load_subject_catalog
from deep20_oracle.config import load_oracle_config
from deep20_oracle.credentials import load_openrouter_api_key
from deep20_oracle.openrouter_provider import OpenRouterOracleProviderSet
from deep20_oracle.service import Oracle


@pytest.mark.integration
def test_live_albert_einstein_episode(tmp_path: Path) -> None:
    if os.environ.get("DEEP20_RUN_LIVE_GAME") != "1":
        pytest.skip("set DEEP20_RUN_LIVE_GAME=1 to run the paid live episode")

    root = Path(__file__).parents[4]
    policy = load_game_policy(root / "config/game.yaml")
    guesser_config = load_model_config(root / "config/guesser.yaml")
    validator_config = load_model_config(root / "config/guess-validator.yaml")
    oracle_config = load_oracle_config(root / "config/oracle.yaml")
    catalog = load_subject_catalog(root / "config/subjects.yaml")
    key = load_openrouter_api_key(root)
    game_audit = GameRunAuditWriter(
        tmp_path / "runs",
        game_policy=policy,
        oracle_config=oracle_config,
        guesser_config=guesser_config,
        validator_config=validator_config,
        subject_catalog_hash=catalog.content_hash(),
        repository=root,
    )
    oracle_audit = RunAuditWriter(
        tmp_path / "runs",
        config=oracle_config,
        subject_catalog_hash=catalog.content_hash(),
        repository=root,
    )

    with (
        OpenRouterGameProvider(
            key,
            guesser_config,
            title="Deep20Bench Guesser Live Test",
        ) as guesser_provider,
        OpenRouterGameProvider(
            key,
            validator_config,
            title="Deep20Bench Validator Live Test",
        ) as validator_provider,
        OpenRouterOracleProviderSet(key, oracle_config) as oracle_providers,
    ):
        engine = GameEngine(
            guesser=Guesser(
                guesser_provider,
                game_audit,
                guesser_config,
                policy,
            ),
            oracle=Oracle(
                oracle_providers.oracle,
                oracle_providers.reviewer,
                oracle_providers.judge,
                oracle_audit,
                oracle_config,
            ),
            validator=GuessValidator(
                validator_provider,
                game_audit,
                validator_config,
            ),
            audit_writer=game_audit,
            policy=policy,
            guesser_config=guesser_config,
            oracle_config=oracle_config,
            validator_config=validator_config,
        )
        result = engine.play(
            GameRequest(
                run_id="live-einstein",
                subject=catalog.subject("T-0001"),
            )
        )

    assert result.scoring_eligible is True
    assert result.guesser_call_count >= 1
