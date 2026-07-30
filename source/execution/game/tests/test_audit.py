from __future__ import annotations

import json

import pytest
from deep20_game.errors import GameAuditError
from deep20_oracle.artifacts import RunArtifactPolicy
from deep20_oracle.audit import RunAuditWriter


def test_game_manifest_precedes_calls_and_is_oracle_compatible(
    audit_writer,
    oracle_config,
) -> None:
    audit_writer.prepare_run("game-run")
    manifest_path = audit_writer.runs_root / "game-run" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())

    assert manifest["schema_version"] == 2
    assert manifest["run_kind"] == "game"
    assert manifest["game_context"]["history_contract"].startswith("full_visible")
    for filename in (
        "oracle-calls.jsonl",
        "guesser-calls.jsonl",
        "guess-validator-calls.jsonl",
        "episode-events.jsonl",
    ):
        assert (audit_writer.runs_root / "game-run" / filename).is_file()

    oracle_writer = RunAuditWriter(
        audit_writer.runs_root,
        config=oracle_config,
        subject_catalog_hash="a" * 64,
        repository=audit_writer.repository,
        artifact_policy=RunArtifactPolicy(verbose=True),
    )
    oracle_writer.prepare_run("game-run")


def test_legacy_oracle_manifest_requires_new_game_run_id(
    tmp_path,
    audit_writer,
    oracle_config,
    monkeypatch,
) -> None:
    oracle_writer = RunAuditWriter(
        tmp_path / "runs",
        config=oracle_config,
        subject_catalog_hash="a" * 64,
        repository=tmp_path,
        artifact_policy=RunArtifactPolicy(verbose=True),
    )
    monkeypatch.setattr(
        oracle_writer,
        "_git",
        lambda arguments: "abc123" if arguments == ["rev-parse", "HEAD"] else "",
    )
    oracle_writer.prepare_run("legacy")

    with pytest.raises(GameAuditError) as failure:
        audit_writer.prepare_run("legacy")

    assert failure.value.code == "legacy_run_manifest"


def test_tampered_game_log_is_rejected(audit_writer) -> None:
    audit_writer.prepare_run("tampered")
    audit_writer.append_episode_event(
        "tampered",
        {
            "schema_version": 1,
            "event_id": "EV-" + "0" * 32,
            "episode_id": "EP-" + "0" * 32,
            "event_type": "episode_started",
            "payload": {},
            "recorded_at": "now",
        },
    )
    path = audit_writer.runs_root / "tampered" / "episode-events.jsonl"
    record = json.loads(path.read_text())
    record["event_type"] = "changed"
    path.write_text(json.dumps(record) + "\n")

    with pytest.raises(GameAuditError, match="integrity hash mismatch"):
        audit_writer.prepare_run("tampered")


def test_started_episode_without_terminal_event_is_interrupted(audit_writer) -> None:
    audit_writer.prepare_run("interrupted")
    episode_id = "EP-" + "3" * 32
    audit_writer.append_episode_event(
        "interrupted",
        {
            "schema_version": 1,
            "event_id": "EV-" + "3" * 32,
            "episode_id": episode_id,
            "event_type": "episode_started",
            "payload": {},
            "recorded_at": "now",
        },
    )

    assert audit_writer.interrupted_episode_ids("interrupted") == (episode_id,)
