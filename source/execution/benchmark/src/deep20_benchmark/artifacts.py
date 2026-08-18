from __future__ import annotations

import copy
import fcntl
import json
import os
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeVar

import yaml
from deep20_game.config import GamePolicy, ModelConfig
from deep20_game.models import (
    EpisodeEvent,
    EpisodeFinishedEvent,
    EpisodeResult,
    EpisodeTerminalFailure,
    GuesserCall,
    GuesserFailureRecord,
    GuesserSuccessRecord,
    GuessValidatorCall,
    ValidatorFailureRecord,
    ValidatorSuccessRecord,
)
from deep20_oracle.config import OracleConfig
from deep20_oracle.models import (
    OracleCall,
    PersistedRecord,
    ProviderTrace,
    StrictModel,
    Subject,
)
from deep20_oracle.provider_output import error_outputs_from_trace
from deep20_oracle.sinks import OracleFailureRecord, OracleSuccessRecord
from deep20_oracle.util import canonical_json, sha256_text, timestamp
from pydantic import TypeAdapter

from .aggregation import SUMMARY_USD_QUANTUM, round_summary_value
from .models import (
    ERROR_OUTPUT_PREVIEW_MAX_CHARACTERS,
    ArtifactFileReference,
    BenchmarkDefinitionSnapshot,
    BenchmarkManifest,
    BenchmarkModelSnapshot,
    BenchmarkProgressEvent,
    BenchmarkRequest,
    BenchmarkResult,
    BenchmarkRunArtifactReferences,
    BenchmarkState,
    BenchmarkSummaryArtifact,
    CompletedTrialResult,
    CompletedTrialSummaryEntry,
    ComponentCallId,
    ErrorOutputPreview,
    ErrorOutputRecord,
    ExecutionResumedEvent,
    InfrastructureFailedTrialSummaryEntry,
    SubjectBenchmarkResult,
    SubjectId,
    SubjectSummaryEntry,
    TrialArtifactReferences,
    TrialAuditManifest,
    TrialBenchmarkResult,
    TrialIdentity,
    TrialSummaryEntry,
)

_ModelT = TypeVar("_ModelT", bound=StrictModel)
_TRIAL_ADAPTER: TypeAdapter[TrialBenchmarkResult] = TypeAdapter(TrialBenchmarkResult)
_EVENT_ADAPTER: TypeAdapter[BenchmarkProgressEvent] = TypeAdapter(BenchmarkProgressEvent)


@dataclass(frozen=True)
class _FileFingerprint:
    inode: int
    size: int
    modified_ns: int
    changed_ns: int


@dataclass(frozen=True)
class _EventLogCache:
    fingerprint: _FileFingerprint | None
    events: tuple[BenchmarkProgressEvent, ...]
    event_ids: frozenset[str]


class ArtifactIntegrityError(RuntimeError):
    pass


class BenchmarkExecutionLocked(RuntimeError):
    """Raised when another process already owns one benchmark execution."""

    code = "benchmark_execution_locked"


def _signed_payload(payload: dict[str, object]) -> dict[str, object]:
    unsigned = dict(payload)
    unsigned.pop("integrity_hash", None)
    return {
        **unsigned,
        "integrity_hash": sha256_text(canonical_json(unsigned)),
    }


def _verify_signed(payload: dict[str, object], label: str) -> None:
    unsigned = dict(payload)
    stored = unsigned.pop("integrity_hash", None)
    if stored != sha256_text(canonical_json(unsigned)):
        raise ArtifactIntegrityError(f"{label} integrity hash mismatch")


