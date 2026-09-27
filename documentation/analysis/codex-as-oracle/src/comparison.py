"""Compare completed direct-adjudication games with the saved regular run."""

from __future__ import annotations

from decimal import Decimal

import bridge
from deep20_benchmark.artifacts import ArtifactStore
from deep20_benchmark.models import (
    BenchmarkExecutionId,
    CompletedTrialResult,
    TrialBenchmarkResult,
)
from deep20_oracle.models import StrictModel
from deep20_oracle.util import load_yaml_unique, timestamp

BASELINE = bridge.BASELINE


class TrialEnvelope(StrictModel):
    payload: TrialBenchmarkResult
    integrity_hash: str


class IterationComparison(StrictModel):
    iteration: int
    regular_questions: int | None
    regular_score: int | None
    regular_success: bool | None
    direct_questions: int | None
    direct_score: int | None
    direct_success: bool | None
    improvement: int | None


class SubjectComparison(StrictModel):
    target_id: str
    name: str
    iterations: tuple[IterationComparison, ...]
    regular_average: Decimal | None
    direct_average: Decimal | None
    matched_average_improvement: Decimal | None
    complete: bool


class Comparison(StrictModel):
    baseline_execution: str
    direct_execution: str
    updated_at: str
    completed_games: int
    scheduled_games: int
    subjects: tuple[SubjectComparison, ...]
    guesser_configuration_matches: bool
    game_policy_matches: bool
    subject_snapshots_match: bool | None
    base_seed_matches: bool
    comparison_notes: tuple[str, ...]


def mean(values: tuple[int, ...]) -> Decimal | None:
    return Decimal(sum(values)) / len(values) if values else None


def score(trial: TrialBenchmarkResult | None) -> int | None:
    if not isinstance(trial, CompletedTrialResult) or not trial.result.scoring_eligible:
        return None
    return trial.result.counted_questions if trial.result.success else 41


def show(value: Decimal | None) -> str:
    return f"{value:.2f}" if value is not None else "-"


