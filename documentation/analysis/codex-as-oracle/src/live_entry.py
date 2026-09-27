"""Explicitly authorized startup, one Guesser canary, then the bounded experiment."""

from __future__ import annotations

import argparse
import json
import os

import bridge
from deep20_benchmark.canary import run_guesser_canary
from deep20_benchmark.catalog import load_model_catalog
from deep20_benchmark.preflight import OpenRouterRouteMetadata, validate_catalog_routes
from deep20_game.errors import GameError
from deep20_game.models import GameProviderExchange, GameProviderRequest
from deep20_game.openrouter_provider import OpenRouterGameProvider
from deep20_oracle import load_openrouter_api_key
from deep20_oracle.config import PromptProfile
from deep20_oracle.diagnostics import diagnose_exception
from deep20_oracle.models import ProviderTrace, StrictModel
from deep20_oracle.result_audit import provider_result_audit
from deep20_oracle.util import timestamp


class LaunchStatus(StrictModel):
    phase: str
    updated_at: str
    message: str


def status(phase: str, message: str) -> None:
    bridge.write_model(
        bridge.ROOT / "launch-status.json",
        LaunchStatus(phase=phase, updated_at=timestamp(), message=message),
    )
    print(json.dumps({"phase": phase, "message": message}), flush=True)


class CanaryProvider:
    def __init__(self, inner: bridge.GuesserProvider):
        self.inner = inner

    def complete(self, request: GameProviderRequest) -> GameProviderExchange:
        try:
            result = self.inner.complete(request)
        except GameError as error:
            bridge.write_model(bridge.ROOT / "guesser-canary-failure.json", diagnose_exception(error))
            trace_data = error.details.get("provider_trace")
            if trace_data is not None:
                trace = ProviderTrace.model_validate(trace_data)
                bridge.write_model(
                    bridge.ROOT / "guesser-canary-usage.json", provider_result_audit(trace)
                )
            raise
        bridge.write_model(
            bridge.ROOT / "guesser-canary-usage.json", provider_result_audit(result.trace)
        )
        return result

    def close(self) -> None:
        self.inner.close()


def main(provider_factory: bridge.ProviderFactory | None = None) -> None:
    if (bridge.ROOT / "runs").exists() or (bridge.ROOT / "launch-status.json").exists():
        raise ValueError("live startup requires a fresh experiment directory")
    # Claim startup before the canary. A failed canary has no runs/ directory yet.
    with (bridge.ROOT / "launch.claim").open("x"):
        pass
    factory = provider_factory or OpenRouterGameProvider
    status("preflight", "Checking the Guesser's exact route.")
    models = load_model_catalog(bridge.REPOSITORY / "config/models.yaml")
    preflight = validate_catalog_routes(
        models, OpenRouterRouteMetadata(), model_ids=(bridge.MODEL,)
    )
    bridge.write_model(bridge.ROOT / "route-preflight.json", preflight)
    if not preflight.valid:
        raise RuntimeError("Guesser route preflight failed")
    key = load_openrouter_api_key(bridge.REPOSITORY)
    model = models.model(bridge.MODEL)
    status("canary", "Checking one Guesser structured action before the games.")
    canary = run_guesser_canary(
        model,
        api_key=key,
        profile=PromptProfile.QUALIFIED_V1,
        provider=CanaryProvider(
            factory(
                key, model.configuration, title="Deep20Bench Direct Experiment Canary"
            )
        ),
    )
    bridge.write_model(bridge.ROOT / "guesser-canary.json", canary)
    if not canary.valid:
        raise RuntimeError("Guesser startup canary failed")
    status("running", "Guesser is running; Codex supplies support decisions directly.")
    if provider_factory is None:
        bridge.run()
    else:
        bridge.run(provider_factory)
    status("completed", "All requested games have terminal results.")


if __name__ == "__main__":
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if not args.live:
        parser.error("this paid experiment requires --live")
    try:
        main()
    except Exception as error:  # noqa: BLE001 - redact errors at the executable boundary.
        # Do not log provider payloads, credentials, or raw exception messages.
        status("interrupted", f"Experiment stopped with {type(error).__name__}.")
        raise SystemExit(1) from None
