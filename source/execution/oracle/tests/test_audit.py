from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from deep20_oracle.audit import RunAuditWriter
from deep20_oracle.errors import OracleProtocolError
from deep20_oracle.models import OracleRequest, OracleRole
from deep20_oracle.prompt import PROMPT_VERSION, prompt_hash, render_messages
from deep20_oracle.util import canonical_json, sha256_text


def test_concurrent_records_are_complete_and_integrity_hashed(
    oracle_request: OracleRequest, audit_writer: RunAuditWriter
) -> None:
    messages = render_messages(oracle_request)

    def write(index: int) -> None:
        error = OracleProtocolError(f"failure {index}", code="test_failure")
        audit_writer.write_failure(
            call_id=f"OC-{index:032x}",
            request=oracle_request,
            prompt_version=PROMPT_VERSION,
            prompt_hash=prompt_hash(messages),
            messages=messages,
            component=OracleRole.ORACLE,
            error=error,
            provider_trace=None,
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(write, range(12)))

    path = audit_writer.runs_root / "test-run" / "oracle-calls.jsonl"
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 12
    assert len({record["call_id"] for record in records}) == 12
    for record in records:
        stored_hash = record.pop("integrity_hash")
        assert stored_hash == sha256_text(canonical_json(record))


def test_run_rejects_configuration_or_catalog_changes(
    oracle_request: OracleRequest, audit_writer: RunAuditWriter
) -> None:
    messages = render_messages(oracle_request)
    error = OracleProtocolError("failure", code="test_failure")
    arguments = {
        "call_id": "OC-" + "0" * 32,
        "request": oracle_request,
        "prompt_version": PROMPT_VERSION,
        "prompt_hash": prompt_hash(messages),
        "messages": messages,
        "component": OracleRole.ORACLE,
        "error": error,
        "provider_trace": None,
    }
    audit_writer.write_failure(**arguments)
    manifest_path = audit_writer.runs_root / "test-run" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["subject_catalog_hash"] = "b" * 64
    unsigned = {key: value for key, value in manifest.items() if key != "integrity_hash"}
    manifest["integrity_hash"] = sha256_text(canonical_json(unsigned))
    manifest_path.write_text(json.dumps(manifest))

    with pytest.raises(Exception, match="different subject catalog"):
        audit_writer.write_failure(**{**arguments, "call_id": "OC-" + "1" * 32})


def test_tampered_log_is_rejected(
    oracle_request: OracleRequest, audit_writer: RunAuditWriter
) -> None:
    messages = render_messages(oracle_request)
    arguments = {
        "request": oracle_request,
        "prompt_version": PROMPT_VERSION,
        "prompt_hash": prompt_hash(messages),
        "messages": messages,
        "component": OracleRole.ORACLE,
        "error": OracleProtocolError("failure", code="test_failure"),
        "provider_trace": None,
    }
    audit_writer.write_failure(call_id="OC-" + "0" * 32, **arguments)
    path = audit_writer.runs_root / "test-run" / "oracle-calls.jsonl"
    record = json.loads(path.read_text())
    record["error"]["message"] = "tampered"
    path.write_text(json.dumps(record) + "\n")

    with pytest.raises(Exception, match="integrity hash mismatch"):
        audit_writer.write_failure(call_id="OC-" + "1" * 32, **arguments)
