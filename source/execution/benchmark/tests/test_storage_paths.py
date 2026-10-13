from pathlib import Path

import pytest
from deep20_benchmark.artifact_paths import repository_relative_path
from deep20_benchmark.history_cache import LazyOracleHistoryCache
from deep20_benchmark.models import (
    BenchmarkExecutionId,
    BenchmarkId,
    BenchmarkModelId,
    BenchmarkRequest,
)
from deep20_game.config import BenchmarkMode
from deep20_oracle.models import OracleRequest
from test_history_cache import seed
from test_runner import FakeExecutor, _runner, assert_markdown_links_resolve


def linked_run(root: Path, storage: Path, execution: str) -> Path:
    destination = storage / execution
    destination.mkdir(parents=True)
    link = root / "runs/M-0001" / execution
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(destination, target_is_directory=True)
    return destination


def test_benchmark_persists_and_resumes_through_external_storage_link(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    destination = linked_run(root, tmp_path / "storage", "BX-external")
    executor = FakeExecutor()
    runner, store = _runner(root, executor)
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-external"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        iterations_override=1,
    )
    result = runner.run(request)
    assert (destination / "result.yml").is_file()
    assert result.artifacts.result.relative_path == "runs/M-0001/BX-external/result.yml"
    assert store.load_benchmark_result(request.model_id, request.execution_id) == result
    assert_markdown_links_resolve(destination / "summary.md")
    calls = len(executor.calls)
    assert runner.run(request) == result
    assert len(executor.calls) == calls


def test_same_execution_answers_keep_integrity_checks_through_storage_link(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    destination = linked_run(root, tmp_path / "storage", "BX-source")
    store, definition, subjects = seed(root)
    cache = LazyOracleHistoryCache(root)
    cache.prepare(definition, execution_id="BX-source")
    result = store.load_benchmark_result("M-0001", "BX-source")
    assert result is not None
    trial = result.subjects[0].trials[0]
    path = root / "runs/M-0001/BX-source/subjects/T-0001/trials/trial-001/result.yml"
    cache.remember_completed_trial(trial.identity, path)
    answer = cache.lookup(OracleRequest(
        run_id="reader", subject=subjects.subject("T-0001"),
        question="Was this person born before 1900?",
    ))
    assert answer is not None
    assert answer.source.policy == "same_execution_ask_v1"
    fingerprint = cache._file(path)
    (destination / "subjects/T-0001/trials/trial-001/result.yml").write_text("tampered")
    with pytest.raises(ValueError, match="history source changed"):
        cache._read(fingerprint)


def test_artifact_references_reject_paths_outside_repository(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    for path in (tmp_path / "storage/result.yml", root / "../storage/result.yml"):
        with pytest.raises(ValueError):
            repository_relative_path(root, path)
