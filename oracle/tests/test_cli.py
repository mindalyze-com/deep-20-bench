from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import provider_trace
from deep20_oracle import cli
from deep20_oracle.config import OracleConfig
from deep20_oracle.provider import ProviderExchange, ProviderRequest
from typer.testing import CliRunner


class CliProvider:
    seen_config = None
    seen_api_key = None

    def __init__(self, api_key, config):
        self.config = config
        if isinstance(config, OracleConfig):
            type(self).seen_config = config
        type(self).seen_api_key = api_key

    def close(self) -> None:
        pass

    def complete(self, request: ProviderRequest) -> ProviderExchange:
        is_oracle = isinstance(self.config, OracleConfig)
        raw = (
            json.dumps(
                {
                    "answer": "YES",
                    "evidence": [
                        {
                            "source_url": "https://example.test/source",
                            "excerpt": "A source excerpt.",
                            "validation": "model_reported",
                        }
                    ],
                }
            )
            if is_oracle
            else json.dumps(
                {
                    "answer": "YES",
                    "basis": "evidence",
                    "evidence_indices": [1],
                }
            )
        )
        trace = provider_trace(
            raw_output=raw,
            search_count=int(is_oracle),
            model=self.config.model,
            provider=self.config.provider,
        )
        return ProviderExchange(raw_output=raw, trace=trace)


class CliProviderSet:
    def __init__(self, api_key, config):
        self.oracle = CliProvider(api_key, config)
        self.reviewer = CliProvider(api_key, config.reviewer)
        self.judge = CliProvider(api_key, config.judge)

    def close(self) -> None:
        self.oracle.close()
        self.reviewer.close()
        self.judge.close()


@pytest.mark.parametrize("verbose", [False, True])
@pytest.mark.parametrize(
    ("yaml_parallel_search", "search_flag", "expected_parallel_search"),
    [
        (False, "--parallel-search", True),
        (True, "--no-parallel-search", False),
    ],
)
def test_cli_asks_oracle_and_respects_artifact_verbosity(
    tmp_path: Path,
    monkeypatch,
    config,
    subject,
    verbose: bool,
    yaml_parallel_search: bool,
    search_flag: str,
    expected_parallel_search: bool,
) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "oracle.yaml").write_text(
        f"""\
gateway: openrouter
model: openai/test-model
provider: openai
reasoning_effort: high
allow_fallbacks: false
parallel_search: {str(yaml_parallel_search).lower()}
max_search_results: 5
max_output_tokens: 1500
timeout_seconds: 30
"""
    )
    (tmp_path / "config" / "subjects.yaml").write_text(
        """\
version: 1
subjects:
  T-0001:
    target_id: T-0001
    canonical_name: Albert Einstein
    aliases: [Einstein]
    entity_type: person
    description: The physicist identified by Wikidata Q937.
"""
    )
    monkeypatch.setattr(cli, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(cli, "OpenRouterOracleProviderSet", CliProviderSet)
    monkeypatch.setattr(
        cli.RunAuditWriter,
        "_git",
        lambda self, arguments: "abc123" if arguments == ["rev-parse", "HEAD"] else "",
    )

    arguments = [
        "oracle",
        "ask",
        "T-0001",
        "Was this person born before 1900?",
        "--run-id",
        "cli-test",
        "--model",
        "openai/alternate-model",
        "--reasoning-effort",
        "medium",
        "--provider",
        "openai",
        search_flag,
        "--max-search-results",
        "3",
        "--max-output-tokens",
        "800",
        "--timeout-seconds",
        "45",
    ]
    if verbose:
        arguments.append("--verbose")
    result = CliRunner().invoke(
        cli.app,
        arguments,
        env={"OPENROUTER_API_KEY": "not-a-real-key"},
    )

    assert result.exit_code == 0, result.output
    output = json.loads(result.output)
    assert output["result"]["answer"] == "YES"
    assert output["metrics"]["cost_usd"] == "0.02"
    assert output["metrics"]["latency_ms"] == 2_000
    assert output["metrics"]["cached_input_tokens"] == 0
    assert output["metrics"]["cache_write_tokens"] == 0
    assert "cost_usd" not in output
    assert "llm_latency_ms" not in output
    assert CliProvider.seen_config.model == "openai/alternate-model"
    assert CliProvider.seen_config.reasoning_effort == "medium"
    assert CliProvider.seen_config.parallel_search is expected_parallel_search
    assert CliProvider.seen_config.max_search_results == 3
    assert CliProvider.seen_config.max_output_tokens == 800
    assert CliProvider.seen_config.timeout_seconds == 45
    run_root = tmp_path / "runs" / "cli-test"
    if verbose:
        assert {path.name for path in run_root.iterdir()} == {
            "manifest.json",
            "oracle-calls.jsonl",
        }
    else:
        assert not run_root.exists()


def test_cli_loads_api_key_from_private_yaml(tmp_path: Path, monkeypatch, config, subject) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / "config").mkdir()
    (tmp_path / "private").mkdir()
    (tmp_path / "config" / "oracle.yaml").write_text(
        """\
gateway: openrouter
model: openai/test-model
provider: openai
reasoning_effort: high
allow_fallbacks: false
parallel_search: true
max_search_results: 5
max_output_tokens: 1500
timeout_seconds: 30
"""
    )
    (tmp_path / "config" / "subjects.yaml").write_text(
        """\
version: 1
subjects:
  T-0001:
    target_id: T-0001
    canonical_name: Albert Einstein
    aliases: [Einstein]
    entity_type: person
    description: The physicist identified by Wikidata Q937.
"""
    )
    (tmp_path / "private" / "openrouter.yaml").write_text(
        "api:\n  api_key: key-loaded-from-private-file\n"
    )
    monkeypatch.setattr(cli, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(cli, "OpenRouterOracleProviderSet", CliProviderSet)
    monkeypatch.setattr(
        cli.RunAuditWriter,
        "_git",
        lambda self, arguments: "abc123" if arguments == ["rev-parse", "HEAD"] else "",
    )

    result = CliRunner().invoke(
        cli.app,
        [
            "oracle",
            "ask",
            "T-0001",
            "Was this person born before 1900?",
            "--run-id",
            "cli-private-key-test",
        ],
        env={"OPENROUTER_API_KEY": ""},
    )

    assert result.exit_code == 0, result.output
    assert CliProvider.seen_api_key == "key-loaded-from-private-file"