def main() -> None:
    original = ArtifactStore(bridge.REPOSITORY)
    baseline = original.load_benchmark_result(bridge.MODEL, BASELINE)
    if baseline is None:
        raise ValueError("regular comparison run is missing")
    direct = ArtifactStore(bridge.REPOSITORY)
    direct.runs_root = bridge.ROOT / "runs"
    manifest = direct.load_manifest(bridge.MODEL, BenchmarkExecutionId(bridge.EXECUTION))
    if manifest is None:
        raise ValueError("direct experiment manifest is missing")
    direct_trials: list[TrialBenchmarkResult] = []
    for path in sorted(
        direct.run_root(bridge.MODEL, bridge.EXECUTION).glob("subjects/*/trials/*/result.yml")
    ):
        envelope = TrialEnvelope.model_validate(load_yaml_unique(path))
        trial = direct.load_trial_result(envelope.payload.identity)
        if trial is not None:
            direct_trials.append(trial)
    rows: list[SubjectComparison] = []
    for subject in baseline.subjects:
        if subject.subject.target_id not in {str(value) for value in manifest.definition.subject_ids}:
            continue
        comparisons: list[IterationComparison] = []
        for iteration in range(1, manifest.definition.iterations + 1):
            regular = next(
                (trial for trial in subject.trials if trial.identity.trial_number == iteration), None
            )
            current = next(
                (
                    t
                    for t in direct_trials
                    if str(t.identity.target_id) == subject.subject.target_id
                    and t.identity.trial_number == iteration
                ),
                None,
            )
            left, right = score(regular), score(current)
            comparisons.append(
                IterationComparison(
                    iteration=iteration,
                    regular_questions=regular.result.counted_questions
                    if isinstance(regular, CompletedTrialResult)
                    else None,
                    regular_score=left,
                    regular_success=regular.result.success
                    if isinstance(regular, CompletedTrialResult)
                    else None,
                    direct_questions=current.result.counted_questions
                    if isinstance(current, CompletedTrialResult)
                    else None,
                    direct_score=right,
                    direct_success=current.result.success
                    if isinstance(current, CompletedTrialResult)
                    else None,
                    improvement=left - right if left is not None and right is not None else None,
                )
            )
        rows.append(
            SubjectComparison(
                target_id=subject.subject.target_id,
                name=subject.subject.canonical_name,
                iterations=tuple(comparisons),
                regular_average=mean(
                    tuple(i.regular_score for i in comparisons if i.regular_score is not None)
                ),
                direct_average=mean(
                    tuple(i.direct_score for i in comparisons if i.direct_score is not None)
                ),
                matched_average_improvement=mean(
                    tuple(i.improvement for i in comparisons if i.improvement is not None)
                ),
                complete=all(i.direct_score is not None for i in comparisons),
            )
        )
    completed = tuple(t for t in direct_trials if isinstance(t, CompletedTrialResult))
    report = Comparison(
        baseline_execution=str(BASELINE),
        direct_execution=bridge.EXECUTION,
        updated_at=timestamp(),
        completed_games=sum(isinstance(t, CompletedTrialResult) for t in direct_trials),
        scheduled_games=len(manifest.definition.subject_ids) * manifest.definition.iterations,
        subjects=tuple(rows),
        guesser_configuration_matches=baseline.run.model.configuration
        == manifest.model.configuration,
        game_policy_matches=baseline.run.definition.game_policy == manifest.definition.game_policy,
        subject_snapshots_match=all(
            any(s.subject == trial.result.run.subject for s in baseline.subjects)
            for trial in completed
        ) if completed else None,
        base_seed_matches=baseline.run.base_seed == manifest.request.base_seed,
        comparison_notes=(
            "Lower scores are better. Model failures score 41; infrastructure failures have no score.",
            "Positive improvement means fewer questions with Codex on matching completed iterations.",
            "Pending direct games do not contribute to direct averages or paired differences.",
            "The regular run uses independent support models and compatible ASK answer reuse.",
            "The direct run uses this Codex conversation for all support decisions and disables ASK reuse.",
            "Support roles, answer reuse and execution dates differ; this comparison does not isolate one cause.",
        ),
    )
    bridge.write_model(bridge.ROOT / "comparison.json", report)
    lines = [
        f"# {baseline.run.model.display_name}: direct versus regular adjudication",
        "",
        f"Updated {report.updated_at}. Completed {report.completed_games}/{report.scheduled_games} games.",
        "",
        "Scores are questions; lower is better. A failed game scores 41. A dash means pending.",
        "Improvement compares only matching completed iterations; positive values favor direct Codex.",
        "",
        "| Subject | Regular iterations | Regular mean | Codex iterations | Codex mean so far | Paired improvement |",
        "| --- | --- | ---: | --- | ---: | ---: |",
    ]
    for row in rows:
        regular_scores = " / ".join(
            str(i.regular_score) if i.regular_score is not None else "-" for i in row.iterations
        )
        direct_scores = " / ".join(
            str(i.direct_score) if i.direct_score is not None else "-" for i in row.iterations
        )
        lines.append(
            f"| {row.name} | {regular_scores} | {show(row.regular_average)} | "
            f"{direct_scores} | {show(row.direct_average)} | {show(row.matched_average_improvement)} |"
        )
    lines.extend(
        (
            "",
            "Game policy matches: " + str(report.game_policy_matches),
            "Guesser configuration matches: " + str(report.guesser_configuration_matches),
            "Subject snapshots match: " + str(report.subject_snapshots_match),
            "Base seed matches: " + str(report.base_seed_matches),
            "",
        )
    )
    lines.extend(report.comparison_notes)
    (bridge.ROOT / "comparison.md").write_text("\n".join(lines) + "\n")
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
