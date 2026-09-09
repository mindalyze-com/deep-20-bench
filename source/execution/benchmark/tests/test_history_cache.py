from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest
from deep20_benchmark.artifacts import ArtifactStore, _signed_payload
from deep20_benchmark.history_cache import LazyOracleHistoryCache
from deep20_benchmark.models import (
    BenchmarkExecutionId,
    BenchmarkId,
    BenchmarkModelId,
    BenchmarkRequest,
    CompletedTrialResult,
)
from deep20_benchmark.runner import BenchmarkRunner
from deep20_game.answer_cache import normalized_question
from deep20_game.config import BenchmarkMode
from deep20_game.models import (
    ActionTurnResult,
    ActionType,
    EpisodeResultAudit,
    GuesserAction,
    OracleResearchAttemptResultCallAudit,
    OracleResearchResultCallAudit,
    OracleResultCallAudit,
    OracleRoleResultCallAudit,
    ResultPromptAudit,
    TurnAdjudication,
)
from deep20_oracle import cache_contract
from deep20_oracle.models import (
    Evidence,
    EvidenceDecisionBasis,
    EvidenceReviewRequest,
    EvidenceReviewResult,
    OracleAdjudication,
    OracleAnswer,
    OracleDecisionPath,
    OracleRequest,
    OracleResearchOutcome,
    OracleResearchQuestionClass,
    OracleResearchResolution,
    OracleResearchStrategy,
    OracleRole,
    ProviderResultAudit,
)
from deep20_oracle.prompt import (
    evidence_review_prompt_version,
    prompt_hash,
    render_evidence_review_messages,
    render_messages,
    research_prompt_version,
)
from deep20_oracle.util import timestamp
from test_runner import FakeExecutor, fixtures


def seed(root: Path, *, execution: str = "BX-source", answer: OracleAnswer = OracleAnswer.YES):
    models, catalog, subjects = fixtures()
    store = ArtifactStore(root)
    store._git = lambda arguments: "abc123"  # type: ignore[method-assign]
    result = BenchmarkRunner(
        store=store,
        model_catalog=models,
        benchmark_catalog=catalog,
        subject_catalog=subjects,
        executor=FakeExecutor(),
    ).run(
        BenchmarkRequest(
            benchmark_id=BenchmarkId("B-0001"),
            execution_id=BenchmarkExecutionId(execution),
            model_id=BenchmarkModelId("M-0001"),
            benchmark_mode=BenchmarkMode.EXPERIMENTAL,
            iterations_override=1,
        )
    )
    config = result.run.definition.oracle_configuration
    for subject_result in result.subjects:
        trial = subject_result.trials[0]
        assert isinstance(trial, CompletedTrialResult)
        episode = trial.result
        question = "Was this person born before 1900?"
        request = OracleRequest(run_id=episode.run_id, subject=episode.subject, question=question)
        evidence = (
            Evidence(
                source_url="https://example.test/source",
                excerpt="Original evidence.",
                validation="model_reported",
            ),
        )
        quality = OracleAdjudication(
            oracle_answer=answer,
            reviewer=EvidenceReviewResult(
                answer=answer, basis=EvidenceDecisionBasis.EVIDENCE, evidence_indices=(1,)
            ),
            disagreement=False,
            judge_invoked=False,
            final_answer=answer,
            decision_path=OracleDecisionPath.REVIEWER_AGREEMENT,
        )
        provider = ProviderResultAudit(
            requested_at=episode.started_at,
            completed_at=episode.completed_at,
            latency_ms=1000,
            requested_model=config.model,
            requested_provider=config.provider,
            finish_reason="stop",
            raw_output_present=True,
            raw_output_characters=10,
        )
        primary = OracleRoleResultCallAudit(
            role=OracleRole.ORACLE,
            prompt=ResultPromptAudit(
                version=research_prompt_version(OracleResearchStrategy.PRIMARY),
                hash=prompt_hash(render_messages(request)),
            ),
            provider=provider,
        )
        review_request = EvidenceReviewRequest(
            subject=episode.subject, question=question, evidence=evidence
        )
        reviewer = OracleRoleResultCallAudit(
            role=OracleRole.REVIEWER,
            prompt=ResultPromptAudit(
                version=evidence_review_prompt_version(OracleRole.REVIEWER),
                hash=prompt_hash(
                    render_evidence_review_messages(review_request, role=OracleRole.REVIEWER)
                ),
            ),
            provider=provider.model_copy(
                update={
                    "requested_model": config.reviewer.model,
                    "requested_provider": config.reviewer.provider,
                }
            ),
        )
        audit = OracleResultCallAudit(
            call_id="OC-" + "1" * 32,
            turn_number=1,
            oracle=primary,
            reviewer=reviewer,
            research=OracleResearchResultCallAudit(
                question_class=OracleResearchQuestionClass.CLOSED_FACT,
                resolution=OracleResearchResolution.ANSWERED_PRIMARY,
                attempts=(
                    OracleResearchAttemptResultCallAudit(
                        attempt_number=1,
                        strategy=OracleResearchStrategy.PRIMARY,
                        outcome=OracleResearchOutcome.ANSWERED,
                        attempted_queries=("Original search",),
                        evidence_count=1,
                        prompt=primary.prompt,
                        provider=provider,
                    ),
                ),
            ),
        )
        turn = ActionTurnResult(
            turn_number=1,
            action=GuesserAction(
                action=ActionType.ASK, question=question, name=None, description=None
            ),
            adjudication=TurnAdjudication(
                component="oracle",
                call_id=audit.call_id,
                answer=answer,
                evidence=evidence,
                oracle_quality=quality,
            ),
            counted=True,
            counted_questions=1,
            guesser_call_id="GC-" + "1" * 32,
        )
        episode = episode.model_copy(
            update={
                "turns": (turn,),
                "summary": episode.summary.model_copy(update={"ask_count": 1, "guess_count": 0}),
                "audit": EpisodeResultAudit(calls=(audit,), unavailable_call_count=1),
            }
        )
        store.write_trial_result(trial.model_copy(update={"result": episode}))
    return store, result.run.definition, subjects


