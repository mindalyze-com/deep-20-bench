from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Literal

import pytest

from deep20_publication.cli import _load_run, _read_json, _read_yaml
from deep20_publication.compiler import (
    _average,
    _public_run_comparison,
    _public_run_totals,
    _rank,
    _rank_efficiency,
    _reason_codes,
    _select_latest_qualified_runs,
    _trial,
    compile_publication,
)
from deep20_publication.loader import (
    parse_guesser_violation_snapshot,
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
    ModelConfigurationSnapshot,
    PartialTrialMetrics,
    PublicModel,
    PublicRun,
    PublicRunComparison,
    PublicRunCostTotals,
    PublicRunModel,
    PublicRunTotals,
    PublishedDataset,
    RepairAggregateSnapshot,
    SupersededInfrastructureAttemptSnapshot,
    TrialArtifactReferences,
    TrialIdentity,
)

REPOSITORY = Path(__file__).resolve().parents[4]
SITE_SOURCE = REPOSITORY / "source" / "publication" / "site" / "src"


def _site_styles_source() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8") for path in sorted((SITE_SOURCE / "styles").glob("*.css"))
    )


def _episode_source() -> str:
    paths = (
        SITE_SOURCE / "views" / "EpisodeView.vue",
        *sorted((SITE_SOURCE / "components" / "episode").glob("*.vue")),
    )
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def _run_source() -> str:
    paths = (
        SITE_SOURCE / "views" / "workspace" / "RunOverviewPane.vue",
        *sorted((SITE_SOURCE / "components" / "run").glob("*.vue")),
    )
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


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
            Decimal(valid_outputs) / Decimal(evaluated_outputs) if evaluated_outputs else None
        ),
        status=("breached" if violations else ("clean" if evaluated_outputs else "not_evaluable")),
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
    question_score: Decimal | None,
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
        question_score=question_score if classification == "official" else None,
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
            guesser_calls=10,
        ),
        comparison=PublicRunComparison(
            guesser_cost_per_episode_usd=Decimal("0.5"),
            full_cost_per_episode_usd=Decimal("0.5"),
            support_cost_per_episode_usd=Decimal(0),
            support_cost_share=Decimal(0),
            runtime_per_episode_ms=Decimal(500),
            guesser_think_time_per_episode_ms=Decimal(250),
            guesser_latency_per_call_ms=Decimal(50),
            cost_adjusted_question_score=(
                question_score * Decimal("0.5")
                if classification == "official" and question_score is not None
                else None
            ),
            efficiency_status=(
                "ranked"
                if classification == "official" and question_score is not None
                else "question_score_unavailable"
            ),
        ),
        models=(),
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


def test_model_configuration_accepts_json_object_output_mode() -> None:
    payload = _model_configuration("M-0017")
    payload["structured_output_mode"] = "json_object"

    configuration = ModelConfigurationSnapshot.model_validate(payload)

    assert configuration.structured_output_mode == "json_object"


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
                    "summary_markdown": {"relative_path": "subjects/T-0001/summary.md"},
                }
            ],
            "result": {"relative_path": "runs/M-0001/result.yml"},
            "summary_markdown": {"relative_path": "runs/M-0001/summary.md"},
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
                        '{"category":"thing","event":"BEGIN","variation_token":"SYNTHETIC"}'
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
                    "provider_usage": {
                        "providers": [
                            {
                                "provider": "test-provider",
                                "calls": 1,
                                "cost_usd": "0.01",
                                "latency_ms": 1_000,
                            }
                        ]
                    },
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
                    "provider_usage": {
                        "providers": [
                            {
                                "provider": "test-provider",
                                "calls": 1,
                                "cost_usd": "0.02",
                                "latency_ms": 2_000,
                            }
                        ],
                        "fallback_calls": 1,
                    },
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
                artifacts=_artifacts(),
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
    )

    assert projected.status == "model_failure"
    assert projected.counted_questions == 7
    assert projected.penalized_questions == Decimal(51)
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
    )

    assert projected.status == "success"
    assert projected.penalized_questions == Decimal(30)
    assert projected.contract is not None
    assert projected.contract.status == "breached"
    assert projected.contract.counted_penalties == 1


