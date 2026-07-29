from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal

import pytest

from deep20_publication.cli import _read_yaml
from deep20_publication.compiler import (
    _b20_score,
    _public_run_totals,
    _rank,
    _reason_codes,
    _select_latest_qualified_runs,
    _trial,
    compile_publication,
)
from deep20_publication.loader import (
    parse_publication_config,
    parse_subject_catalog,
)
from deep20_publication.models import (
    ArtifactReference,
    BenchmarkFailure,
    BenchmarkManifestArtifact,
    BenchmarkStateArtifact,
    BenchmarkSummaryArtifact,
    CohortConfig,
    CompletedTrialSummary,
    ContractReliabilitySnapshot,
    EpisodeResultArtifact,
    LeaderboardRow,
    LoadedEpisode,
    LoadedRun,
    PartialTrialMetrics,
    PublicModel,
    PublicRun,
    PublicRunCostTotals,
    PublicRunTotals,
    PublishedDataset,
    RepairAggregateSnapshot,
    SupersededInfrastructureAttemptSnapshot,
    TrialArtifactReferences,
    TrialIdentity,
)

REPOSITORY = Path(__file__).resolve().parents[2]


def _identity() -> TrialIdentity:
    return TrialIdentity(
        execution_id="BX-test",
        model_id="M-0001",
        target_id="T-0001",
        trial_id="trial-001",
        trial_number=1,
        episode_run_id=f"BR-{'0' * 40}",
    )


def _artifacts() -> TrialArtifactReferences:
    return TrialArtifactReferences(
        trial_result=ArtifactReference(relative_path="trials/trial-001/result.yml")
    )


def _contract(
    *,
    evaluated_outputs: int = 1,
    violations: int = 0,
    counted_penalties: int = 0,
) -> ContractReliabilitySnapshot:
    valid_outputs = evaluated_outputs - violations
    return ContractReliabilitySnapshot(
        evaluated_outputs=evaluated_outputs,
        valid_outputs=valid_outputs,
        violations=violations,
        counted_penalties=counted_penalties,
        affected_trials=1 if violations else 0,
        compliance_rate=(
            Decimal(valid_outputs) / Decimal(evaluated_outputs)
            if evaluated_outputs
            else None
        ),
        status=(
            "breached"
            if violations
            else ("clean" if evaluated_outputs else "not_evaluable")
        ),
    )


def _model(model_id: str, name: str) -> PublicModel:
    return PublicModel(
        model_id=model_id,
        display_name=name,
        route="provider/model",
        provider="provider",
        reasoning_effort="default",
        seed_capability="supported",
        configuration_hash="0" * 64,
    )


def _public_run(
    *,
    model_id: str,
    execution_id: str,
    completed_at: datetime,
    penalized_score: Decimal | None,
    classification: Literal["official", "lab"] = "official",
) -> PublicRun:
    return PublicRun(
        execution_id=execution_id,
        model_id=model_id,
        model_name=model_id,
        benchmark_id="B-0001",
        benchmark_name="Benchmark",
        classification=classification,
        reason_codes=() if classification == "official" else ("experimental",),
        completed_at=completed_at,
        created_at=completed_at,
        git_commit="test",
        benchmark_mode="official" if classification == "official" else "experimental",
        target_ids=("T-0001",),
        iterations=1,
        base_seed=0,
        max_questions=50,
        success_rate=Decimal("0.5"),
        descriptive_score=penalized_score,
        descriptive_b20_score=Decimal(10) if penalized_score is not None else None,
        penalized_score=penalized_score if classification == "official" else None,
        b20_score=Decimal(10) if classification == "official" else None,
        total_cost_usd=Decimal(1),
        successful=1,
        model_failed=1,
        infrastructure_failed=0,
        terminal_trials=2,
        contract=_contract(evaluated_outputs=2),
        totals=PublicRunTotals(
            costs_usd=PublicRunCostTotals(
                guesser=Decimal(1),
                primary_oracle=Decimal(0),
                reviewer=Decimal(0),
                judge=Decimal(0),
                validator=Decimal(0),
                total=Decimal(1),
            ),
            total_tokens=100,
            runtime_ms=1_000,
            guesser_think_time_ms=500,
        ),
        subjects=(),
    )


def _recovery_policy() -> dict[str, int]:
    return {
        "max_elapsed_seconds": 300,
        "max_request_attempts": 8,
        "no_result_retries": 1,
        "invalid_output_retries": 1,
        "rate_limit_max_elapsed_seconds": 900,
        "rate_limit_max_request_attempts": 20,
        "retry_jitter_ms": 1_000,
    }


