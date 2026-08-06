from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from .models import (
    AggregateSummary,
    BenchmarkResult,
    BenchmarkState,
    CompletedTrialResult,
    DistributionSummary,
    SubjectBenchmarkResult,
)


def _rate(summary: AggregateSummary) -> str:
    return "n/a" if summary.success_rate is None else f"{summary.success_rate * 100:.1f}%"


def _median(summary: AggregateSummary) -> str:
    value = summary.questions_all_eligible.median
    return _decimal(value)


def _contract_rate(summary: AggregateSummary) -> str:
    return _percentage(summary.contract.compliance_rate)


def _percentage(value: Decimal | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def _contract_line(summary: AggregateSummary) -> str:
    contract = summary.contract
    return (
        f"- Output-contract reliability: `{contract.status}` · "
        f"compliance `{_contract_rate(summary)}` · "
        f"{contract.violations} violation(s) across "
        f"{contract.affected_trials} trial(s) · "
        f"{contract.counted_penalties} counted-turn penalties"
    )


def _oracle_quality_line(summary: AggregateSummary) -> str:
    quality = summary.oracle_quality
    return (
        "- Oracle quality control: "
        f"{quality.reviewed_questions} reviewed · "
        f"agreement `{_percentage(quality.agreement_rate)}` · "
        f"{quality.disagreements} disagreement(s) / "
        f"{quality.judge_invocations} Judge call(s) · "
        f"{quality.oracle_answers_changed} Oracle answer(s) changed "
        f"(`{_percentage(quality.oracle_answer_change_rate)}`) · "
        f"QC cost `{_cost(quality.quality_control_cost_usd)}` USD"
    )


def _oracle_question_type_line(summary: AggregateSummary) -> str:
    if not summary.oracle_quality.question_types:
        return "- Oracle disagreement by question type: n/a"
    values = " · ".join(
        f"`{item.question_type}` "
        f"{item.disagreements}/{item.reviewed_questions} "
        f"(`{_percentage(item.disagreement_rate)}`)"
        for item in summary.oracle_quality.question_types
    )
    return f"- Oracle disagreement by question type: {values}"


def _decimal(value: Decimal | None) -> str:
    if value is None:
        return "n/a"
    return format(value.normalize(), "f")


def _cost(value: Decimal | None) -> str:
    return "n/a" if value is None else format(value, ".4f")


def _duration(value: Decimal | None) -> str:
    return "n/a" if value is None else f"{value / Decimal(1_000):.1f}"


def _range(
    distribution: DistributionSummary,
    formatter: Callable[[Decimal | None], str] = _decimal,
) -> str:
    if distribution.minimum is None or distribution.maximum is None:
        return "n/a"
    return f"{formatter(distribution.minimum)}–{formatter(distribution.maximum)}"


def _overview_table(summary: AggregateSummary) -> list[str]:
    return [
        "| Metric | Median | Mean | Range |",
        "|---|---:|---:|---:|",
        (
            "| Questions (eligible) | "
            f"{_decimal(summary.questions_all_eligible.median)} | "
            f"{_decimal(summary.questions_all_eligible.mean)} | "
            f"{_range(summary.questions_all_eligible)} |"
        ),
        (
            "| Questions (successful) | "
            f"{_decimal(summary.questions_successful.median)} | "
            f"{_decimal(summary.questions_successful.mean)} | "
            f"{_range(summary.questions_successful)} |"
        ),
        (
            "| Guesser cost (USD) | "
            f"{_cost(summary.guesser_cost_usd.median)} | "
            f"{_cost(summary.guesser_cost_usd.mean)} | "
            f"{_range(summary.guesser_cost_usd, _cost)} |"
        ),
        (
            "| Oracle cost (USD) | "
            f"{_cost(summary.oracle_cost_usd.median)} | "
            f"{_cost(summary.oracle_cost_usd.mean)} | "
            f"{_range(summary.oracle_cost_usd, _cost)} |"
        ),
        (
            "| Verifier cost (USD) | "
            f"{_cost(summary.validator_cost_usd.median)} | "
            f"{_cost(summary.validator_cost_usd.mean)} | "
            f"{_range(summary.validator_cost_usd, _cost)} |"
        ),
        (
            "| Terminal-attempt cost (USD) | "
            f"{_cost(summary.cost_usd.median)} | "
            f"{_cost(summary.cost_usd.mean)} | "
            f"{_range(summary.cost_usd, _cost)} |"
        ),
        (
            "| Tokens | "
            f"{_decimal(summary.tokens.median)} | "
            f"{_decimal(summary.tokens.mean)} | "
            f"{_range(summary.tokens)} |"
        ),
        (
            "| LLM latency (ms) | "
            f"{_decimal(summary.latency_ms.median)} | "
            f"{_decimal(summary.latency_ms.mean)} | "
            f"{_range(summary.latency_ms)} |"
        ),
        (
            "| Trial duration (s) | "
            f"{_duration(summary.duration_ms.median)} | "
            f"{_duration(summary.duration_ms.mean)} | "
            f"{_range(summary.duration_ms, _duration)} |"
        ),
    ]


def _average_cost_line(summary: AggregateSummary) -> str:
    return (
        "- Average cost per terminal run (USD): "
        f"Guesser `{_cost(summary.guesser_cost_usd.mean)}` · "
        f"Oracle `{_cost(summary.oracle_cost_usd.mean)}` · "
        f"Verifier `{_cost(summary.validator_cost_usd.mean)}` · "
        f"Total `{_cost(summary.cost_usd.mean)}`"
    )


def _benchmark_total_cost(result: BenchmarkResult) -> Decimal:
    return result.summary.total_cost_usd


def _total_cost_line(value: Decimal) -> str:
    return f"- Total execution cost (USD): `{_cost(value)}`"


def _repair_line(summary: AggregateSummary) -> str:
    repair = summary.repair
    return (
        "- Superseded infrastructure attempts: "
        f"{repair.superseded_attempts} across {repair.affected_trials} trial(s) · "
        f"cost `{_cost(repair.partial_metrics.cost_usd)}` USD"
    )


def _trial_question_list(result: SubjectBenchmarkResult) -> str:
    values = []
    for trial in result.trials:
        if isinstance(trial, CompletedTrialResult):
            suffix = f" ({trial.failure.code})" if trial.failure is not None else ""
            values.append(f"{trial.identity.trial_id}={trial.result.counted_questions}{suffix}")
        else:
            values.append(
                f"{trial.identity.trial_id}={trial.partial_metrics.counted_questions} "
                "(infrastructure failed)"
            )
    return ", ".join(values)


def render_subject(result: SubjectBenchmarkResult) -> str:
    question_summary = result.summary.questions_all_eligible
    lines = [
        f"# {result.subject.canonical_name}",
        "",
        f"- Target: `{result.subject.target_id}`",
        f"- Success rate: {_rate(result.summary)}",
        f"- Counted questions by run: {_trial_question_list(result)}",
        (
            "- Counted questions (scoring-eligible): "
            f"average `{_decimal(question_summary.mean)}` · "
            f"minimum `{_decimal(question_summary.minimum)}` · "
            f"median `{_decimal(question_summary.median)}` · "
            f"maximum `{_decimal(question_summary.maximum)}`"
        ),
        _average_cost_line(result.summary),
        _repair_line(result.summary),
        _contract_line(result.summary),
        _oracle_quality_line(result.summary),
        _oracle_question_type_line(result.summary),
        "- Files: [raw result](result.yml)",
        "",
        (
            "| Trial | Status | Success | Questions | Contract | "
            "Violations | Cost (USD) | Result |"
        ),
        "|---|---|---:|---:|---|---:|---:|---|",
    ]
    for trial in result.trials:
        if isinstance(trial, CompletedTrialResult):
            status = str(trial.result.terminal_reason)
            if trial.failure is not None:
                status = f"{status} ({trial.failure.code})"
            lines.append(
                "| "
                f"{trial.identity.trial_id} | {status} | "
                f"{str(trial.result.success).lower()} | {trial.result.counted_questions} | "
                f"{trial.result.summary.contract.status} "
                f"({_percentage(trial.result.summary.contract.compliance_rate)}) | "
                f"{trial.result.summary.contract.violations} | "
                f"{_cost(trial.result.costs_usd.total)} | "
                f"[result](trials/{trial.identity.trial_id}/result.yml) |"
            )
        else:
            lines.append(
                "| "
                f"{trial.identity.trial_id} | infrastructure_failed | false | "
                f"{trial.partial_metrics.counted_questions} | not_evaluable | n/a | "
                f"{_cost(trial.partial_metrics.cost_usd)} | "
                f"[result](trials/{trial.identity.trial_id}/result.yml) |"
            )
    return "\n".join(lines) + "\n"


def render_benchmark(result: BenchmarkResult) -> str:
    model = result.run.model
    lines = [
        f"# {result.run.definition.display_name}",
        "",
        f"- Execution: `{result.run.execution_id}`",
        f"- Benchmark: `{result.run.definition.benchmark_id}`",
        f"- Model: `{model.model_id}` - {model.display_name}",
        f"- Exact route: `{model.configuration.model}`",
        f"- Execution commits: {', '.join(f'`{item}`' for item in result.run.git_commits)}",
        f"- Status: {'completed' if result.outcome.complete else 'failed'}",
        f"- Success rate: {_rate(result.summary)}",
        f"- Median counted questions: {_median(result.summary)}",
        f"- Subjects: {len(result.run.definition.subject_ids)}",
        f"- Iterations per subject: {result.run.definition.iterations}",
        (
            f"- Trials: {result.summary.counts.successful} successful / "
            f"{result.summary.counts.scoring_eligible} scoring-eligible / "
            f"{result.summary.counts.scheduled} scheduled"
        ),
        (
            f"- Completeness: {result.summary.counts.scoring_eligible}/"
            f"{result.summary.counts.scheduled} scheduled trials scoring-eligible"
        ),
        f"- Infrastructure failures: {result.summary.counts.infrastructure_failed}",
        (
            "- Recovery: "
            f"{result.summary.recovery.recovered_calls} recovered calls / "
            f"{result.summary.recovery.retried_calls} retried calls / "
            f"{result.summary.recovery.exhausted_retries} exhausted"
        ),
        _contract_line(result.summary),
        _oracle_quality_line(result.summary),
        _oracle_question_type_line(result.summary),
        (
            "- Terminal failure codes: "
            + (
                ", ".join(
                    f"`{item.code}`={item.count}"
                    for item in result.summary.failure_codes
                )
                or "none"
            )
        ),
        _average_cost_line(result.summary),
        _repair_line(result.summary),
        _total_cost_line(_benchmark_total_cost(result)),
        (
            "- Files: [raw summary](summary.yml) · [full typed result](result.yml) · "
            "[live state](state.yml)"
        ),
        "",
        "## Overall metrics",
        "",
        *_overview_table(result.summary),
        "",
        "## Subjects",
        "",
        (
            "| Subject | ID | Trials | Success rate | Contract compliance | "
            "Violations | Median questions | Mean cost (USD) | Files |"
        ),
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for subject in result.subjects:
        lines.append(
            f"| [{subject.subject.canonical_name}]"
            f"(subjects/{subject.subject.target_id}/summary.md) | "
            f"`{subject.subject.target_id}` | "
            f"{subject.summary.counts.terminal} | {_rate(subject.summary)} | "
            f"{_contract_rate(subject.summary)} ({subject.summary.contract.status}) | "
            f"{subject.summary.contract.violations} | "
            f"{_median(subject.summary)} | {_cost(subject.summary.cost_usd.mean)} | "
            f"[report](subjects/{subject.subject.target_id}/summary.md) · "
            f"[raw](subjects/{subject.subject.target_id}/result.yml) |"
        )
    lines.extend(
        [
            "",
            "Each subject report links to every individual typed trial result.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_progress(state: BenchmarkState) -> str:
    return (
        "\n".join(
            [
                f"# Benchmark {state.execution_id}",
                "",
                f"- Status: `{state.status}`",
                f"- Progress: {state.terminal_trials}/{state.scheduled_trials} terminal trials",
                f"- Model: `{state.model_id}`",
                f"- Current subject: `{state.current_target_id or '-'}`",
                f"- Current trial: `{state.current_trial_id or '-'}`",
                f"- Accumulated cost: {state.accumulated_cost_usd} USD",
                "",
                "This file is refreshed after every terminal trial. See `state.yml` for live state.",
            ]
        )
        + "\n"
    )