def test_repair_metrics_are_excluded_from_public_costs_and_trials() -> None:
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

    assert run.summary.summary.total_cost_usd == Decimal("5.25")
    assert totals.costs_usd.guesser == Decimal(0)
    assert totals.costs_usd.primary_oracle == Decimal(0)
    assert totals.costs_usd.reviewer == Decimal(0)
    assert totals.costs_usd.judge == Decimal(0)
    assert totals.costs_usd.validator == Decimal(0)
    assert totals.costs_usd.total == Decimal(0)
    assert totals.excluded_repair.cost_usd == Decimal("5.25")
    assert totals.excluded_repair.superseded_attempts == 1
    assert totals.excluded_repair.affected_trials == 1
    assert totals.total_tokens == 0

    trial = loaded.summary.subjects[0].trials[0]
    assert isinstance(trial, CompletedTrialSummary)
    repaired_trial = trial.model_copy(update={"superseded_attempt_count": 1})
    projected = _trial(
        repaired_trial,
        failure_penalty=Decimal(51),
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


def test_average_uses_exact_decimal_values() -> None:
    assert _average((Decimal(51), Decimal(4), Decimal(10), Decimal(8), Decimal(7))) == Decimal(16)
    assert _average((Decimal(51), Decimal(4), Decimal(10), Decimal(8))) == Decimal("18.25")


def test_rank_preserves_exact_joint_ties_and_places_awaiting_last() -> None:
    rows = (
        LeaderboardRow(
            rank=None,
            model=_model("M-0001", "Beta"),
            status="evaluated",
            question_score=Decimal("12.00"),
            contract=_contract(),
        ),
        LeaderboardRow(
            rank=None,
            model=_model("M-0002", "Alpha"),
            status="evaluated",
            question_score=Decimal("12.00"),
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


def test_run_comparison_uses_terminal_episode_and_guesser_cost_basis() -> None:
    comparison = _public_run_comparison(
        totals=PublicRunTotals(
            costs_usd=PublicRunCostTotals(
                guesser=Decimal(2),
                primary_oracle=Decimal(1),
                reviewer=Decimal("0.5"),
                judge=Decimal("0.25"),
                validator=Decimal("0.25"),
                total=Decimal(4),
            ),
            total_tokens=1_000,
            runtime_ms=20_000,
            guesser_think_time_ms=8_000,
            guesser_calls=20,
        ),
        terminal_trials=10,
        question_score=Decimal("12.5"),
    )

    assert comparison.guesser_cost_per_episode_usd == Decimal("0.2")
    assert comparison.full_cost_per_episode_usd == Decimal("0.4")
    assert comparison.support_cost_per_episode_usd == Decimal("0.2")
    assert comparison.support_cost_share == Decimal("0.5")
    assert comparison.runtime_per_episode_ms == Decimal(2_000)
    assert comparison.guesser_think_time_per_episode_ms == Decimal(800)
    assert comparison.guesser_latency_per_call_ms == Decimal(400)
    assert comparison.cost_adjusted_question_score == Decimal("2.50")
    assert comparison.efficiency_status == "ranked"


def test_run_comparison_does_not_treat_zero_recorded_cost_as_free() -> None:
    comparison = _public_run_comparison(
        totals=PublicRunTotals(
            costs_usd=PublicRunCostTotals(
                guesser=Decimal(0),
                primary_oracle=Decimal(0),
                reviewer=Decimal(0),
                judge=Decimal(0),
                validator=Decimal(0),
                total=Decimal(0),
            ),
            total_tokens=10,
            runtime_ms=100,
            guesser_think_time_ms=50,
            guesser_calls=1,
        ),
        terminal_trials=1,
        question_score=Decimal(10),
    )

    assert comparison.efficiency_status == "recorded_guesser_cost_unavailable"
    assert comparison.cost_adjusted_question_score is None


def test_efficiency_rank_and_pareto_efficiency_are_independent_of_question_rank() -> None:
    rows = (
        LeaderboardRow(
            rank=1,
            model=_model("M-0001", "Quality"),
            status="evaluated",
            question_score=Decimal(10),
            guesser_cost_per_episode_usd=Decimal("0.10"),
            cost_adjusted_question_score=Decimal("1.0"),
            efficiency_status="ranked",
        ),
        LeaderboardRow(
            rank=2,
            model=_model("M-0002", "Value"),
            status="evaluated",
            question_score=Decimal(12),
            guesser_cost_per_episode_usd=Decimal("0.05"),
            cost_adjusted_question_score=Decimal("0.6"),
            efficiency_status="ranked",
        ),
        LeaderboardRow(
            rank=3,
            model=_model("M-0003", "Dominated"),
            status="evaluated",
            question_score=Decimal(14),
            guesser_cost_per_episode_usd=Decimal("0.20"),
            cost_adjusted_question_score=Decimal("2.8"),
            efficiency_status="ranked",
        ),
    )

    ranked = _rank_efficiency(rows)
    by_id = {row.model.model_id: row for row in ranked}

    assert by_id["M-0002"].efficiency_rank == 1
    assert by_id["M-0001"].efficiency_rank == 2
    assert by_id["M-0003"].efficiency_rank == 3
    assert by_id["M-0001"].ideal_distance_rank == 1
    assert by_id["M-0002"].ideal_distance_rank == 2
    assert by_id["M-0003"].ideal_distance_rank == 3
    assert by_id["M-0002"].product_efficiency_rank == 1
    assert by_id["M-0001"].product_efficiency_rank == 2
    assert by_id["M-0003"].product_efficiency_rank == 3
    assert by_id["M-0001"].ideal_distance_score is not None
    assert abs(by_id["M-0001"].ideal_distance_score - Decimal(1) / Decimal(3)) < Decimal("1e-28")
    assert by_id["M-0001"].normalized_question_score == 0
    assert by_id["M-0001"].normalized_guesser_cost is not None
    assert abs(by_id["M-0001"].normalized_guesser_cost - Decimal(1) / Decimal(3)) < Decimal("1e-28")
    assert by_id["M-0001"].pareto_efficient
    assert by_id["M-0002"].pareto_efficient
    assert not by_id["M-0003"].pareto_efficient


def test_efficiency_distance_handles_a_single_model_without_artifact_changes() -> None:
    row = LeaderboardRow(
        rank=1,
        model=_model("M-0001", "Only"),
        status="evaluated",
        question_score=Decimal(12),
        guesser_cost_per_episode_usd=Decimal("0.05"),
        cost_adjusted_question_score=Decimal("0.6"),
        efficiency_status="ranked",
    )

    (ranked,) = _rank_efficiency((row,))

    assert ranked.efficiency_rank == 1
    assert ranked.ideal_distance_rank == 1
    assert ranked.product_efficiency_rank == 1
    assert ranked.ideal_distance_score == 0
    assert ranked.normalized_question_score == 0
    assert ranked.normalized_guesser_cost == 0
    assert ranked.pareto_efficient


def test_efficiency_distance_zeroes_a_degenerate_equal_cost_dimension() -> None:
    rows = (
        LeaderboardRow(
            rank=1,
            model=_model("M-0001", "Lower questions"),
            status="evaluated",
            question_score=Decimal(10),
            guesser_cost_per_episode_usd=Decimal("0.1"),
            cost_adjusted_question_score=Decimal(1),
            efficiency_status="ranked",
        ),
        LeaderboardRow(
            rank=2,
            model=_model("M-0002", "Higher questions"),
            status="evaluated",
            question_score=Decimal(20),
            guesser_cost_per_episode_usd=Decimal("0.1"),
            cost_adjusted_question_score=Decimal(2),
            efficiency_status="ranked",
        ),
    )

    by_id = {row.model.model_id: row for row in _rank_efficiency(rows)}

    assert by_id["M-0001"].normalized_guesser_cost == 0
    assert by_id["M-0002"].normalized_guesser_cost == 0
    assert by_id["M-0001"].ideal_distance_score == 0
    assert by_id["M-0002"].ideal_distance_score == 1
    assert by_id["M-0001"].ideal_distance_rank == 1
    assert by_id["M-0002"].ideal_distance_rank == 2


def test_efficiency_distance_preserves_exact_joint_ties() -> None:
    rows = (
        LeaderboardRow(
            rank=1,
            model=_model("M-0001", "Low questions"),
            status="evaluated",
            question_score=Decimal(10),
            guesser_cost_per_episode_usd=Decimal("0.3"),
            cost_adjusted_question_score=Decimal(3),
            efficiency_status="ranked",
        ),
        LeaderboardRow(
            rank=2,
            model=_model("M-0002", "Middle"),
            status="evaluated",
            question_score=Decimal(15),
            guesser_cost_per_episode_usd=Decimal("0.2"),
            cost_adjusted_question_score=Decimal(3),
            efficiency_status="ranked",
        ),
        LeaderboardRow(
            rank=3,
            model=_model("M-0003", "Low cost"),
            status="evaluated",
            question_score=Decimal(20),
            guesser_cost_per_episode_usd=Decimal("0.1"),
            cost_adjusted_question_score=Decimal(2),
            efficiency_status="ranked",
        ),
    )

    by_id = {row.model.model_id: row for row in _rank_efficiency(rows)}

    assert by_id["M-0001"].ideal_distance_rank == 2
    assert by_id["M-0002"].ideal_distance_rank == 1
    assert by_id["M-0003"].ideal_distance_rank == 2
    assert by_id["M-0002"].normalized_question_score == Decimal("0.5")
    assert by_id["M-0002"].normalized_guesser_cost == Decimal("0.5")
    with localcontext() as context:
        context.prec = 50
        expected_middle_distance = Decimal("0.5").sqrt()
    assert by_id["M-0002"].ideal_distance_score == expected_middle_distance
    assert by_id["M-0003"].efficiency_rank == 1
    assert by_id["M-0001"].efficiency_rank == 2
    assert by_id["M-0002"].efficiency_rank == 2


def test_latest_qualified_run_wins_without_score_selection() -> None:
    prior_better = _public_run(
        model_id="M-0001",
        execution_id="BX-prior-better",
        completed_at=datetime(2026, 1, 1, tzinfo=UTC),
        question_score=Decimal(5),
    )
    newer_worse = _public_run(
        model_id="M-0001",
        execution_id="BX-newer-worse",
        completed_at=datetime(2026, 1, 2, tzinfo=UTC),
        question_score=Decimal(30),
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
        question_score=Decimal(20),
    )
    newer_lab = _public_run(
        model_id="M-0001",
        execution_id="BX-newer-lab",
        completed_at=datetime(2026, 1, 2, tzinfo=UTC),
        question_score=Decimal(10),
        classification="lab",
    )
    same_route_different_id = _public_run(
        model_id="M-0002",
        execution_id="BX-other-model",
        completed_at=datetime(2026, 1, 3, tzinfo=UTC),
        question_score=Decimal(15),
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
        question_score=Decimal(10),
    )
    right = _public_run(
        model_id="M-0001",
        execution_id="BX-right",
        completed_at=completed_at,
        question_score=Decimal(20),
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
                                    first_trial.model_copy(update={"publication_eligible": False}),
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
                        first_subject.model_copy(update={"trials": first_subject.trials[:-1]}),
                        *loaded.summary.subjects[1:],
                    )
                }
            )
        }
    )
    assert _reason_codes(missing_trial, cohort) == ("trial_coverage_mismatch",)

    running = loaded.model_copy(
        update={"state": loaded.state.model_copy(update={"status": "running"})}
    )
    assert _reason_codes(running, cohort) == ("incomplete",)