def _model_configuration(configuration_id: str) -> dict[str, object]:
    return {
        "configuration_id": configuration_id,
        "gateway": "test-gateway",
        "model": "test-provider/current-model",
        "provider": "test-provider",
        "reasoning_effort": "medium",
        "allow_fallbacks": False,
        "max_output_tokens": 4_096,
        "timeout_seconds": 120,
        "recovery": _recovery_policy(),
        "seed_capability": "supported",
        "prompt_cache": {
            "policy": "disabled",
            "control": "none",
            "minimum_cacheable_tokens": 0,
            "ttl_seconds": None,
            "input_usd_per_million": "0",
            "cached_input_usd_per_million": "0",
            "cache_write_multiplier": "1",
        },
    }


def _distribution(value: int) -> dict[str, object]:
    decimal = str(value)
    return {
        "count": 1,
        "minimum": decimal,
        "p25": decimal,
        "median": decimal,
        "p75": decimal,
        "maximum": decimal,
        "mean": decimal,
        "sample_standard_deviation": None,
    }


def _aggregate_summary() -> dict[str, object]:
    counts = {
        "scheduled": 1,
        "started": 1,
        "terminal": 1,
        "scoring_eligible": 1,
        "publication_eligible": 1,
        "successful": 1,
        "model_failed": 0,
        "infrastructure_failed": 0,
    }
    return {
        "counts": counts,
        "success_rate": "1",
        "questions_all_eligible": _distribution(1),
        "questions_successful": _distribution(1),
        "guesser_cost_usd": _distribution(0),
        "oracle_cost_usd": _distribution(0),
        "validator_cost_usd": _distribution(0),
        "cost_usd": _distribution(0),
        "total_cost_usd": "0",
        "tokens": _distribution(0),
        "cached_input_tokens": _distribution(0),
        "cache_write_tokens": _distribution(0),
        "estimated_cache_savings_usd": _distribution(0),
        "latency_ms": _distribution(0),
        "duration_ms": _distribution(0),
        "contract": _contract().model_dump(mode="json"),
        "oracle_quality": {},
        "failure_codes": [],
    }


