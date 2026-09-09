"""Offline coverage of live cache growth, restart, compatibility and provenance."""

from __future__ import annotations

import json

import pytest
from deep20_benchmark.artifacts import ArtifactStore
from deep20_benchmark.history_cache import LazyOracleHistoryCache
from deep20_benchmark.history_models import OracleHistorySnapshot
from deep20_benchmark.models import (
    BenchmarkExecutionId,
    BenchmarkId,
    BenchmarkModelId,
    BenchmarkRequest,
    CompletedTrialResult,
    TrialRepairPolicy,
)
from deep20_benchmark.runner import BenchmarkRunner
from deep20_game.config import BenchmarkMode
from deep20_game.models import EpisodeResultAudit
from deep20_oracle.models import (
    OracleAdjudication,
    OracleAnswer,
    OracleDecisionPath,
    OracleRequest,
    OracleResearchOutcome,
    OracleResearchResolution,
    OracleResearchStrategy,
)
from deep20_oracle.util import canonical_json, sha256_text
from test_history_cache import seed
from test_runner import FakeExecutor, fixtures

QUESTION = "Was this person born before 1900?"


def original_trial(store):
    manifest = store.load_manifest("M-0001", "BX-source")
    trial = store.load_benchmark_result("M-0001", "BX-source").subjects[0].trials[0]
    assert manifest is not None and isinstance(trial, CompletedTrialResult)
    original = store.load_trial_result(trial.identity)
    assert isinstance(original, CompletedTrialResult)
    return manifest, original


def test_current_answers_survive_between_games_and_restore_from_verified_trials(tmp_path):
    store, definition, subjects = seed(tmp_path)
    manifest, trial = original_trial(store)
    cache = LazyOracleHistoryCache(tmp_path, before="2026-07-26T00:00:00+00:00")
    snapshot = cache.prepare(definition, execution_id="BX-source")
    assert snapshot is not None and not snapshot.sources
    assert snapshot.execution_reuse_policy == "same_execution_ask_v1"
    request = OracleRequest(run_id="next-game", subject=subjects.subject("T-0001"), question=QUESTION)
    assert cache.lookup(request) is None  # Even an already-loaded empty subject gets new entries.
    path = store.trial_root(trial.identity) / "result.yml"
    unchanged = path.read_bytes()
    cache.remember_completed_trial(trial.identity, path)
    hit = cache.lookup(request.model_copy(update={"question": QUESTION.upper().replace(" ", "  ")}))
    assert hit is not None and hit.source.policy == "same_execution_ask_v1"
    assert hit.source.execution_id == "BX-source" and hit.source.trial_id == "trial-001"
    assert hit.source.oracle_call_id == trial.result.turns[0].adjudication.call_id
    assert hit.source.source_integrity_hash in path.read_text()
    assert hit.source.question == QUESTION
    assert hit.result.evidence == trial.result.turns[0].adjudication.evidence
    assert cache.lookup(request.model_copy(update={"subject": subjects.subject("T-0002")})) is None
    changed = request.subject.model_copy(update={"description": "Changed trusted description."})
    assert cache.lookup(request.model_copy(update={"subject": changed})) is None
    assert cache.lookup(request.model_copy(update={"question": QUESTION + "!"})) is None

    resumed = LazyOracleHistoryCache(tmp_path)
    resumed.prepare(definition, execution_id="BX-source",
                    existing=manifest.model_copy(update={"oracle_cache": snapshot}))
    assert resumed.lookup(request) is None
    resumed.remember_completed_trial(trial.identity, path)
    assert resumed.lookup(request) == hit
    assert path.read_bytes() == unchanged
    with pytest.raises(ValueError, match="another execution"):
        resumed.remember_completed_trial(trial.identity.model_copy(
            update={"execution_id": BenchmarkExecutionId("BX-other")}), path)


