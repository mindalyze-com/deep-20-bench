"""Benchmark-owned Oracle reuse from immutable history and completed local games."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Literal

import yaml
from deep20_game.answer_cache import normalized_question
from deep20_game.models import (
    ActionTurnResult,
    ActionType,
    CachedOracleAnswer,
    OracleCacheSource,
    OracleResultCallAudit,
)
from deep20_oracle.cache_contract import oracle_contract_hash
from deep20_oracle.models import (
    EvidenceReviewRequest,
    JsonObject,
    OracleRequest,
    OracleResearchStrategy,
    OracleResult,
    OracleRole,
    Subject,
)
from deep20_oracle.prompt import (
    evidence_review_prompt_version,
    prompt_hash,
    render_evidence_review_messages,
    render_messages,
    research_prompt_version,
)
from deep20_oracle.protocol import validate_answer, validate_protocol_result
from deep20_oracle.util import canonical_json, sha256_text, timestamp
from pydantic import JsonValue, TypeAdapter
from yaml.constructor import ConstructorError

from .history_models import (
    HistoryExecution,
    HistoryFile,
    OracleHistoryLoad,
    OracleHistorySnapshot,
    OracleSubjectHistoryStore,
)
from .models import (
    BenchmarkDefinitionSnapshot,
    BenchmarkManifest,
    CompletedTrialResult,
    TrialIdentity,
)

logger = logging.getLogger("deep20.benchmark")
_JSON_OBJECT: TypeAdapter[JsonObject] = TypeAdapter(JsonObject)


class _UniqueLoader(yaml.CSafeLoader):
    def construct_mapping(self, node: yaml.Node, deep: bool = False) -> dict[object, object]:
        if not isinstance(node, yaml.MappingNode):
            raise TypeError("expected a YAML mapping")
        self.flatten_mapping(node)
        result: dict[object, object] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in result:
                raise ConstructorError(None, None, "duplicate YAML key", key_node.start_mark)
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def _unique_pairs(pairs: list[tuple[str, JsonValue]]) -> JsonObject:
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _verified(value: object) -> JsonObject:
    obj = _JSON_OBJECT.validate_python(value)
    unsigned = {key: item for key, item in obj.items() if key != "integrity_hash"}
    if obj.get("integrity_hash") != sha256_text(canonical_json(unsigned)):
        raise ValueError("history integrity mismatch")
    return obj


def _fingerprint(value: object) -> str:
    return sha256_text(canonical_json(value))


def _has_contract_revisions(manifest_path: Path) -> bool:
    events = manifest_path.parent / "benchmark-events.jsonl"
    if not events.exists():
        return False
    for line in events.read_text(encoding="utf-8").splitlines():
        if line and _verified(json.loads(line)).get("oracle_contract_revision") is not None:
            return True
    return False


def _context_hash(definition: BenchmarkDefinitionSnapshot, ignored: tuple[str, ...]) -> str:
    return _fingerprint(
        {
            "benchmark_id": str(definition.benchmark_id),
            "protocol_version": definition.game_policy.version,
            "prompt_profile": definition.game_policy.prompt_profile,
            "oracle_contract": oracle_contract_hash(definition.oracle_configuration),
            "judge_ignored_providers": sorted(ignored),
            "normalization": "casefold-ascii-spaces-v1",
        }
    )


class LazyOracleHistoryCache:
    """Versioned external inventories and private per-subject answer maps."""

    def __init__(
        self,
        repository: Path,
        *,
        before: str | None = None,
        judge_ignored_providers: tuple[str, ...] = (),
    ) -> None:
        self.repository = repository.resolve()
        if before is not None:
            cutoff = datetime.fromisoformat(before)
            if cutoff.tzinfo is None or cutoff > datetime.fromisoformat(timestamp()):
                raise ValueError("Oracle history cutoff must be timezone-aware and in the past")
        self.before = before
        self.ignored = judge_ignored_providers
        self.snapshot: OracleHistorySnapshot | None = None
        self.loads: list[OracleHistoryLoad] = []
        self._definition: BenchmarkDefinitionSnapshot | None = None
        self._execution_id: str | None = None
        self._subject_history: OracleSubjectHistoryStore | None = None
        self._loaded: dict[str, dict[str, CachedOracleAnswer]] = {}
        self._conflicts: dict[str, set[str]] = {}

    def _file(self, path: Path, stat: os.stat_result | None = None) -> HistoryFile:
        if not path.resolve().is_relative_to(self.repository):
            raise ValueError("history file escapes repository")
        stat = stat or path.stat()
        return HistoryFile(
            relative_path=path.relative_to(self.repository).as_posix(),
            size=stat.st_size,
            modified_ns=stat.st_mtime_ns,
            changed_ns=stat.st_ctime_ns,
            inode=stat.st_ino,
        )

    def _read(self, source: HistoryFile) -> bytes:
        path = self.repository / source.relative_path
        with path.open("rb") as handle:
            if self._file(path, os.fstat(handle.fileno())) != source:
                raise ValueError("history source changed after inventory")
            content = handle.read()
            if self._file(path, os.fstat(handle.fileno())) != source:
                raise ValueError("history source changed during read")
        return content

    def prepare(
        self,
        definition: BenchmarkDefinitionSnapshot,
        *,
        execution_id: str,
        existing: BenchmarkManifest | None = None,
        existing_snapshot: OracleHistorySnapshot | None = None,
        reset_for_contract_revision: bool = False,
        subject_history: OracleSubjectHistoryStore | None = None,
    ) -> OracleHistorySnapshot | None:
        started = perf_counter()
        self._loaded.clear()
        self._conflicts.clear()
        self.loads.clear()
        self._definition = definition
        self._execution_id = execution_id
        self._subject_history = subject_history
        context_hash = _context_hash(definition, self.ignored)
        logger.info("benchmark.oracle_cache.loading phase=inventory")
        if existing is not None:
            self.snapshot = existing_snapshot or existing.oracle_cache
            if self.snapshot is not None:
                if self.before is not None and self.snapshot.discovery_policy is not None:
                    raise ValueError("cannot freeze an existing per-subject Oracle history policy")
                if self.before is not None and datetime.fromisoformat(
                    self.before
                ) != datetime.fromisoformat(self.snapshot.cutoff):
                    raise ValueError("cannot change an existing Oracle history cutoff")
                unsigned = self.snapshot.model_dump(mode="json", exclude={"snapshot_hash"})
                if self.snapshot.snapshot_hash != _fingerprint(unsigned):
                    raise ValueError("Oracle history snapshot integrity mismatch")
                if self.snapshot.context_hash != context_hash:
                    if not reset_for_contract_revision:
                        raise ValueError("Oracle history contract changed; use a new execution ID")
                    # The repair keeps its cutoff, but never imports earlier-contract answers.
                    unsigned.update(context_hash=context_hash, sources=[])
                    # Contract repairs keep an empty, fixed external inventory.
                    unsigned.pop("discovery_policy", None)
                    self.snapshot = OracleHistorySnapshot.model_validate_json(canonical_json({
                        **unsigned, "snapshot_hash": _fingerprint(unsigned),
                    }))
            logger.info(
                "benchmark.oracle_cache.loaded phase=inventory resumed=true manifests=%d "
                "files=%d duration_ms=%.2f",
                len(self.snapshot.sources) if self.snapshot else 0,
                sum(len(s.trials) for s in self.snapshot.sources) if self.snapshot else 0,
                (perf_counter() - started) * 1000,
            )
            return self.snapshot
        self.snapshot = self._discover(
            cutoff=self.before or timestamp(),
            refresh_subjects=self.before is None,
        )
        return self.snapshot

    def _discover(
        self, *, cutoff: str, refresh_subjects: bool = False, subject: Subject | None = None,
    ) -> OracleHistorySnapshot:
        started = perf_counter()
        definition = self._definition
        assert definition is not None
        context_hash = _context_hash(definition, self.ignored)
        cutoff_time = datetime.fromisoformat(cutoff)
        if cutoff_time.tzinfo is None or cutoff_time > datetime.fromisoformat(timestamp()):
            raise ValueError("Oracle history cutoff must be timezone-aware and in the past")
        sources: list[HistoryExecution] = []
        discovered = skipped = 0
        contract_hash = oracle_contract_hash(definition.oracle_configuration)
        for root in (
            self.repository / "runs",
            self.repository / "archive",
            self.repository / "benchmark-logs/superseded-runs",
        ):
            for path in sorted(root.glob("**/manifest.json")):
                discovered += 1
                try:
                    manifest_file = self._file(path)
                    raw = _verified(
                        json.loads(self._read(manifest_file), object_pairs_hook=_unique_pairs)
                    )
                    if raw.get("oracle_contract_hash") != contract_hash:
                        continue
                    if _has_contract_revisions(path):
                        continue
                    manifest = BenchmarkManifest.model_validate_json(canonical_json(raw))
                    if (
                        str(manifest.request.execution_id) == self._execution_id
                        or datetime.fromisoformat(manifest.created_at) >= cutoff_time
                        or manifest.oracle_contract_hash != contract_hash
                        or manifest.definition.benchmark_id != definition.benchmark_id
                        or manifest.definition.game_policy.version != definition.game_policy.version
                        or manifest.definition.game_policy.prompt_profile
                        != definition.game_policy.prompt_profile
                        or manifest.definition.oracle_configuration
                        != definition.oracle_configuration
                    ):
                        continue
                    # Repairs that excluded Judge routes cannot seed ordinary routing.
                    if (
                        manifest.oracle_cache is not None
                        and manifest.oracle_cache.context_hash != context_hash
                    ):
                        continue
                    trial_pattern = (
                        f"subjects/{subject.target_id}/trials/*/result.yml" if subject is not None
                        else "subjects/*/trials/*/result.yml"
                    )
                    trials: list[HistoryFile] = []
                    for p in sorted(path.parent.glob(trial_pattern)):
                        try:
                            file = self._file(p)
                            if file.modified_ns <= int(cutoff_time.timestamp() * 1_000_000_000):
                                trials.append(file)
                        except OSError, ValueError:
                            skipped += 1
                    sources.append(
                        HistoryExecution(
                            manifest=manifest_file,
                            manifest_integrity_hash=manifest.integrity_hash,
                            trials=tuple(trials),
                        )
                    )
                except OSError, ValueError, TypeError, yaml.YAMLError:
                    skipped += 1
        unsigned = {
            "execution_reuse_policy": "same_execution_ask_v1",
            "episode_reuse_policy": "same_episode_ask_v1",
            "policy": "historical_ask_v1",
            "normalization": "casefold-ascii-spaces-v1",
            "context_hash": context_hash,
            "cutoff": cutoff,
            "sources": [source.model_dump(mode="json") for source in sources],
        }
        if refresh_subjects:
            unsigned["discovery_policy"] = "per_subject_history_v1"
        snapshot = OracleHistorySnapshot.model_validate_json(
            canonical_json({**unsigned, "snapshot_hash": _fingerprint(unsigned)})
        )
        logger.info(
            "benchmark.oracle_cache.loaded phase=inventory discovered=%d manifests=%d "
            "files=%d skipped=%d duration_ms=%.2f",
            discovered,
            len(sources),
            sum(len(s.trials) for s in sources),
            skipped,
            (perf_counter() - started) * 1000,
        )
        return snapshot

    def _subject_snapshot(self, subject: Subject) -> OracleHistorySnapshot:
        parent = self.snapshot
        assert parent is not None
        if parent.discovery_policy is None:
            return parent
        saved = self._subject_history.load(subject, parent) if self._subject_history else None
        if saved is not None:
            if (
                saved.snapshot_hash != _fingerprint(saved.model_dump(mode="json", exclude={"snapshot_hash"}))
                or saved.context_hash != parent.context_hash
                or saved.discovery_policy is not None
                or datetime.fromisoformat(saved.cutoff) < datetime.fromisoformat(parent.cutoff)
                or any(len(Path(f.relative_path).parts) < 4
                       or Path(f.relative_path).parts[-4] != subject.target_id
                       for source in saved.sources for f in source.trials)
            ):
                raise ValueError("invalid saved Oracle subject history")
            return saved
        snapshot = self._discover(cutoff=timestamp(), subject=subject)
        if self._subject_history is not None:
            self._subject_history.save(subject, parent, snapshot)
        return snapshot

    def lookup(self, request: OracleRequest) -> CachedOracleAnswer | None:
        if self.snapshot is None:
            return None
        self.load_subject(request.subject)
        subject_hash = _fingerprint(request.subject.model_dump(mode="json"))
        return self._loaded[subject_hash].get(normalized_question(request.question))

    def load_subject(self, subject: Subject) -> None:
        """Capture or restore the subject inventory once, before its first game."""
        if self.snapshot is None:
            return
        subject_hash = _fingerprint(subject.model_dump(mode="json"))
        if subject_hash not in self._loaded:
            self._loaded[subject_hash] = self._load_subject(subject, subject_hash)

    def remember_completed_trial(
        self,
        identity: TrialIdentity,
        source_file: Path,
        *,
        contract_since: str | None = None,
    ) -> None:
        """Read the root's committed trial artifact, also when rebuilding on resume."""
        if self.snapshot is None or self.snapshot.execution_reuse_policy is None:
            return
        assert self._definition is not None
        if str(identity.execution_id) != self._execution_id:
            raise ValueError("current-execution cache cannot import another execution")
        try:
            file = self._file(source_file)
            envelope = _verified(yaml.load(self._read(file), Loader=_UniqueLoader))
            payload = _JSON_OBJECT.validate_python(envelope.get("payload"))
            if payload.get("status") != "completed":
                return
            trial = CompletedTrialResult.model_validate_json(canonical_json(payload))
            episode = trial.result
            if (
                trial.identity != identity
                or str(identity.episode_run_id) != episode.run_id
                or str(identity.target_id) != episode.subject.target_id
                or not episode.scoring_eligible
                or episode.llm.oracle.configuration != self._definition.oracle_configuration
                or tuple(sorted(trial.oracle_judge_ignored_providers)) != tuple(sorted(self.ignored))
                or (contract_since is not None and datetime.fromisoformat(episode.started_at)
                    < datetime.fromisoformat(contract_since))
            ):
                return
            audits = {call.call_id: call for call in episode.audit.calls} if episode.audit else {}
            candidates: list[CachedOracleAnswer] = []
            for turn in episode.turns:
                if not isinstance(turn, ActionTurnResult) or turn.action.action is not ActionType.ASK:
                    continue
                audit = audits.get(turn.adjudication.call_id)
                if not isinstance(audit, OracleResultCallAudit):
                    continue
                candidate = self._candidate(
                    trial, turn, audit, file.relative_path, str(envelope["integrity_hash"]),
                    source_policy="same_execution_ask_v1",
                )
                if candidate is not None:
                    candidates.append(candidate)
            if not candidates:
                return
            subject_hash = _fingerprint(episode.subject.model_dump(mode="json"))
            if subject_hash not in self._loaded:
                self._loaded[subject_hash] = self._load_subject(episode.subject, subject_hash)
            index = self._loaded[subject_hash]
            conflicts = self._conflicts[subject_hash]
            for candidate in candidates:
                self._merge(index, conflicts, candidate)
            logger.info(
                "benchmark.oracle_cache.updated target=%s trial=%s eligible=%d entries=%d conflicts=%d",
                identity.target_id, identity.trial_id, len(candidates), len(index), len(conflicts),
            )
        except OSError, ValueError, TypeError, yaml.YAMLError:
            # A cache-source problem is a miss, never a reason to lose the benchmark.
            logger.info(
                "benchmark.oracle_cache.source_skipped target=%s trial=%s",
                identity.target_id, identity.trial_id,
            )

    @staticmethod
    def _merge(
        index: dict[str, CachedOracleAnswer], conflicts: set[str], candidate: CachedOracleAnswer,
    ) -> None:
        key = normalized_question(candidate.source.question)
        if key in conflicts:
            return
        previous = index.get(key)
        if previous and previous.adjudication.final_answer != candidate.adjudication.final_answer:
            conflicts.add(key)
            del index[key]
        elif previous is None or (
            candidate.source.answered_at, candidate.source.oracle_call_id,
        ) > (previous.source.answered_at, previous.source.oracle_call_id):
            index[key] = candidate

    def _load_subject(self, subject: Subject, subject_hash: str) -> dict[str, CachedOracleAnswer]:
        started = perf_counter()
        snapshot = self._subject_snapshot(subject)
        assert snapshot is not None and self._definition is not None
        logger.info("benchmark.oracle_cache.loading phase=subject target=%s", subject.target_id)
        index: dict[str, CachedOracleAnswer] = {}
        conflicts: set[str] = set()
        files = bytes_read = found = eligible = skipped = 0
        for source in snapshot.sources:
            selected = tuple(
                f for f in source.trials if Path(f.relative_path).parts[-4] == subject.target_id
            )
            if not selected:
                continue
            try:
                manifest_raw = _verified(
                    json.loads(self._read(source.manifest), object_pairs_hook=_unique_pairs)
                )
                manifest = BenchmarkManifest.model_validate_json(canonical_json(manifest_raw))
                if manifest.integrity_hash != source.manifest_integrity_hash:
                    raise ValueError("history manifest differs from inventory")
                if _has_contract_revisions(self.repository / source.manifest.relative_path):
                    raise ValueError("history source acquired a contract revision")
            except OSError, ValueError, TypeError:
                skipped += len(selected)
                continue
            for file in selected:
                files += 1
                try:
                    content = self._read(file)
                    bytes_read += len(content)
                    envelope = _verified(yaml.load(content, Loader=_UniqueLoader))
                    payload = _JSON_OBJECT.validate_python(envelope.get("payload"))
                    if payload.get("status") != "completed":
                        continue
                    trial = CompletedTrialResult.model_validate_json(canonical_json(payload))
                    episode = trial.result
                    identity = trial.identity
                    if (
                        tuple(sorted(trial.oracle_judge_ignored_providers))
                        != tuple(sorted(self.ignored))
                        or episode.subject != subject
                        or str(identity.target_id) != subject.target_id
                        or identity.execution_id != manifest.request.execution_id
                        or identity.model_id != manifest.model.model_id
                        or str(identity.episode_run_id) != episode.run_id
                        or Path(file.relative_path).parent.name != str(identity.trial_id)
                        or not episode.scoring_eligible
                        or datetime.fromisoformat(episode.completed_at)
                        > datetime.fromisoformat(snapshot.cutoff)
                        or episode.llm.oracle.configuration != self._definition.oracle_configuration
                    ):
                        raise ValueError("history trial context mismatch")
                    audits = (
                        {call.call_id: call for call in episode.audit.calls}
                        if episode.audit
                        else {}
                    )
                    candidates: list[CachedOracleAnswer] = []
                    for turn in episode.turns:
                        if (
                            not isinstance(turn, ActionTurnResult)
                            or turn.action.action is not ActionType.ASK
                        ):
                            continue
                        found += 1
                        audit = audits.get(turn.adjudication.call_id)
                        if not isinstance(audit, OracleResultCallAudit):
                            continue
                        candidate = self._candidate(
                            trial, turn, audit, file.relative_path, str(envelope["integrity_hash"]),
                            history_snapshot=snapshot,
                        )
                        if candidate is not None:
                            candidates.append(candidate)
                    eligible += len(candidates)
                    for candidate in candidates:
                        self._merge(index, conflicts, candidate)
                except OSError, ValueError, TypeError, yaml.YAMLError:
                    skipped += 1
        self._conflicts[subject_hash] = conflicts
        stats = OracleHistoryLoad(
            snapshot=snapshot if self.snapshot and self.snapshot.discovery_policy else None,
            target_id=subject.target_id,
            subject_hash=subject_hash,
            files=files,
            bytes_read=bytes_read,
            records_found=found,
            eligible_records=eligible,
            entries=len(index),
            conflicts=len(conflicts),
            skipped_files=skipped,
            duration_ms=(perf_counter() - started) * 1000,
        )
        self.loads.append(stats)
        logger.info(
            "benchmark.oracle_cache.loaded phase=subject target=%s files=%d bytes=%d "
            "records=%d eligible=%d entries=%d conflicts=%d skipped=%d duration_ms=%.2f",
            stats.target_id,
            files,
            bytes_read,
            found,
            eligible,
            len(index),
            len(conflicts),
            skipped,
            stats.duration_ms,
        )
        return index

    def _candidate(
        self,
        trial: CompletedTrialResult,
        turn: ActionTurnResult,
        audit: OracleResultCallAudit,
        source_file: str,
        integrity_hash: str,
        *,
        source_policy: Literal["historical_ask_v1", "same_execution_ask_v1"] = "historical_ask_v1",
        history_snapshot: OracleHistorySnapshot | None = None,
    ) -> CachedOracleAnswer | None:
        assert self.snapshot is not None and self._definition is not None
        snapshot = history_snapshot or self.snapshot
        decision = turn.adjudication
        quality = decision.oracle_quality
        question = turn.action.question
        if (
            decision.cache_source is not None
            or audit.cache_source is not None
            or quality is None
            or question is None
            or audit.turn_number != turn.turn_number
            or audit.research is None
        ):
            return None
        config = self._definition.oracle_configuration
        profile = config.prompt_profile
        policy = config.adjudication_policy
        request = OracleRequest(
            run_id=trial.result.run_id, subject=trial.result.subject, question=question
        )
        if audit.oracle.prompt.version != research_prompt_version(
            OracleResearchStrategy.PRIMARY, profile, policy=policy
        ):
            return None
        if audit.oracle.prompt.hash != prompt_hash(render_messages(
            request, profile=profile, policy=policy, research_query_target=config.research_query_target,
        )):
            return None
        for attempt in audit.research.attempts:
            if (
                attempt.provider.requested_model != config.model
                or attempt.provider.requested_provider != config.provider
            ):
                return None
            if attempt.prompt.version != research_prompt_version(
                attempt.strategy, profile, policy=policy
            ) or attempt.prompt.hash != prompt_hash(
                render_messages(
                    request, strategy=attempt.strategy, profile=profile, policy=policy,
                    research_query_target=config.research_query_target,
                )
            ):
                return None
        if audit.research.resolution.value in {"retrieval_exhausted_unknown", "bounded_unknown"}:
            return None
        if (quality.reviewer is None) != (audit.reviewer is None) or (quality.judge is None) != (
            audit.judge is None
        ):
            return None
        validate_answer(quality.oracle_answer, profile)
        validate_answer(quality.final_answer, profile)
        last_attempt = audit.research.attempts[-1]
        result = OracleResult(
            answer=quality.oracle_answer, evidence=decision.evidence,
            basis=last_attempt.basis, supporting_statement=last_attempt.supporting_statement,
        )
        validate_protocol_result(result, profile, role=OracleRole.ORACLE, policy=policy)
        for role, review, role_audit in (
            (OracleRole.REVIEWER, quality.reviewer, audit.reviewer),
            (OracleRole.JUDGE, quality.judge, audit.judge),
        ):
            if review is None or role_audit is None:
                continue
            assert role is OracleRole.REVIEWER or role is OracleRole.JUDGE
            validate_protocol_result(review, profile, role=role, policy=config.adjudication_policy)
            if any(index > len(decision.evidence) for index in review.evidence_indices):
                return None
            review_request = EvidenceReviewRequest(
                subject=request.subject, question=question, evidence=decision.evidence
            )
            if role_audit.prompt.version != evidence_review_prompt_version(
                role, profile, policy=config.adjudication_policy
            ) or role_audit.prompt.hash != prompt_hash(
                render_evidence_review_messages(
                    review_request, role=role, profile=profile, policy=config.adjudication_policy
                )
            ):
                return None
        providers = [attempt.provider for attempt in audit.research.attempts]
        providers.extend(
            role.provider for role in (audit.reviewer, audit.judge) if role is not None
        )
        if any(provider.finish_reason != "stop" for provider in providers):
            return None
        answered = max(datetime.fromisoformat(provider.completed_at) for provider in providers)
        cutoff = (snapshot.cutoff if source_policy == "historical_ask_v1"
                  else trial.result.completed_at)
        if answered > datetime.fromisoformat(cutoff):
            return None
        identity = trial.identity
        source = OracleCacheSource(
            policy=source_policy,
            context_hash=snapshot.context_hash,
            snapshot_hash=snapshot.snapshot_hash,
            execution_id=str(identity.execution_id),
            model_id=str(identity.model_id),
            benchmark_id=str(self._definition.benchmark_id),
            target_id=str(identity.target_id),
            trial_id=str(identity.trial_id),
            episode_id=trial.result.episode_id,
            turn_number=turn.turn_number,
            oracle_call_id=audit.call_id,
            question=question,
            answered_at=answered.isoformat(),
            source_file=source_file,
            source_integrity_hash=integrity_hash,
        )
        return CachedOracleAnswer(
            result=result, adjudication=quality, source=source, original_audit=audit
        )