def _qualification_context() -> tuple[LoadedRun, CohortConfig]:
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    identity = _identity()
    model = {
        "model_id": identity.model_id,
        "display_name": "Current Test Model",
        "configuration": _model_configuration(identity.model_id),
        "configuration_hash": "0" * 64,
    }
    completed_trial = CompletedTrialSummary(
        identity=identity,
        success=True,
        scoring_eligible=True,
        publication_eligible=True,
        counted_questions=1,
        contract=_contract(),
        cost_usd=Decimal(0),
        duration_ms=0,
        artifacts=_artifacts(),
    )
    summary = BenchmarkSummaryArtifact.model_validate(
        {
            "schema_version": 3,
            "execution_id": identity.execution_id,
            "benchmark_id": "B-0001",
            "display_name": "Current benchmark",
            "model": model,
            "outcome": {
                "complete": True,
                "has_infrastructure_failures": False,
                "publication_eligible": True,
            },
            "summary": _aggregate_summary(),
            "subjects": [
                {
                    "target_id": identity.target_id,
                    "display_name": "Test subject",
                    "entity_type": "thing",
                    "outcome": {
                        "complete": True,
                        "has_infrastructure_failures": False,
                    },
                    "summary": _aggregate_summary(),
                    "trials": [completed_trial.model_dump(mode="json")],
                    "result": {"relative_path": "subjects/T-0001/result.yml"},
                    "summary_markdown": {
                        "relative_path": "subjects/T-0001/summary.md"
                    },
                }
            ],
            "result": {"relative_path": "runs/M-0001/result.yml"},
            "summary_markdown": {
                "relative_path": "runs/M-0001/summary.md"
            },
        }
    )
    manifest = BenchmarkManifestArtifact.model_validate(
        {
            "schema_version": 3,
            "request": {
                "benchmark_id": "B-0001",
                "execution_id": identity.execution_id,
                "model_id": identity.model_id,
                "benchmark_mode": "official",
                "target_ids": [identity.target_id],
                "iterations_override": 1,
                "base_seed": 0,
            },
            "definition": {
                "benchmark_id": "B-0001",
                "display_name": "Current benchmark",
                "subject_ids": [identity.target_id],
                "iterations": 1,
                "game_policy": {
                    "version": 9,
                    "benchmark_mode": "official",
                    "max_questions": 50,
                    "max_consecutive_contract_violations": 5,
                    "reveal_entity_type": True,
                    "final_guess_after_limit": True,
                    "include_oracle_evidence": True,
                    "include_guesser_conversation": True,
                },
                "oracle_configuration": {},
                "validator_configuration": _model_configuration("validator"),
                "definition_hash": "1" * 64,
            },
            "model": model,
            "subject_catalog_hash": "2" * 64,
            "git_commit": "test",
            "created_at": created_at,
            "integrity_hash": "3" * 64,
        }
    )
    state = BenchmarkStateArtifact(
        execution_id=identity.execution_id,
        model_id=identity.model_id,
        status="completed",
        scheduled_trials=1,
        started_trials=1,
        terminal_trials=1,
        accumulated_cost_usd=Decimal(0),
        updated_at=created_at,
    )
    episode_result = EpisodeResultArtifact.model_validate(
        {
            "schema_version": 9,
            "run": {
                "run_id": identity.episode_run_id,
                "episode_id": f"EP-{'0' * 32}",
                "subject": {
                    "target_id": identity.target_id,
                    "canonical_name": "Test subject",
                    "aliases": [],
                    "entity_type": "thing",
                    "description": "A synthetic current-protocol subject.",
                    "reference_url": "https://example.com/subject",
                },
                "started_at": created_at,
                "completed_at": created_at,
                "duration_ms": 0,
            },
            "outcome": {
                "success": True,
                "terminal_reason": "success",
                "scoring_eligible": True,
                "publication_eligible": True,
            },
            "summary": {
                "total_turns": 1,
                "counted_questions": 1,
                "guesser_call_count": 1,
                "ask_count": 0,
                "guess_count": 1,
                "rejected_guess_count": 0,
                "oracle_unknown_count": 0,
                "oracle_quality": {},
                "contract": _contract().model_dump(mode="json"),
                "cache_status": "compliant",
                "costs_usd": {
                    "guesser": "0",
                    "oracle": "0",
                    "validator": "0",
                    "total": "0",
                },
                "tokens": {
                    "guesser": 0,
                    "oracle": 0,
                    "validator": 0,
                    "total": 0,
                },
            },
            "models": {
                "under_test": {
                    "role": "guesser",
                    "configuration_id": identity.model_id,
                    "requested_model": "test-provider/current-model",
                    "requested_provider": "test-provider",
                    "resolved_models": ["test-provider/current-model"],
                    "resolved_providers": ["test-provider"],
                    "reasoning_effort": "medium",
                    "prompt_version": "guesser-v7",
                },
                "oracle": {
                    "role": "oracle",
                    "configuration_id": None,
                    "requested_model": "test-provider/current-model",
                    "requested_provider": "test-provider",
                    "resolved_models": [],
                    "resolved_providers": [],
                    "reasoning_effort": "medium",
                    "prompt_version": "oracle-v7",
                },
                "validator": {
                    "role": "validator",
                    "configuration_id": "validator",
                    "requested_model": "test-provider/current-model",
                    "requested_provider": "test-provider",
                    "resolved_models": ["test-provider/current-model"],
                    "resolved_providers": ["test-provider"],
                    "reasoning_effort": "medium",
                    "prompt_version": "validator-v7",
                },
            },
            "turns": [
                {
                    "turn_type": "action",
                    "turn_number": 1,
                    "action": {
                        "action": "GUESS",
                        "question": None,
                        "name": "Test subject",
                        "description": "A synthetic current-protocol subject.",
                    },
                    "adjudication": {
                        "component": "guess_validator",
                        "call_id": f"VC-{'0' * 32}",
                        "answer": "YES",
                        "evidence": [],
                        "explanation": "The guess matches.",
                        "oracle_quality": None,
                    },
                    "counted": True,
                    "counted_questions": 1,
                    "guesser_call_id": f"GC-{'0' * 32}",
                }
            ],
            "guesser_conversation": [
                {
                    "role": "system",
                    "content": "SYNTHETIC_GUESSER_SYSTEM",
                },
                {
                    "role": "user",
                    "content": (
                        '{"category":"thing","event":"BEGIN",'
                        '"variation_token":"SYNTHETIC"}'
                    ),
                },
                {
                    "role": "assistant",
                    "content": (
                        '{"result":{"action":"GUESS","description":'
                        '"A synthetic current-protocol subject.",'
                        '"name":"Test subject"}}'
                    ),
                    "turn_number": 1,
                },
            ],
            "llm_details": {
                "guesser": {
                    "configuration": _model_configuration(identity.model_id),
                    "metrics": {},
                },
                "oracle": {
                    "configuration": {
                        "gateway": "test-gateway",
                        "model": "test-provider/current-model",
                        "provider": "test-provider",
                        "reasoning_effort": "medium",
                        "allow_fallbacks": False,
                        "max_output_tokens": 4_096,
                        "timeout_seconds": 120,
                        "recovery": _recovery_policy(),
                        "parallel_search": True,
                        "max_search_results": 5,
                        "reviewer": {
                            "gateway": "test-gateway",
                            "model": "test-provider/current-model",
                            "provider": "test-provider",
                            "reasoning_effort": "medium",
                            "allow_fallbacks": False,
                            "max_output_tokens": 4_096,
                            "timeout_seconds": 120,
                            "recovery": _recovery_policy(),
                        },
                        "judge": {
                            "gateway": "test-gateway",
                            "model": "test-provider/current-model",
                            "provider": "test-provider",
                            "reasoning_effort": "medium",
                            "allow_fallbacks": False,
                            "max_output_tokens": 4_096,
                            "timeout_seconds": 120,
                            "recovery": _recovery_policy(),
                        },
                    },
                    "metrics": {},
                },
                "validator": {
                    "configuration": _model_configuration("validator"),
                    "metrics": {},
                },
            },
            "failure": None,
        }
    )
    loaded = LoadedRun(
        summary=summary,
        manifest=manifest,
        state=state,
        episodes=(
            LoadedEpisode(
                identity=identity,
                result=episode_result,
                relative_path=_artifacts().trial_result.relative_path,
                integrity_hash="4" * 64,
            ),
        ),
        summary_path="synthetic/current-v7/summary.yml",
    )
    cohort = CohortConfig(
        cohort_id="test",
        display_name="Test",
        active=True,
        benchmark_id="B-0001",
        benchmark_version=9,
        target_ids=(identity.target_id,),
        iterations=1,
        base_seed=0,
        max_questions=50,
        model_ids=(identity.model_id,),
    )
    return loaded, cohort


