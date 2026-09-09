from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from deep20_benchmark.artifacts import ArtifactIntegrityError, ArtifactSubjectHistoryStore
from deep20_benchmark.history_cache import LazyOracleHistoryCache
from deep20_benchmark.history_models import OracleHistorySnapshot
from deep20_oracle.models import OracleRequest
from deep20_oracle.util import canonical_json, sha256_text, timestamp
from test_history_cache import seed


def question(subjects, target="T-0001"):
    return OracleRequest(run_id="reader", subject=subjects.subject(target),
                         question="Was this person born before 1900?")


def test_new_external_games_are_discovered_only_for_unloaded_subjects(tmp_path):
    _, definition, subjects = seed(tmp_path)
    cache = LazyOracleHistoryCache(tmp_path)
    parent = cache.prepare(definition, execution_id="BX-reader")
    first = cache.lookup(question(subjects))
    seed(tmp_path, execution="BX-later")
    assert cache.lookup(question(subjects)) == first
    second = cache.lookup(question(subjects, "T-0002"))
    assert second is not None and second.source.execution_id == "BX-later"
    assert parent == cache.snapshot
    assert parent.discovery_policy == "per_subject_history_v1"
    inventory = cache.loads[1].snapshot
    assert inventory is not None and second.source.snapshot_hash == inventory.snapshot_hash
    assert inventory.cutoff > parent.cutoff
    assert all("/T-0002/" in f.relative_path for s in inventory.sources for f in s.trials)


def test_reader_sees_atomic_trial_written_later_by_another_process(tmp_path):
    _, definition, subjects = seed(tmp_path, execution="BX-reader")
    cache = LazyOracleHistoryCache(tmp_path)
    parent = cache.prepare(definition, execution_id="BX-reader")
    frozen = LazyOracleHistoryCache(tmp_path, before=timestamp())
    frozen.prepare(definition, execution_id="BX-reader")
    assert not parent.sources
    # The other process writes complete games after both readers have started.
    script = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[2])
from test_history_cache import seed
root = Path(sys.argv[1])
store, _, _ = seed(root, execution="BX-writer")
# A running benchmark need not have its aggregate run/subject results yet.
run = store.run_root("M-0001", "BX-writer")
(run / "result.yml").unlink()
for path in run.glob("subjects/*/result.yml"):
    path.unlink()