def test_compiler_uses_run_model_metadata_and_requires_all_trials() -> None:
    loaded, cohort = _qualification_context()
    config = parse_publication_config(
        _read_yaml(REPOSITORY / "config" / "publication.yml"),
        "config/publication.yml",
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
                        first_subject.model_copy(update={"trials": first_subject.trials[:-1]}),
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
        built_at=datetime(2026, 7, 30, 12, 34, 56, tzinfo=UTC),
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
    assert dataset.provenance.built_at == datetime(2026, 7, 30, 12, 34, 56, tzinfo=UTC)
    assert dataset.models[0].configuration_hash == (loaded.manifest.model.configuration_hash)
    run_models = dataset.official_runs[0].models
    assert tuple(model.role for model in run_models) == (
        "guesser",
        "oracle",
        "reviewer",
        "judge",
        "validator",
    )
    guesser_model = run_models[0]
    reviewer_model = run_models[2]
    judge_model = run_models[3]
    validator_model = run_models[4]
    assert reviewer_model.requested_model == "test-provider/current-model"
    assert judge_model.requested_model == "test-provider/current-model"
    assert reviewer_model.calls == 0
    assert judge_model.calls == 0
    assert guesser_model.provider_routing == "exact"
    assert guesser_model.providers[0].provider == "test-provider"
    assert guesser_model.providers[0].calls == 1
    assert validator_model.providers[0].cost_usd == Decimal("0.02")
    assert validator_model.fallback_calls == 1
    episode = dataset.official_runs[0].subjects[0].trials[0].episode
    assert episode is not None
    episode_json = episode.model_dump_json()
    assert '"models"' not in episode_json
    assert '"oracle_support"' not in episode_json
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


def test_public_run_model_defaults_to_exact_without_route_totals() -> None:
    legacy = PublicRunModel.model_validate(
        {
            "role": "guesser",
            "configuration_id": "M-legacy",
            "requested_model": "test/legacy",
            "requested_provider": "test-provider",
            "resolved_models": ["test/legacy"],
            "resolved_providers": ["Test Provider"],
            "reasoning_effort": "medium",
            "prompt_version": "legacy-v1",
            "calls": 3,
            "cost_usd": "0.03",
        }
    )

    assert legacy.provider_routing == "exact"
    assert legacy.providers == ()
    assert legacy.unreported_calls == 0


def test_run_overview_discloses_provider_routing_and_legacy_state() -> None:
    source = _run_source()

    assert "Resolved provider details" in source
    assert "OpenRouter automatic routing" in source
    assert "model.providers" in source
    assert "model.resolved_providers" in source
    assert "Fallback calls" in source
    assert "Legacy run" in source


def test_publication_and_report_ui_have_no_execution_component_imports() -> None:
    source_roots = (
        REPOSITORY / "source" / "publication" / "compiler" / "src",
        REPOSITORY / "source" / "publication" / "site" / "src",
    )
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for source_root in source_roots
        for suffix in ("*.py", "*.ts", "*.vue")
        for path in sorted(source_root.rglob(suffix))
    )

    assert "deep20_game" not in source
    assert "deep20_oracle" not in source
    assert "deep20_benchmark" not in source
    assert "OPENROUTER_API_KEY" not in source

    execution_source = "\n".join(
        path.read_text(encoding="utf-8")
        for source_root in (
            REPOSITORY / "source" / "execution" / "benchmark" / "src",
            REPOSITORY / "source" / "execution" / "game" / "src",
            REPOSITORY / "source" / "execution" / "oracle" / "src",
        )
        for path in sorted(source_root.rglob("*.py"))
    )
    assert "deep20_publication" not in execution_source
    assert "app-build.json" not in execution_source
    assert "question_score_confidence_interval" not in execution_source
    assert "stratified-welch-t-v1" not in execution_source
    assert "confidenceIntervalWidth" not in execution_source
    assert "classifyConfidenceWidths" not in execution_source

    report_source = "\n".join(
        path.read_text(encoding="utf-8")
        for suffix in ("*.ts", "*.vue")
        for path in sorted((REPOSITORY / "source" / "publication" / "site" / "src").rglob(suffix))
    )
    assert "guesser_conversation" not in report_source
    assert "subject_snapshot" not in report_source
    assert "results-reliability" in report_source
    assert "system_instructions" not in report_source
    assert "variation_token" not in report_source
    assert "clean_worktree" not in report_source
    assert "dirty_worktree" not in report_source
    assert "Model broke the output contract." in report_source
    assert "Contract compliance" in report_source
    assert "What the model returned" in report_source
    assert "What a valid response looks like" in report_source
    assert "The provider returned no textual completion for this call." in report_source
    assert "rejected_outputs" in report_source
    assert "v-html" not in (
        REPOSITORY / "source" / "publication" / "site" / "src" / "views" / "EpisodeView.vue"
    ).read_text(encoding="utf-8")
    assert "Awaiting official run" not in report_source
    assert "Earlier official runs" not in report_source
    static_render_source = (
        REPOSITORY / "source" / "publication" / "site" / "scripts" / "prerender.mjs"
    ).read_text(encoding="utf-8")
    assert "manifest.json" in static_render_source
    assert "leaderboard.json" in static_render_source
    assert "deep20bench-v9.json" in static_render_source
    for private_source in (
        "guesser_conversation",
        "subject_snapshot",
        "raw_response",
        "oracle_search_results",
        "provider_trace",
        "error-outputs.jsonl",
        "private/",
    ):
        assert private_source not in static_render_source
    route_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            REPOSITORY
            / "source"
            / "publication"
            / "site"
            / "src"
            / "views"
            / "workspace"
            / "BenchmarkWorkspaceView.vue",
            REPOSITORY
            / "source"
            / "publication"
            / "site"
            / "src"
            / "views"
            / "workspace"
            / "SubjectWorkspaceView.vue",
            REPOSITORY / "source" / "publication" / "site" / "src" / "views" / "EpisodeView.vue",
        )
    )
    assert "dataset.lab_runs" not in route_source

    public_schema = json.dumps(PublishedDataset.model_json_schema(), sort_keys=True)
    assert "guesser_disclosure" in public_schema
    assert "recorded_output" in public_schema
    assert "rejected_outputs" in public_schema
    assert "required_formats" in public_schema
    for forbidden_field in (
        "call_id",
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
        "response_id",
        "session_id",
        "cache_key",
        "error_output_preview",
        "error_outputs",
    ):
        assert forbidden_field not in public_schema


def test_published_contract_violations_include_only_sanitized_guesser_text() -> None:
    dataset_path = REPOSITORY / "docs" / "data" / "deep20bench-v9.json"
    dataset = PublishedDataset.model_validate_json(dataset_path.read_text(encoding="utf-8"))
    violations = tuple(
        turn
        for run in dataset.official_runs
        for subject in run.subjects
        for trial in subject.trials
        if trial.episode is not None
        for turn in trial.episode.turns
        if turn.turn_type == "contract_violation"
    )
    retained = tuple(output for turn in violations for output in turn.rejected_outputs)

    snapshot_path = (
        REPOSITORY / "source" / "publication" / "data" / "guesser-violation-outputs-v1.json"
    )
    snapshot = parse_guesser_violation_snapshot(_read_json(snapshot_path), str(snapshot_path))
    selected_runs = {run.execution_id for run in dataset.official_runs}
    expected = {
        (record.execution_id, record.target_id, record.trial_id, record.turn_number): record
        for record in snapshot.records
        if record.execution_id in selected_runs
    }
    actual = {
        (run.execution_id, subject.target_id, trial.trial_id, turn.turn_number): turn
        for run in dataset.official_runs
        for subject in run.subjects
        for trial in subject.trials
        if trial.episode is not None
        for turn in trial.episode.turns
        if turn.turn_type == "contract_violation"
    }
    assert actual.keys() == expected.keys()
    assert len(violations) == sum(run.contract.violations for run in dataset.official_runs)
    assert retained
    for identity, turn in actual.items():
        assert turn.rejected_outputs == expected[identity].rejected_outputs
    assert all(output.text for output in retained)
    assert all(
        trial.episode.guesser_disclosure is not None
        and trial.episode.guesser_disclosure.required_formats is not None
        for run in dataset.official_runs
        for subject in run.subjects
        for trial in subject.trials
        if trial.episode is not None
        and any(turn.turn_type == "contract_violation" for turn in trial.episode.turns)
    )


def test_report_cost_labels_define_episode_and_run_scope() -> None:
    views = REPOSITORY / "source" / "publication" / "site" / "src" / "views"
    episode_source = _episode_source()
    workspace = views / "workspace"
    subject_source = (workspace / "SubjectWorkspaceView.vue").read_text(encoding="utf-8")
    run_source = (
        (workspace / "BenchmarkWorkspaceView.vue").read_text(encoding="utf-8")
        + _run_source()
        + (views.parent / "lib" / "run-roles.ts").read_text(encoding="utf-8")
    )
    leaderboard_source = (views / "HomeView.vue").read_text(encoding="utf-8")

    assert "Episode cost" in episode_source
    assert "detail: `All ${props.episode.total_turns} turns`" in episode_source
    assert "Full run {{ money(run.total_cost_usd) }}" in episode_source
    assert "Judge" in run_source
    assert "Exact Guesser setup" in episode_source
    assert "Recorded Guesser output" in episode_source
    assert "Why this output was rejected" in episode_source
    assert "Exact Guesser provider text" in episode_source
    assert "1 · Guesser asks" in episode_source
    assert (
        '2 · {{ turn.adjudicator === "oracle" ? "Adjudication" : "Validator" }} returns'
        in episode_source
    )
    assert episode_source.index("Recorded Guesser output") < episode_source.rindex(
        "Oracle evidence"
    )
    assert "<th data-numeric>Latency</th>" in episode_source
    assert "seconds(row.values.latency_ms)" in episode_source
    assert "`Q${turn.counted_questions}`" in episode_source
    assert "No question charge" in episode_source
    assert "moneyEpisode(trial.cost_usd)" in subject_source
    assert "<dt>Run cost</dt>" not in run_source
    assert "Complete benchmark" in run_source
    assert "Model under test" in run_source
    assert 'label="Question score"' in run_source
    assert 'class="workspace-metrics workspace-detail-boundary"' in run_source
    assert "Run ledger." in run_source
    assert "Guesser time" in run_source
    assert "Primary Oracle" in run_source
    assert "Game support" in run_source
    assert "run.totals.total_tokens" in run_source
    assert "current.totals.guesser_think_time_ms" in run_source
    assert "{ label: 'Benchmark run cost', value: money(row.total_cost_usd) }" in leaderboard_source