def test_failed_completed_trial_keeps_contract_breach_and_receives_penalty() -> None:
    trial = CompletedTrialSummary(
        identity=_identity(),
        success=False,
        scoring_eligible=True,
        publication_eligible=True,
        failure=BenchmarkFailure(code="guess_rejected", type="model", message=""),
        counted_questions=7,
        contract=_contract(
            evaluated_outputs=3,
            violations=1,
            counted_penalties=1,
        ),
        cost_usd=Decimal("0.25"),
        duration_ms=100,
        artifacts=_artifacts(),
    )

    projected = _trial(
        trial,
        failure_penalty=Decimal(51),
        b20_target_questions=20,
    )

    assert projected.status == "model_failure"
    assert projected.counted_questions == 7
    assert projected.scored_questions == Decimal(51)
    assert projected.b20_score == Decimal(0)
    assert projected.contract is not None
    assert projected.contract.status == "breached"
    assert projected.contract.violations == 1


def test_successful_completed_trial_still_keeps_contract_breach() -> None:
    trial = CompletedTrialSummary(
        identity=_identity(),
        success=True,
        scoring_eligible=True,
        publication_eligible=True,
        counted_questions=30,
        contract=_contract(
            evaluated_outputs=31,
            violations=1,
            counted_penalties=1,
        ),
        cost_usd=Decimal("0.25"),
        duration_ms=100,
        artifacts=_artifacts(),
    )

    projected = _trial(
        trial,
        failure_penalty=Decimal(51),
        b20_target_questions=20,
    )

    assert projected.status == "success"
    assert projected.scored_questions == Decimal(30)
    assert projected.contract is not None
    assert projected.contract.status == "breached"
    assert projected.contract.counted_penalties == 1


