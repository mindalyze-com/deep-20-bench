from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from deep20_oracle.artifacts import RunArtifactPolicy
from deep20_oracle.audit import RunAuditWriter
from deep20_oracle.catalog import load_subject_catalog
from deep20_oracle.config import load_oracle_config
from deep20_oracle.console import configure_console_logging
from deep20_oracle.credentials import CredentialLoadError, load_openrouter_api_key
from deep20_oracle.diagnostics import diagnose_exception
from deep20_oracle.errors import OracleError
from deep20_oracle.openrouter_provider import OpenRouterOracleProviderSet
from deep20_oracle.service import Oracle
from deep20_oracle.util import repository_root

from .audit import GameRunAuditWriter
from .cache_probe import (
    load_cache_probe,
    run_cache_probe,
    write_cache_probe,
)
from .config import BenchmarkMode, load_game_policy, load_model_config
from .engine import GameEngine
from .errors import GameError
from .guesser import Guesser
from .models import GameRequest, GuesserSamplingContext
from .openrouter_provider import OpenRouterGameProvider
from .validator import GuessValidator

game_app = typer.Typer(help="Play one Twenty Questions episode.")


def _error_payload(error: Exception) -> str:
    diagnostics = diagnose_exception(error)
    return json.dumps(
        {
            "error": {
                "code": getattr(error, "code", "unexpected_game_failure"),
                "message": diagnostics.causes[0].message,
                "diagnostics": diagnostics.model_dump(mode="json"),
            }
        }
    )


@game_app.command("play")
def play(
    target_id: str,
    run_id: Annotated[str, typer.Option(help="Immutable run directory identifier.")],
    game_config_path: Annotated[
        Path | None, typer.Option("--game-config", help="Game-policy YAML.")
    ] = None,
    guesser_config_path: Annotated[
        Path | None, typer.Option("--guesser-config", help="Guesser model YAML.")
    ] = None,
    validator_config_path: Annotated[
        Path | None,
        typer.Option("--validator-config", help="Guess Validator model YAML."),
    ] = None,
    oracle_config_path: Annotated[
        Path | None, typer.Option("--oracle-config", help="Oracle model YAML.")
    ] = None,
    catalog_path: Annotated[Path | None, typer.Option(help="Subject catalog YAML.")] = None,
    cache_probe_path: Annotated[
        Path | None,
        typer.Option(
            "--cache-probe",
            help="Successful cache-probe artifact required for official runs.",
        ),
    ] = None,
    base_seed: Annotated[
        int,
        typer.Option(
            "--seed",
            min=0,
            max=(2**31) - 1,
            help="Base seed for controlled Guesser sampling when the model supports it.",
        ),
    ] = 0,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            help="Write auxiliary manifests, component call logs, and episode events.",
        ),
    ] = False,
) -> None:
    configure_console_logging()
    root = repository_root()
    try:
        policy = load_game_policy(game_config_path or root / "config" / "game.yaml")
        guesser_config = load_model_config(guesser_config_path or root / "config" / "guesser.yaml")
        validator_config = load_model_config(
            validator_config_path or root / "config" / "guess-validator.yaml"
        )
        oracle_config = load_oracle_config(oracle_config_path or root / "config" / "oracle.yaml")
        catalog = load_subject_catalog(catalog_path or root / "config" / "subjects.yaml")
        subject = catalog.subject(target_id)
        probe = (
            load_cache_probe(cache_probe_path, guesser_config)
            if cache_probe_path is not None
            else None
        )
        if policy.benchmark_mode is BenchmarkMode.OFFICIAL and probe is None:
            raise GameError(
                "official game runs require --cache-probe",
                code="official_cache_probe_required",
            )
        api_key = load_openrouter_api_key(root)
        artifact_policy = RunArtifactPolicy(verbose=verbose)
        game_audit = GameRunAuditWriter(
            root / "runs",
            game_policy=policy,
            oracle_config=oracle_config,
            guesser_config=guesser_config,
            validator_config=validator_config,
            subject_catalog_hash=catalog.content_hash(),
            repository=root,
            cache_probe_summary=probe.summary() if probe else None,
            artifact_policy=artifact_policy,
        )
        oracle_audit = RunAuditWriter(
            root / "runs",
            config=oracle_config,
            subject_catalog_hash=catalog.content_hash(),
            repository=root,
            artifact_policy=artifact_policy,
        )
        guesser_provider = OpenRouterGameProvider(
            api_key,
            guesser_config,
            title="Deep20Bench Guesser",
        )
        validator_provider = OpenRouterGameProvider(
            api_key,
            validator_config,
            title="Deep20Bench Guess Validator",
        )
        oracle_providers = OpenRouterOracleProviderSet(api_key, oracle_config)
        try:
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
                    run_id=run_id,
                    subject=subject,
                    guesser_sampling=GuesserSamplingContext(base_seed=base_seed),
                )
            )
        finally:
            guesser_provider.close()
            validator_provider.close()
            oracle_providers.close()
    except (CredentialLoadError, GameError, OracleError, ValueError, OSError) as error:
        typer.echo(_error_payload(error), err=True)
        raise typer.Exit(1) from error
    typer.echo(result.model_dump_json(indent=2))


@game_app.command("cache-probe")
def cache_probe(
    guesser_config_path: Annotated[
        Path | None, typer.Option("--guesser-config", help="Guesser model YAML.")
    ] = None,
    game_config_path: Annotated[
        Path | None, typer.Option("--game-config", help="Game-policy YAML.")
    ] = None,
    output_path: Annotated[
        Path | None, typer.Option("--output", help="Cache-probe artifact path.")
    ] = None,
) -> None:
    configure_console_logging()
    root = repository_root()
    try:
        policy = load_game_policy(game_config_path or root / "config" / "game.yaml")
        config = load_model_config(guesser_config_path or root / "config" / "guesser.yaml")
        api_key = load_openrouter_api_key(root)
        provider = OpenRouterGameProvider(
            api_key,
            config,
            title="Deep20Bench Guesser Cache Probe",
        )
        try:
            artifact = run_cache_probe(provider, config, policy)
        finally:
            provider.close()
        destination = output_path or (
            root / "cache-probes" / f"{config.configuration_id}-{artifact.probe_id}.json"
        )
        write_cache_probe(destination, artifact)
    except (CredentialLoadError, GameError, OracleError, ValueError, OSError) as error:
        typer.echo(_error_payload(error), err=True)
        raise typer.Exit(1) from error
    typer.echo(
        json.dumps(
            {
                "path": str(destination),
                "success": artifact.success,
                "failure_reason": artifact.failure_reason,
                "cached_input_tokens": (
                    artifact.second_trace.usage.cached_input_tokens if artifact.second_trace else 0
                ),
            },
            indent=2,
        )
    )
    if not artifact.success:
        raise typer.Exit(1)
