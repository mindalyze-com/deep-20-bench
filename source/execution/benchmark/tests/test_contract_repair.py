from pathlib import Path

import pytest
from deep20_benchmark.history_cache import LazyOracleHistoryCache
from deep20_benchmark.models import (
    BenchmarkExecutionId,
    BenchmarkId,
    BenchmarkModelId,
    BenchmarkRequest,
    ExecutionResumedEvent,
    TrialRepairPolicy,
)
from deep20_game.config import BenchmarkMode
from deep20_oracle import cache_contract
from test_history_cache import seed
from test_runner import FakeExecutor, _runner


@pytest.mark.parametrize("cached", (False, True))
def test_contract_repair_preserves_success_and_records_revision(tmp_path: Path, monkeypatch, cached):
    old_version = cache_contract.ORACLE_FACTUAL_CONTRACT_VERSION
    if cached:
        seed(tmp_path)
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"), execution_id=BenchmarkExecutionId("BX-contract-repair"),
        model_id=BenchmarkModelId("M-0001"), benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        iterations_override=1,
    )
    runner, store = _runner(tmp_path, FakeExecutor(fail_first=True))
    if cached:
        runner.oracle_cache = LazyOracleHistoryCache(tmp_path)
    first = runner.run(request)
    root = store.run_root(request.model_id, request.execution_id)
    manifest_before = (root / "manifest.json").read_bytes()
    success_path = root / "subjects/T-0002/trials/trial-001/result.yml"
    success_before = success_path.read_bytes()
    events_before = (root / "benchmark-events.jsonl").read_bytes()
    if cached:
        assert first.run.oracle_cache.sources
    monkeypatch.setattr(cache_contract, "ORACLE_FACTUAL_CONTRACT_VERSION", "test-revised-contract")
    denied_executor = FakeExecutor()
    denied, _ = _runner(tmp_path, denied_executor)
    if cached:
        denied.oracle_cache = LazyOracleHistoryCache(tmp_path)
    with pytest.raises(ValueError, match="Oracle contract changed"):
        denied.run(request, repair=TrialRepairPolicy())
    assert not denied_executor.calls
    assert (root / "benchmark-events.jsonl").read_bytes() == events_before
    repair_executor = FakeExecutor(fail_first=True)
    repair, _ = _runner(tmp_path, repair_executor)
    if cached:
        repair.oracle_cache = LazyOracleHistoryCache(tmp_path)
    second = repair.run(request, repair=TrialRepairPolicy(allow_oracle_contract_change=True))
    assert len(repair_executor.calls) == 1
    assert len(second.run.oracle_contract_revisions) == 1
    revision = second.run.oracle_contract_revisions[0]
    assert revision.previous_hash != revision.current_hash
    if cached:
        assert not revision.oracle_cache.sources
        assert revision.oracle_cache.cutoff == first.run.oracle_cache.cutoff
        assert revision.oracle_cache.context_hash != first.run.oracle_cache.context_hash
    assert (root / "manifest.json").read_bytes() == manifest_before
    assert success_path.read_bytes() == success_before
    # A further repair uses the recorded active contract without another revision flag.
    final_executor = FakeExecutor()
    final, _ = _runner(tmp_path, final_executor)
    if cached:
        final.oracle_cache = LazyOracleHistoryCache(tmp_path)
    result = final.run(request, repair=TrialRepairPolicy())
    assert len(final_executor.calls) == 1
    assert not result.outcome.has_infrastructure_failures
    assert not result.outcome.publication_eligible
    assert result.run.oracle_contract_revisions == (revision,)
    assert len(result.subjects[0].trials[0].superseded_attempts) == 2
    assert success_path.read_bytes() == success_before
    assert (root / "manifest.json").read_bytes() == manifest_before
    assert store.load_benchmark_result(request.model_id, request.execution_id) == result
    events = store.load_events(request.model_id, request.execution_id)
    assert sum(isinstance(e, ExecutionResumedEvent) and e.oracle_contract_revision is not None
               for e in events) == 1
    for context in final_executor.calls:
        assert "oracle_contract_revision" not in context.model_dump_json()
    # A mixed-contract execution cannot seed even a future old-contract inventory.
    monkeypatch.setattr(cache_contract, "ORACLE_FACTUAL_CONTRACT_VERSION", old_version)
    history = LazyOracleHistoryCache(tmp_path)
    inventory = history.prepare(first.run.definition, execution_id="BX-future")
    assert all("BX-contract-repair" not in item.manifest.relative_path for item in inventory.sources)


def test_official_repair_cannot_change_oracle_contract(tmp_path: Path, monkeypatch):
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"), execution_id=BenchmarkExecutionId("BX-official-repair"),
        model_id=BenchmarkModelId("M-0001"), benchmark_mode=BenchmarkMode.OFFICIAL,
        iterations_override=1,
    )
    runner, _ = _runner(tmp_path, FakeExecutor(fail_first=True))
    runner.run(request)
    monkeypatch.setattr(cache_contract, "ORACLE_FACTUAL_CONTRACT_VERSION", "test-revised-contract")
    retry, _ = _runner(tmp_path, FakeExecutor())
    with pytest.raises(ValueError, match="Oracle contract changed"):
        retry.run(request, repair=TrialRepairPolicy(allow_oracle_contract_change=True))