@pytest.mark.parametrize("damage", [
    "integrity", "duplicate", "missing_audit", "missing_reviewer", "prompt", "config",
    "routing", "infrastructure", "contract_revision", "reused",
])
def test_ineligible_current_answers_do_not_seed_later_games(tmp_path, damage):
    store, definition, subjects = seed(tmp_path)
    _, trial = original_trial(store)
    cache = LazyOracleHistoryCache(tmp_path)
    cache.prepare(definition, execution_id="BX-source")
    path = store.trial_root(trial.identity) / "result.yml"
    episode = trial.result
    audit = episode.audit.calls[0]
    if damage == "integrity":
        path.write_text(path.read_text().replace("Original evidence.", "Tampered evidence."))
    elif damage == "duplicate":
        path.write_text(path.read_text() + "\nintegrity_hash: duplicate\n")
    elif damage == "contract_revision":
        pass
    else:
        if damage == "missing_audit":
            episode = episode.model_copy(update={"audit": None})
        elif damage == "missing_reviewer":
            audit = audit.model_copy(update={"reviewer": None})
        elif damage == "prompt":
            oracle = audit.oracle.model_copy(update={"prompt": audit.oracle.prompt.model_copy(
                update={"hash": "f" * 64})})
            audit = audit.model_copy(update={"oracle": oracle, "research": None})
        elif damage == "config":
            episode = episode.model_copy(update={"llm_details": episode.llm_details.model_copy(
                update={"oracle": episode.llm_details.oracle.model_copy(update={
                    "configuration": definition.oracle_configuration.model_copy(
                        update={"max_output_tokens": 999})})})})
        elif damage == "routing":
            trial = trial.model_copy(update={"oracle_judge_ignored_providers": ("excluded",)})
        elif damage == "infrastructure":
            episode = episode.model_copy(update={"outcome": episode.outcome.model_copy(
                update={"scoring_eligible": False})})
        elif damage == "reused":
            cache.remember_completed_trial(trial.identity, path)
            hit = cache.lookup(OracleRequest(run_id="next", subject=episode.subject, question=QUESTION))
            assert hit is not None
            source = hit.source
            episode = episode.model_copy(update={
                "turns": (episode.turns[0].model_copy(update={"adjudication":
                    episode.turns[0].adjudication.model_copy(update={"cache_source": source})}),),
                "summary": episode.summary.model_copy(update={"oracle_cache_hits": 1}),
            })
            audit = audit.model_copy(update={"cache_source": source})
            cache.prepare(definition, execution_id="BX-source")
        if damage != "missing_audit":
            episode = episode.model_copy(update={"audit": episode.audit.model_copy(
                update={"calls": (audit,)})})
        store.write_trial_result(trial.model_copy(update={"result": episode}))
    cache.remember_completed_trial(trial.identity, path,
        contract_since="2026-09-08T00:00:00+00:00" if damage == "contract_revision" else None)
    assert cache.lookup(OracleRequest(run_id="next", subject=subjects.subject("T-0001"),
                                     question=QUESTION)) is None


def test_current_conflict_stays_disabled_after_another_matching_answer(tmp_path):
    store, definition, subjects = seed(tmp_path)
    _, first = original_trial(store)
    cache = LazyOracleHistoryCache(tmp_path)
    cache.prepare(definition, execution_id="BX-source")
    request = OracleRequest(run_id="next", subject=subjects.subject("T-0001"), question=QUESTION)
    path = store.trial_root(first.identity) / "result.yml"
    cache.remember_completed_trial(first.identity, path)
    assert cache.lookup(request) is not None
    turn = first.result.turns[0]
    quality = turn.adjudication.oracle_quality
    quality = quality.model_copy(update={"oracle_answer": OracleAnswer.NO,
        "final_answer": OracleAnswer.NO,
        "reviewer": quality.reviewer.model_copy(update={"answer": OracleAnswer.NO})})
    turn = turn.model_copy(update={"adjudication": turn.adjudication.model_copy(
        update={"answer": OracleAnswer.NO, "oracle_quality": quality})})
    conflicting = first.model_copy(update={"result": first.result.model_copy(update={"turns": (turn,)})})
    store.write_trial_result(conflicting)
    cache.remember_completed_trial(conflicting.identity, path)
    assert cache.lookup(request) is None
    store.write_trial_result(first)
    cache.remember_completed_trial(first.identity, path)
    assert cache.lookup(request) is None