def test_cost_documentation_excludes_superseded_infrastructure_attempts() -> None:
    cost_source = (
        REPOSITORY
        / "source"
        / "publication"
        / "site"
        / "src"
        / "views"
        / "results"
        / "ResultsCostView.vue"
    ).read_text(encoding="utf-8")
    methodology_source = (
        REPOSITORY / "source" / "publication" / "site" / "src" / "views" / "MethodologyView.vue"
    ).read_text(encoding="utf-8")
    run_source = _run_source()

    cost_copy = " ".join(cost_source.split())
    methodology_copy = " ".join(methodology_source.split())
    assert "Superseded infrastructure attempts and support costs are excluded." in cost_copy
    assert "do not increase the published model or benchmark cost" in cost_copy
    assert "Excluded repair overhead" in cost_copy
    assert "Excluded repair overhead" in run_source
    assert "do not increase public model or benchmark costs" in methodology_copy


def test_generated_homepage_matches_the_official_result_state() -> None:
    dataset_path = REPOSITORY / "docs" / "data" / "deep20bench-v9.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    evaluated = [row for row in dataset["leaderboard"] if row["status"] == "evaluated"]
    homepage = (
        REPOSITORY / "source" / "publication" / "site" / "src" / "views" / "HomeView.vue"
    ).read_text(encoding="utf-8")
    homepage_copy = " ".join(homepage.split())
    data_page = (
        REPOSITORY / "source" / "publication" / "site" / "src" / "views" / "DataView.vue"
    ).read_text(encoding="utf-8")
    site_footer = (
        REPOSITORY / "source" / "publication" / "site" / "src" / "components" / "SiteFooter.vue"
    ).read_text(encoding="utf-8")
    result_chart = (
        REPOSITORY / "source" / "publication" / "site" / "src" / "lib" / "result-chart.ts"
    ).read_text(encoding="utf-8")
    publication_time = (
        REPOSITORY
        / "source"
        / "publication"
        / "site"
        / "src"
        / "components"
        / "PublicationTime.vue"
    ).read_text(encoding="utf-8")
    site_resources = (
        REPOSITORY / "source" / "publication" / "site" / "src" / "lib" / "site-resources.ts"
    ).read_text(encoding="utf-8")
    model_run_link = (
        REPOSITORY / "source" / "publication" / "site" / "src" / "components" / "ModelRunLink.vue"
    ).read_text(encoding="utf-8")
    mobile_result_card = (
        REPOSITORY
        / "source"
        / "publication"
        / "site"
        / "src"
        / "components"
        / "MobileResultCard.vue"
    ).read_text(encoding="utf-8")
    methodology = (
        REPOSITORY / "source" / "publication" / "site" / "src" / "views" / "MethodologyView.vue"
    ).read_text(encoding="utf-8")
    illustrative_round = (
        REPOSITORY
        / "source"
        / "publication"
        / "site"
        / "src"
        / "components"
        / "IllustrativeRoundExample.vue"
    ).read_text(encoding="utf-8")

    assert "How well can AI models play Twenty Questions?" in homepage
    assert "Prototype · Twenty Questions for AI models" in homepage
    assert "more than the traditional twenty" in homepage
    assert "The game combines several abilities." in homepage
    assert "The concept works and the first step is complete." in homepage_copy
    assert "cost is the main constraint." in homepage_copy
    assert "small first step" not in homepage
    assert "not a definitive ranking" not in homepage
    assert "Use GitHub Discussions to suggest what we should test next." in homepage
    assert "https://github.com/mindalyze-com/deep-20-bench/discussions" in homepage
    assert "Use all prior questions and answers to plan the next question." in homepage
    assert "The Guesser asks. Three roles determine the answer." in homepage
    assert "The Guesser is the LLM under test" in homepage
    assert "the Oracle must search the live web and cite evidence" in homepage
    assert "independent second decision on every YES or NO" in homepage
    assert "If the decisions disagree, a blind" in homepage
    assert "The Guesser is isolated from this process" in homepage
    assert "Read the full game and answer-checking method" in homepage
    assert "hash: '#answer-checks'" in homepage
    assert "Early runs exposed rare but basic Oracle errors" not in homepage
    assert "From one round to a comparable score." in methodology
    assert "<IllustrativeRoundExample />" in homepage
    assert "<IllustrativeRoundExample />" in methodology
    assert "Question score (single round)" in illustrative_round
    assert "The correct guess is excluded." in illustrative_round
    assert "Questions and guesses follow separate paths." in methodology
    assert "The Oracle must search the live web instead of relying on memory" in methodology
    assert "without seeing the Oracle answer" in methodology
    assert "without seeing either answer" in methodology
    assert "Oracle UNKNOWN" in methodology
    assert "Guess Validator" in methodology
    assert "The Guesser is fully isolated from adjudication." in methodology
    assert (
        "contains only the broad category, its own prior actions, final YES, NO, or UNKNOWN"
        in methodology
    )
    assert "searches, evidence, citations, adjudicator" in methodology
    assert "provider traces, or private artifacts" in methodology
    assert "Early runs exposed rare but basic Oracle errors" in methodology
    assert "One round becomes {{ totalTrials }} isolated trials." in methodology
    assert "subject-independent" in methodology
    assert "Twenty Questions names the game, not the scoring limit" in methodology
    assert "Every additional" in methodology
    assert "question increases the trial value" in methodology
    assert "Subject design and contamination" in methodology
    assert "Seven subjects is too small for broad conclusions" in methodology
    assert "does not claim that this public cohort is resistant" in methodology
    assert "Future cohorts will aim to include more subjects" in methodology
    assert "not a general ranking of model intelligence" in methodology
    assert "Question score is the average counted questions." in methodology
    assert "questions used · failed trial = {{ penalty }}" in methodology
    assert "One divided by T, times the sum of trial scores" in methodology
    assert "One divided by S, times the sum of subject averages" in methodology
    assert "number of trials for the subject" in methodology
    assert "number of subjects" in methodology
    assert "A score built from repeated trials." not in homepage
    assert "Each model completes the full subject set several times." not in homepage
    assert "Only complete, comparable runs enter the leaderboard." in methodology
    assert "Publication happens after play is finished." in methodology
    assert "Published data never returns to the Guesser." in methodology
    assert "questionScoreChartSummary" in homepage
    assert "companion plot shows each exact" in result_chart
    assert "three bands divide the displayed width scale" in result_chart
    assert 'class="protocol-flow"' not in homepage
    assert "Homepage built" not in homepage
    assert "home-build-note" not in homepage
    assert "Publication updated" in site_footer
    assert "App built" not in site_footer
    assert "getAppBuild" not in site_footer
    assert ':datetime="value"' in publication_time
    assert '<PublicationTime :value="publicationUpdatedAt" />' in site_footer
    assert "site-resources" in site_footer
    assert "How to cite" in site_resources
    assert "Report an error" in site_resources
    assert "Support on Ko-fi" in site_resources
    assert "https://ko-fi.com/mindalyze" in site_resources
    assert "source-available under a dual-license model" in site_footer
    assert "Software licensing - source-available" in site_resources
    assert "data-build-note" not in data_page
    assert "deep20bench-v9.schema.json" in data_page
    assert "Verify and reuse" in data_page
    assert "CC BY 4.0" in data_page
    assert ".model.display_name" in data_page
    assert "Read the publication method" in data_page
    assert "Support future benchmark runs" in homepage
    if evaluated:
        assert '<template v-if="evaluated.length > 0">' in homepage
        assert "<ComparisonRankingTable" in homepage
        assert 'variant="home"' in homepage
        assert '@click="openRun(row)"' in homepage
        assert "<ModelRunLink" in homepage
        assert "<RunTableAction" not in homepage
        assert "<MobileResultCard" in homepage
        assert 'variant="table"' in homepage
        assert "tone: 'primary'" not in homepage
        assert "@click.stop" in model_run_link
        assert "model-run-link-chevron" in model_run_link
        assert "Explore full run · questions, answers & evidence" in mobile_result_card
        assert "result-row--navigable" in homepage
    else:
        assert '<article v-else class="empty-results">' in homepage
    assert "Pilot comparison in progress." in homepage


