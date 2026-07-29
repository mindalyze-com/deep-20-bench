from __future__ import annotations

import fcntl
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, TextIO

import yaml
from deep20_oracle.artifacts import RESULT_ARTIFACT, RunArtifactPolicy
from deep20_oracle.config import OracleConfig
from deep20_oracle.models import PersistedRecord
from deep20_oracle.prompt import (
    JUDGE_PROMPT_VERSION,
    REVIEWER_PROMPT_VERSION,
)
from deep20_oracle.prompt import (
    PROMPT_VERSION as ORACLE_PROMPT_VERSION,
)
from deep20_oracle.util import canonical_json, sha256_text, timestamp

from .config import BenchmarkMode, CachePolicy, GamePolicy, ModelConfig
from .errors import GameAuditError
from .models import (
    EpisodeEvent,
    EpisodeResult,
    GuesserCall,
    GuesserFailureRecord,
    GuesserSuccessRecord,
    GuessValidatorCall,
    ValidatorFailureRecord,
    ValidatorSuccessRecord,
)
from .prompt import GUESSER_PROMPT_VERSION, VALIDATOR_PROMPT_VERSION

GAME_ARTIFACTS = (
    "oracle-calls.jsonl",
    "guesser-calls.jsonl",
    "guess-validator-calls.jsonl",
    "episode-events.jsonl",
)


