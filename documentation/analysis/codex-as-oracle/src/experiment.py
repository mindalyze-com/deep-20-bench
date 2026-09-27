"""One on-demand Codex Oracle experiment interface for every registered Guesser."""

from __future__ import annotations

import argparse
import json
import os
import runpy
import sys
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from urllib.parse import quote

import bridge
import httpx
import live_entry
from deep20_benchmark.catalog import BenchmarkCatalog, load_model_catalog
from deep20_benchmark.models import (
    BenchmarkExecutionId,
    BenchmarkModelId,
    BenchmarkModelSnapshot,
    BenchmarkRequest,
    SubjectId,
)
from deep20_game.config import BenchmarkMode, ModelConfig
from deep20_game.openrouter_provider import OpenRouterGameProvider
from deep20_oracle import load_subject_catalog
from deep20_oracle.cache_contract import oracle_contract_hash
from deep20_oracle.models import StrictModel
from pydantic import Field, model_validator
from spend_guard import Budget, BudgetState, price_bound


class Command(StrEnum):
    MODELS = "models"
    PREVIEW = "preview"
    RUN = "run"
    PENDING = "pending"
    NEXT = "next"
    SUBMIT = "submit"
    PROGRESS = "progress"
    COMPARISON = "comparison"


class Options(StrictModel):
    command: Command
    model: BenchmarkModelId | None = None
    execution: BenchmarkExecutionId | None = None
    baseline: BenchmarkExecutionId | None = None
    budget_usd: Decimal | None = Field(default=None, gt=0, allow_inf_nan=False)
    iterations: int | None = Field(default=None, ge=1, le=100)
    seed: int | None = Field(default=None, ge=0, le=2**31 - 1)
    live: bool = False
    input: Path | None = None
    after: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def required_options(self) -> Options:
        if self.command is not Command.MODELS and self.execution is None:
            raise ValueError("--execution is required")
        if self.command is Command.PREVIEW:
            if self.model is None or self.budget_usd is None:
                raise ValueError("preview requires --model and --budget-usd")
        elif any(
            value is not None
            for value in (
                self.budget_usd,
                self.iterations,
                self.seed,
                self.baseline,
            )
        ):
            raise ValueError("schedule, baseline and budget options belong to preview")
        if self.command is Command.RUN and not self.live:
            raise ValueError("paid execution requires --live")
        if self.command is Command.SUBMIT and self.input is None:
            raise ValueError("submit requires --input")
        return self