def test_generated_drilldown_pages_keep_current_location_visible() -> None:
    views = REPOSITORY / "source" / "publication" / "site" / "src" / "views"
    workspace = views / "workspace"
    run_source = (workspace / "BenchmarkWorkspaceView.vue").read_text(encoding="utf-8")
    subject_source = (workspace / "SubjectWorkspaceView.vue").read_text(encoding="utf-8")
    episode_source = _episode_source()

    assert 'level: "Run workspace"' in run_source
    assert 'id="route-content"' in run_source
    assert 'class="model-rail"' in run_source
    assert "<RouterView v-else />" in run_source
    assert 'level: "Subject workspace"' in subject_source
    assert 'class="episode-rail"' in subject_source
    assert "`${index + 1} of ${subjects.value.length}`" in subject_source
    assert "<RouterView v-else />" in subject_source
    assert "hash:" not in run_source
    assert "hash:" not in subject_source
    assert 'level: "Episode"' in episode_source
    assert 'id="episode-overview"' in episode_source
    assert "previous: previousTrial" in episode_source
    assert "next: nextTrial" in episode_source
    assert episode_source.index('id="transcript"') < episode_source.index('id="technical"')
    assert "model-under-test" not in episode_source


def test_drilldown_navigation_is_sticky_and_scroll_safe() -> None:
    source_root = REPOSITORY / "source" / "publication" / "site" / "src"
    component = (source_root / "components" / "DrilldownBar.vue").read_text(encoding="utf-8")
    global_css = _site_styles_source()
    app_source = (source_root / "App.vue").read_text(encoding="utf-8")
    episode_page = _episode_source()

    assert 'class="drilldown-bar"' in component
    assert 'aria-label="Current location"' in component
    assert 'aria-current="page"' in component
    assert 'rel="prev"' in component
    assert 'rel="next"' in component
    assert "overflow-x: clip" in global_css
    assert "overflow-y: auto" in global_css
    assert "prefers-reduced-motion: reduce" in global_css
    assert "scrollPositions" in app_source
    assert "app-viewport--workspace" in app_source
    assert '<SiteFooter v-if="route.meta.workspace !== true" />' in app_source
    assert ".site-footer" not in global_css
    assert "<Transition" not in app_source
    assert "panel-deeper" not in global_css
    assert "panel-back" not in global_css
    assert "<KeepAlive" in app_source
    assert 'class="episode-tabs"' in episode_page
    assert 'class="episode-content"' in episode_page
    assert "overflow: hidden" in episode_page
    assert "ModelUnderTest" not in episode_page


def test_generated_question_scores_use_subject_averages_then_average() -> None:
    dataset_path = REPOSITORY / "docs" / "data" / "deep20bench-v9.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))

    assert dataset["score_policy"]["version"] == "average-then-average-v1"
    for run in dataset["official_runs"]:
        subject_averages: list[Decimal] = []
        for subject in run["subjects"]:
            trial_values = tuple(
                Decimal(trial["penalized_questions"]) for trial in subject["trials"]
            )
            subject_average = _average(trial_values)
            assert Decimal(subject["average_questions"]) == subject_average
            subject_averages.append(subject_average)
        expected_score = sum(subject_averages, start=Decimal(0)) / Decimal(len(subject_averages))
        assert Decimal(run["question_score"]) == expected_score

    leaderboard_by_model = {row["model"]["model_id"]: row for row in dataset["leaderboard"]}
    fable = leaderboard_by_model["M-0014"]
    opus = leaderboard_by_model["M-0006"]
    kimi = leaderboard_by_model["M-0007"]
    assert Decimal(fable["question_score"]) == Decimal("12.05714285714285714285714286")
    assert Decimal(opus["question_score"]) == Decimal("12.34285714285714285714285714")
    assert Decimal(kimi["question_score"]) == Decimal("12.74285714285714285714285714")
    opus_interval = opus["question_score_confidence_interval"]
    assert opus_interval["method"] == "stratified-welch-t-v1"
    assert Decimal(opus_interval["confidence_level"]) == Decimal("0.95")
    assert Decimal(opus_interval["lower"]) == pytest.approx(Decimal("11.4128149952043132"))
    assert Decimal(opus_interval["upper"]) == pytest.approx(Decimal("13.2728992905099725"))
    assert opus_interval["subject_count"] == 7
    assert opus_interval["trial_count"] == 35
    scored_rows = [row for row in dataset["leaderboard"] if row["question_score"] is not None]
    for row in scored_rows:
        assert row["rank"] == 1 + sum(
            Decimal(other["question_score"]) < Decimal(row["question_score"])
            for other in scored_rows
        )


def test_generated_efficiency_distance_is_reproducible_from_public_decimals() -> None:
    dataset_path = REPOSITORY / "docs" / "data" / "deep20bench-v9.json"
    dataset = PublishedDataset.model_validate_json(dataset_path.read_text(encoding="utf-8"))
    rows = tuple(row for row in dataset.leaderboard if row.ideal_distance_rank is not None)

    question_minimum = min(row.question_score for row in rows if row.question_score is not None)
    question_maximum = max(row.question_score for row in rows if row.question_score is not None)
    cost_minimum = min(
        row.guesser_cost_per_episode_usd
        for row in rows
        if row.guesser_cost_per_episode_usd is not None
    )
    cost_maximum = max(
        row.guesser_cost_per_episode_usd
        for row in rows
        if row.guesser_cost_per_episode_usd is not None
    )
    for row in rows:
        assert row.question_score is not None
        assert row.guesser_cost_per_episode_usd is not None
        assert row.normalized_question_score is not None
        assert row.normalized_guesser_cost is not None
        assert row.ideal_distance_score is not None
        with localcontext() as context:
            context.prec = 50
            normalized_question = (row.question_score - question_minimum) / (
                question_maximum - question_minimum
            )
            normalized_cost = (row.guesser_cost_per_episode_usd - cost_minimum) / (
                cost_maximum - cost_minimum
            )
            distance = (
                normalized_question * normalized_question + normalized_cost * normalized_cost
            ).sqrt()
        assert row.normalized_question_score == normalized_question
        assert row.normalized_guesser_cost == normalized_cost
        assert row.ideal_distance_score == distance

    for row in rows:
        assert row.ideal_distance_score is not None
        assert row.question_score is not None
        assert row.guesser_cost_per_episode_usd is not None
        assert row.ideal_distance_rank == 1 + sum(
            other.ideal_distance_score < row.ideal_distance_score
            for other in rows
            if other.ideal_distance_score is not None
        )
        dominated = any(
            other.question_score <= row.question_score
            and other.guesser_cost_per_episode_usd <= row.guesser_cost_per_episode_usd
            and (
                other.question_score < row.question_score
                or other.guesser_cost_per_episode_usd < row.guesser_cost_per_episode_usd
            )
            for other in rows
            if other.question_score is not None
            and other.guesser_cost_per_episode_usd is not None
        )
        assert row.pareto_efficient is not dominated
        assert row.efficiency_rank == row.product_efficiency_rank


def test_pre_question_score_run_compiles_without_migration() -> None:
    execution_id = "BX-20260728-official-M0001-010"
    summary_path = REPOSITORY / "runs" / "M-0001" / execution_id / "summary.yml"
    snapshot_path = (
        REPOSITORY / "source" / "publication" / "data" / "guesser-violation-outputs-v1.json"
    )
    loaded = _load_run(
        summary_path,
        REPOSITORY,
        parse_guesser_violation_snapshot(
            _read_json(snapshot_path),
            str(snapshot_path),
        ),
    )
    config = parse_publication_config(
        _read_yaml(REPOSITORY / "config" / "publication.yml"),
        "config/publication.yml",
    )
    subjects, subject_hash = parse_subject_catalog(
        _read_yaml(REPOSITORY / "config" / "subjects.yaml"),
        "config/subjects.yaml",
    )

    dataset = compile_publication(
        runs=(loaded,),
        config=config,
        subject_catalog=subjects,
        subject_catalog_hash=subject_hash,
        built_at=datetime(2026, 7, 30, 12, 34, 56, tzinfo=UTC),
    )

    assert tuple(run.execution_id for run in dataset.official_runs) == (execution_id,)
    assert dataset.official_runs[0].question_score == Decimal("17.74285714285714285714285714")
    assert dataset.schema_version == 9
    assert dataset.leaderboard[0].efficiency_rank == 1
    assert dataset.leaderboard[0].ideal_distance_rank == 1
    assert dataset.leaderboard[0].ideal_distance_score == 0
    assert dataset.leaderboard[0].normalized_question_score == 0
    assert dataset.leaderboard[0].normalized_guesser_cost == 0
    assert all(
        trial.penalized_questions is not None
        for subject in dataset.official_runs[0].subjects
        for trial in subject.trials
    )