def test_lazy_history_source_provenance_and_zero_repeat_reads(tmp_path, monkeypatch, caplog):
    _, definition, subjects = seed(tmp_path)
    cache = LazyOracleHistoryCache(tmp_path)
    with caplog.at_level(logging.INFO, logger="deep20.benchmark"):
        snapshot = cache.prepare(definition, execution_id="BX-next")
        assert snapshot is not None and len(snapshot.sources) == 1
        assert not cache.loads
        opened = []
        original = cache._read

        def read(source):
            opened.append(source.relative_path)
            return original(source)

        monkeypatch.setattr(cache, "_read", read)
        request = OracleRequest(
            run_id="new",
            subject=subjects.subject("T-0001"),
            question="WAS  this person born before 1900?",
        )
        hit = cache.lookup(request)
        assert hit is not None
        assert hit.result.evidence[0].excerpt == "Original evidence."
        assert hit.source.execution_id == "BX-source"
        assert hit.source.oracle_call_id == "OC-" + "1" * 32
        assert hit.source.turn_number == 1
        assert hit.source.question == "Was this person born before 1900?"
        assert all("/T-0002/" not in path for path in opened)
        opened.clear()
        assert cache.lookup(request) == hit
        assert not opened
        assert cache.lookup(request.model_copy(update={"subject": subjects.subject("T-0002")}))
        assert len(cache.loads) == 2
        assert cache.loads[0].records_found == cache.loads[0].entries == 1
    logs = "\n".join(record.message for record in caplog.records)
    assert "benchmark.oracle_cache.loading phase=subject" in logs
    assert "records=1 eligible=1 entries=1" in logs and "duration_ms=" in logs
    assert "Original evidence" not in logs and "OC-" not in logs


def test_empty_subject_is_remembered(tmp_path, monkeypatch):
    _, definition, subjects = seed(tmp_path)
    cache = LazyOracleHistoryCache(tmp_path)
    cache.prepare(definition, execution_id="BX-next")
    subject = subjects.subject("T-0001").model_copy(update={"target_id": "T-9999"})
    request = OracleRequest(run_id="new", subject=subject, question="Nothing?")
    assert cache.lookup(request) is None
    monkeypatch.setattr(cache, "_load_subject", lambda *args: pytest.fail("empty subject reloaded"))
    assert cache.lookup(request) is None
    assert cache.loads[0].files == 0