def test_repair_metrics_are_typed_and_counted_without_entering_public_trials() -> None:
    loaded, _ = _qualification_context()
    superseded = SupersededInfrastructureAttemptSnapshot(
        attempt_number=1,
        failure=BenchmarkFailure(
            code="oracle_transport_failed",
            type="infrastructure",
            message="retryable failure",
        ),
        partial_metrics=PartialTrialMetrics(cost_usd=Decimal("0.1")),
        superseded_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    repair = RepairAggregateSnapshot(
        superseded_attempts=1,
        affected_trials=1,
        partial_metrics=PartialTrialMetrics(
            guesser_cost_usd=Decimal(2),
            oracle_cost_usd=Decimal(3),
            reviewer_cost_usd=Decimal(1),
            judge_cost_usd=Decimal("0.5"),
            validator_cost_usd=Decimal("0.25"),
            cost_usd=Decimal("5.25"),
            tokens=12,
        ),
    )
    aggregate = loaded.summary.summary.model_copy(
        update={
            "repair": repair,
            "total_cost_usd": Decimal("5.25"),
        }
    )
    run = loaded.model_copy(
        update={
            "summary": loaded.summary.model_copy(update={"summary": aggregate}),
        }
    )

    totals = _public_run_totals(run)

    assert totals.costs_usd.guesser == Decimal(2)
    assert totals.costs_usd.primary_oracle == Decimal("1.5")
    assert totals.costs_usd.reviewer == Decimal(1)
    assert totals.costs_usd.judge == Decimal("0.5")
    assert totals.costs_usd.validator == Decimal("0.25")
    assert totals.costs_usd.total == Decimal("5.25")
    assert totals.total_tokens == 12

    trial = loaded.summary.subjects[0].trials[0]
    assert isinstance(trial, CompletedTrialSummary)
    repaired_trial = trial.model_copy(update={"superseded_attempt_count": 1})
    projected = _trial(
        repaired_trial,
        failure_penalty=Decimal(51),
        b20_target_questions=20,
        episode=loaded.episodes[0],
    )

    assert repaired_trial.superseded_attempt_count == 1
    assert superseded.attempt_number == 1
    assert "superseded_attempt" not in projected.model_dump_json()


def test_contract_reliability_counts_are_strict() -> None:
    from pydantic import ValidationError

    try:
        ContractReliabilitySnapshot(
            evaluated_outputs=2,
            valid_outputs=2,
            violations=1,
            counted_penalties=1,
            affected_trials=1,
            compliance_rate=Decimal("0.5"),
            status="breached",
        )
    except ValidationError as error:
        assert "valid outputs plus violations" in str(error)
    else:
        raise AssertionError("inconsistent contract reliability was accepted")


def test_b20_score_is_linear_and_anchored_to_twenty_questions() -> None:
    failure_penalty = Decimal(51)

    assert _b20_score(
        Decimal(20),
        failure_penalty=failure_penalty,
        target_questions=20,
    ) == Decimal(20)
    assert _b20_score(
        Decimal(51),
        failure_penalty=failure_penalty,
        target_questions=20,
    ) == Decimal(0)
    assert _b20_score(
        Decimal(0),
        failure_penalty=failure_penalty,
        target_questions=20,
    ) == Decimal(1020) / Decimal(31)


def test_rank_preserves_exact_joint_ties_and_places_awaiting_last() -> None:
    rows = (
        LeaderboardRow(
            rank=None,
            model=_model("M-0001", "Beta"),
            status="evaluated",
            penalized_score=Decimal("12.00"),
            contract=_contract(),
        ),
        LeaderboardRow(
            rank=None,
            model=_model("M-0002", "Alpha"),
            status="evaluated",
            penalized_score=Decimal("12.00"),
            contract=_contract(),
        ),
        LeaderboardRow(
            rank=None,
            model=_model("M-0003", "Gamma"),
            status="awaiting_official_run",
        ),
    )

    ranked = _rank(rows)

    assert tuple(row.model.display_name for row in ranked) == ("Alpha", "Beta", "Gamma")
    assert tuple(row.rank for row in ranked) == (1, 1, None)


def test_latest_qualified_run_wins_without_score_selection() -> None:
    prior_better = _public_run(
        model_id="M-0001",
        execution_id="BX-prior-better",
        completed_at=datetime(2026, 1, 1, tzinfo=UTC),
        penalized_score=Decimal(5),
    )
    newer_worse = _public_run(
        model_id="M-0001",
        execution_id="BX-newer-worse",
        completed_at=datetime(2026, 1, 2, tzinfo=UTC),
        penalized_score=Decimal(30),
    )

    selected = _select_latest_qualified_runs(
        (prior_better, newer_worse),
        ("M-0001",),
    )

    assert selected == (newer_worse,)


def test_newer_unqualified_run_is_ignored_and_distinct_models_stay_distinct() -> None:
    qualified = _public_run(
        model_id="M-0001",
        execution_id="BX-qualified",
        completed_at=datetime(2026, 1, 1, tzinfo=UTC),
        penalized_score=Decimal(20),
    )
    newer_lab = _public_run(
        model_id="M-0001",
        execution_id="BX-newer-lab",
        completed_at=datetime(2026, 1, 2, tzinfo=UTC),
        penalized_score=Decimal(10),
        classification="lab",
    )
    same_route_different_id = _public_run(
        model_id="M-0002",
        execution_id="BX-other-model",
        completed_at=datetime(2026, 1, 3, tzinfo=UTC),
        penalized_score=Decimal(15),
    )

    selected = _select_latest_qualified_runs(
        (qualified, newer_lab, same_route_different_id),
        ("M-0001", "M-0002", "M-0003"),
    )

    assert selected == (qualified, same_route_different_id)


def test_latest_qualified_timestamp_tie_is_rejected() -> None:
    completed_at = datetime(2026, 1, 1, tzinfo=UTC)
    left = _public_run(
        model_id="M-0001",
        execution_id="BX-left",
        completed_at=completed_at,
        penalized_score=Decimal(10),
    )
    right = _public_run(
        model_id="M-0001",
        execution_id="BX-right",
        completed_at=completed_at,
        penalized_score=Decimal(20),
    )

    with pytest.raises(ValueError, match="official run timestamp tie"):
        _select_latest_qualified_runs((left, right), ("M-0001",))


def test_qualification_requires_full_completed_trial_coverage_only() -> None:
    loaded, cohort = _qualification_context()
    assert loaded.manifest.definition.game_policy.version == 9
    assert not _reason_codes(loaded, cohort)

    changed_metadata = loaded.model_copy(
        update={
            "manifest": loaded.manifest.model_copy(
                update={
                    "request": loaded.manifest.request.model_copy(
                        update={
                            "benchmark_id": "B-9999",
                            "base_seed": loaded.manifest.request.base_seed + 1,
                        }
                    ),
                    "model": loaded.manifest.model.model_copy(
                        update={
                            "configuration": (
                                loaded.manifest.model.configuration.model_copy(
                                    update={
                                        "max_output_tokens": (
                                            loaded.manifest.model.configuration.max_output_tokens
                                            + 1
                                        )
                                    }
                                )
                            )
                        }
                    ),
                }
            )
        }
    )
    assert not _reason_codes(changed_metadata, cohort)

    first_subject = loaded.summary.subjects[0]
    first_trial = first_subject.trials[0]
    assert isinstance(first_trial, CompletedTrialSummary)
    cache_flagged_run = loaded.model_copy(
        update={
            "summary": loaded.summary.model_copy(
                update={
                    "outcome": loaded.summary.outcome.model_copy(
                        update={"publication_eligible": False}
                    ),
                    "subjects": (
                        first_subject.model_copy(
                            update={
                                "trials": (
                                    first_trial.model_copy(
                                        update={"publication_eligible": False}
                                    ),
                                    *first_subject.trials[1:],
                                )
                            }
                        ),
                        *loaded.summary.subjects[1:],
                    ),
                }
            )
        }
    )
    assert not _reason_codes(cache_flagged_run, cohort)

    missing_trial = loaded.model_copy(
        update={
            "summary": loaded.summary.model_copy(
                update={
                    "subjects": (
                        first_subject.model_copy(
                            update={"trials": first_subject.trials[:-1]}
                        ),
                        *loaded.summary.subjects[1:],
                    )
                }
            )
        }
    )
    assert _reason_codes(missing_trial, cohort) == ("trial_coverage_mismatch",)

    running = loaded.model_copy(
        update={
            "state": loaded.state.model_copy(update={"status": "running"})
        }
    )
    assert _reason_codes(running, cohort) == ("incomplete",)


def test_compiler_uses_run_model_metadata_and_requires_all_trials() -> None:
    loaded, cohort = _qualification_context()
    config = parse_publication_config(
        _read_yaml(REPOSITORY / "publication" / "publication.yml"),
        "publication.yml",
    )
    config = config.model_copy(update={"cohorts": (cohort,)})
    subjects, subject_catalog_hash = parse_subject_catalog(
        _read_yaml(REPOSITORY / "config" / "subjects.yaml"),
        "subjects.yaml",
    )
    first_subject = loaded.summary.subjects[0]
    removed_trial = first_subject.trials[-1]
    unqualified = loaded.model_copy(
        update={
            "summary": loaded.summary.model_copy(
                update={
                    "subjects": (
                        first_subject.model_copy(
                            update={"trials": first_subject.trials[:-1]}
                        ),
                        *loaded.summary.subjects[1:],
                    )
                }
            ),
            "episodes": tuple(
                episode
                for episode in loaded.episodes
                if (
                    episode.identity.target_id,
                    episode.identity.trial_id,
                )
                != (
                    removed_trial.identity.target_id,
                    removed_trial.identity.trial_id,
                )
            ),
        }
    )

    dataset = compile_publication(
        runs=(unqualified, loaded),
        config=config,
        subject_catalog=subjects,
        subject_catalog_hash=subject_catalog_hash,
    )

    assert tuple(model.model_id for model in dataset.models) == ("M-0001",)
    assert tuple(row.status for row in dataset.leaderboard) == ("evaluated",)
    assert len(dataset.official_runs) == 1
    assert dataset.official_runs[0].execution_id == loaded.summary.execution_id
    assert dataset.official_runs[0].totals.total_tokens == 0
    assert dataset.official_runs[0].totals.guesser_think_time_ms == 0
    assert dataset.official_runs[0].totals.costs_usd.total == Decimal(0)
    assert dataset.lab_runs == ()
    assert dataset.provenance.source_run_count == 2
    assert dataset.provenance.official_run_count == 1
    assert dataset.provenance.lab_run_count == 0
    assert dataset.models[0].configuration_hash == (
        loaded.manifest.model.configuration_hash
    )
    episode = dataset.official_runs[0].subjects[0].trials[0].episode
    assert episode is not None
    assert episode.oracle_support.reviewer.requested_model == (
        "test-provider/current-model"
    )
    assert episode.oracle_support.judge.requested_model == "test-provider/current-model"
    assert episode.oracle_support.reviewer.calls == 0
    assert episode.oracle_support.judge.calls == 0
    assert episode.guesser_disclosure is not None
    assert episode.guesser_disclosure.system_message == "SYNTHETIC_GUESSER_SYSTEM"
    assert episode.guesser_disclosure.begin_message.startswith(
        '{"category":"thing","event":"BEGIN"'
    )
    assert episode.turns[0].turn_type == "action"
    assert episode.turns[0].recorded_output == (
        '{"result":{"action":"GUESS","description":'
        '"A synthetic current-protocol subject.","name":"Test subject"}}'
    )


def test_subject_catalog_hash_matches_benchmark_producer_contract() -> None:
    subject_path = REPOSITORY / "config" / "subjects.yaml"
    _, subject_hash = parse_subject_catalog(_read_yaml(subject_path), str(subject_path))

    assert subject_hash == "2cb28dee2ab7639a755940e30525b011f5683d3971fcc0d70bcb7cdd29baea0a"


def test_publication_and_report_ui_have_no_execution_component_imports() -> None:
    source_roots = (
        REPOSITORY / "publication" / "src",
        REPOSITORY / "publication" / "site" / "src",
    )
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for source_root in source_roots
        for suffix in ("*.py", "*.ts", "*.astro")
        for path in sorted(source_root.rglob(suffix))
    )

    assert "deep20_game" not in source
    assert "deep20_oracle" not in source
    assert "deep20_benchmark" not in source
    assert "OPENROUTER_API_KEY" not in source

    execution_source = "\n".join(
        path.read_text(encoding="utf-8")
        for source_root in (
            REPOSITORY / "benchmark" / "src",
            REPOSITORY / "game" / "src",
            REPOSITORY / "oracle" / "src",
        )
        for path in sorted(source_root.rglob("*.py"))
    )
    assert "deep20_publication" not in execution_source

    report_source = "\n".join(
        path.read_text(encoding="utf-8")
        for suffix in ("*.ts", "*.astro")
        for path in sorted((REPOSITORY / "publication" / "site" / "src").rglob(suffix))
    )
    assert "guesser_conversation" not in report_source
    assert "subject_snapshot" not in report_source
    assert "system_instructions" not in report_source
    assert "variation_token" not in report_source
    assert "clean_worktree" not in report_source
    assert "dirty_worktree" not in report_source
    assert "Model broke the output contract." in report_source
    assert "Contract compliance" in report_source
    assert "Awaiting official run" not in report_source
    assert "Earlier official runs" not in report_source
    assert not (REPOSITORY / "publication" / "site" / "src" / "pages" / "lab.astro").exists()

    route_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(
            (REPOSITORY / "publication" / "site" / "src" / "pages" / "runs").rglob(
                "*.astro"
            )
        )
    )
    assert "dataset.lab_runs" not in route_source

    public_schema = json.dumps(PublishedDataset.model_json_schema(), sort_keys=True)
    assert "guesser_disclosure" in public_schema
    assert "recorded_output" in public_schema
    for forbidden_field in (
        "guesser_conversation",
        "subject_snapshot",
        "system_instructions",
        "variation_token",
        "raw_response",
        "oracle_raw_response",
        "oracle_search_results",
        "reviewer_answer",
        "judge_answer",
        "provider_trace",
        "session_id",
        "cache_key",
    ):
        assert forbidden_field not in public_schema