def test_result_metric_charts_use_tree_shaken_echarts() -> None:
    source_root = REPOSITORY / "source" / "publication" / "site" / "src"
    component = (source_root / "components" / "MetricBars.vue").read_text(encoding="utf-8")
    responsive_runtime = (source_root / "lib" / "use-responsive-echart.ts").read_text(
        encoding="utf-8"
    )
    chart_registration = (source_root / "lib" / "chart-registration.ts").read_text(
        encoding="utf-8"
    )
    chart_axis = (source_root / "lib" / "chart-axis.ts").read_text(encoding="utf-8")
    chart_series = (source_root / "lib" / "chart-series.ts").read_text(encoding="utf-8")
    chart_tooltip = (source_root / "lib" / "chart-tooltip.ts").read_text(encoding="utf-8")
    use_linked_echart = (source_root / "lib" / "use-linked-echart.ts").read_text(
        encoding="utf-8"
    )
    chart_model_key = (source_root / "components" / "ChartModelKey.vue").read_text(
        encoding="utf-8"
    )
    chart_accessible_data = (
        source_root / "components" / "ChartAccessibleData.vue"
    ).read_text(encoding="utf-8")
    cost_donut = (source_root / "components" / "CostDonut.vue").read_text(encoding="utf-8")
    info_popover = (source_root / "components" / "InfoPopover.vue").read_text(encoding="utf-8")
    question_score = (source_root / "components" / "QuestionScore.vue").read_text(encoding="utf-8")
    stacked_costs = (source_root / "components" / "StackedMetricBars.vue").read_text(
        encoding="utf-8"
    )
    efficiency_scatter = (source_root / "components" / "EfficiencyScatter.vue").read_text(
        encoding="utf-8"
    )
    efficiency_marker_legend = (
        source_root / "components" / "EfficiencyMarkerLegend.vue"
    ).read_text(encoding="utf-8")
    score_dot_plot = (source_root / "components" / "ScoreDotPlot.vue").read_text(encoding="utf-8")
    homepage = (source_root / "views" / "HomeView.vue").read_text(encoding="utf-8")
    package = (REPOSITORY / "source" / "publication" / "site" / "package.json").read_text(
        encoding="utf-8"
    )

    assert '"echarts": "6.1.0"' in package
    assert 'from "echarts/core"' in chart_registration
    assert "BarChart" in component
    assert "SVGRenderer" in chart_registration
    assert "standardChartComponents" in component
    assert 'renderer: "svg"' in responsive_runtime
    assert "xAxis:" in component
    assert "chartValueDomain" in responsive_runtime
    assert "chartValueDomain" not in component
    assert "min: 0" in component
    assert "scale: true" not in component
    assert "The value axis starts at zero" in component
    assert "aria:" in component
    assert "tooltip:" in component
    assert "useResponsiveEChart" in component
    assert 'name: "View full run"' in component
    assert 'barGap: "-100%"' in component
    assert "Select a model row to view its full run" in component
    assert "ResizeObserver" in responsive_runtime
    assert 'chart.on("click", options.onClick)' in responsive_runtime
    assert "PieChart" in cost_donut
    assert "<InfoPopover" in question_score
    assert 'event.key === "Escape"' in info_popover
    assert 'document.addEventListener("pointerdown"' in info_popover
    assert "position: absolute;" in info_popover
    assert "position: fixed;" in info_popover
    assert 'radius: ["58%", "83%"]' in cost_donut
    assert "BarChart" in stacked_costs
    assert 'stack: "full-cost"' in stacked_costs
    assert 'name: "Adaptive axis offset"' not in stacked_costs
    assert "visibleValue" not in stacked_costs
    assert "chartValueDomain" not in stacked_costs
    assert "min: 0" in stacked_costs
    assert "scale: true" not in stacked_costs
    assert "row.values[segmentIndex] ?? 0" in stacked_costs
    assert "Exact adjudication breakdown" in stacked_costs
    assert "Exact adjudication costs by model" in stacked_costs
    assert 'scope="row"' in stacked_costs
    assert "ScatterChart" in efficiency_scatter
    assert "LineChart" in efficiency_scatter
    assert "Pareto-efficient" in efficiency_scatter
    assert "Diamond" in efficiency_marker_legend
    assert "Circle" in efficiency_marker_legend
    assert "no other model is both cheaper and better" in efficiency_marker_legend
    assert "props.expanded ? 720 : 620" in efficiency_scatter
    assert "props.expanded ? 80 : 96" in efficiency_scatter
    assert 'v-if="!expanded"' in efficiency_scatter
    assert "<ChartModelKey" in efficiency_scatter
    assert "desktopChartHeight" in efficiency_scatter
    assert "figureResizeObserver" in efficiency_scatter
    assert "plotSize + (props.expanded ? 48 : 76)" in efficiency_scatter
    assert 'type: "log"' not in efficiency_scatter
    assert 'type: "value"' in chart_axis
    assert 'name: "Models"' in efficiency_scatter
    assert "clip: false" in efficiency_scatter
    assert "theme.results.efficiency" in efficiency_scatter
    assert "show: !mobile" in chart_series
    assert "hideOverlap" in chart_series
    assert 'moveOverlap: "shiftY"' in chart_series
    assert "chart-model-key" in chart_model_key
    assert "distanceGuideData" in efficiency_scatter
    assert "width: plotSize" in efficiency_scatter
    assert "height: plotSize" in efficiency_scatter
    assert "min: 0" in efficiency_scatter
    assert "max: 1" in efficiency_scatter
    assert "boundaryGap: [0, 0]" in efficiency_scatter
    assert 'name: "Distance labels"' in efficiency_scatter
    assert "distance > 1 ? 0.45 : 0.9" in efficiency_scatter
    assert "ScatterChart" in score_dot_plot
    assert "BarChart" in score_dot_plot
    assert "CustomChart" in score_dot_plot
    assert 'type: "custom"' in score_dot_plot
    assert 'name: "95% CI of average"' in score_dot_plot
    assert "intentionally not exposed for now" in score_dot_plot
    assert "confidenceDisplay" in score_dot_plot
    assert 'name: "View full run"' in score_dot_plot
    assert "scoreDomain.value.minimum" in score_dot_plot
    assert "lineStyle: { color: theme.gridLine, width: 1 }" in score_dot_plot
    assert "color: theme.ink" in score_dot_plot
    assert "confidenceBandColor" in score_dot_plot
    assert "stroke, lineWidth: 2.6" in score_dot_plot
    for linked_axis_chart in (component, stacked_costs, score_dot_plot):
        assert "triggerEvent: true" in linked_axis_chart
        assert 'parameters.componentType === "yAxis"' in linked_axis_chart
    for linked_model_chart in (
        component,
        stacked_costs,
        score_dot_plot,
    ):
        assert "View full run" in linked_model_chart
    assert "chartTooltipRunLink" in efficiency_scatter
    assert "useLinkedEChart" in efficiency_scatter
    assert "View full run" in chart_tooltip
    assert "View full run" in chart_accessible_data
    assert "router.push" in use_linked_echart
    for chart_source in (
        component,
        cost_donut,
        stacked_costs,
        efficiency_scatter,
        score_dot_plot,
    ):
        assert "aria:" in chart_source
    assert 'renderer: "svg"' in responsive_runtime
    assert "chartValueDomain" in score_dot_plot
    assert "scale: true" in score_dot_plot
    assert "Question score · lower is better" in score_dot_plot
    assert "<ScoreDotPlot" in homepage
    assert "@media (max-width: 620px)" in component