class ArtifactStore:
    """Own the complete artifact hierarchy for each single-model benchmark run."""

    def __init__(self, repository: Path):
        self.repository = repository.resolve()
        self.runs_root = self.repository / "runs"
        self._event_logs: dict[Path, _EventLogCache] = {}

    def run_root(self, model_id: object, execution_id: object) -> Path:
        return self.runs_root / str(model_id) / str(execution_id)

    def subject_root(self, model_id: object, execution_id: object, target_id: object) -> Path:
        return self.run_root(model_id, execution_id) / "subjects" / str(target_id)

    def trial_root(self, identity: TrialIdentity) -> Path:
        return (
            self.subject_root(identity.model_id, identity.execution_id, identity.target_id)
            / "trials"
            / str(identity.trial_id)
        )

    def prepare_execution(self, manifest: BenchmarkManifest, state: BenchmarkState) -> None:
        run_root = self.run_root(manifest.model.model_id, manifest.request.execution_id)
        run_root.mkdir(parents=True, exist_ok=True)
        manifest_path = run_root / "manifest.json"
        if manifest_path.exists():
            existing = BenchmarkManifest.model_validate_json(
                manifest_path.read_text(encoding="utf-8")
            )
            if existing != manifest:
                comparable_existing = existing.model_copy(
                    update={
                        "integrity_hash": manifest.integrity_hash,
                    }
                )
                if comparable_existing != manifest:
                    raise ArtifactIntegrityError(
                        "execution ID already has a different immutable benchmark context"
                    )
        else:
            self._atomic_write(manifest_path, manifest.model_dump_json(indent=2) + "\n")
        events_path = run_root / "benchmark-events.jsonl"
        if not events_path.exists():
            self._atomic_write(events_path, "")
        if not (run_root / "state.yml").exists():
            self.write_state(state)

    def load_manifest(
        self,
        model_id: object,
        execution_id: object,
    ) -> BenchmarkManifest | None:
        path = self.run_root(model_id, execution_id) / "manifest.json"
        if not path.exists():
            return None
        return BenchmarkManifest.model_validate_json(path.read_text(encoding="utf-8"))

    def load_state(
        self,
        model_id: object,
        execution_id: object,
    ) -> BenchmarkState | None:
        path = self.run_root(model_id, execution_id) / "state.yml"
        if not path.exists():
            return None
        return BenchmarkState.model_validate(self._read_envelope(path))

    def write_state(self, state: BenchmarkState) -> ArtifactFileReference:
        return self._write_envelope(
            self.run_root(state.model_id, state.execution_id) / "state.yml",
            state,
        )

    def append_event(
        self,
        model_id: object,
        execution_id: object,
        event: BenchmarkProgressEvent,
    ) -> PersistedRecord:
        payload = _signed_payload(_EVENT_ADAPTER.dump_python(event, mode="json"))
        path = self.run_root(model_id, execution_id) / "benchmark-events.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self._jsonl_lock_path(path)
        with lock_path.open("a", encoding="utf-8") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            cached = self._load_events_locked(path)
            event_id = str(event.event_id)
            if event_id in cached.event_ids:
                raise ArtifactIntegrityError(f"duplicate durable record {event_id}")
            with path.open("a", encoding="utf-8") as handle:
                os.chmod(path, 0o644)
                handle.write(canonical_json(payload) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            self._event_logs[path] = _EventLogCache(
                fingerprint=self._file_fingerprint(path),
                events=(*cached.events, event),
                event_ids=frozenset((*cached.event_ids, event_id)),
            )
        return PersistedRecord(
            record_id=str(event.event_id),
            relative_path=self._relative(path),
            integrity_hash=str(payload["integrity_hash"]),
        )

    def load_events(
        self,
        model_id: object,
        execution_id: object,
    ) -> tuple[BenchmarkProgressEvent, ...]:
        path = self.run_root(model_id, execution_id) / "benchmark-events.jsonl"
        lock_path = self._jsonl_lock_path(path)
        with lock_path.open("a", encoding="utf-8") as lock:
            fcntl.flock(lock, fcntl.LOCK_SH)
            return self._load_events_locked(path).events

    def _load_events_locked(self, path: Path) -> _EventLogCache:
        fingerprint = self._file_fingerprint(path)
        cached = self._event_logs.get(path)
        if cached is not None and cached.fingerprint == fingerprint:
            return cached
        if fingerprint is None:
            empty = _EventLogCache(
                fingerprint=None,
                events=(),
                event_ids=frozenset(),
            )
            self._event_logs[path] = empty
            return empty

        events: list[BenchmarkProgressEvent] = []
        event_ids: set[str] = set()
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            payload = json.loads(line)
            _verify_signed(payload, str(path))
            payload.pop("integrity_hash", None)
            event = _EVENT_ADAPTER.validate_python(payload)
            event_id = str(event.event_id)
            if event_id in event_ids:
                raise ArtifactIntegrityError(f"duplicate durable record {event_id}")
            event_ids.add(event_id)
            events.append(event)
        verified_fingerprint = self._file_fingerprint(path)
        if verified_fingerprint != fingerprint:
            raise ArtifactIntegrityError("event log changed while it was being verified")
        loaded = _EventLogCache(
            fingerprint=verified_fingerprint,
            events=tuple(events),
            event_ids=frozenset(event_ids),
        )
        self._event_logs[path] = loaded
        return loaded

    def write_trial_result(self, trial: TrialBenchmarkResult) -> ArtifactFileReference:
        path = self.trial_root(trial.identity) / "result.yml"
        return self._write_union_envelope(path, _TRIAL_ADAPTER, trial)

    def append_error_output(
        self,
        identity: TrialIdentity,
        record: ErrorOutputRecord,
    ) -> PersistedRecord:
        payload = _signed_payload(record.model_dump(mode="json"))
        path = self.trial_root(identity) / "error-outputs.jsonl"
        self._append_jsonl(
            path,
            payload,
            identity=str(record.call_id),
            file_mode=0o600,
        )
        return PersistedRecord(
            record_id=str(record.call_id),
            relative_path=self._relative(path),
            integrity_hash=str(payload["integrity_hash"]),
        )

    def load_trial_result(self, identity: TrialIdentity) -> TrialBenchmarkResult | None:
        path = self.trial_root(identity) / "result.yml"
        if not path.exists():
            return None
        payload = self._read_envelope(path)
        return _TRIAL_ADAPTER.validate_python(payload)

    def trial_started_without_result(self, identity: TrialIdentity) -> bool:
        trial_root = self.trial_root(identity)
        return (trial_root / "result.yml").exists() is False and (
            trial_root.exists() or self.trial_event_recorded(identity, "trial_started")
        )

    def trial_event_recorded(self, identity: TrialIdentity, event_type: str) -> bool:
        return self.trial_event_count(identity, event_type) > 0

    def trial_attempt_event_recorded(
        self,
        identity: TrialIdentity,
        event_type: str,
        attempt_number: int,
    ) -> bool:
        return any(
            getattr(event, "event_type", None) == event_type
            and getattr(event, "identity", None) == identity
            and getattr(event, "attempt_number", None) == attempt_number
            for event in self.load_events(identity.model_id, identity.execution_id)
        )

    def trial_event_count(self, identity: TrialIdentity, event_type: str) -> int:
        return sum(
            getattr(event, "event_type", None) == event_type
            and getattr(event, "identity", None) == identity
            for event in self.load_events(identity.model_id, identity.execution_id)
        )

    @contextmanager
    def execution_lock(
        self,
        model_id: object,
        execution_id: object,
    ) -> Iterator[None]:
        """Hold a non-blocking single-writer lock for one complete execution."""

        material = f"{self.repository}:{model_id}:{execution_id}"
        lock_path = Path(tempfile.gettempdir()) / (
            f"deep20-benchmark-execution-{sha256_text(material)}.lock"
        )
        with lock_path.open("a", encoding="utf-8") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise BenchmarkExecutionLocked(
                    f"benchmark execution {execution_id} is already active"
                ) from error
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def execution_git_commits(
        self,
        model_id: object,
        execution_id: object,
    ) -> tuple[str, ...]:
        manifest = self.load_manifest(model_id, execution_id)
        commits: list[str] = [manifest.git_commit] if manifest is not None else []
        for event in self.load_events(model_id, execution_id):
            if isinstance(event, ExecutionResumedEvent) and event.git_commit not in commits:
                commits.append(event.git_commit)
        return tuple(commits)

    def write_subject_result(
        self,
        model_id: object,
        execution_id: object,
        result: SubjectBenchmarkResult,
    ) -> ArtifactFileReference:
        return self._write_envelope(
            self.subject_root(model_id, execution_id, result.subject.target_id) / "result.yml",
            result,
        )

    def _subject_summary_entries(
        self,
        result: BenchmarkResult,
    ) -> tuple[SubjectSummaryEntry, ...]:
        subject_entries: list[SubjectSummaryEntry] = []
        for subject in result.subjects:
            trial_entries: list[TrialSummaryEntry] = []
            for trial in subject.trials:
                artifacts = TrialArtifactReferences(
                    trial_result=self._file_reference(
                        self.trial_root(trial.identity) / "result.yml"
                    ),
                    error_outputs=trial.artifacts.error_outputs,
                )
                if isinstance(trial, CompletedTrialResult):
                    trial_entries.append(
                        CompletedTrialSummaryEntry(
                            identity=trial.identity,
                            success=trial.result.success,
                            scoring_eligible=trial.result.scoring_eligible,
                            publication_eligible=trial.result.publication_eligible,
                            failure=trial.failure,
                            counted_questions=trial.result.counted_questions,
                            contract=trial.result.summary.contract,
                            cost_usd=round_summary_value(
                                trial.result.costs_usd.total,
                                SUMMARY_USD_QUANTUM,
                            ),
                            duration_ms=trial.result.duration_ms,
                            superseded_attempt_count=len(trial.superseded_attempts),
                            artifacts=artifacts,
                        )
                    )
                else:
                    trial_entries.append(
                        InfrastructureFailedTrialSummaryEntry(
                            identity=trial.identity,
                            failure=trial.failure,
                            partial_metrics=trial.partial_metrics.model_copy(
                                update={
                                    "guesser_cost_usd": round_summary_value(
                                        trial.partial_metrics.guesser_cost_usd,
                                        SUMMARY_USD_QUANTUM,
                                    ),
                                    "oracle_cost_usd": round_summary_value(
                                        trial.partial_metrics.oracle_cost_usd,
                                        SUMMARY_USD_QUANTUM,
                                    ),
                                    "validator_cost_usd": round_summary_value(
                                        trial.partial_metrics.validator_cost_usd,
                                        SUMMARY_USD_QUANTUM,
                                    ),
                                    "cost_usd": round_summary_value(
                                        trial.partial_metrics.cost_usd,
                                        SUMMARY_USD_QUANTUM,
                                    ),
                                    "estimated_cache_savings_usd": round_summary_value(
                                        trial.partial_metrics.estimated_cache_savings_usd,
                                        SUMMARY_USD_QUANTUM,
                                    ),
                                }
                            ),
                            superseded_attempt_count=len(trial.superseded_attempts),
                            artifacts=artifacts,
                        )
                    )
            subject_root = self.subject_root(
                result.run.model.model_id,
                result.run.execution_id,
                subject.subject.target_id,
            )
            subject_entries.append(
                SubjectSummaryEntry(
                    target_id=SubjectId(subject.subject.target_id),
                    display_name=subject.subject.canonical_name,
                    entity_type=subject.subject.entity_type,
                    outcome=subject.outcome,
                    summary=subject.summary,
                    trials=tuple(trial_entries),
                    result=self._file_reference(subject_root / "result.yml"),
                    summary_markdown=self._file_reference(subject_root / "summary.md"),
                )
            )
        return tuple(subject_entries)

    def write_benchmark_result(self, result: BenchmarkResult) -> ArtifactFileReference:
        path = self.run_root(result.run.model.model_id, result.run.execution_id) / "result.yml"
        self._atomic_write(
            path,
            yaml.safe_dump(
                result.model_dump(mode="json"),
                allow_unicode=True,
                sort_keys=False,
            ),
        )
        return ArtifactFileReference(
            relative_path=self._relative(path),
            record_count=1,
            integrity_hash=result.integrity_hash,
        )

    def load_benchmark_result(
        self,
        model_id: object,
        execution_id: object,
    ) -> BenchmarkResult | None:
        path = self.run_root(model_id, execution_id) / "result.yml"
        if not path.exists():
            return None
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        result = BenchmarkResult.model_validate(value)
        unsigned = copy.deepcopy(value)
        unsigned.pop("integrity_hash", None)
        unsigned["artifacts"]["result"]["integrity_hash"] = None
        if result.integrity_hash != sha256_text(canonical_json(unsigned)):
            raise ArtifactIntegrityError("benchmark result integrity hash mismatch")
        return result

    def build_benchmark_summary(self, result: BenchmarkResult) -> BenchmarkSummaryArtifact:
        run_root = self.run_root(result.run.model.model_id, result.run.execution_id)
        return BenchmarkSummaryArtifact(
            execution_id=result.run.execution_id,
            benchmark_id=result.run.definition.benchmark_id,
            display_name=result.run.definition.display_name,
            model=result.run.model,
            outcome=result.outcome,
            summary=result.summary,
            subjects=self._subject_summary_entries(result),
            result=self._file_reference(run_root / "result.yml"),
            summary_markdown=self._file_reference(run_root / "summary.md"),
        )

    def write_benchmark_summary(
        self,
        summary: BenchmarkSummaryArtifact,
    ) -> ArtifactFileReference:
        return self._write_envelope(
            self.run_root(summary.model.model_id, summary.execution_id) / "summary.yml",
            summary,
        )

    def load_benchmark_summary(
        self,
        model_id: object,
        execution_id: object,
    ) -> BenchmarkSummaryArtifact | None:
        path = self.run_root(model_id, execution_id) / "summary.yml"
        if not path.exists():
            return None
        return BenchmarkSummaryArtifact.model_validate(self._read_envelope(path))

    def write_markdown(self, path: Path, content: str) -> ArtifactFileReference:
        self._atomic_write(path, content.rstrip() + "\n")
        return ArtifactFileReference(
            relative_path=self._relative(path),
            record_count=1,
            integrity_hash=sha256_text(content.rstrip() + "\n"),
        )

    def benchmark_artifact_references(
        self,
        model_id: object,
        execution_id: object,
    ) -> BenchmarkRunArtifactReferences:
        root = self.run_root(model_id, execution_id)
        manifest_payload = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        return BenchmarkRunArtifactReferences(
            manifest=ArtifactFileReference(
                relative_path=self._relative(root / "manifest.json"),
                integrity_hash=manifest_payload["integrity_hash"],
            ),
            state=self._file_reference(root / "state.yml"),
            events=self._file_reference(
                root / "benchmark-events.jsonl",
                record_count=self._line_count(root / "benchmark-events.jsonl"),
            ),
            result=ArtifactFileReference(
                relative_path=self._relative(root / "result.yml"),
                integrity_hash=None,
            ),
            summary_yaml=ArtifactFileReference(
                relative_path=self._relative(root / "summary.yml"),
                integrity_hash=None,
            ),
            summary_markdown=ArtifactFileReference(
                relative_path=self._relative(root / "summary.md"),
                integrity_hash=None,
            ),
        )

    def execution_manifest(
        self,
        *,
        request: BenchmarkRequest,
        definition: BenchmarkDefinitionSnapshot,
        model: BenchmarkModelSnapshot,
        subject_catalog_hash: str,
    ) -> BenchmarkManifest:
        unsigned = {
            "schema_version": 3,
            "request": request.model_dump(mode="json"),
            "definition": definition.model_dump(mode="json"),
            "model": model.model_dump(mode="json"),
            "subject_catalog_hash": subject_catalog_hash,
            "git_commit": self._git(["rev-parse", "HEAD"]),
            "created_at": timestamp(),
        }
        return BenchmarkManifest.model_validate(_signed_payload(unsigned))

    def _write_envelope(self, path: Path, model: _ModelT) -> ArtifactFileReference:
        payload = model.model_dump(mode="json")
        signed = _signed_payload({"payload": payload})
        self._atomic_write(
            path,
            yaml.safe_dump(signed, allow_unicode=True, sort_keys=False),
        )
        return ArtifactFileReference(
            relative_path=self._relative(path),
            record_count=1,
            integrity_hash=str(signed["integrity_hash"]),
        )

    def _write_union_envelope(
        self,
        path: Path,
        adapter: TypeAdapter[TrialBenchmarkResult],
        model: TrialBenchmarkResult,
    ) -> ArtifactFileReference:
        signed = _signed_payload({"payload": adapter.dump_python(model, mode="json")})
        self._atomic_write(
            path,
            yaml.safe_dump(signed, allow_unicode=True, sort_keys=False),
        )
        return ArtifactFileReference(
            relative_path=self._relative(path),
            record_count=1,
            integrity_hash=str(signed["integrity_hash"]),
        )

    @staticmethod
    def _read_envelope(path: Path) -> object:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ArtifactIntegrityError(f"{path} is not an artifact envelope")
        _verify_signed(value, str(path))
        return value.get("payload")

    def _file_reference(
        self,
        path: Path,
        *,
        record_count: int = 1,
    ) -> ArtifactFileReference:
        return ArtifactFileReference(
            relative_path=self._relative(path),
            record_count=record_count,
            integrity_hash=(
                sha256_text(path.read_text(encoding="utf-8")) if path.exists() else None
            ),
        )

    def _relative(self, path: Path) -> str:
        return path.resolve().relative_to(self.repository).as_posix()

    @staticmethod
    def _line_count(path: Path) -> int:
        if not path.exists():
            return 0
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line)

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
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

    @staticmethod
    def _file_fingerprint(path: Path) -> _FileFingerprint | None:
        try:
            status = path.stat()
        except FileNotFoundError:
            return None
        return _FileFingerprint(
            inode=status.st_ino,
            size=status.st_size,
            modified_ns=status.st_mtime_ns,
            changed_ns=status.st_ctime_ns,
        )

    @staticmethod
    def _jsonl_lock_path(path: Path) -> Path:
        return Path(tempfile.gettempdir()) / (
            f"deep20-benchmark-{sha256_text(str(path.resolve()))}.lock"
        )

    @staticmethod
    def _append_jsonl(
        path: Path,
        payload: dict[str, object],
        *,
        identity: str,
        file_mode: int = 0o644,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = ArtifactStore._jsonl_lock_path(path)
        with lock_path.open("a", encoding="utf-8") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if path.exists():
                for line in path.read_text(encoding="utf-8").splitlines():
                    if not line:
                        continue
                    existing = json.loads(line)
                    _verify_signed(existing, str(path))
                    if existing.get("event_id") == identity or existing.get("call_id") == identity:
                        raise ArtifactIntegrityError(f"duplicate durable record {identity}")
            with path.open("a", encoding="utf-8") as handle:
                os.chmod(path, file_mode)
                handle.write(canonical_json(payload) + "\n")
                handle.flush()
                os.fsync(handle.fileno())

    def _git(self, arguments: list[str]) -> str:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=self.repository,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()


class BenchmarkTrialSink:
    """Typed benchmark sink that persists only error-output diagnostics."""

    def __init__(self, store: ArtifactStore, manifest: TrialAuditManifest):
        self.store = store
        self.manifest = manifest
        self.identity = manifest.identity
        self.trial_root = store.trial_root(manifest.identity)
        self._prepared = False
        self._seen: set[str] = set()
        self._latest_error_output_preview: ErrorOutputPreview | None = None
        self.terminal_failure: EpisodeTerminalFailure | None = None

    def prepare_run(self, run_id: str) -> None:
        if run_id != str(self.identity.episode_run_id):
            raise ArtifactIntegrityError("episode run ID differs from the scheduled trial")
        self._prepared = True

    def persist_guesser_success(self, source: GuesserSuccessRecord) -> GuesserCall:
        payload = _signed_payload(source.model_dump(mode="json"))
        self._claim(source.call_id)
        self._persist_error_outputs(
            component="guesser",
            call_id=source.call_id,
            failure_code=None,
            recovered=True,
            trace=source.audit.provider,
            recorded_at=source.recorded_at,
        )
        return GuesserCall.model_validate(
            {key: value for key, value in payload.items() if key != "status"}
        )

    def persist_guesser_failure(self, source: GuesserFailureRecord) -> PersistedRecord:
        base = source.model_dump(mode="json", exclude={"failure"})
        base.update(
            {
                "action": None,
                "error": source.failure.model_dump(mode="json"),
            }
        )
        persisted = self._ack(
            source.call_id,
            "guesser-calls",
            _signed_payload(base),
        )
        self._persist_error_outputs(
            component="guesser",
            call_id=source.call_id,
            failure_code=source.failure.code,
            recovered=False,
            trace=source.audit.provider,
            recorded_at=source.recorded_at,
        )
        return persisted

    def persist_validator_success(self, source: ValidatorSuccessRecord) -> GuessValidatorCall:
        payload = _signed_payload(source.model_dump(mode="json"))
        self._claim(source.call_id)
        self._persist_error_outputs(
            component="guess_validator",
            call_id=source.call_id,
            failure_code=None,
            recovered=True,
            trace=source.audit.provider,
            recorded_at=source.recorded_at,
        )
        return GuessValidatorCall.model_validate(
            {key: value for key, value in payload.items() if key != "status"}
        )

    def persist_validator_failure(self, source: ValidatorFailureRecord) -> PersistedRecord:
        base = source.model_dump(mode="json", exclude={"failure"})
        base.update(
            {
                "result": None,
                "error": source.failure.model_dump(mode="json"),
            }
        )
        persisted = self._ack(
            source.call_id,
            "guess-validator-calls",
            _signed_payload(base),
        )
        self._persist_error_outputs(
            component="guess_validator",
            call_id=source.call_id,
            failure_code=source.failure.code,
            recovered=False,
            trace=source.audit.provider,
            recorded_at=source.recorded_at,
        )
        return persisted

    def persist_oracle_success(self, source: OracleSuccessRecord) -> OracleCall:
        payload = _signed_payload(source.model_dump(mode="json"))
        self._claim(source.call_id)
        self._persist_error_outputs(
            component="oracle",
            call_id=source.call_id,
            failure_code=None,
            recovered=True,
            trace=source.audit.provider,
            recorded_at=source.recorded_at,
        )
        if source.audit.research is not None:
            for attempt in source.audit.research.attempts[1:]:
                self._persist_error_outputs(
                    component="oracle",
                    call_id=source.call_id,
                    failure_code=None,
                    recovered=True,
                    trace=attempt.provider,
                    recorded_at=source.recorded_at,
                )
        if source.audit.reviewer is not None:
            self._persist_error_outputs(
                component="reviewer",
                call_id=source.call_id,
                failure_code=None,
                recovered=True,
                trace=source.audit.reviewer.provider,
                recorded_at=source.recorded_at,
            )
        if source.audit.judge is not None:
            self._persist_error_outputs(
                component="judge",
                call_id=source.call_id,
                failure_code=None,
                recovered=True,
                trace=source.audit.judge.provider,
                recorded_at=source.recorded_at,
            )
        return OracleCall.model_validate(
            {key: value for key, value in payload.items() if key != "status"}
        )

    def persist_oracle_failure(self, source: OracleFailureRecord) -> PersistedRecord:
        base: dict[str, object] = {
            "schema_version": source.schema_version,
            "status": source.status,
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
                "role_traces": tuple(trace.model_dump(mode="json") for trace in source.role_traces),
            },
            "error": source.failure.model_dump(mode="json"),
            "recorded_at": source.recorded_at,
        }
        persisted = self._ack(
            source.call_id,
            "oracle-calls",
            _signed_payload(base),
        )
        for role_trace in source.role_traces:
            if role_trace.role is source.component and role_trace.provider == source.provider_trace:
                continue
            self._persist_error_outputs(
                component=role_trace.role.value,
                call_id=source.call_id,
                failure_code=None,
                recovered=True,
                trace=role_trace.provider,
                recorded_at=source.recorded_at,
            )
        self._persist_error_outputs(
            component=source.component.value,
            call_id=source.call_id,
            failure_code=source.failure.code,
            recovered=False,
            trace=source.provider_trace,
            recorded_at=source.recorded_at,
        )
        return persisted

    def persist_episode_event(self, event: EpisodeEvent) -> PersistedRecord:
        if isinstance(event, EpisodeFinishedEvent):
            self.terminal_failure = event.payload.failure
        return self._ack(
            event.event_id,
            "episode-events",
            _signed_payload(event.model_dump(mode="json")),
        )

    def persist_episode_result(self, result: EpisodeResult) -> PersistedRecord:
        return self._ack(
            result.episode_id,
            "episode-result",
            _signed_payload(result.model_dump(mode="json")),
        )

    def references(self) -> TrialArtifactReferences:
        error_outputs_path = self.trial_root / "error-outputs.jsonl"
        return TrialArtifactReferences(
            trial_result=ArtifactFileReference(
                relative_path=self.store._relative(self.trial_root / "result.yml"),
                integrity_hash=None,
            ),
            error_outputs=(
                self.store._file_reference(
                    error_outputs_path,
                    record_count=self.store._line_count(error_outputs_path),
                )
                if error_outputs_path.exists()
                else None
            ),
        )

    @property
    def latest_error_output_preview(self) -> ErrorOutputPreview | None:
        """Return the in-memory preview without reading the private artifact back."""

        return self._latest_error_output_preview

    def _persist_error_outputs(
        self,
        *,
        component: Literal[
            "guesser",
            "oracle",
            "reviewer",
            "judge",
            "guess_validator",
        ],
        call_id: str,
        failure_code: str | None,
        recovered: bool,
        trace: ProviderTrace | None,
        recorded_at: str,
    ) -> None:
        if trace is None:
            return
        outputs = error_outputs_from_trace(
            trace,
            include_current=not recovered,
        )
        if not outputs:
            return
        latest = outputs[-1]
        preview_text = latest.output[:ERROR_OUTPUT_PREVIEW_MAX_CHARACTERS]
        self._latest_error_output_preview = ErrorOutputPreview(
            component=component,
            attempt_number=latest.attempt_number,
            finish_reason=latest.finish_reason,
            text=preview_text,
            original_characters=len(latest.output),
            trailing_whitespace_characters=(len(latest.output) - len(latest.output.rstrip())),
            truncated=len(latest.output) > len(preview_text),
        )
        self.store.append_error_output(
            self.identity,
            ErrorOutputRecord(
                component=component,
                call_id=ComponentCallId(call_id),
                failure_code=failure_code,
                recovered=recovered,
                recovery=trace.recovery,
                outputs=outputs,
                recorded_at=recorded_at,
            ),
        )

    def _ack(
        self,
        record_id: str,
        record_type: str,
        payload: dict[str, object],
    ) -> PersistedRecord:
        self._claim(record_id)
        return PersistedRecord(
            record_id=record_id,
            relative_path=f"benchmark-memory/{self.identity.episode_run_id}/{record_type}",
            integrity_hash=str(payload["integrity_hash"]),
        )

    def _claim(self, record_id: str) -> None:
        if not self._prepared:
            raise ArtifactIntegrityError("benchmark trial sink was not prepared")
        if record_id in self._seen:
            raise ArtifactIntegrityError(f"duplicate in-memory record {record_id}")
        self._seen.add(record_id)


def signed_trial_manifest(
    *,
    identity: TrialIdentity,
    subject_catalog_hash: str,
    subject: Subject,
    model: BenchmarkModelSnapshot,
    game_policy: GamePolicy,
    oracle_configuration: OracleConfig,
    validator_configuration: ModelConfig,
) -> TrialAuditManifest:
    unsigned = {
        "schema_version": 3,
        "identity": identity.model_dump(mode="json"),
        "subject_catalog_hash": subject_catalog_hash,
        "subject": subject.model_dump(mode="json"),
        "model": model.model_dump(mode="json"),
        "game_policy": game_policy.model_dump(mode="json"),
        "oracle_configuration": oracle_configuration.model_dump(mode="json"),
        "validator_configuration": validator_configuration.model_dump(mode="json"),
        "created_at": timestamp(),
    }
    return TrialAuditManifest.model_validate(_signed_payload(unsigned))