@pytest.mark.parametrize(
    "difference", ["subject", "config", "benchmark", "protocol", "prompt", "legacy", "research_policy"]
)
def test_history_fails_closed_on_incompatible_context(tmp_path, difference, monkeypatch):
    store, definition, subjects = seed(tmp_path)
    if difference in {"legacy", "prompt"}:
        path = store.run_root("M-0001", "BX-source") / "manifest.json"
        raw = json.loads(path.read_text())
        if difference == "legacy":
            raw.pop("oracle_contract_hash")
        else:
            raw["oracle_contract_hash"] = "f" * 64
        path.write_text(json.dumps(_signed_payload(raw)))
    elif difference == "config":
        definition = definition.model_copy(
            update={
                "oracle_configuration": definition.oracle_configuration.model_copy(
                    update={"max_output_tokens": 999}
                )
            }
        )
    elif difference == "benchmark":
        definition = definition.model_copy(update={"benchmark_id": BenchmarkId("B-9999")})
    elif difference == "protocol":
        definition = definition.model_copy(
            update={"game_policy": definition.game_policy.model_copy(update={"version": 999})}
        )
    elif difference == "research_policy":
        monkeypatch.setattr(cache_contract, "ORACLE_FACTUAL_CONTRACT_VERSION", "historical_ask_v1")
    cache = LazyOracleHistoryCache(tmp_path)
    cache.prepare(definition, execution_id="BX-next")
    subject = subjects.subject("T-0001")
    if difference == "subject":
        subject = subject.model_copy(update={"description": "Changed identity."})
    assert (
        cache.lookup(
            OracleRequest(
                run_id="new", subject=subject, question="Was this person born before 1900?"
            )
        )
        is None
    )


def test_conflicting_answers_are_not_reused(tmp_path):
    seed(tmp_path, execution="BX-one")
    _, definition, subjects = seed(tmp_path, execution="BX-two", answer=OracleAnswer.NO)
    cache = LazyOracleHistoryCache(tmp_path)
    cache.prepare(definition, execution_id="BX-next")
    assert (
        cache.lookup(
            OracleRequest(
                run_id="new",
                subject=subjects.subject("T-0001"),
                question="Was this person born before 1900?",
            )
        )
        is None
    )
    assert cache.loads[0].conflicts == 1 and cache.loads[0].eligible_records == 2


def test_changed_source_and_new_history_do_not_enter_frozen_inventory(tmp_path):
    store, definition, subjects = seed(tmp_path)
    cache = LazyOracleHistoryCache(tmp_path, before=timestamp())
    cache.prepare(definition, execution_id="BX-next")
    path = store.run_root("M-0001", "BX-source") / "subjects/T-0001/trials/trial-001/result.yml"
    path.write_text(path.read_text() + "\n")
    seed(tmp_path, execution="BX-later")
    assert (
        cache.lookup(
            OracleRequest(
                run_id="new",
                subject=subjects.subject("T-0001"),
                question="Was this person born before 1900?",
            )
        )
        is None
    )
    assert cache.loads[0].skipped_files == 1


@pytest.mark.parametrize("damage", ["truncated", "duplicate", "integrity"])
def test_invalid_original_yaml_is_skipped(tmp_path, damage):
    store, definition, subjects = seed(tmp_path)
    path = store.run_root("M-0001", "BX-source") / "subjects/T-0001/trials/trial-001/result.yml"
    text = path.read_text()
    path.write_text(
        text[:100]
        if damage == "truncated"
        else text + "\nintegrity_hash: duplicate\n"
        if damage == "duplicate"
        else text.replace("Original evidence.", "Tampered evidence.")
    )
    cache = LazyOracleHistoryCache(tmp_path)
    cache.prepare(definition, execution_id="BX-next")
    assert (
        cache.lookup(
            OracleRequest(
                run_id="new",
                subject=subjects.subject("T-0001"),
                question="Was this person born before 1900?",
            )
        )
        is None
    )
    assert cache.loads[0].skipped_files == 1


def test_two_independent_instances_use_same_cutoff_and_read_only_sources(tmp_path):
    _, definition, subjects = seed(tmp_path)
    cutoff = timestamp()
    first = LazyOracleHistoryCache(tmp_path, before=cutoff)
    second = LazyOracleHistoryCache(tmp_path, before=cutoff)
    assert first.prepare(definition, execution_id="BX-first") == second.prepare(
        definition, execution_id="BX-second"
    )
    request = OracleRequest(
        run_id="new",
        subject=subjects.subject("T-0001"),
        question="Was this person born before 1900?",
    )
    assert first.lookup(request) == second.lookup(request)
    assert first._loaded is not second._loaded
    assert not list(tmp_path.glob("**/*cache*.db"))


def test_only_case_and_repeated_ascii_spaces_are_normalized():
    assert normalized_question("IS  This?") == "is this?"
    assert normalized_question("is this?") != normalized_question("is this")
    assert normalized_question("is\tthis?") != normalized_question("is this?")
    assert normalized_question(" is this?") != normalized_question("is this?")