class GameRunAuditWriter:
    """Prepare a complete run context and append integrity-checked game records."""

    MANIFEST_SCHEMA_VERSION = 2
    RECORD_SCHEMA_VERSION = 2

    def __init__(
        self,
        runs_root: Path,
        *,
        game_policy: GamePolicy,
        oracle_config: OracleConfig,
        guesser_config: ModelConfig,
        validator_config: ModelConfig,
        subject_catalog_hash: str,
        repository: Path,
        cache_probe_summary: dict[str, Any] | None = None,
        artifact_policy: RunArtifactPolicy | None = None,
    ):
        if re.fullmatch(r"[0-9a-f]{64}", subject_catalog_hash) is None:
            raise ValueError("subject_catalog_hash must be a SHA-256 hex digest")
        self.runs_root = runs_root
        self.game_policy = game_policy
        self.oracle_config = oracle_config
        self.guesser_config = guesser_config
        self.validator_config = validator_config
        self.subject_catalog_hash = subject_catalog_hash
        self.repository = repository.resolve()
        self.cache_probe_summary = cache_probe_summary
        self.artifact_policy = artifact_policy or RunArtifactPolicy()

    def prepare_run(self, run_id: str) -> None:
        """Create or validate all immutable context before a paid game call."""
        try:
            if (
                self.game_policy.benchmark_mode is BenchmarkMode.OFFICIAL
                and self.guesser_config.prompt_cache.policy is not CachePolicy.REQUIRED
            ):
                raise GameAuditError(
                    "official runs require prompt_cache.policy=required",
                    code="official_cache_policy_required",
                )
            if self.official_cache_probe_required() and self.cache_probe_summary is None:
                raise GameAuditError(
                    "official runs require a successful compatible cache probe",
                    code="official_cache_probe_required",
                )
            run_root = self.runs_root / run_id
            run_root.mkdir(parents=True, exist_ok=True)
            with self._lock(run_root):
                self._ensure_manifest(run_root, run_id)
                result_path = run_root / RESULT_ARTIFACT
                if result_path.exists():
                    self._validate_episode_result(result_path, run_id)
                    raise GameAuditError(
                        "run already has a completed result; use a new run ID",
                        code="game_result_exists",
                    )
                for filename in GAME_ARTIFACTS:
                    path = run_root / filename
                    existing = path.read_text(encoding="utf-8") if path.exists() else ""
                    self._validate_log(existing, filename)
                    if not path.exists() and self.artifact_policy.permits(filename):
                        self._atomic_write(path, "")
        except GameAuditError:
            raise
        except Exception as error:
            raise GameAuditError(
                f"could not prepare game audit context for run {run_id!r}",
                code="game_audit_prepare_failed",
                details={"exception_type": type(error).__name__},
            ) from error

    def append_guesser_call(self, run_id: str, record: dict[str, Any]) -> dict[str, Any]:
        return self._append_record(
            run_id,
            filename="guesser-calls.jsonl",
            identity_field="call_id",
            record=record,
        )

    def persist_guesser_success(self, source: GuesserSuccessRecord) -> GuesserCall:
        record = self.append_guesser_call(
            source.run_id,
            source.model_dump(mode="json"),
        )
        return GuesserCall.model_validate(
            {key: value for key, value in record.items() if key != "status"}
        )

    def persist_guesser_failure(self, source: GuesserFailureRecord) -> PersistedRecord:
        record = self.append_guesser_call(
            source.run_id,
            {
                **source.model_dump(mode="json", exclude={"failure"}),
                "action": None,
                "error": source.failure.model_dump(mode="json"),
            },
        )
        return PersistedRecord(
            record_id=source.call_id,
            relative_path="guesser-calls.jsonl",
            integrity_hash=str(record["integrity_hash"]),
        )

    def append_validator_call(self, run_id: str, record: dict[str, Any]) -> dict[str, Any]:
        return self._append_record(
            run_id,
            filename="guess-validator-calls.jsonl",
            identity_field="call_id",
            record=record,
        )

    def persist_validator_success(self, source: ValidatorSuccessRecord) -> GuessValidatorCall:
        record = self.append_validator_call(
            source.run_id,
            source.model_dump(mode="json"),
        )
        return GuessValidatorCall.model_validate(
            {key: value for key, value in record.items() if key != "status"}
        )

    def persist_validator_failure(self, source: ValidatorFailureRecord) -> PersistedRecord:
        record = self.append_validator_call(
            source.run_id,
            {
                **source.model_dump(mode="json", exclude={"failure"}),
                "result": None,
                "error": source.failure.model_dump(mode="json"),
            },
        )
        return PersistedRecord(
            record_id=source.call_id,
            relative_path="guess-validator-calls.jsonl",
            integrity_hash=str(record["integrity_hash"]),
        )

    def append_episode_event(self, run_id: str, record: dict[str, Any]) -> dict[str, Any]:
        return self._append_record(
            run_id,
            filename="episode-events.jsonl",
            identity_field="event_id",
            record=record,
        )

    def persist_episode_event(self, event: EpisodeEvent) -> PersistedRecord:
        record = self.append_episode_event(
            event.run_id,
            event.model_dump(mode="json"),
        )
        return PersistedRecord(
            record_id=event.event_id,
            relative_path="episode-events.jsonl",
            integrity_hash=str(record["integrity_hash"]),
        )

    def write_episode_result(self, run_id: str, result: EpisodeResult) -> Path:
        """Write the completed benchmark result once as an integrity-protected YAML file."""
        try:
            payload = result.model_dump(mode="json")
            run_root = self.runs_root / run_id
            run_root.mkdir(parents=True, exist_ok=True)
            with self._lock(run_root):
                self._ensure_manifest(run_root, run_id)
                path = run_root / RESULT_ARTIFACT
                if path.exists():
                    raise GameAuditError(
                        "run already has a completed result; use a new run ID",
                        code="game_result_exists",
                    )
                run = payload.get("run")
                if not isinstance(run, dict) or run.get("run_id") != run_id:
                    raise GameAuditError(
                        "episode result run ID does not match its directory",
                        code="game_result_run_mismatch",
                    )
                unsigned = dict(payload)
                unsigned.pop("integrity_hash", None)
                signed = {
                    **unsigned,
                    "integrity_hash": sha256_text(canonical_json(unsigned)),
                }
                self._atomic_write(
                    path,
                    yaml.safe_dump(
                        signed,
                        allow_unicode=True,
                        sort_keys=False,
                    ),
                )
                return path
        except GameAuditError:
            raise
        except Exception as error:
            raise GameAuditError(
                f"could not write result.yml for run {run_id!r}",
                code="game_result_write_failed",
                details={"exception_type": type(error).__name__},
            ) from error

    def persist_episode_result(self, result: EpisodeResult) -> PersistedRecord:
        self.write_episode_result(result.run_id, result)
        unsigned = result.model_dump(mode="json")
        return PersistedRecord(
            record_id=result.episode_id,
            relative_path=RESULT_ARTIFACT,
            integrity_hash=sha256_text(canonical_json(unsigned)),
        )

    def interrupted_episode_ids(self, run_id: str) -> tuple[str, ...]:
        """Return started episodes without a durable terminal event."""
        path = self.runs_root / run_id / "episode-events.jsonl"
        content = path.read_text(encoding="utf-8") if path.exists() else ""
        self._validate_log(content, "episode-events.jsonl")
        started: set[str] = set()
        finished: set[str] = set()
        for line in content.splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            episode_id = record.get("episode_id")
            if not isinstance(episode_id, str):
                continue
            if record.get("event_type") == "episode_started":
                started.add(episode_id)
            elif record.get("event_type") == "episode_finished":
                finished.add(episode_id)
        return tuple(sorted(started - finished))

    def _append_record(
        self,
        run_id: str,
        *,
        filename: str,
        identity_field: str,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            if filename not in GAME_ARTIFACTS:
                raise ValueError("unsupported game artifact")
            identity = record.get(identity_field)
            if not isinstance(identity, str):
                raise GameAuditError(
                    f"invalid {identity_field} in {filename}",
                    code="game_audit_duplicate_id",
                )
            unsigned = dict(record)
            unsigned.pop("integrity_hash", None)
            signed = {
                **unsigned,
                "integrity_hash": sha256_text(canonical_json(unsigned)),
            }
            if not self.artifact_policy.permits(filename):
                return signed
            run_root = self.runs_root / run_id
            run_root.mkdir(parents=True, exist_ok=True)
            with self._lock(run_root):
                self._ensure_manifest(run_root, run_id)
                path = run_root / filename
                existing = path.read_text(encoding="utf-8") if path.exists() else ""
                seen = self._validate_log(existing, filename, identity_field=identity_field)
                if identity in seen:
                    raise GameAuditError(
                        f"invalid or duplicate {identity_field} in {filename}",
                        code="game_audit_duplicate_id",
                    )
                self._atomic_write(path, existing + canonical_json(signed) + "\n")
                return signed
        except GameAuditError:
            raise
        except Exception as error:
            raise GameAuditError(
                f"could not append {filename} for run {run_id!r}",
                code="game_audit_write_failed",
                details={"exception_type": type(error).__name__},
            ) from error

    def _ensure_manifest(self, run_root: Path, run_id: str) -> None:
        path = run_root / "manifest.json"
        context = self._game_context()
        context_hash = sha256_text(canonical_json(context))
        oracle_snapshot = self.oracle_config.model_dump(mode="json")
        oracle_hash = sha256_text(canonical_json(oracle_snapshot))
        if path.exists():
            manifest = json.loads(path.read_text(encoding="utf-8"))
            self._validate_integrity_hash(manifest, "run manifest")
            if manifest.get("run_id") != run_id:
                raise GameAuditError(
                    "run manifest ID does not match its directory",
                    code="game_audit_manifest_mismatch",
                )
            if manifest.get("schema_version") != self.MANIFEST_SCHEMA_VERSION:
                raise GameAuditError(
                    "existing Oracle-only run cannot be extended as a game run; use a new run ID",
                    code="legacy_run_manifest",
                )
            if manifest.get("game_context_hash") != context_hash:
                raise GameAuditError(
                    "run already uses a different immutable game context",
                    code="game_audit_configuration_mismatch",
                )
            return
        if not self.artifact_policy.permits(path.name):
            return

        manifest = {
            "schema_version": self.MANIFEST_SCHEMA_VERSION,
            "run_kind": "game",
            "run_id": run_id,
            "created_at": timestamp(),
            "git_commit": self._git(["rev-parse", "HEAD"]),
            "working_tree_dirty_before_run": bool(
                self._git(["status", "--porcelain", "--untracked-files=normal"])
            ),
            "oracle_config": oracle_snapshot,
            "oracle_config_hash": oracle_hash,
            "subject_catalog_hash": self.subject_catalog_hash,
            "game_context": context,
            "game_context_hash": context_hash,
            "reproducibility": "artifact_replay_only_live_llm_and_web_reruns_may_differ",
            "evidence_validation": "model_reported",
        }
        manifest["integrity_hash"] = sha256_text(canonical_json(manifest))
        self._atomic_write(
            path,
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        )

    def _game_context(self) -> dict[str, Any]:
        return {
            "benchmark_mode": self.game_policy.benchmark_mode,
            "game_policy": self.game_policy.model_dump(mode="json"),
            "guesser_configurations": {
                self.guesser_config.configuration_id: self.guesser_config.model_dump(mode="json")
            },
            "guess_validator_config": self.validator_config.model_dump(mode="json"),
            "prompt_versions": {
                "guesser": GUESSER_PROMPT_VERSION,
                "oracle": ORACLE_PROMPT_VERSION,
                "oracle_reviewer": REVIEWER_PROMPT_VERSION,
                "oracle_judge": JUDGE_PROMPT_VERSION,
                "guess_validator": VALIDATOR_PROMPT_VERSION,
            },
            "cache_probe": self.cache_probe_summary,
            "prompt_cache_contract": (
                "provider_prompt_prefix_only_no_response_or_application_cache"
            ),
            "history_contract": "full_visible_transcript_no_hidden_reasoning_state",
        }

    def official_cache_probe_required(self) -> bool:
        return (
            self.game_policy.benchmark_mode is BenchmarkMode.OFFICIAL
            and self.guesser_config.prompt_cache.policy is CachePolicy.REQUIRED
        )

    def _lock(self, run_root: Path) -> TextIO:
        lock_path = Path(tempfile.gettempdir()) / (
            f"deep20bench-{sha256_text(str(run_root.resolve()))}.lock"
        )
        lock = lock_path.open("a", encoding="utf-8")
        fcntl.flock(lock, fcntl.LOCK_EX)
        return lock

    @classmethod
    def _validate_log(
        cls,
        content: str,
        label: str,
        *,
        identity_field: str | None = None,
    ) -> set[str]:
        seen: set[str] = set()
        expected_identity = identity_field
        if expected_identity is None:
            expected_identity = "event_id" if label == "episode-events.jsonl" else "call_id"
        for line_number, line in enumerate(content.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise GameAuditError(
                    f"{label} line {line_number} is not valid JSON",
                    code="game_audit_log_corrupt",
                ) from error
            if not isinstance(record, dict):
                raise GameAuditError(
                    f"{label} line {line_number} is not an object",
                    code="game_audit_log_corrupt",
                )
            cls._validate_integrity_hash(record, f"{label} line {line_number}")
            identity = record.get(expected_identity)
            if not isinstance(identity, str) or identity in seen:
                raise GameAuditError(
                    f"{label} line {line_number} has an invalid or duplicate ID",
                    code="game_audit_log_corrupt",
                )
            seen.add(identity)
        return seen

    @staticmethod
    def _validate_integrity_hash(value: dict[str, Any], label: str) -> None:
        unsigned = dict(value)
        stored = unsigned.pop("integrity_hash", None)
        if stored != sha256_text(canonical_json(unsigned)):
            raise GameAuditError(
                f"{label} integrity hash mismatch",
                code="game_audit_integrity_mismatch",
            )

    @classmethod
    def _validate_episode_result(cls, path: Path, run_id: str) -> None:
        try:
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            raise GameAuditError(
                "result.yml is not valid YAML",
                code="game_result_corrupt",
            ) from error
        run = value.get("run") if isinstance(value, dict) else None
        if not isinstance(run, dict) or run.get("run_id") != run_id:
            raise GameAuditError(
                "result.yml does not match its run directory",
                code="game_result_corrupt",
            )
        cls._validate_integrity_hash(value, "result.yml")

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
    def safe_details(value: Any) -> Any:
        if value is None or isinstance(value, str | int | float | bool):
            return value
        if isinstance(value, dict):
            return {str(key): GameRunAuditWriter.safe_details(item) for key, item in value.items()}
        if isinstance(value, list | tuple):
            return [GameRunAuditWriter.safe_details(item) for item in value]
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
