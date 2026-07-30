from __future__ import annotations

import json
from pathlib import Path
from typing import ClassVar

import pytest
from deep20_game import cli
from deep20_game.errors import GameError
from deep20_game.models import GameProviderExchange
from deep20_game.sampling import derive_guesser_prompt_nonce
from deep20_oracle import cli as root_cli
from deep20_oracle.cli import app
from typer._click.utils import strip_ansi
from typer.testing import CliRunner

from .conftest import provider_trace


def test_cli_error_payload_retains_sanitized_diagnostics_without_call_id() -> None:
    error = GameError(
        "request failed with api_key=sk-test-secret-value",
        code="provider_request_failed",
        call_id="GC-" + "1" * 32,
        details={
            "exception_type": "RuntimeError",
            "subject": "private subject snapshot",
        },
    )

    payload = json.loads(cli._error_payload(error))

    assert payload["error"]["code"] == "provider_request_failed"
    assert payload["error"]["message"] == "request failed with api_key=[REDACTED]"
    assert payload["error"]["diagnostics"]["causes"][0]["exception_type"] == "GameError"
    assert payload["error"]["diagnostics"]["metadata"] == {"exception_type": "RuntimeError"}
    serialized = json.dumps(payload)
    assert "call_id" not in serialized
    assert "private subject snapshot" not in serialized
    assert "sk-test-secret-value" not in serialized


def test_root_cli_exposes_game_and_cache_probe_commands() -> None:
    root = CliRunner().invoke(app, ["--help"])
    game = CliRunner().invoke(app, ["game", "--help"])
    play = CliRunner().invoke(app, ["game", "play", "--help"])

    assert root.exit_code == 0
    assert "game" in strip_ansi(root.output)
    assert game.exit_code == 0
    assert "cache-probe" in strip_ansi(game.output)
    assert play.exit_code == 0
    play_output = strip_ansi(play.output)
    assert "--cache-probe" in play_output
    assert "--seed" in play_output
    assert "--verbose" in play_output


class _CliGameProvider:
    requests: ClassVar[list] = []

    def __init__(self, api_key, config, *, title):
        self.config = config

    def complete(self, request):
        type(self).requests.append(request)
        if request.schema_name == "guesser_action_v3":
            raw = json.dumps(
                {
                    "result": {
                        "action": "GUESS",
                        "question": None,
                        "name": "Albert Einstein",
                        "description": "The theoretical physicist known for relativity.",
                    }
                }
            )
        else:
            raw = json.dumps(
                {
                    "answer": "YES",
                    "explanation": "The proposal identifies the exact subject.",
                }
            )
        return GameProviderExchange(
            raw_output=raw,
            trace=provider_trace(self.config, raw),
        )

    def close(self) -> None:
        pass


class _UnusedOracleProvider:
    def __init__(self, api_key, config):
        pass

    def close(self) -> None:
        pass


class _UnusedOracleProviderSet:
    def __init__(self, api_key, config):
        self.oracle = _UnusedOracleProvider(api_key, config)
        self.reviewer = _UnusedOracleProvider(api_key, config.reviewer)
        self.judge = _UnusedOracleProvider(api_key, config.judge)

    def close(self) -> None:
        self.oracle.close()
        self.reviewer.close()
        self.judge.close()


@pytest.mark.parametrize("verbose", [False, True])
def test_game_play_cli_runs_one_complete_fake_episode(
    tmp_path: Path,
    monkeypatch,
    verbose: bool,
) -> None:
    root = Path(__file__).parents[4]
    (tmp_path / ".git").mkdir()
    (tmp_path / "config").mkdir()
    for filename in (
        "game.yaml",
        "guesser.yaml",
        "guess-validator.yaml",
        "oracle.yaml",
    ):
        (tmp_path / "config" / filename).write_text((root / "config" / filename).read_text())
    (tmp_path / "config" / "subjects.yaml").write_text(
        (root / "config" / "subjects.yaml").read_text()
    )
    monkeypatch.setattr(cli, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(cli, "load_openrouter_api_key", lambda repository: "fake-key")
    monkeypatch.setattr(cli, "OpenRouterGameProvider", _CliGameProvider)
    monkeypatch.setattr(cli, "OpenRouterOracleProviderSet", _UnusedOracleProviderSet)
    monkeypatch.setattr(
        cli.GameRunAuditWriter,
        "_git",
        lambda self, arguments: "abc123" if arguments == ["rev-parse", "HEAD"] else "",
    )

    _CliGameProvider.requests = []
    arguments = [
        "game",
        "play",
        "T-0001",
        "--run-id",
        "cli-game",
        "--seed",
        "123",
    ]
    if verbose:
        arguments.append("--verbose")
    result = CliRunner().invoke(root_cli.app, arguments)

    assert result.exit_code == 0, result.output
    output = json.loads(result.stdout)
    assert output["schema_version"] == 9
    assert output["outcome"]["success"] is True
    assert output["summary"]["total_turns"] == 1
    assert output["run"]["duration_ms"] >= 0
    assert output["models"]["under_test"]["requested_model"] == "openai/gpt-5.6-luna"
    assert output["models"]["under_test"]["resolved_models"] == ["openai/gpt-5.6-luna"]
    assert (
        output["models"]["oracle"]["prompt_version"]
        == "live-web-oracle-v7-direct-negative-evidence"
    )
    assert output["summary"]["costs_usd"] == {
        "guesser": "0.01",
        "oracle": "0",
        "validator": "0.01",
        "total": "0.02",
    }
    assert output["summary"]["tokens"] == {
        "guesser": 100,
        "oracle": 0,
        "validator": 100,
        "total": 200,
    }
    assert output["summary"]["counted_questions"] == 0
    assert output["turns"][0]["action"]["name"] == "Albert Einstein"
    assert output["turns"][0]["adjudication"]["answer"] == "YES"
    assert [message["role"] for message in output["guesser_conversation"]] == [
        "system",
        "user",
        "assistant",
    ]
    assert output["llm_details"]["oracle"]["configuration"]["model"] == "openai/gpt-5.6-luna"
    assert output["llm_details"]["oracle"]["metrics"]["calls"] == 0
    guesser_request = next(
        request
        for request in _CliGameProvider.requests
        if request.schema_name == "guesser_action_v3"
    )
    assert all(set(message) == {"role", "content"} for message in guesser_request.messages)
    assert guesser_request.seed is None
    assert json.loads(guesser_request.messages[1]["content"]) == {
        "category": "person",
        "event": "BEGIN",
        "variation_token": derive_guesser_prompt_nonce(
            base_seed=123,
            trial_number=1,
        ),
    }
    serialized_request = guesser_request.model_dump_json()
    assert "verbose" not in serialized_request
    assert "artifact" not in serialized_request
    run_root = tmp_path / "runs" / "cli-game"
    expected = {"result.yml"}
    if verbose:
        expected.update(
            {
                "manifest.json",
                "oracle-calls.jsonl",
                "guesser-calls.jsonl",
                "guess-validator-calls.jsonl",
                "episode-events.jsonl",
            }
        )
    assert {path.name for path in run_root.iterdir()} == expected
