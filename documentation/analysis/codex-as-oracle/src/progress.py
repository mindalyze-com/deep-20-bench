"""Read only persisted outcomes and report a running question score."""

from __future__ import annotations

import json
from decimal import Decimal

import bridge
from deep20_benchmark.artifacts import ArtifactStore
from deep20_benchmark.models import (
    BenchmarkExecutionId,
    BenchmarkRequest,
    CompletedTrialResult,
    TrialBenchmarkResult,
)
from deep20_oracle import load_subject_catalog
from deep20_oracle.models import ProviderResultAudit, StrictModel
from deep20_oracle.util import load_yaml_unique
from pydantic import TypeAdapter
from spend_guard import BudgetState

adapter: TypeAdapter[TrialBenchmarkResult] = TypeAdapter(TrialBenchmarkResult)


class TrialEnvelope(StrictModel):
    payload: TrialBenchmarkResult
    integrity_hash: str


store = ArtifactStore(bridge.REPOSITORY)
store.runs_root = bridge.ROOT / "runs"
run_root = bridge.ROOT / "runs" / str(bridge.MODEL) / bridge.EXECUTION
manifest = store.load_manifest(bridge.MODEL, BenchmarkExecutionId(bridge.EXECUTION))
request_path = bridge.ROOT / "request.json"
scheduled_games: int | None = None
if manifest is not None:
    scheduled_games = len(manifest.definition.subject_ids) * manifest.definition.iterations
elif request_path.exists():
    prepared_request = BenchmarkRequest.model_validate_json(request_path.read_text())
    count = len(prepared_request.target_ids) or len(
        load_subject_catalog(bridge.REPOSITORY / "config/subjects.yaml").active_subjects()
    )
    scheduled_games = count * (prepared_request.iterations_override or 3)
budget: BudgetState | None = None
if (bridge.ROOT / "experiment.json").exists() and (bridge.ROOT / "budget.json").exists():
    budget = BudgetState.model_validate_json((bridge.ROOT / "budget.json").read_text())
loaded_trials = tuple(
    store.load_trial_result(TrialEnvelope.model_validate(load_yaml_unique(path)).payload.identity)
    for path in sorted(run_root.glob("subjects/*/trials/*/result.yml"))
)
trials = tuple(t for t in loaded_trials if t is not None)
completed = tuple(t for t in trials if isinstance(t, CompletedTrialResult))
eligible = tuple(t for t in completed if t.result.scoring_eligible)
scores = tuple(Decimal(t.result.counted_questions if t.result.success else 41) for t in eligible)
guesser_cost = sum((t.result.costs_usd.guesser for t in completed), Decimal(0))
canary_path = bridge.ROOT / "guesser-canary-usage.json"
canary_cost: Decimal | None = None
if canary_path.exists():
    canary_cost = ProviderResultAudit.model_validate_json(
        canary_path.read_text()
    ).usage.cost_usd
subjects = tuple(sorted({str(t.identity.target_id) for t in trials}))
subject_scores = {
    subject: [
        Decimal(t.result.counted_questions if t.result.success else 41)
        for t in eligible
        if str(t.identity.target_id) == subject
    ]
    for subject in subjects
}
balanced = [sum(values) / len(values) for values in subject_scores.values() if values]
print(
    json.dumps(
        {
            "completed_games": len(completed),
            "scheduled_games": scheduled_games,
            "infrastructure_failures": len(trials) - len(completed),
            "successes": sum(t.result.success for t in eligible),
            "eligible_games": len(eligible),
            "running_game_mean_question_score": str(sum(scores) / len(scores)) if scores else None,
            "running_subject_mean_question_score": str(sum(balanced) / len(balanced))
            if balanced
            else None,
            "completed_game_guesser_cost_usd": str(guesser_cost),
            "canary_cost_usd": str(canary_cost) if canary_cost is not None else None,
            "budget": budget.model_dump(mode="json") if budget is not None else None,
            "subjects": {
                key: [str(value) for value in values] for key, values in subject_scores.items()
            },
            "waiting_for_codex": (bridge.ROOT / "work/pending.json").exists(),
        },
        indent=2,
    )
)
