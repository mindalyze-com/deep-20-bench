from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from deep20_game.models import guesser_contract_reliability
from deep20_oracle.models import OracleQuestionType
from deep20_oracle.recovery import combine_recovery_totals

from .models import (
    AggregateSummary,
    CompletedTrialResult,
    DistributionSummary,
    FailureCodeCount,
    InfrastructureFailedTrialResult,
    OracleQualityAggregate,
    OracleQuestionTypeAggregate,
    PartialTrialMetrics,
    RepairAggregate,
    ResultCounts,
    TrialBenchmarkResult,
)

SUMMARY_RATE_QUANTUM = Decimal("0.0001")
SUMMARY_USD_QUANTUM = Decimal("0.00000001")
SUMMARY_STATISTIC_QUANTUM = Decimal("0.01")


def round_summary_value(value: Decimal, quantum: Decimal) -> Decimal:
    """Round a published statistic and remove insignificant trailing zeroes."""
    rounded = value.quantize(quantum, rounding=ROUND_HALF_UP)
    text = format(rounded, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return Decimal(text)


def _quantile(values: tuple[Decimal, ...], fraction: Decimal) -> Decimal | None:
    if not values:
        return None
    ordered = tuple(sorted(values))
    if len(ordered) == 1:
        return ordered[0]
    position = Decimal(len(ordered) - 1) * fraction
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    remainder = position - Decimal(lower_index)
    return ordered[lower_index] + (ordered[upper_index] - ordered[lower_index]) * remainder


def distribution(
    values: tuple[Decimal, ...],
    *,
    quantum: Decimal = SUMMARY_STATISTIC_QUANTUM,
) -> DistributionSummary:
    if not values:
        return DistributionSummary(count=0)
    ordered = tuple(sorted(values))
    mean = sum(ordered, start=Decimal(0)) / Decimal(len(ordered))
    deviation = None
    if len(ordered) >= 2:
        variance = sum(
            ((value - mean) ** 2 for value in ordered),
            start=Decimal(0),
        ) / Decimal(len(ordered) - 1)
        deviation = variance.sqrt()
    p25 = _quantile(ordered, Decimal("0.25"))
    median = _quantile(ordered, Decimal("0.5"))
    p75 = _quantile(ordered, Decimal("0.75"))
    assert p25 is not None and median is not None and p75 is not None
    return DistributionSummary(
        count=len(ordered),
        minimum=round_summary_value(ordered[0], quantum),
        p25=round_summary_value(p25, quantum),
        median=round_summary_value(median, quantum),
        p75=round_summary_value(p75, quantum),
        maximum=round_summary_value(ordered[-1], quantum),
        mean=round_summary_value(mean, quantum),
        sample_standard_deviation=(
            round_summary_value(deviation, quantum) if deviation is not None else None
        ),
    )


def summary_total(
    values: tuple[Decimal, ...],
    *,
    quantum: Decimal = SUMMARY_STATISTIC_QUANTUM,
) -> Decimal:
    return round_summary_value(
        sum(values, start=Decimal(0)),
        quantum,
    )


def _aggregate_superseded_attempts(
    trials: tuple[TrialBenchmarkResult, ...],
) -> RepairAggregate:
    attempts = tuple(
        attempt for trial in trials for attempt in trial.superseded_attempts
    )
    failure_counts: dict[str, int] = {}
    for attempt in attempts:
        failure_counts[attempt.failure.code] = (
            failure_counts.get(attempt.failure.code, 0) + 1
        )
    return RepairAggregate(
        superseded_attempts=len(attempts),
        affected_trials=sum(bool(trial.superseded_attempts) for trial in trials),
        partial_metrics=PartialTrialMetrics(
            counted_questions=sum(
                attempt.partial_metrics.counted_questions for attempt in attempts
            ),
            guesser_cost_usd=sum(
                (
                    attempt.partial_metrics.guesser_cost_usd
                    for attempt in attempts
                ),
                start=Decimal(0),
            ),
            oracle_cost_usd=sum(
                (
                    attempt.partial_metrics.oracle_cost_usd
                    for attempt in attempts
                ),
                start=Decimal(0),
            ),
            reviewer_cost_usd=sum(
                (
                    attempt.partial_metrics.reviewer_cost_usd
                    for attempt in attempts
                ),
                start=Decimal(0),
            ),
            judge_cost_usd=sum(
                (
                    attempt.partial_metrics.judge_cost_usd
                    for attempt in attempts
                ),
                start=Decimal(0),
            ),
            validator_cost_usd=sum(
                (
                    attempt.partial_metrics.validator_cost_usd
                    for attempt in attempts
                ),
                start=Decimal(0),
            ),
            cost_usd=sum(
                (attempt.partial_metrics.cost_usd for attempt in attempts),
                start=Decimal(0),
            ),
            tokens=sum(attempt.partial_metrics.tokens for attempt in attempts),
            cached_input_tokens=sum(
                attempt.partial_metrics.cached_input_tokens for attempt in attempts
            ),
            cache_write_tokens=sum(
                attempt.partial_metrics.cache_write_tokens for attempt in attempts
            ),
            estimated_cache_savings_usd=sum(
                (
                    attempt.partial_metrics.estimated_cache_savings_usd
                    for attempt in attempts
                ),
                start=Decimal(0),
            ),
            latency_ms=sum(attempt.partial_metrics.latency_ms for attempt in attempts),
            duration_ms=sum(attempt.partial_metrics.duration_ms for attempt in attempts),
            recovery=combine_recovery_totals(
                *(attempt.partial_metrics.recovery for attempt in attempts)
            ),
        ),
        failure_codes=tuple(
            FailureCodeCount(code=code, count=count)
            for code, count in sorted(failure_counts.items())
        ),
    )


def aggregate_trials(
    trials: tuple[TrialBenchmarkResult, ...],
    *,
    scheduled: int | None = None,
) -> AggregateSummary:
    completed = tuple(
        trial for trial in trials if isinstance(trial, CompletedTrialResult)
    )
    infrastructure = tuple(
        trial for trial in trials if isinstance(trial, InfrastructureFailedTrialResult)
    )
    eligible = tuple(trial for trial in completed if trial.result.scoring_eligible)
    successful = tuple(trial for trial in eligible if trial.result.success)
    publication = tuple(trial for trial in completed if trial.result.publication_eligible)
    model_failed = tuple(trial for trial in eligible if not trial.result.success)
    repair = _aggregate_superseded_attempts(trials)

    question_values = tuple(Decimal(trial.result.counted_questions) for trial in eligible)
    successful_question_values = tuple(
        Decimal(trial.result.counted_questions) for trial in successful
    )
    cost_values = tuple(trial.result.costs_usd.total for trial in completed) + tuple(
        trial.partial_metrics.cost_usd for trial in infrastructure
    )
    guesser_cost_values = tuple(
        trial.result.costs_usd.guesser for trial in completed
    ) + tuple(trial.partial_metrics.guesser_cost_usd for trial in infrastructure)
    oracle_cost_values = tuple(
        trial.result.costs_usd.oracle for trial in completed
    ) + tuple(trial.partial_metrics.oracle_cost_usd for trial in infrastructure)
    validator_cost_values = tuple(
        trial.result.costs_usd.validator for trial in completed
    ) + tuple(trial.partial_metrics.validator_cost_usd for trial in infrastructure)
    token_values = tuple(Decimal(trial.result.tokens.total) for trial in completed) + tuple(
        Decimal(trial.partial_metrics.tokens) for trial in infrastructure
    )
    cached_input_values = tuple(
        Decimal(
            trial.result.llm.guesser.metrics.cached_input_tokens
            + trial.result.llm.oracle.metrics.cached_input_tokens
            + trial.result.llm.validator.metrics.cached_input_tokens
        )
        for trial in completed
    ) + tuple(Decimal(trial.partial_metrics.cached_input_tokens) for trial in infrastructure)
    cache_write_values = tuple(
        Decimal(
            trial.result.llm.guesser.metrics.cache_write_tokens
            + trial.result.llm.oracle.metrics.cache_write_tokens
            + trial.result.llm.validator.metrics.cache_write_tokens
        )
        for trial in completed
    ) + tuple(Decimal(trial.partial_metrics.cache_write_tokens) for trial in infrastructure)
    cache_savings_values = tuple(
        trial.result.llm.guesser.metrics.estimated_cache_savings_usd
        + trial.result.llm.oracle.metrics.estimated_cache_savings_usd
        + trial.result.llm.validator.metrics.estimated_cache_savings_usd
        for trial in completed
    ) + tuple(
        trial.partial_metrics.estimated_cache_savings_usd for trial in infrastructure
    )
    latency_values = tuple(
        Decimal(
            trial.result.llm.guesser.metrics.latency_ms
            + trial.result.llm.oracle.metrics.latency_ms
            + trial.result.llm.validator.metrics.latency_ms
        )
        for trial in completed
    ) + tuple(Decimal(trial.partial_metrics.latency_ms) for trial in infrastructure)
    duration_values = tuple(Decimal(trial.result.duration_ms) for trial in completed) + tuple(
        Decimal(trial.partial_metrics.duration_ms) for trial in infrastructure
    )
    recovery = combine_recovery_totals(
        *(
            combine_recovery_totals(
                trial.result.llm.guesser.metrics.recovery,
                trial.result.llm.oracle.metrics.recovery,
                trial.result.llm.validator.metrics.recovery,
            )
            if isinstance(trial, CompletedTrialResult)
            else trial.partial_metrics.recovery
            for trial in trials
        ),
        repair.partial_metrics.recovery,
    )
    evaluated_outputs = sum(
        trial.result.summary.contract.evaluated_outputs for trial in completed
    )
    contract_violations = sum(
        trial.result.summary.contract.violations for trial in completed
    )
    contract_penalties = sum(
        trial.result.summary.contract.counted_penalties for trial in completed
    )
    affected_trials = sum(
        trial.result.summary.contract.affected_trials for trial in completed
    )
    failure_counts: dict[str, int] = {}
    for trial in trials:
        failure = trial.failure
        if failure is not None:
            failure_counts[failure.code] = failure_counts.get(failure.code, 0) + 1
    eligible_count = len(eligible)
    reviewed_questions = sum(
        trial.result.summary.oracle_quality.reviewed_questions for trial in completed
    )
    agreements = sum(
        trial.result.summary.oracle_quality.agreements for trial in completed
    )
    disagreements = sum(
        trial.result.summary.oracle_quality.disagreements for trial in completed
    )
    judge_invocations = sum(
        trial.result.summary.oracle_quality.judge_invocations
        for trial in completed
    )
    oracle_answers_changed = sum(
        trial.result.summary.oracle_quality.oracle_answers_changed
        for trial in completed
    )
    question_type_reviews: dict[OracleQuestionType, int] = {}
    question_type_disagreements: dict[OracleQuestionType, int] = {}
    for trial in completed:
        for item in trial.result.summary.oracle_quality.question_types:
            question_type_reviews[item.question_type] = (
                question_type_reviews.get(item.question_type, 0)
                + item.reviewed_questions
            )
            question_type_disagreements[item.question_type] = (
                question_type_disagreements.get(item.question_type, 0)
                + item.disagreements
            )
    success_rate = (
        round_summary_value(
            Decimal(len(successful)) / Decimal(eligible_count),
            SUMMARY_RATE_QUANTUM,
        )
        if eligible_count
        else None
    )
    terminal = len(trials)
    return AggregateSummary(
        counts=ResultCounts(
            scheduled=scheduled if scheduled is not None else terminal,
            started=terminal,
            terminal=terminal,
            scoring_eligible=eligible_count,
            publication_eligible=len(publication),
            successful=len(successful),
            model_failed=len(model_failed),
            infrastructure_failed=len(infrastructure),
        ),
        success_rate=success_rate,
        questions_all_eligible=distribution(question_values),
        questions_successful=distribution(successful_question_values),
        guesser_cost_usd=distribution(
            guesser_cost_values,
            quantum=SUMMARY_USD_QUANTUM,
        ),
        oracle_cost_usd=distribution(
            oracle_cost_values,
            quantum=SUMMARY_USD_QUANTUM,
        ),
        validator_cost_usd=distribution(
            validator_cost_values,
            quantum=SUMMARY_USD_QUANTUM,
        ),
        cost_usd=distribution(cost_values, quantum=SUMMARY_USD_QUANTUM),
        total_cost_usd=summary_total(
            (*cost_values, repair.partial_metrics.cost_usd),
            quantum=SUMMARY_USD_QUANTUM,
        ),
        tokens=distribution(token_values),
        cached_input_tokens=distribution(cached_input_values),
        cache_write_tokens=distribution(cache_write_values),
        estimated_cache_savings_usd=distribution(
            cache_savings_values,
            quantum=SUMMARY_USD_QUANTUM,
        ),
        latency_ms=distribution(latency_values),
        duration_ms=distribution(duration_values),
        recovery=recovery,
        repair=repair,
        contract=guesser_contract_reliability(
            evaluated_outputs=evaluated_outputs,
            violations=contract_violations,
            counted_penalties=contract_penalties,
            affected_trials=affected_trials,
        ),
        oracle_quality=OracleQualityAggregate(
            reviewed_questions=reviewed_questions,
            agreements=agreements,
            disagreements=disagreements,
            agreement_rate=(
                round_summary_value(
                    Decimal(agreements) / Decimal(reviewed_questions),
                    SUMMARY_RATE_QUANTUM,
                )
                if reviewed_questions
                else None
            ),
            disagreement_rate=(
                round_summary_value(
                    Decimal(disagreements) / Decimal(reviewed_questions),
                    SUMMARY_RATE_QUANTUM,
                )
                if reviewed_questions
                else None
            ),
            judge_invocations=judge_invocations,
            oracle_answers_changed=oracle_answers_changed,
            oracle_answer_change_rate=(
                round_summary_value(
                    Decimal(oracle_answers_changed) / Decimal(judge_invocations),
                    SUMMARY_RATE_QUANTUM,
                )
                if judge_invocations
                else None
            ),
            final_unknown_answers=sum(
                trial.result.summary.oracle_quality.final_unknown_answers
                for trial in completed
            ),
            judge_yes_answers=sum(
                trial.result.summary.oracle_quality.judge_yes_answers
                for trial in completed
            ),
            judge_no_answers=sum(
                trial.result.summary.oracle_quality.judge_no_answers
                for trial in completed
            ),
            judge_unknown_answers=sum(
                trial.result.summary.oracle_quality.judge_unknown_answers
                for trial in completed
            ),
            reviewer_cost_usd=round_summary_value(
                sum(
                    (
                        trial.result.summary.oracle_quality.reviewer_cost_usd
                        for trial in completed
                    ),
                    start=Decimal(0),
                ),
                SUMMARY_USD_QUANTUM,
            ),
            judge_cost_usd=round_summary_value(
                sum(
                    (
                        trial.result.summary.oracle_quality.judge_cost_usd
                        for trial in completed
                    ),
                    start=Decimal(0),
                ),
                SUMMARY_USD_QUANTUM,
            ),
            quality_control_cost_usd=round_summary_value(
                sum(
                    (
                        trial.result.summary.oracle_quality.quality_control_cost_usd
                        for trial in completed
                    ),
                    start=Decimal(0),
                ),
                SUMMARY_USD_QUANTUM,
            ),
            question_types=tuple(
                OracleQuestionTypeAggregate(
                    question_type=question_type,
                    reviewed_questions=reviewed,
                    disagreements=question_type_disagreements[question_type],
                    disagreement_rate=round_summary_value(
                        Decimal(question_type_disagreements[question_type])
                        / Decimal(reviewed),
                        SUMMARY_RATE_QUANTUM,
                    ),
                )
                for question_type, reviewed in sorted(
                    question_type_reviews.items(),
                    key=lambda item: item[0].value,
                )
            ),
        ),
        failure_codes=tuple(
            FailureCodeCount(code=code, count=count)
            for code, count in sorted(failure_counts.items())
        ),
    )