@pytest.mark.parametrize("resolution", [
    OracleResearchResolution.GENUINE_UNKNOWN_PRIMARY,
    OracleResearchResolution.RETRIEVAL_EXHAUSTED_UNKNOWN,
    OracleResearchResolution.BOUNDED_UNKNOWN,
])
def test_only_semantic_unknown_is_reused(tmp_path, resolution):
    store, definition, _ = seed(tmp_path)
    _, trial = original_trial(store)
    episode = trial.result
    original = episode.audit.calls[0]
    semantic = resolution is OracleResearchResolution.GENUINE_UNKNOWN_PRIMARY
    attempt = original.research.attempts[0].model_copy(update={
        "evidence_count": 0, "outcome": OracleResearchOutcome.AMBIGUOUS_QUESTION if semantic
        else OracleResearchOutcome.NO_RESULTS,
    })
    attempts = (attempt,)
    if resolution is OracleResearchResolution.RETRIEVAL_EXHAUSTED_UNKNOWN:
        from deep20_oracle.prompt import prompt_hash, render_messages, research_prompt_version
        request = OracleRequest(run_id=episode.run_id, subject=episode.subject, question=QUESTION)
        strategy = OracleResearchStrategy.DIVERSIFIED_RECOVERY
        attempts += (attempt.model_copy(update={"attempt_number": 2, "strategy": strategy,
            "prompt": attempt.prompt.model_copy(update={"version": research_prompt_version(strategy),
                "hash": prompt_hash(render_messages(request, strategy=strategy))})}),)
    audit = original.model_copy(update={"reviewer": None,
        "research": original.research.model_copy(update={"resolution": resolution, "attempts": attempts})})
    quality = OracleAdjudication(oracle_answer=OracleAnswer.UNKNOWN, final_answer=OracleAnswer.UNKNOWN,
        disagreement=False, judge_invoked=False, decision_path=OracleDecisionPath.ORACLE_UNKNOWN)
    turn = episode.turns[0].model_copy(update={"adjudication":
        episode.turns[0].adjudication.model_copy(update={"answer": OracleAnswer.UNKNOWN,
            "evidence": (), "oracle_quality": quality})})
    trial = trial.model_copy(update={"result": episode.model_copy(update={"turns": (turn,),
        "audit": episode.audit.model_copy(update={"calls": (audit,)})})})
    store.write_trial_result(trial)
    cache = LazyOracleHistoryCache(tmp_path)
    cache.prepare(definition, execution_id="BX-source")
    cache.remember_completed_trial(trial.identity, store.trial_root(trial.identity) / "result.yml")
    hit = cache.lookup(OracleRequest(run_id="next", subject=episode.subject, question=QUESTION))
    assert (hit is not None) is semantic


def test_older_manifests_keep_original_reuse_policy_and_hash(tmp_path):
    store, definition, _ = seed(tmp_path)
    manifest, trial = original_trial(store)
    snapshot = LazyOracleHistoryCache(tmp_path).prepare(definition, execution_id="BX-source")
    unsigned = snapshot.model_dump(mode="json", exclude={"snapshot_hash", "execution_reuse_policy"})
    original = {**unsigned, "snapshot_hash": sha256_text(canonical_json(unsigned))}
    older = OracleHistorySnapshot.model_validate_json(json.dumps(original))
    assert older.model_dump(mode="json") == original
    for policy in (None, older):
        cache = LazyOracleHistoryCache(tmp_path)
        assert cache.prepare(definition, execution_id="BX-source",
            existing=manifest.model_copy(update={"oracle_cache": policy})) == policy
        cache.remember_completed_trial(trial.identity, store.trial_root(trial.identity) / "result.yml")
        assert cache.lookup(OracleRequest(run_id="next", subject=trial.result.subject,
                                         question=QUESTION)) is None


