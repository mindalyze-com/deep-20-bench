from __future__ import annotations

import fcntl
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .artifacts import RunArtifactPolicy
from .config import OracleConfig
from .diagnostics import diagnose_exception
from .errors import AuditWriteError
from .models import (
    OracleAdjudication,
    OracleAuditTrace,
    OracleCall,
    OracleMetrics,
    OracleRequest,
    OracleResult,
    OracleRole,
    PersistedRecord,
)
from .sinks import OracleFailureRecord, OracleSuccessRecord
from .util import canonical_json, sha256_text, timestamp


class RunAuditWriter:
    """Build signed Oracle records and optionally persist verbose run artifacts."""

    MANIFEST_SCHEMA_VERSION = 1
    RECORD_SCHEMA_VERSION = 5

    def __init__(
        self,
        runs_root: Path,
        *,
        config: OracleConfig,
        subject_catalog_hash: str,
        repository: Path,
        artifact_policy: RunArtifactPolicy | None = None,
    ):
        if re.fullmatch(r"[0-9a-f]{64}", subject_catalog_hash) is None:
            raise ValueError("subject_catalog_hash must be a SHA-256 hex digest")
        self.runs_root = runs_root
        self.config = config
        self.subject_catalog_hash = subject_catalog_hash
        self.repository = repository.resolve()
        self.artifact_policy = artifact_policy or RunArtifactPolicy()

    def prepare_run(self, run_id: str) -> None:
        """Validate existing context and create it only for verbose artifacts."""
        try:
            run_root = self.runs_root / run_id
            if self.artifact_policy.verbose:
                run_root.mkdir(parents=True, exist_ok=True)
            elif not run_root.exists():
                return
            lock_path = Path(tempfile.gettempdir()) / (
                f"deep20bench-{sha256_text(str(run_root.resolve()))}.lock"
            )
            with lock_path.open("a", encoding="utf-8") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                self._ensure_manifest(run_root, run_id)
                log_path = run_root / "oracle-calls.jsonl"
                existing = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
                self._validate_existing_log(existing)
        except AuditWriteError:
            raise
        except Exception as error:
            raise AuditWriteError(
                f"could not prepare Oracle audit context for run {run_id!r}",
                code="audit_write_failed",
                details={"exception_type": type(error).__name__},
            ) from error

    def write_success(
        self,
        *,
        call_id: str,
        request: OracleRequest,
        result: OracleResult,
        adjudication: OracleAdjudication,
        metrics: OracleMetrics,
        audit: OracleAuditTrace,
        recorded_at: str,
    ) -> OracleCall:
        return self.persist_oracle_success(
            OracleSuccessRecord(
                call_id=call_id,
                request=request,
                result=result,
                adjudication=adjudication,
                metrics=metrics,
                audit=audit,
                recorded_at=recorded_at,
            )
        )

    def persist_oracle_success(self, source: OracleSuccessRecord) -> OracleCall:
        base = {
            "schema_version": self.RECORD_SCHEMA_VERSION,
            "status": "success",
            "call_id": source.call_id,
            "request": source.request.model_dump(mode="json"),
            "result": source.result.model_dump(mode="json"),
            "adjudication": source.adjudication.model_dump(mode="json"),
            "metrics": source.metrics.model_dump(mode="json"),
            "audit": source.audit.model_dump(mode="json"),
            "recorded_at": source.recorded_at,
        }
        integrity_hash = sha256_text(canonical_json(base))
        record = {**base, "integrity_hash": integrity_hash}
        self._write_record(source.request.run_id, record)
        return OracleCall.model_validate({key: value for key, value in record.items() if key != "status"})

    def write_failure(
        self,
        *,
        call_id: str,
        request: OracleRequest,
        prompt_version: str,
        prompt_hash: str,
        messages: tuple[dict[str, str], ...],
        component: OracleRole,
        error: Exception,
        provider_trace: dict[str, Any] | None,
    ) -> str:
        from .sinks import AuditFailure

        trace = None
        if provider_trace is not None:
            from .models import ProviderTrace

            trace = ProviderTrace.model_validate(provider_trace)
        diagnostics = diagnose_exception(error)
        persisted = self.persist_oracle_failure(
            OracleFailureRecord(
                call_id=call_id,
                request=request,
                component=component,
                prompt_version=prompt_version,
                prompt_hash=prompt_hash,
                messages=messages,
                failure=AuditFailure(
                    code=getattr(error, "code", "unexpected_error"),
                    type=type(error).__name__,
                    message=diagnostics.causes[0].message,
                    details=self._safe_details(getattr(error, "details", {})),
                    diagnostics=diagnostics,
                ),
                provider_trace=trace,
                recorded_at=timestamp(),
            )
        )
        return persisted.integrity_hash

    def persist_oracle_failure(self, source: OracleFailureRecord) -> PersistedRecord:
        base = {
            "schema_version": self.RECORD_SCHEMA_VERSION,
            "status": "failure",
            "call_id": source.call_id,
            "request": source.request.model_dump(mode="json"),
            "result": None,
            "adjudication": None,
            "audit": {
                "component": source.component,
                "prompt_version": source.prompt_version,
                "prompt_hash": source.prompt_hash,
                "messages": source.messages,
                "evidence_validation": "model_reported",
                "provider": (
                    source.provider_trace.model_dump(mode="json")
                    if source.provider_trace is not None
                    else None
                ),
                "role_traces": tuple(
                    trace.model_dump(mode="json") for trace in source.role_traces
                ),
            },
            "error": source.failure.model_dump(mode="json"),
            "recorded_at": source.recorded_at,
        }
        integrity_hash = sha256_text(canonical_json(base))
        self._write_record(source.request.run_id, {**base, "integrity_hash": integrity_hash})
        return PersistedRecord(
            record_id=source.call_id,
            relative_path="oracle-calls.jsonl",
            integrity_hash=integrity_hash,
        )

    def _write_record(self, run_id: str, record: dict[str, Any]) -> None:
        if not self.artifact_policy.permits("oracle-calls.jsonl"):
            return
        try:
            run_root = self.runs_root / run_id
            run_root.mkdir(parents=True, exist_ok=True)
            lock_path = Path(tempfile.gettempdir()) / (
                f"deep20bench-{sha256_text(str(run_root.resolve()))}.lock"
            )
            with lock_path.open("a", encoding="utf-8") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                self._ensure_manifest(run_root, run_id)
                log_path = run_root / "oracle-calls.jsonl"
                existing = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
                self._validate_existing_log(existing)
                self._atomic_write(log_path, existing + canonical_json(record) + "\n")
        except AuditWriteError:
            raise
        except Exception as error:
            raise AuditWriteError(
                f"could not persist Oracle audit record for run {run_id!r}",
                code="audit_write_failed",
                details={"exception_type": type(error).__name__},
            ) from error

    def _ensure_manifest(self, run_root: Path, run_id: str) -> None:
        path = run_root / "manifest.json"
        config_snapshot = self.config.model_dump(mode="json")
        config_hash = sha256_text(canonical_json(config_snapshot))
        if path.exists():
            manifest = json.loads(path.read_text(encoding="utf-8"))
            self._validate_integrity_hash(manifest, "run manifest")
            if manifest.get("run_id") != run_id:
                raise AuditWriteError(
                    "run manifest ID does not match its directory",
                    code="audit_manifest_mismatch",
                )
            if manifest.get("oracle_config_hash") != config_hash:
                raise AuditWriteError(
                    "run already uses a different Oracle configuration",
                    code="audit_configuration_mismatch",
                )
            if manifest.get("subject_catalog_hash") != self.subject_catalog_hash:
                raise AuditWriteError(
                    "run already uses a different subject catalog",
                    code="audit_catalog_mismatch",
                )
            return
        if not self.artifact_policy.permits(path.name):
            return
        manifest = {
            "schema_version": self.MANIFEST_SCHEMA_VERSION,
            "run_id": run_id,
            "created_at": timestamp(),
            "git_commit": self._git(["rev-parse", "HEAD"]),
            "working_tree_dirty_before_run": bool(
                self._git(["status", "--porcelain", "--untracked-files=normal"])
            ),
            "oracle_config": config_snapshot,
            "oracle_config_hash": config_hash,
            "subject_catalog_hash": self.subject_catalog_hash,
            "reproducibility": "artifact_replay_only_live_web_reruns_may_differ",
            "evidence_validation": "model_reported",
        }
        manifest["integrity_hash"] = sha256_text(canonical_json(manifest))
        self._atomic_write(path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    @classmethod
    def _validate_existing_log(cls, content: str) -> None:
        seen: set[str] = set()
        for line_number, line in enumerate(content.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise AuditWriteError(
                    f"existing Oracle audit line {line_number} is not valid JSON",
                    code="audit_log_corrupt",
                ) from error
            if not isinstance(record, dict):
                raise AuditWriteError(
                    f"existing Oracle audit line {line_number} is not an object",
                    code="audit_log_corrupt",
                )
            cls._validate_integrity_hash(record, f"Oracle audit line {line_number}")
            call_id = record.get("call_id")
            if not isinstance(call_id, str) or call_id in seen:
                raise AuditWriteError(
                    f"existing Oracle audit line {line_number} has an invalid or duplicate call ID",
                    code="audit_log_corrupt",
                )
            seen.add(call_id)

    @staticmethod
    def _validate_integrity_hash(value: dict[str, Any], label: str) -> None:
        unsigned = dict(value)
        stored = unsigned.pop("integrity_hash", None)
        if stored != sha256_text(canonical_json(unsigned)):
            raise AuditWriteError(
                f"{label} integrity hash mismatch",
                code="audit_integrity_mismatch",
            )

    def _git(self, arguments: list[str]) -> str:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=self.repository,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()

    @staticmethod
    def _safe_details(value: Any) -> Any:
        """Retain controlled diagnostics without serializing provider/client objects."""
        if value is None or isinstance(value, str | int | float | bool):
            return value
        if isinstance(value, dict):
            return {str(key): RunAuditWriter._safe_details(item) for key, item in value.items()}
        if isinstance(value, list | tuple):
            return [RunAuditWriter._safe_details(item) for item in value]
        if isinstance(value, BaseException):
            return {"type": type(value).__name__, "message": str(value)[:500]}
        return {"unserializable_type": type(value).__name__}

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, 0o644)
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