"""
    child = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path), str(Path(__file__).parent)],
        capture_output=True, text=True, timeout=30, check=False,
    )
    assert child.returncode == 0, child.stderr
    hit = cache.lookup(question(subjects))
    assert hit is not None and hit.source.execution_id == "BX-writer"
    assert frozen.lookup(question(subjects)) is None


@pytest.mark.parametrize("damage", ["truncated", "duplicate", "integrity", "changed_after_scan"])
def test_new_external_files_still_require_complete_immutable_results(tmp_path, monkeypatch, damage):
    store, definition, subjects = seed(tmp_path, execution="BX-reader")
    cache = LazyOracleHistoryCache(tmp_path)
    cache.prepare(definition, execution_id="BX-reader")
    seed(tmp_path, execution="BX-writer")
    path = store.run_root("M-0001", "BX-writer") / "subjects/T-0001/trials/trial-001/result.yml"
    original = path.read_text()
    if damage == "changed_after_scan":
        discover = cache._discover

        def change(**kwargs):
            snapshot = discover(**kwargs)
            path.write_text(original + "\n")
            return snapshot

        monkeypatch.setattr(cache, "_discover", change)
    else:
        path.write_text(original[:100] if damage == "truncated" else
                        original + "\nintegrity_hash: duplicate\n" if damage == "duplicate" else
                        original.replace("Original evidence.", "Tampered evidence."))
    assert cache.lookup(question(subjects)) is None
    assert cache.loads[0].skipped_files == 1


@pytest.mark.parametrize("empty", [False, True])
def test_subject_inventory_is_persisted_before_reuse_and_restored_on_resume(tmp_path, empty):
    store, definition, subjects = seed(tmp_path, execution="BX-reader")
    manifest = store.load_manifest("M-0001", "BX-reader")
    history_store = ArtifactSubjectHistoryStore(store, manifest.request)
    cache = LazyOracleHistoryCache(tmp_path)
    parent = cache.prepare(definition, execution_id="BX-reader", subject_history=history_store)
    if not empty:
        seed(tmp_path, execution="BX-writer")
    before = cache.lookup(question(subjects))
    assert (before is None) == empty
    saved = history_store.load(question(subjects).subject, parent)
    assert saved == cache.loads[0].snapshot
    seed(tmp_path, execution="BX-later")
    resumed = LazyOracleHistoryCache(tmp_path)
    resumed.prepare(definition, execution_id="BX-reader", subject_history=history_store,
                    existing=manifest.model_copy(update={"oracle_cache": parent}))
    assert resumed.lookup(question(subjects)) == before
    assert resumed.loads[0].snapshot == saved
    assert resumed.lookup(question(subjects, "T-0002")).source.execution_id == "BX-later"


def test_failed_checkpoint_write_cannot_supply_a_cached_answer(tmp_path, monkeypatch):
    store, definition, subjects = seed(tmp_path, execution="BX-reader")
    manifest = store.load_manifest("M-0001", "BX-reader")
    history_store = ArtifactSubjectHistoryStore(store, manifest.request)
    cache = LazyOracleHistoryCache(tmp_path)
    cache.prepare(definition, execution_id="BX-reader", subject_history=history_store)
    seed(tmp_path, execution="BX-writer")

    def fail(*args):
        raise OSError("checkpoint write failed")

    monkeypatch.setattr(history_store, "save", fail)
    with pytest.raises(OSError, match="checkpoint write failed"):
        cache.lookup(question(subjects))
    assert not cache.loads and not cache._loaded


@pytest.mark.parametrize("damage", ["missing", "corrupt"])
def test_resume_rejects_lost_checkpoint_for_started_subject(tmp_path, damage):
    store, definition, subjects = seed(tmp_path, execution="BX-reader")
    manifest = store.load_manifest("M-0001", "BX-reader")
    history_store = ArtifactSubjectHistoryStore(store, manifest.request)
    cache = LazyOracleHistoryCache(tmp_path)
    parent = cache.prepare(definition, execution_id="BX-reader", subject_history=history_store)
    assert cache.lookup(question(subjects)) is None
    path = next(store.run_root("M-0001", "BX-reader").glob("subjects/T-0001/oracle-history-*.json"))
    if damage == "missing":
        path.unlink()
    else:
        path.write_text(path.read_text().replace(parent.snapshot_hash, "f" * 64))
    seed(tmp_path, execution="BX-later")
    resumed = LazyOracleHistoryCache(tmp_path)
    resumed.prepare(
        definition, execution_id="BX-reader",
        existing=manifest.model_copy(update={"oracle_cache": parent}),
        subject_history=ArtifactSubjectHistoryStore(store, manifest.request, resumed=True),
    )
    with pytest.raises(ArtifactIntegrityError):
        resumed.lookup(question(subjects))
    assert not resumed.loads and not resumed._loaded


def test_old_policy_remains_frozen_and_cannot_be_changed_on_resume(tmp_path):
    store, definition, subjects = seed(tmp_path, execution="BX-reader")
    manifest = store.load_manifest("M-0001", "BX-reader")
    parent = LazyOracleHistoryCache(tmp_path).prepare(definition, execution_id="BX-reader")
    unsigned = parent.model_dump(mode="json", exclude={"snapshot_hash", "discovery_policy"})
    old = OracleHistorySnapshot.model_validate_json(canonical_json({
        **unsigned, "snapshot_hash": sha256_text(canonical_json(unsigned)),
    }))
    cache = LazyOracleHistoryCache(tmp_path)
    cache.prepare(definition, execution_id="BX-reader",
                  existing=manifest.model_copy(update={"oracle_cache": old}))
    seed(tmp_path, execution="BX-writer")
    assert cache.lookup(question(subjects)) is None
    with pytest.raises(ValueError, match="cannot freeze"):
        LazyOracleHistoryCache(tmp_path, before=parent.cutoff).prepare(
            definition, execution_id="BX-reader",
            existing=manifest.model_copy(update={"oracle_cache": parent}),
        )