def test_results_use_document_scroll_and_coalesce_chart_work() -> None:
    source_root = REPOSITORY / "source" / "publication" / "site" / "src"
    router = (source_root / "router.ts").read_text(encoding="utf-8")
    app = (source_root / "App.vue").read_text(encoding="utf-8")
    app_css = _site_styles_source()
    workspace = (source_root / "views" / "results" / "ResultsWorkspaceView.vue").read_text(
        encoding="utf-8"
    )
    chart_runtime = (source_root / "lib" / "use-responsive-echart.ts").read_text(encoding="utf-8")

    assert "resultsWorkspace" not in router
    assert "app-viewport--results" not in app
    assert "route.meta.workspace !== true" in app
    assert "to.meta.workspace === true" in app
    assert "scrollRestoreVersion" in app
    assert ".app-viewport--results" not in app_css
    assert "overflow-anchor: none;" in app_css
    assert "pointer-events: none;" in app_css
    assert "touch-action: pan-y;" in app_css
    assert "scroll-behavior: smooth" not in app_css
    assert 'ref="resultsBody"' not in workspace
    assert "resetResultsScroll" in workspace
    assert "window.scrollTo({ top: 0, left: 0 })" in workspace
    assert "min-height: 60vh" in workspace
    assert "overflow-y: auto" not in workspace
    assert "results-workspace--stability" in workspace
    assert "results-workspace--efficiency" in workspace
    assert "--result-accent" in workspace
    assert "refreshPending" in chart_runtime
    assert "onDeactivated" in chart_runtime
    assert '"(max-width: 760px)"' in chart_runtime


def test_results_pages_keep_model_metrics_explicit() -> None:
    source_root = REPOSITORY / "source" / "publication" / "site" / "src"
    results = source_root / "views" / "results"
    results_nav = (source_root / "components" / "ResultsNav.vue").read_text(encoding="utf-8")
    app_css = _site_styles_source()
    overview = (results / "ResultsOverviewView.vue").read_text(encoding="utf-8")
    cost = (results / "ResultsCostView.vue").read_text(encoding="utf-8")
    time = (results / "ResultsTimeView.vue").read_text(encoding="utf-8")
    efficiency = (results / "ResultsEfficiencyView.vue").read_text(encoding="utf-8")
    reliability = (results / "ResultsReliabilityView.vue").read_text(encoding="utf-8")
    reliability_scatter = (source_root / "components" / "ReliabilityScatter.vue").read_text(
        encoding="utf-8"
    )
    result_help = (source_root / "components" / "ResultHelp.vue").read_text(encoding="utf-8")
    metric_definition_card = (source_root / "components" / "MetricDefinitionCard.vue").read_text(
        encoding="utf-8"
    )
    model_run_link = (source_root / "components" / "ModelRunLink.vue").read_text(encoding="utf-8")
    mobile_result_card = (source_root / "components" / "MobileResultCard.vue").read_text(
        encoding="utf-8"
    )
    comparison_ranking_table = (
        source_root / "components" / "ComparisonRankingTable.vue"
    ).read_text(encoding="utf-8")
    ranking_table = (source_root / "components" / "RankingTable.vue").read_text(
        encoding="utf-8"
    )
    official_run_ranking_row = (
        source_root / "components" / "OfficialRunRankingRow.vue"
    ).read_text(encoding="utf-8")
    official_run_data = (source_root / "lib" / "use-official-run-data.ts").read_text(
        encoding="utf-8"
    )
    result_chart = (source_root / "lib" / "result-chart.ts").read_text(encoding="utf-8")

    assert '{ label: "Score", name: "results" }' in results_nav
    assert '{ label: "Stability", name: "results-reliability" }' in results_nav
    assert '{ label: "Cost", name: "results-cost" }' in results_nav
    assert '{ label: "Time", name: "results-time" }' in results_nav
    assert '{ label: "Efficiency", name: "results-efficiency" }' in results_nav
    assert ".result-row-link::after" not in app_css
    assert "<ScoreDotPlot" in overview
    assert "<MetricBars" in cost
    assert "<MetricBars" in time
    assert "<MetricBars" in efficiency
    assert "<StackedMetricBars" in cost
    assert "<EfficiencyScatter" in efficiency
    assert "<ReliabilityScatter" in reliability
    assert "<MetricBars" not in reliability
    assert "<ScoreDotPlot" not in reliability
    assert "<ReliabilityComparisonPlot" not in reliability
    assert 'value-format="currency"' in cost
    assert 'value-format="duration"' in time
    assert "<ComparisonRankingTable" in overview
    assert 'variant="results-overview"' in overview
    assert "const metricWidth" in comparison_ranking_table
    assert "<colgroup>" in comparison_ranking_table
    assert '"comparison-ranking-table"' in comparison_ranking_table
    assert 'variant="table"' in overview
    assert "primary-metric-column" in overview
    assert "tone: 'primary'" not in overview
    assert '@click="openRun(row)"' in overview
    assert "result-row--navigable" in overview
    assert "@click.stop" in model_run_link
    assert "View full run" in model_run_link
    assert ":focus-visible" in model_run_link
    assert "model-run-link-chevron" in model_run_link
    assert ".ranking-table .rank-column" in app_css
    assert ".ranking-table .run-column" not in app_css
    assert "position: sticky;" in app_css
    assert "overflow: visible;" in app_css
    assert ".table-header-stack" in app_css
    assert ".ranking-table-wrap" in app_css
    assert ".mobile-result-list" in app_css
    assert "grid-template-columns: repeat(auto-fit, minmax(5rem, 1fr));" in mobile_result_card
    assert "data-tone" not in mobile_result_card
    assert "background: inherit;" in mobile_result_card
    assert "min-height: 2.75rem;" in mobile_result_card
    assert "Explore full run · questions, answers & evidence" in mobile_result_card
    assert "translateX(0.2rem)" in mobile_result_card
    for table_source in (overview, efficiency, reliability):
        assert "result-row--clickable" in table_source
        assert "result-row--navigable" in table_source
    assert "<ModelRunLink" in overview
    for table_source in (efficiency, reliability):
        assert "<RankingDataRow" in table_source
    for table_source in (cost, time):
        assert "<OfficialRunRankingRow" in table_source
    assert "result-row--clickable" in official_run_ranking_row
    assert "result-row--navigable" in official_run_ranking_row
    for table_source in (overview, cost, time, efficiency, reliability):
        assert "<RunTableAction" not in table_source
        assert "<MobileResultCard" in table_source
        assert "mobile-result-list" in table_source
        assert "panel-heading--with-help" in table_source
        assert "result-chart-panel" in table_source
    assert "ranking-table-wrap" in comparison_ranking_table
    assert '"ranking-table"' in comparison_ranking_table
    assert "ranking-table-wrap" in ranking_table
    assert 'ranking-table results-table' in ranking_table
    for table_source in (cost, time, efficiency, reliability):
        assert "<RankingTable" in table_source
    assert overview.count("<ResultHelp") == 1
    assert reliability.count("<ResultHelp") == 1
    assert cost.count("<ResultHelp") == 1
    assert time.count("<ResultHelp") == 1
    assert efficiency.count("<ResultHelp") == 2
    for table_source in (cost, time):
        assert "providerFor" in table_source
        assert "useOfficialRunData" in table_source
    assert "getLeaderboard()" in official_run_data
    assert "getOfficialRuns()" in official_run_data
    assert "Model time / episode" in overview
    assert 'label="Question score"' in overview
    assert 'label="CI width"' in overview
    assert 'label="Success and contract"' in overview
    assert ("Number(left.totals.costs_usd.total) - Number(right.totals.costs_usd.total)") in cost
    assert (
        "Number(left.totals.costs_usd.guesser) -\n        Number(right.totals.costs_usd.guesser)"
    ) in cost
    assert "value: Number(run.totals.costs_usd.guesser)" in cost
    assert 'direction-label="Guesser cost · lower is better"' in cost
    assert 'label="Guesser and support cost"' in cost
    assert 'label="Per episode"' in cost
    assert 'label="How this page is ordered"' in cost
    assert "Total benchmark cost" in cost
    assert 'direction-label="Total benchmark cost by component"' in cost
    assert 'key: "adjudication"' in cost
    assert 'label: "Adjudication"' in cost
    assert 'label: "Reviewer"' in cost
    assert 'label: "Judge"' in cost
    assert 'label: "Validator"' in cost
    assert "adjudicationRows.reduce" in cost
    assert "breakdown: adjudicationRows.map" in cost
    assert 'class="panel result-chart-panel component-ledger"' in cost
    assert 'class="component-ledger panel-frame"' not in cost
    assert 'class="result-chart-stack"' in cost
    assert cost.count("result-chart-panel") == 2
    assert "`value-signal value-signal--${costBand(index)}`" in cost
    assert "min-width: 4rem;" in cost
    assert "Model time across the run." in time
    assert (
        "left.totals.guesser_think_time_ms -\n          right.totals.guesser_think_time_ms"
    ) in time
    assert ("left.totals.runtime_ms - right.totals.runtime_ms") in time
    assert "value: run.totals.guesser_think_time_ms" in time
    assert "value: run.totals.runtime_ms" in time
    assert 'direction-label="Model time · lower is faster"' in time
    assert 'label="Model time"' in time
    assert 'label="End-to-end time"' in time
    assert "End-to-end benchmark time" in time
    assert 'direction-label="End-to-end time · lower is faster"' in time
    assert 'class="panel result-chart-panel runtime-ledger"' in time
    assert 'class="runtime-ledger panel-frame"' not in time
    assert 'class="result-chart-stack"' in time
    assert time.count("result-chart-panel") == 2
    assert ".result-chart-stack" in app_css
    assert ".result-chart-panel" in app_css
    assert ".result-chart-panel > .panel-heading h2" in app_css
    assert ".result-chart-panel > .panel-heading h3" in app_css
    assert "align-items: start;" in app_css
    assert "gap: clamp(1.5rem, 4vw, 2.5rem);" in app_css
    assert ".result-chart-panel > .panel-heading" in app_css
    assert "@media (min-width: 761px)" in app_css
    assert "border-bottom: 0;" in app_css
    assert "average penalized trial values" in efficiency
    assert "normalized question score 0.06" in efficiency
    assert "Guesser cost range" in efficiency
    assert 'label="Ideal distance"' in efficiency
    assert 'label="Trade-off map"' in efficiency
    assert 'class="tradeoff-panel panel-frame"' in efficiency
    assert 'class="tradeoff-copy"' in efficiency
    assert 'class="tradeoff-visual"' in efficiency
    assert 'class="expanded-chart-dialog"' in efficiency
    assert 'class="expanded-chart-legend"' in efficiency
    assert "openExpandedChart" in efficiency
    assert "Close expanded graph" in efficiency
    assert "chart-expand-icon" in efficiency
    assert "border-bottom-color: currentColor" in efficiency
    assert '<h3 id="tradeoff-title">Normalized cost and question score.</h3>' in efficiency
    assert efficiency.count("result-chart-panel") == 1
    assert 'color="efficiency"' in efficiency
    assert "ideal_distance_rank" in efficiency
    assert "ideal_distance_score" in efficiency
    assert "product_efficiency_rank" not in efficiency
    assert "cost_adjusted_question_score" not in efficiency
    assert "Legacy product" not in efficiency
    assert "pareto_efficient" in efficiency
    assert "pareto-badge" in efficiency
    assert "efficiency-results-table" in efficiency
    assert "efficiency-col--pareto" in efficiency
    assert "table-layout: fixed" in efficiency
    assert 'label: "Pareto-efficient"' in efficiency
    assert "Lowest ideal distance" not in efficiency
    assert "confidenceIntervalWidth" in reliability
    assert "left.intervalWidth - right.intervalWidth" in reliability
    assert "reliabilityChartItems" in reliability
    assert "Stable does not mean good" in reliability
    assert "Every model uses the same 95% confidence level" in reliability
    assert 'label="CI width"' in reliability
    assert 'label="Score and stability"' in reliability
    assert "smaller CI width" in " ".join(reliability.split())
    assert "Question score." in overview
    assert "questionScoreChartSummary" in overview
    assert "companion plot shows each exact" in result_chart
    assert "visual guide, not fixed quality thresholds" in overview
    assert '"CI width · lower is better"' in reliability_scatter
    assert '"Question score"' in reliability_scatter
    assert "value: [item.intervalWidth, item.score]" in reliability_scatter
    assert "theme.results.stability" in reliability_scatter
    assert "Lower-left is better" in reliability_scatter
    assert 'class="result-help"' in result_help
    assert "<slot />" in result_help
    assert "padding: 0;" not in result_help
    assert "Definitions" not in result_help
    assert "font-size: var(--text-small);" in result_help
    assert "opacity: 0.78;" not in result_help
    assert ".panel-heading--with-help" in app_css
    assert 'grid-template-areas: "title text help";' in app_css
    assert ".panel-heading--with-help > .result-help" in app_css
    assert "padding-left: 1rem;" in app_css
    assert 'class="metric-definition-card"' in metric_definition_card
    assert "font-size: var(--text-card-title);" in metric_definition_card
    assert "align-content: start;" in metric_definition_card
    assert '<details class="disclosure metric-definition-details">' in metric_definition_card
    assert "<MetricDefinitionCard" in efficiency
    assert "<MetricDefinitionCard" in reliability
    assert "definition-section" not in efficiency
    assert "definition-section" not in reliability


