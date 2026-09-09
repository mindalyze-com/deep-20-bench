from __future__ import annotations

import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCRIPT = PROJECT_ROOT / "scripts/run-all-models.sh"
NOW = datetime(2026, 9, 7, 10, tzinfo=UTC)


@pytest.fixture
def launcher() -> ModuleType:
    spec = importlib.util.spec_from_file_location("batch_launcher", SCRIPT.with_suffix(".py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    config = tmp_path / "config"
    config.mkdir()
    for filename in ("models.yaml", "benchmarks.yaml"):
        shutil.copyfile(PROJECT_ROOT / "config" / filename, config / filename)
    monkeypatch.setenv("RUN_DATE", "20260907")
    return tmp_path


def test_wrapper_requires_explicit_benchmark_and_mode() -> None:
    syntax = subprocess.run(["bash", "-n", str(SCRIPT)], check=False, capture_output=True, text=True)
    assert syntax.returncode == 0, syntax.stderr
    for arguments in ([], ["experimental"], ["official", "002", "3"]):
        result = subprocess.run([str(SCRIPT), *arguments], cwd=PROJECT_ROOT,
                                check=False, capture_output=True, text=True)
        assert result.returncode == 2
        assert "<official|experimental>" in result.stderr


@pytest.mark.parametrize("cutoff", [None, "2026-09-01T00:00:00+00:00"])
def test_real_wrapper_dry_run_defaults_to_refresh_and_accepts_explicit_cutoff(cutoff) -> None:
    result = subprocess.run(
        [str(SCRIPT), "B-0003", "experimental", "999", "--model", "M-0001",
         "--model", "M-0006", "--dry-run",
         *(["--oracle-history-before", cutoff] if cutoff else [])], cwd=PROJECT_ROOT,
        env={**os.environ, "RUN_DATE": "19990101"}, check=False, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    commands = [shlex.split(line) for line in result.stdout.splitlines()]
    assert len(commands) == 2
    for command, model in zip(commands, ("M-0001", "M-0006"), strict=True):
        assert command[:6] == ["uv", "run", "deep20", "benchmark", "run", "B-0003"]
        assert command[command.index("--model") + 1] == model
        assert command[command.index("--iterations") + 1] == "3"
        assert command[command.index("--seed") + 1] == "0"
        assert "--canary" in command
        assert "--targets" not in command
        assert "--no-oracle-cache" not in command
        if cutoff is None:
            assert "--oracle-cache" in command and "--oracle-history-before" not in command
        else:
            assert command[command.index("--oracle-history-before") + 1] == cutoff
    assert not (PROJECT_ROOT / "benchmark-logs/BX-19990101-B-0003-experimental-ALL-999").exists()


@pytest.mark.parametrize("arguments", [
    ["B-0003", "official"], ["B-9999", "experimental"],
    ["B-0003", "experimental", "--model", "M-9999"],
    ["B-0003", "experimental", "--exclude-model", "M-9999"],
    ["B-0003", "experimental", "--model", "M-0001", "--model", "M-0001"],
    ["B-0003", "experimental", "--model", "M-0001", "--exclude-model", "M-0001"],
    ["B-0003", "experimental", "--oracle-history-before", "2099-01-01T00:00:00Z"],
])
def test_invalid_batch_is_rejected_before_launch(launcher, repository, arguments) -> None:
    with pytest.raises(ValueError):
        launcher.prepare_plan(launcher.parse_options(arguments), repository, now=NOW)
    assert not (repository / "benchmark-logs").exists()


@pytest.mark.parametrize("arguments", [
    ["B-0003", "experimental", "../escape"],
    ["B-0003", "experimental", "001", "0"],
    ["B-0003", "experimental", "--oracle-history-before", "2026-09-01T00:00:00"],
    ["B-0003", "experimental", "--no-oracle-cache",
     "--oracle-history-before", "2026-09-01T00:00:00Z"],
])
def test_invalid_options_stop_at_parsing(launcher, arguments) -> None:
    with pytest.raises(SystemExit) as error:
        launcher.parse_options(arguments)
    assert error.value.code == 2


def test_selection_exclusions_and_catalog_iterations(launcher, repository) -> None:
    plan = launcher.prepare_plan(launcher.parse_options([
        "B-0003", "experimental", "--exclude-model", "M-0013", "--exclude-model", "M-0017",
    ]), repository, now=NOW)
    registered = {
        model.root
        for model in launcher.load_model_catalog(repository / "config/models.yaml").registered_model_ids()
    }
    selected = {model.root for model in plan.model_ids}
    assert selected == registered - {"M-0013", "M-0017"}
    assert len(plan.model_ids) == len(selected)
    assert plan.iterations == 3
    concise = launcher.prepare_plan(launcher.parse_options([
        "B-0002", "experimental",
    ]), repository, now=NOW)
    assert concise.iterations == 5
    standard = launcher.prepare_plan(launcher.parse_options([
        "B-0001", "official", "001", "4", "--model", "M-0001", "--no-oracle-cache",
    ]), repository, now=NOW)
    assert standard.iterations == 4
    assert "--no-oracle-cache" in standard.command(standard.model_ids[0])
    assert "--oracle-history-before" not in standard.command(standard.model_ids[0])
    assert plan.execution_id(plan.model_ids[0]) != concise.execution_id(concise.model_ids[0])


def test_saved_plan_reuses_cutoff_and_rejects_changes(launcher, repository) -> None:
    arguments = ["B-0003", "experimental", "--model", "M-0001"]
    options = launcher.parse_options(arguments)
    plan = launcher.prepare_plan(launcher.parse_options(
        arguments + ["--oracle-history-before", NOW.isoformat()],
    ), repository, now=NOW)
    path = repository / "benchmark-logs" / plan.batch_id / "batch.json"
    path.parent.mkdir(parents=True)
    path.write_text(plan.model_dump_json())
    assert "refresh_oracle_history" not in json.loads(path.read_text())
    assert launcher.prepare_plan(options, repository, now=NOW + timedelta(hours=1)) == plan
    for extra in (["--no-oracle-cache"], ["--model", "M-0006"], ["--refresh-oracle-history"],
                  ["--oracle-history-before", "2026-09-06T00:00:00Z"]):
        with pytest.raises(ValueError, match="saved plan"):
            launcher.prepare_plan(launcher.parse_options(arguments + extra), repository, now=NOW)


def test_refresh_batch_uses_per_subject_history_and_preserves_mode(launcher, repository) -> None:
    arguments = ["B-0003", "experimental", "--model", "M-0001", "--refresh-oracle-history"]
    options = launcher.parse_options(arguments)
    plan = launcher.prepare_plan(options, repository, now=NOW)
    command = plan.command(plan.model_ids[0])
    assert "--oracle-cache" in command
    assert "--oracle-history-before" not in command and "--no-oracle-cache" not in command
    assert plan.refresh_oracle_history and plan.oracle_history_before is None
    path = repository / "benchmark-logs" / plan.batch_id / "batch.json"
    path.parent.mkdir(parents=True)
    path.write_text(plan.model_dump_json())
    assert launcher.prepare_plan(options, repository, now=NOW + timedelta(hours=1)) == plan
    assert launcher.prepare_plan(launcher.parse_options(arguments[:-1]), repository, now=NOW) == plan
    for conflicting in (["--no-oracle-cache"],
                        ["--oracle-history-before", "2026-09-01T00:00:00Z"]):
        with pytest.raises(SystemExit):
            launcher.parse_options(arguments + conflicting)


def test_launch_runs_children_concurrently_and_retains_logs(launcher, repository, monkeypatch) -> None:
    bin_dir = repository / "bin"
    bin_dir.mkdir()
    calls = repository / "calls"
    calls.mkdir()
    fake_uv = bin_dir / "uv"
    fake_uv.write_text(f'''#!{sys.executable}
import json
import pathlib
import sys
import time
arguments = sys.argv[1:]
model = arguments[arguments.index("--model") + 1]
calls = pathlib.Path({str(calls)!r})
(calls / (model + ".json")).write_text(json.dumps(arguments))
deadline = time.monotonic() + 3
while len(list(calls.glob("*.json"))) < 2:
    if time.monotonic() > deadline:
        sys.exit(99)
    time.sleep(0.01)
print("stdout " + model)
print("stderr " + model, file=sys.stderr)
sys.exit(7 if model == "M-0006" else 0)
''')
    fake_uv.chmod(0o700)
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ["PATH"])
    plan = launcher.prepare_plan(launcher.parse_options([
        "B-0003", "experimental", "--model", "M-0001", "--model", "M-0006",
    ]), repository, now=NOW)
    assert launcher.launch(plan, repository, stagger_seconds=0) == 1
    paths = sorted(calls.glob("*.json"))
    assert len(paths) == 2
    log_dir = repository / "benchmark-logs" / plan.batch_id
    assert launcher.BatchPlan.model_validate_json((log_dir / "batch.json").read_text()) == plan
    for model in plan.model_ids:
        args = json.loads((calls / f"{model}.json").read_text())
        assert args == plan.command(model)[1:]
        output = (log_dir / f"{model}.log").read_text()
        assert f"stdout {model}" in output and f"stderr {model}" in output