def test_report_cost_labels_define_episode_and_run_scope() -> None:
    pages = REPOSITORY / "publication" / "site" / "src" / "pages"
    episode_source = (
        pages
        / "runs"
        / "[execution_id]"
        / "subjects"
        / "[target_id]"
        / "episodes"
        / "[trial_id].astro"
    ).read_text(encoding="utf-8")
    subject_source = (
        pages / "runs" / "[execution_id]" / "subjects" / "[target_id]" / "index.astro"
    ).read_text(encoding="utf-8")
    run_source = (pages / "runs" / "[execution_id]" / "index.astro").read_text(
        encoding="utf-8"
    )
    leaderboard_source = (pages / "index.astro").read_text(encoding="utf-8")

    assert "Episode cost" in episode_source
    assert "All {episode.total_turns} turns" in episode_source
    assert "Full run {money(run.total_cost_usd)}" in episode_source
    assert 'role: "Judge"' in episode_source
    assert "Oracle support role breakdown" in episode_source
    assert "Exact Guesser setup" in episode_source
    assert "Recorded Guesser output" in episode_source
    assert "Original provider bytes and hidden reasoning are not retained." in (
        episode_source
    )
    assert "<th>Latency (s)</th>" in episode_source
    assert "seconds(row.values.latency_ms)" in episode_source
    assert "`Q${turn.counted_questions}`" in episode_source
    assert "No question charge" in episode_source
    assert "counted question ${turn.counted_questions}" not in episode_source
    assert "Episode cost" in subject_source
    assert "<dt>Run cost</dt>" not in run_source
    assert "Total benchmark cost" in run_source
    assert "Model cost" in run_source
    assert "cost-row-guesser" in run_source
    assert 'variant="hero"' in run_source
    assert 'class="run-facts"' in run_source
    assert "Full run totals." in run_source
    assert "Guesser think time" in run_source
    assert "Primary Oracle" in run_source
    assert "run.totals.total_tokens" in run_source
    assert "run.totals.guesser_think_time_ms" in run_source
    assert "Run cost" in leaderboard_source