class PreparedExperiment(StrictModel):
    request: BenchmarkRequest
    model: BenchmarkModelSnapshot
    benchmark_catalog: BenchmarkCatalog
    subject_catalog_hash: str
    oracle_contract_hash: str
    baseline: BenchmarkExecutionId | None = None
    budget_usd: Decimal = Field(gt=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def matching_model(self) -> PreparedExperiment:
        if self.request.model_id != self.model.model_id:
            raise ValueError("prepared model differs from request")
        return self


def root_for(execution: BenchmarkExecutionId) -> Path:
    return bridge.REPOSITORY / "private/reviews/codex-oracle" / str(execution)


def select(prepared: PreparedExperiment) -> None:
    """Bind the existing engine and reporting helpers to one prepared experiment."""
    bridge.ROOT = root_for(prepared.request.execution_id)
    bridge.EXECUTION = str(prepared.request.execution_id)
    bridge.MODEL = prepared.request.model_id
    if prepared.baseline is not None:
        bridge.BASELINE = prepared.baseline


def prepare(options: Options) -> PreparedExperiment:
    assert options.model is not None and options.execution is not None
    assert options.budget_usd is not None
    models = load_model_catalog(bridge.REPOSITORY / "config/models.yaml")
    model = models.model(options.model)
    subjects = load_subject_catalog(bridge.REPOSITORY / "config/subjects.yaml")
    catalog = bridge.experimental_catalog()
    request = BenchmarkRequest(
        benchmark_id=bridge.BENCHMARK,
        execution_id=options.execution,
        model_id=options.model,
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        target_ids=tuple(SubjectId(subject.target_id) for subject in subjects.active_subjects()),
        iterations_override=options.iterations if options.iterations is not None else 3,
        base_seed=options.seed if options.seed is not None else 0,
    )
    if not request.target_ids:
        raise ValueError("no active subjects")
    prepared = PreparedExperiment(
        request=request,
        model=model,
        benchmark_catalog=catalog,
        subject_catalog_hash=subjects.content_hash(),
        oracle_contract_hash=oracle_contract_hash(
            catalog.entry(bridge.BENCHMARK).oracle_configuration
        ),
        baseline=options.baseline,
        budget_usd=options.budget_usd,
    )
    select(prepared)
    # Atomic creation prevents two previews from selecting/overwriting the same execution.
    bridge.ROOT.mkdir(parents=True, exist_ok=False)
    bridge.preview(request)
    bridge.write_model(bridge.ROOT / "experiment.json", prepared)
    return prepared


def load_prepared(options: Options) -> PreparedExperiment:
    assert options.execution is not None
    root = root_for(options.execution)
    prepared = PreparedExperiment.model_validate_json((root / "experiment.json").read_text())
    if prepared.request.execution_id != options.execution:
        raise ValueError("execution does not match the prepared experiment")
    if options.model is not None and options.model != prepared.request.model_id:
        raise ValueError("model does not match the prepared experiment")
    select(prepared)
    return prepared


def validate_prepared(prepared: PreparedExperiment) -> None:
    """Reject preview drift before credentials, metadata requests or paid calls."""
    models = load_model_catalog(bridge.REPOSITORY / "config/models.yaml")
    subjects = load_subject_catalog(bridge.REPOSITORY / "config/subjects.yaml")
    catalog = bridge.experimental_catalog()
    saved_request = BenchmarkRequest.model_validate_json((bridge.ROOT / "request.json").read_text())
    saved_catalog = BenchmarkCatalog.model_validate_json(
        (bridge.ROOT / "benchmark-catalog.json").read_text()
    )
    if (
        models.model(prepared.request.model_id) != prepared.model
        or subjects.content_hash() != prepared.subject_catalog_hash
        or catalog != prepared.benchmark_catalog
        or saved_catalog != prepared.benchmark_catalog
        or saved_request != prepared.request
        or oracle_contract_hash(catalog.entry(bridge.BENCHMARK).oracle_configuration)
        != prepared.oracle_contract_hash
    ):
        raise ValueError("prepared configuration changed; prepare a fresh execution")


def launch(prepared: PreparedExperiment) -> None:
    validate_prepared(prepared)
    if (bridge.ROOT / "launch-status.json").exists() or (bridge.ROOT / "runs").exists():
        raise ValueError("launch requires a fresh execution")
    # Protect metadata, accounting and the canary together, including failed startups.
    with (bridge.ROOT / "budget-launch.claim").open("x"):
        pass
    expected_config = prepared.model.configuration
    response = httpx.get(
        "https://openrouter.ai/api/v1/models/"
        + quote(expected_config.model, safe="/")
        + "/endpoints",
        timeout=30,
    )
    response.raise_for_status()
    pricing = price_bound(response.content, expected_config)
    metadata_path = bridge.ROOT / "route-pricing.json"
    metadata_path.write_bytes(response.content)
    metadata_path.chmod(0o600)
    bridge.write_model(bridge.ROOT / "price-bound.json", pricing)
    state = BudgetState(limit_usd=prepared.budget_usd)
    budget_path = bridge.ROOT / "budget.json"
    if budget_path.exists():
        raise ValueError("preserve the existing budget ledger")
    bridge.write_model(budget_path, state)
    budget = Budget(state, pricing, lambda updated: bridge.write_model(budget_path, updated))

    def provider_factory(
        api_key: str, config: ModelConfig, *, title: str
    ) -> OpenRouterGameProvider:
        if config != expected_config:
            raise ValueError("provider configuration differs from the prepared model")
        provider = OpenRouterGameProvider(api_key, config, title=title)
        provider.http_client._client.event_hooks = {
            "request": [budget.reserve],
            "response": [budget.settle],
        }
        return provider

    try:
        live_entry.main(provider_factory)
    except Exception as error:
        live_entry.status("interrupted", f"Experiment stopped with {type(error).__name__}.")
        raise


def main(argv: list[str] | None = None) -> None:
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=tuple(Command))
    parser.add_argument("--model")
    parser.add_argument("--execution")
    parser.add_argument("--baseline")
    parser.add_argument("--budget-usd")
    parser.add_argument("--iterations", type=int)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--after", type=int, default=0)
    options = Options.model_validate(vars(parser.parse_args(argv)))
    if options.command is Command.MODELS:
        models = load_model_catalog(bridge.REPOSITORY / "config/models.yaml")
        for entry in models.models.values():
            print(f"{entry.model_id}\t{entry.display_name}\t{entry.configuration.model}")
        return
    if options.command is Command.PREVIEW:
        prepare(options)
        return
    prepared = load_prepared(options)
    if options.command is Command.RUN:
        launch(prepared)
    elif options.command is Command.PENDING:
        bridge.pending()
    elif options.command is Command.SUBMIT:
        assert options.input is not None
        bridge.submit(options.input, require_identity=True)
    elif options.command is Command.COMPARISON:
        if prepared.baseline is None:
            raise ValueError("comparison requires a --baseline selected during preview")
        import comparison

        comparison.BASELINE = prepared.baseline
        comparison.main()
    else:
        previous_argv = sys.argv
        try:
            sys.argv = [str(options.command) + ".py"]
            if options.command is Command.NEXT:
                sys.argv.extend(("--after", str(options.after)))
            runpy.run_path(
                str(Path(__file__).with_name(str(options.command) + ".py")), run_name="__main__"
            )
        finally:
            sys.argv = previous_argv


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001 - no credentials or raw payloads in console errors.
        print(
            json.dumps(
                {
                    "status": "failed",
                    "code": "interactive_experiment_failed",
                    "error_type": type(error).__name__,
                }
            ),
            file=sys.stderr,
        )
        raise SystemExit(1) from None