@pytest.mark.parametrize("field", ["version", "hash"])
def test_mismatched_role_audit_is_not_a_cache_entry(tmp_path, field):
    import yaml

    store, definition, subjects = seed(tmp_path)
    path = store.run_root("M-0001", "BX-source") / "subjects/T-0001/trials/trial-001/result.yml"
    data = yaml.safe_load(path.read_text())
    audit = data["payload"]["result"]["audit"]["calls"][0]
    audit["reviewer"]["prompt"][field] = "different-version" if field == "version" else "f" * 64
    path.write_text(yaml.safe_dump(_signed_payload(data)))
    cache = LazyOracleHistoryCache(tmp_path)
    cache.prepare(definition, execution_id="BX-next")
    assert (
        cache.lookup(
            OracleRequest(
                run_id="new",
                subject=subjects.subject("T-0001"),
                question="Was this person born before 1900?",
            )
        )
        is None
    )


def test_actual_independent_processes_read_the_same_sources(tmp_path):
    import subprocess
    import sys

    seed(tmp_path)
    cutoff = timestamp()
    script = """
import json, sys
from pathlib import Path
from deep20_benchmark.artifacts import ArtifactStore
from deep20_benchmark.history_cache import LazyOracleHistoryCache
from deep20_oracle.models import OracleRequest
import yaml
root = Path(sys.argv[1])
manifest = ArtifactStore(root).load_manifest("M-0001", "BX-source")
trial = yaml.safe_load((root / "runs/M-0001/BX-source/subjects/T-0001/trials/trial-001/result.yml").read_text())
cache = LazyOracleHistoryCache(root, before=sys.argv[2])
snapshot = cache.prepare(manifest.definition, execution_id="BX-child")
request = OracleRequest.model_validate({"run_id": "new", "subject": trial["payload"]["result"]["run"]["subject"], "question": "Was this person born before 1900?"})
hit = cache.lookup(request)
print(json.dumps({"snapshot": snapshot.snapshot_hash, "source": hit.source.model_dump(mode="json")}))
"""
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", script, str(tmp_path), cutoff],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(2)
    ]
    results = [process.communicate(timeout=30) for process in processes]
    assert all(process.returncode == 0 for process in processes), results
    assert json.loads(results[0][0]) == json.loads(results[1][0])