@pytest.mark.parametrize("restart", [False, True])
def test_runner_reuses_across_three_repetitions_and_after_repair(tmp_path, restart):
    template_store, _, _ = seed(tmp_path / "fixtures")
    _, template = original_trial(template_store)
    models, catalog, subjects = fixtures()
    store = ArtifactStore(tmp_path / "run")
    store._git = lambda arguments: "abc123"
    misses = []

    class RepeatingExecutor(FakeExecutor):
        def execute(self, context, sink, observer):
            result = super().execute(context, sink, observer)
            request = OracleRequest(run_id=result.run_id, subject=context.subject, question=QUESTION)
            hit = cache.lookup(request)
            if hit is None:
                misses.append(context.identity)
            turn = template.result.turns[0]
            audit = template.result.audit.calls[0]
            # The first subject's fully audited live fixture is also used in a second
            # subject's live response, with its actual blind prompt hashes.
            from deep20_oracle.models import EvidenceReviewRequest, OracleRole
            from deep20_oracle.prompt import (
                prompt_hash,
                render_evidence_review_messages,
                render_messages,
            )
            primary = audit.oracle.model_copy(update={"prompt": audit.oracle.prompt.model_copy(
                update={"hash": prompt_hash(render_messages(request))})})
            reviewer = audit.reviewer.model_copy(update={"prompt": audit.reviewer.prompt.model_copy(
                update={"hash": prompt_hash(render_evidence_review_messages(EvidenceReviewRequest(
                    subject=context.subject, question=QUESTION, evidence=turn.adjudication.evidence),
                    role=OracleRole.REVIEWER))})})
            audit = audit.model_copy(update={"oracle": primary, "reviewer": reviewer,
                "research": audit.research.model_copy(update={"attempts": (
                    audit.research.attempts[0].model_copy(update={"prompt": primary.prompt}),)})})
            source = hit.source if hit else None
            turn = turn.model_copy(update={"adjudication": turn.adjudication.model_copy(
                update={"cache_source": source})})
            audit = (hit.original_audit if hit else audit).model_copy(update={"cache_source": source})
            return result.model_copy(update={"turns": (turn,),
                "summary": result.summary.model_copy(update={"ask_count": 1, "guess_count": 0,
                    "counted_questions": 1, "oracle_cache_hits": int(hit is not None)}),
                "audit": EpisodeResultAudit(calls=(audit,), unavailable_call_count=1)})

    request = BenchmarkRequest(benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-repetitions"), model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL, iterations_override=3)

    def runner(executor):
        return BenchmarkRunner(store=store, model_catalog=models, benchmark_catalog=catalog,
                               subject_catalog=subjects, executor=executor, oracle_cache=cache)

    cache = LazyOracleHistoryCache(tmp_path / "run")
    if restart:
        with pytest.raises(KeyboardInterrupt):
            runner(RepeatingExecutor(interrupt_call=2)).run(request)
        cache = LazyOracleHistoryCache(tmp_path / "run")
    result = runner(RepeatingExecutor()).run(request,
        repair=TrialRepairPolicy() if restart else None)
    assert not result.outcome.has_infrastructure_failures
    assert len(misses) == 2  # One fresh adjudication per subject, not six.
    for subject in result.subjects:
        first, second, third = subject.trials
        assert [trial.result.summary.oracle_cache_hits for trial in subject.trials] == [0, 1, 1]
        for reused in (second, third):
            source = reused.result.turns[0].adjudication.cache_source
            assert source.policy == "same_execution_ask_v1"
            assert source.execution_id == str(request.execution_id)
            assert source.trial_id == str(first.identity.trial_id)
            assert source.episode_id == first.result.episode_id
    assert store.load_benchmark_result("M-0001", "BX-repetitions") == result
