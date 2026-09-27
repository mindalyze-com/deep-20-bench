"""Offline verification of retained startup failures and private-data projection."""

from pathlib import Path

import bridge
import pytest
from deep20_game.errors import GameProviderError
from deep20_game.models import GameProviderExchange, GameProviderRequest
from deep20_game.openrouter_provider import OpenRouterGameProvider
from deep20_oracle.models import ProviderTrace
from live_entry import CanaryProvider


def test_startup_failure_retains_diagnostics_without_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trace = ProviderTrace(
        requested_at="2026-09-10T19:26:09Z",
        completed_at="2026-09-10T19:28:10Z",
        latency_ms=121_000,
        http_status_code=400,
        requested_model="openai/gpt-6-astra",
        requested_provider="openai",
        request={"messages": [{"content": "PRIVATE-PROMPT-SENTINEL"}]},
        response={"error": {"code": 400, "message": "Invalid fixture parameter"}},
    )
    failure = GameProviderError(
        "OpenRouter request failed", code="provider_invalid_request",
        details={"provider_trace": trace.model_dump(mode="json")},
    )

    def fail(
        self: OpenRouterGameProvider, request: GameProviderRequest
    ) -> GameProviderExchange:
        raise failure

    monkeypatch.setattr(bridge, "ROOT", tmp_path)
    monkeypatch.setattr(OpenRouterGameProvider, "complete", fail)
    provider = CanaryProvider(object.__new__(OpenRouterGameProvider))
    request = GameProviderRequest(
        messages=({"role": "user", "content": "PRIVATE-PROMPT-SENTINEL"},),
        output_schema={}, schema_name="fixture", session_id="fixture", prompt_cache_key="fixture",
    )
    with pytest.raises(GameProviderError) as captured:
        provider.complete(request)
    assert captured.value is failure
    diagnostic = (tmp_path / "guesser-canary-failure.json").read_text()
    usage = (tmp_path / "guesser-canary-usage.json").read_text()
    assert "Invalid fixture parameter" in diagnostic
    assert '"http_status_code": 400' in usage
    assert "PRIVATE-PROMPT-SENTINEL" not in diagnostic + usage
    assert (tmp_path / "guesser-canary-failure.json").stat().st_mode & 0o777 == 0o600