def test_generated_homepage_matches_the_official_result_state() -> None:
    dataset_path = (
        REPOSITORY
        / "publication"
        / "site"
        / "public"
        / "data"
        / "deep20bench-v3.json"
    )
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    evaluated = [
        row for row in dataset["leaderboard"] if row["status"] == "evaluated"
    ]
    homepage = (REPOSITORY / "docs" / "index.html").read_text(encoding="utf-8")

    assert "Can an LLM ask its way to the answer?" in homepage
    assert "Simple rules. Several abilities." in homepage
    assert "The same game, made comparable." in homepage
    if evaluated:
        assert 'class="data-table leaderboard-table"' in homepage
        assert "Official comparison in progress." not in homepage
    else:
        assert "Official comparison in progress." in homepage
        assert 'class="data-table leaderboard-table"' not in homepage


def test_homepage_and_story_share_one_typed_illustrative_round() -> None:
    source_root = REPOSITORY / "publication" / "site" / "src"
    shared_round = (
        source_root / "lib" / "illustrative-round.ts"
    ).read_text(encoding="utf-8")
    homepage = (source_root / "pages" / "index.astro").read_text(encoding="utf-8")
    story = (source_root / "pages" / "story.astro").read_text(encoding="utf-8")

    assert "satisfies IllustrativeRound" in shared_round
    assert 'from "../lib/illustrative-round"' in homepage
    assert 'from "../lib/illustrative-round"' in story
