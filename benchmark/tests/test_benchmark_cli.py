import json
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest
from deep20_benchmark import cli
from deep20_benchmark.canary import LlmCanaryResult, StartupCanaryResult
from deep20_benchmark.cli import benchmark_app
from deep20_benchmark.models import BenchmarkLlmRole
from typer._click.utils import strip_ansi
from typer.testing import CliRunner


def test_benchmark_mode_is_required_and_lists_every_choice() -> None:
    result = CliRunner().invoke(
        benchmark_app,
        [
            "run",
            "B-0001",
            "--run-id",
            "BX-mode-required-001",
            "--model",
            "M-0001",
        ],
    )

    output = strip_ansi(result.output)

    assert result.exit_code == 2
    assert "Missing option '--benchmark-mode'" in output
    assert "official" in output
    assert "experimental" in output


def test_benchmark_mode_rejects_values_outside_the_declared_choices() -> None:
    result = CliRunner().invoke(
        benchmark_app,
        [
            "run",
            "B-0001",
            "--run-id",
            "BX-mode-invalid-001",
            "--model",
            "M-0001",
            "--benchmark-mode",
            "draft",
        ],
    )

    output = strip_ansi(result.output)

    assert result.exit_code == 2
    assert "Invalid value for '--benchmark-mode': 'draft'" in output
    assert "official" in output
    assert "experimental" in output