@pytest.mark.parametrize("same_episode", [False, True])
def test_benchmark_persists_cache_inventory_load_counts_and_original_source(tmp_path, caplog, same_episode):
    from deep20_game.models import (
        CachedOracleMetrics,
        CallMetrics,
        EpisodeOracleCacheSource,
        TurnProgress,
    )

    store, _, subjects = seed(tmp_path)
    models, catalog, _ = fixtures()
    history = LazyOracleHistoryCache(tmp_path)

    class CachedExecutor(FakeExecutor):
        def execute(self, context, sink, observer):
            result = super().execute(context, sink, observer)
            hit = history.lookup(
                OracleRequest(
                    run_id=str(context.identity.episode_run_id),
                    subject=context.subject,
                    question="Was this person born before 1900?",
                )
            )
            assert hit is not None
            turn = ActionTurnResult(
                turn_number=1,
                action=GuesserAction(
                    action=ActionType.ASK, question=hit.source.question, name=None, description=None
                ),
                adjudication=TurnAdjudication(
                    component="oracle",
                    call_id="OC-" + "2" * 32,
                    answer=hit.adjudication.final_answer,
                    evidence=hit.result.evidence,
                    oracle_quality=hit.adjudication,
                    cache_source=hit.source,
                ),
                counted=True,
                counted_questions=1,
                guesser_call_id="GC-" + "2" * 32,
            )
            original_turn = None
            if same_episode:
                original_turn = turn.model_copy(update={
                    "adjudication": turn.adjudication.model_copy(update={
                        "call_id": hit.original_audit.call_id, "cache_source": None}),
                })
                local_source = EpisodeOracleCacheSource(
                    run_id=result.run_id, episode_id=result.episode_id,
                    target_id=context.subject.target_id, turn_number=1,
                    oracle_call_id=hit.original_audit.call_id, question=hit.source.question,
                    answered_at=hit.source.answered_at,
                )
                turn = turn.model_copy(update={"turn_number": 2, "counted_questions": 2,
                    "guesser_call_id": "GC-" + "3" * 32,
                    "adjudication": turn.adjudication.model_copy(update={"cache_source": local_source}),
                })
            observer.observe(
                TurnProgress(
                    run_id=result.run_id,
                    episode_id=result.episode_id,
                    turn=turn,
                    guesser_metrics=CallMetrics(
                        cost_usd=0,
                        latency_ms=0,
                        input_tokens=0,
                        output_tokens=0,
                        cached_input_tokens=0,
                        cache_write_tokens=0,
                        reasoning_tokens=0,
                    ),
                    adjudicator_metrics=CachedOracleMetrics(),
                )
            )
            return result.model_copy(
                update={
                    "turns": (original_turn, turn) if original_turn else (turn,),
                    "summary": result.summary.model_copy(
                        update={"ask_count": 1 + int(same_episode), "guess_count": 0,
                                "oracle_cache_hits": 1, "total_turns": 1 + int(same_episode),
                                "guesser_call_count": 1 + int(same_episode),
                                "counted_questions": 1 + int(same_episode)}
                    ),
                    "audit": EpisodeResultAudit(
                        calls=((hit.original_audit.model_copy(update={"turn_number": 1}),)
                               if same_episode else ()) + (
                            hit.original_audit.model_copy(
                                update={
                                    "call_id": turn.adjudication.call_id,
                                    "turn_number": turn.turn_number,
                                    "cache_source": turn.adjudication.cache_source,
                                }
                            ),
                        ),
                        unavailable_call_count=1 + int(same_episode),
                    ),
                }
            )

    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-cached"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        iterations_override=1,
    )
    runner = BenchmarkRunner(
        store=store,
        model_catalog=models,
        benchmark_catalog=catalog,
        subject_catalog=subjects,
        executor=CachedExecutor(),
        oracle_cache=history,
    )
    with caplog.at_level(logging.INFO, logger="deep20.benchmark"):
        result = runner.run(request)
    assert not result.outcome.has_infrastructure_failures, [
        trial.failure for subject in result.subjects for trial in subject.trials
    ]
    assert result.run.oracle_cache == history.snapshot
    assert len(result.run.oracle_cache_loads) == 2
    assert all(load.snapshot is not None for load in result.run.oracle_cache_loads)
    checkpoints = tuple(store.run_root("M-0001", "BX-cached").glob("subjects/*/oracle-history-*.json"))
    assert len(checkpoints) == 2
    text = (store.run_root("M-0001", "BX-cached") / "result.yml").read_text()
    assert (
        "oracle_cache_hits: 1" in text and "Original evidence." in text
    )
    assert "eligible_records: 1" in text and "duration_ms:" in text
    assert store.load_benchmark_result("M-0001", "BX-cached") == result
    logs = "\n".join(record.message for record in caplog.records)
    if same_episode:
        assert "answer_source=same_episode source_episode=" in logs and "source_turn=1" in logs
        assert "policy: same_episode_ask_v1" in text
    else:
        assert "answer_source=historical source_execution=BX-source source_model=M-0001 source_target=T-0001 source_trial=trial-001" in logs
        assert "source_file:" in text
    assert "Original evidence." not in logs and "OC-" not in logs
    # Completed execution resume returns the same result without another subject scan.
    assert runner.run(request) == result
    no_cache = BenchmarkRunner(
        store=store,
        model_catalog=models,
        benchmark_catalog=catalog,
        subject_catalog=subjects,
        executor=FakeExecutor(),
    )
    with pytest.raises(ValueError, match="cannot disable"):
        no_cache.run(request)


def test_episode_reuse_policy_is_frozen_on_resume(tmp_path):
    from deep20_benchmark.history_models import OracleHistorySnapshot
    from deep20_oracle.util import canonical_json, sha256_text

    store, definition, _ = seed(tmp_path)
    manifest = store.load_manifest("M-0001", "BX-source")
    assert manifest is not None
    cache = LazyOracleHistoryCache(tmp_path)
    snapshot = cache.prepare(definition, execution_id="BX-next")
    assert snapshot is not None and snapshot.episode_reuse_policy == "same_episode_ask_v1"
    unsigned = snapshot.model_dump(mode="json", exclude={"snapshot_hash", "episode_reuse_policy"})
    older = OracleHistorySnapshot.model_validate_json(canonical_json({
        **unsigned, "snapshot_hash": sha256_text(canonical_json(unsigned)),
    }))
    for original in (None, older, snapshot):
        existing = manifest.model_copy(update={"oracle_cache": original})
        resumed = LazyOracleHistoryCache(tmp_path)
        assert resumed.prepare(definition, execution_id="BX-source", existing=existing) == original
        if original is older:
            assert resumed.snapshot.episode_reuse_policy is None