def test_mobile_drilldowns_keep_all_facts_and_compact_turn_navigation() -> None:
    source_root = REPOSITORY / "source" / "publication" / "site" / "src"
    episode = _episode_source()
    drilldown = (source_root / "components" / "DrilldownBar.vue").read_text(encoding="utf-8")
    app_css = _site_styles_source()
    run_overview = (source_root / "views" / "workspace" / "RunOverviewPane.vue").read_text(
        encoding="utf-8"
    )
    subject_workspace = (
        source_root / "views" / "workspace" / "SubjectWorkspaceView.vue"
    ).read_text(encoding="utf-8")
    results_nav = (source_root / "components" / "ResultsNav.vue").read_text(encoding="utf-8")

    assert 'class="turn-map"' in episode
    assert 'id="turn-map-title"' in episode
    assert "jumpToTurn(turn.turnNumber)" in episode
    assert ':id="`turn-${turn.turn_number}`"' in episode
    assert "answerCounts" in episode
    assert 'class="episode-summary-metrics"' in episode
    assert ':max-columns="5"' in episode
    assert "display: block;" in episode
    assert "grid-template-columns: repeat(5, minmax(0, 1fr));" in app_css
    assert "flex: 1 1 0;" in episode
    assert "grid-template-columns: 2.3rem minmax(0, 1fr) auto;" in episode
    assert ".answer span" in episode
    assert 'role="tablist"' in episode
    assert ":aria-selected=\"activeTab === 'transcript'\"" in episode
    assert "@keydown=\"onEpisodeTabKeydown($event, 'transcript')\"" in episode
    assert "@media (max-height: 520px)" in episode
    assert 'class="drilldown-mobile-crumbs"' in drilldown
    assert "crumbs.value.slice(-2)" in drilldown
    assert ".drilldown-mobile-crumbs" in app_css
    assert "font-size: 1.25rem;" in app_css
    assert "<CostDonut" in run_overview
    assert "current.totals.costs_usd.guesser" in run_overview
    assert "Recorded total" not in run_overview
    assert ':max-columns="4"' in run_overview
    assert 'class="attempt-score-track"' in subject_workspace
    assert 'class="eyebrow rail-section-label"' in subject_workspace
    assert 'aria-label="Episodes for this subject"' in subject_workspace
    assert "{{ trials.length }} · choose one" in subject_workspace
    assert "@media (max-height: 800px) and (min-width: 761px)" in subject_workspace
    assert 'exact-active-class="active"' in results_nav


def test_homepage_and_method_share_one_typed_illustrative_round() -> None:
    source_root = REPOSITORY / "source" / "publication" / "site" / "src"
    shared_round = (source_root / "lib" / "illustrative-round.ts").read_text(encoding="utf-8")
    homepage = (source_root / "views" / "HomeView.vue").read_text(encoding="utf-8")
    method = (source_root / "views" / "MethodologyView.vue").read_text(encoding="utf-8")
    story = (source_root / "views" / "StoryView.vue").read_text(encoding="utf-8")

    assert "satisfies IllustrativeRound" in shared_round
    assert "<IllustrativeRoundExample />" in homepage
    assert "<IllustrativeRoundExample />" in method
    assert 'from "@/lib/illustrative-round"' not in story
    assert "2 September 2026" in story
    assert "Claude Fable 5.1 (high) added." in story
    assert "12.1 questions with 34 of 35 successful trials." in story
    assert "23 August 2026" in story
    assert "OpenRouter’s Ox Alpha (high) tested." in story
    assert "17.6 questions, placing 12th of 15." in story
    assert "15 August 2026" in story
    assert "17 August 2026" in story
    assert "Gemini 3.7 Flash (high) added." in story
    assert "Grok 4.6 (high) added." in story
    assert "5 August 2026" in story
    assert "Claude Fable 5 (high) added." in story
    assert 'class="round-section"' not in story
    assert 'class="scope-section"' not in story
    assert 'class="apple-spotlight"' not in story