def test_success_relies_on_concise_result_log_without_dumping_typed_result(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class FakeRunner:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def run(self, _request: object, **_kwargs: object) -> object:
            return SimpleNamespace(
                outcome=SimpleNamespace(has_infrastructure_failures=False),
                model_dump_json=lambda **_kwargs: pytest.fail(
                    "successful benchmark result must not be dumped to the console"
                )
            )

    monkeypatch.setattr(cli, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(cli, "load_model_catalog", lambda _path: object())
    monkeypatch.setattr(cli, "load_benchmark_catalog", lambda _path: object())
    monkeypatch.setattr(cli, "load_subject_catalog", lambda _path: object())
    monkeypatch.setattr(cli, "load_openrouter_api_key", lambda _root: "unused")
    monkeypatch.setattr(cli, "ArtifactStore", lambda _root: object())
    monkeypatch.setattr(cli, "BenchmarkRunner", FakeRunner)
    monkeypatch.setattr(cli, "prevent_idle_system_sleep", nullcontext)

    result = CliRunner().invoke(
        benchmark_app,
        [
            "run",
            "B-0001",
            "--run-id",
            "BX-no-result-dump-001",
            "--model",
            "M-0001",
            "--benchmark-mode",
            "experimental",
        ],
    )

    assert result.exit_code == 0
    assert result.output == ""


@pytest.mark.parametrize("command", ("run", "repair"))
def test_official_execution_with_no_canary_skips_route_probes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    command: str,
) -> None:
    class FakeRunner:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def run(self, _request: object, **_kwargs: object) -> object:
            return SimpleNamespace(
                outcome=SimpleNamespace(has_infrastructure_failures=False)
            )

    monkeypatch.setattr(cli, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(cli, "load_model_catalog", lambda _path: object())
    monkeypatch.setattr(cli, "load_benchmark_catalog", lambda _path: object())
    monkeypatch.setattr(cli, "load_subject_catalog", lambda _path: object())
    monkeypatch.setattr(cli, "load_openrouter_api_key", lambda _root: "unused")
    monkeypatch.setattr(cli, "ArtifactStore", lambda _root: object())
    monkeypatch.setattr(cli, "BenchmarkRunner", FakeRunner)
    monkeypatch.setattr(
        cli,
        "OpenRouterRouteMetadata",
        lambda: pytest.fail("official startup must use real echo calls"),
    )

    result = CliRunner().invoke(
        benchmark_app,
        [
            command,
            "B-0001",
            "--run-id",
            f"BX-{command}-no-canary-001",
            "--model",
            "M-0004",
            "--benchmark-mode",
            "official",
            "--no-canary",
        ],
    )

    assert result.exit_code == 0


@pytest.mark.parametrize("command", ("run", "repair"))
def test_official_execution_runs_paid_startup_canaries_by_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    command: str,
) -> None:
    selected_model = object()
    selected_benchmark = object()
    canary_inputs: tuple[object, object, str] | None = None

    class FakeModels:
        def model(self, _model_id: object) -> object:
            return selected_model

    class FakeBenchmarks:
        def entry(self, _benchmark_id: object) -> object:
            return selected_benchmark

    class FakeRunner:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def run(self, _request: object, **_kwargs: object) -> object:
            return SimpleNamespace(
                outcome=SimpleNamespace(has_infrastructure_failures=False)
            )

    def fake_canaries(
        model: object,
        benchmark: object,
        *,
        api_key: str,
    ) -> object:
        nonlocal canary_inputs
        canary_inputs = (model, benchmark, api_key)
        return SimpleNamespace(valid=True, roles=())

    monkeypatch.setattr(cli, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(cli, "load_model_catalog", lambda _path: FakeModels())
    monkeypatch.setattr(
        cli,
        "load_benchmark_catalog",
        lambda _path: FakeBenchmarks(),
    )
    monkeypatch.setattr(cli, "load_subject_catalog", lambda _path: object())
    monkeypatch.setattr(cli, "load_openrouter_api_key", lambda _root: "unused")
    monkeypatch.setattr(cli, "ArtifactStore", lambda _root: object())
    monkeypatch.setattr(cli, "BenchmarkRunner", FakeRunner)
    monkeypatch.setattr(cli, "run_startup_canaries", fake_canaries)

    result = CliRunner().invoke(
        benchmark_app,
        [
            command,
            "B-0001",
            "--run-id",
            f"BX-{command}-startup-canary-001",
            "--model",
            "M-0004",
            "--benchmark-mode",
            "official",
        ],
    )

    assert result.exit_code == 0
    assert canary_inputs == (selected_model, selected_benchmark, "unused")


def test_repair_exits_nonzero_when_infrastructure_failures_remain(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class FakeRunner:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def run(self, _request: object, **_kwargs: object) -> object:
            return SimpleNamespace(
                outcome=SimpleNamespace(has_infrastructure_failures=True),
                summary=SimpleNamespace(
                    counts=SimpleNamespace(infrastructure_failed=2)
                ),
            )

    monkeypatch.setattr(cli, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(cli, "load_model_catalog", lambda _path: object())
    monkeypatch.setattr(cli, "load_benchmark_catalog", lambda _path: object())
    monkeypatch.setattr(cli, "load_subject_catalog", lambda _path: object())
    monkeypatch.setattr(cli, "load_openrouter_api_key", lambda _root: "unused")
    monkeypatch.setattr(cli, "ArtifactStore", lambda _root: object())
    monkeypatch.setattr(cli, "BenchmarkRunner", FakeRunner)
    monkeypatch.setattr(cli, "prevent_idle_system_sleep", nullcontext)

    result = CliRunner().invoke(
        benchmark_app,
        [
            "repair",
            "B-0001",
            "--run-id",
            "BX-repair-failures-remain-001",
            "--model",
            "M-0001",
            "--benchmark-mode",
            "experimental",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["error"]["code"] == "benchmark_infrastructure_failures_remain"
    assert (
        "contains 2 infrastructure-failed terminal trial(s)"
        in payload["error"]["message"]
    )


def test_failed_startup_canary_prevents_benchmark_artifacts_and_execution(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class FakeModels:
        def model(self, _model_id: object) -> object:
            return object()

    class FakeBenchmarks:
        def entry(self, _benchmark_id: object) -> object:
            return object()

    def forbidden(*_args: object, **_kwargs: object) -> object:
        pytest.fail("failed startup canary must stop before benchmark construction")

    failed = StartupCanaryResult(
        valid=False,
        roles=(
            LlmCanaryResult(
                role=BenchmarkLlmRole.JUDGE,
                model="anthropic/test",
                provider="anthropic",
                valid=False,
                error_code="provider_unavailable",
            ),
        ),
    )
    monkeypatch.setattr(cli, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(cli, "load_model_catalog", lambda _path: FakeModels())
    monkeypatch.setattr(
        cli,
        "load_benchmark_catalog",
        lambda _path: FakeBenchmarks(),
    )
    monkeypatch.setattr(cli, "load_subject_catalog", forbidden)
    monkeypatch.setattr(cli, "load_openrouter_api_key", lambda _root: "unused")
    monkeypatch.setattr(cli, "ArtifactStore", forbidden)
    monkeypatch.setattr(cli, "BenchmarkRunner", forbidden)
    monkeypatch.setattr(
        cli,
        "run_startup_canaries",
        lambda *_args, **_kwargs: failed,
    )

    result = CliRunner().invoke(
        benchmark_app,
        [
            "run",
            "B-0001",
            "--run-id",
            "BX-startup-canary-failed-001",
            "--model",
            "M-0004",
            "--benchmark-mode",
            "official",
        ],
    )

    assert result.exit_code == 1
    assert "LLM startup canary failed: judge: provider_unavailable" in result.output
