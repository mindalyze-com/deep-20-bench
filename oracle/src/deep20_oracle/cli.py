from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Annotated

import typer

from .artifacts import RunArtifactPolicy
from .audit import RunAuditWriter
from .catalog import load_subject_catalog
from .config import OracleConfig, load_oracle_config
from .console import configure_console_logging
from .credentials import CredentialLoadError, load_openrouter_api_key
from .diagnostics import diagnose_exception
from .errors import OracleError
from .models import OracleRequest
from .openrouter_provider import OpenRouterOracleProviderSet
from .service import Oracle
from .util import repository_root

app = typer.Typer(help="Deep20Bench benchmark, game engine, and live-web Oracle.")
oracle_app = typer.Typer(help="Ask the independent live-web Oracle.")
app.add_typer(oracle_app, name="oracle")

try:
    from deep20_game.cli import game_app as imported_game_app
except ImportError:
    pass
else:
    app.add_typer(imported_game_app, name="game")

try:
    from deep20_benchmark.cli import benchmark_app as imported_benchmark_app
except ImportError:
    pass
else:
    app.add_typer(imported_benchmark_app, name="benchmark")

logger = logging.getLogger("deep20.oracle")


@oracle_app.command("ask")
def ask(
    target_id: str,
    question: str,
    run_id: Annotated[str, typer.Option(help="Run directory identifier for the audit record.")],
    config_path: Annotated[Path | None, typer.Option(help="Oracle YAML configuration.")] = None,
    catalog_path: Annotated[Path | None, typer.Option(help="Subject catalog YAML.")] = None,
    model: Annotated[str | None, typer.Option(help="Override the exact model slug.")] = None,
    reasoning_effort: Annotated[
        str | None, typer.Option(help="Override model reasoning effort.")
    ] = None,
    provider_route: Annotated[
        str | None, typer.Option("--provider", help="Override the provider route.")
    ] = None,
    allow_fallbacks: Annotated[
        bool | None,
        typer.Option(
            "--allow-fallbacks/--no-allow-fallbacks",
            help="Override provider fallback routing.",
        ),
    ] = None,
    parallel_search: Annotated[
        bool | None,
        typer.Option(
            "--parallel-search/--no-parallel-search",
            help="Use Parallel instead of automatic/native web search.",
        ),
    ] = None,
    max_search_results: Annotated[
        int | None, typer.Option(help="Override maximum web-search results.")
    ] = None,
    max_output_tokens: Annotated[
        int | None, typer.Option(help="Override maximum completion tokens.")
    ] = None,
    timeout_seconds: Annotated[
        int | None, typer.Option(help="Override request timeout in seconds.")
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            help="Write auxiliary run manifest and Oracle call log.",
        ),
    ] = False,
) -> None:
    configure_console_logging()
    root = repository_root()
    config_file = config_path or root / "config" / "oracle.yaml"
    catalog_file = catalog_path or root / "config" / "subjects.yaml"
    base_config = load_oracle_config(config_file)
    overrides = {
        key: value
        for key, value in {
            "model": model,
            "reasoning_effort": reasoning_effort,
            "provider": provider_route,
            "allow_fallbacks": allow_fallbacks,
            "parallel_search": parallel_search,
            "max_search_results": max_search_results,
            "max_output_tokens": max_output_tokens,
            "timeout_seconds": timeout_seconds,
        }.items()
        if value is not None
    }
    config = OracleConfig.model_validate({**base_config.model_dump(mode="python"), **overrides})
    catalog = load_subject_catalog(catalog_file)
    try:
        api_key = load_openrouter_api_key(root)
    except CredentialLoadError as error:
        diagnostics = diagnose_exception(error)
        typer.echo(
            json.dumps(
                {
                    "error": {
                        "code": error.code,
                        "message": diagnostics.causes[0].message,
                        "diagnostics": diagnostics.model_dump(mode="json"),
                    }
                }
            ),
            err=True,
        )
        raise typer.Exit(2)
    providers = OpenRouterOracleProviderSet(api_key, config)
    writer = RunAuditWriter(
        root / "runs",
        config=config,
        subject_catalog_hash=catalog.content_hash(),
        repository=root,
        artifact_policy=RunArtifactPolicy(verbose=verbose),
    )
    service = Oracle(
        providers.oracle,
        providers.reviewer,
        providers.judge,
        writer,
        config,
    )
    subject = catalog.subject(target_id)
    logger.info(
        "oracle.run run=%s target=%s model=%s provider=%s",
        run_id,
        subject.target_id,
        config.model,
        config.provider,
    )
    try:
        try:
            call = service.ask(
                OracleRequest(
                    run_id=run_id,
                    subject=subject,
                    question=question,
                )
            )
        finally:
            providers.close()
    except OracleError as error:
        diagnostics = diagnose_exception(error)
        typer.echo(
            json.dumps(
                {
                    "error": {
                        "code": error.code,
                        "message": diagnostics.causes[0].message,
                        "diagnostics": diagnostics.model_dump(mode="json"),
                    }
                }
            ),
            err=True,
        )
        raise typer.Exit(1) from error
    typer.echo(call.model_dump_json(indent=2))


if __name__ == "__main__":
    app()
