from __future__ import annotations

import math
from decimal import Decimal, localcontext
from typing import Literal

from .models import QuestionScoreConfidenceInterval

CONFIDENCE_LEVEL = Decimal("0.95")
CONFIDENCE_METHOD: Literal["stratified-welch-t-v1"] = "stratified-welch-t-v1"


def _average(values: tuple[Decimal, ...]) -> Decimal:
    return sum(values, start=Decimal(0)) / Decimal(len(values))


def _sample_variance(values: tuple[Decimal, ...]) -> Decimal:
    mean = _average(values)
    return sum((value - mean) ** 2 for value in values) / Decimal(len(values) - 1)


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    maximum_iterations = 200
    epsilon = 3e-14
    minimum = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < minimum:
        d = minimum
    d = 1.0 / d
    result = d
    for iteration in range(1, maximum_iterations + 1):
        doubled = 2 * iteration
        coefficient = iteration * (b - iteration) * x / ((qam + doubled) * (a + doubled))
        d = 1.0 + coefficient * d
        if abs(d) < minimum:
            d = minimum
        c = 1.0 + coefficient / c
        if abs(c) < minimum:
            c = minimum
        d = 1.0 / d
        result *= d * c
        coefficient = -((a + iteration) * (qab + iteration) * x / ((a + doubled) * (qap + doubled)))
        d = 1.0 + coefficient * d
        if abs(d) < minimum:
            d = minimum
        c = 1.0 + coefficient / c
        if abs(c) < minimum:
            c = minimum
        d = 1.0 / d
        delta = d * c
        result *= delta
        if abs(delta - 1.0) <= epsilon:
            return result
    raise ArithmeticError("incomplete beta continued fraction did not converge")


def _regularized_incomplete_beta(a: float, b: float, x: float) -> float:
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    front = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _beta_continued_fraction(a, b, x) / a
    return 1.0 - front * _beta_continued_fraction(b, a, 1.0 - x) / b


def _student_t_cdf(value: float, degrees_of_freedom: float) -> float:
    beta_x = degrees_of_freedom / (degrees_of_freedom + value * value)
    tail = 0.5 * _regularized_incomplete_beta(
        degrees_of_freedom / 2.0,
        0.5,
        beta_x,
    )
    return 1.0 - tail if value >= 0 else tail


def _student_t_quantile(probability: float, degrees_of_freedom: float) -> float:
    if not 0.5 < probability < 1.0:
        raise ValueError("Student t quantile requires a probability between 0.5 and 1")
    if degrees_of_freedom <= 0:
        raise ValueError("Student t quantile requires positive degrees of freedom")
    lower = 0.0
    upper = 1.0
    while _student_t_cdf(upper, degrees_of_freedom) < probability:
        upper *= 2.0
    for _ in range(100):
        midpoint = (lower + upper) / 2.0
        if _student_t_cdf(midpoint, degrees_of_freedom) < probability:
            lower = midpoint
        else:
            upper = midpoint
    return (lower + upper) / 2.0


def stratified_question_score_confidence_interval(
    strata: tuple[tuple[Decimal, ...], ...],
    *,
    estimate: Decimal,
) -> QuestionScoreConfidenceInterval | None:
    """Estimate repeated-trial uncertainty for fixed, equally weighted subjects."""
    if not strata or any(len(values) < 2 for values in strata):
        return None
    with localcontext() as context:
        context.prec = 40
        subject_count = Decimal(len(strata))
        variance_terms = tuple(
            _sample_variance(values) / (subject_count * subject_count * Decimal(len(values)))
            for values in strata
        )
        estimated_variance = sum(variance_terms, start=Decimal(0))
        standard_error = estimated_variance.sqrt()
        trial_count = sum(len(values) for values in strata)
        if standard_error == 0:
            return QuestionScoreConfidenceInterval(
                confidence_level=CONFIDENCE_LEVEL,
                method=CONFIDENCE_METHOD,
                estimate=estimate,
                lower=estimate,
                upper=estimate,
                standard_error=Decimal(0),
                degrees_of_freedom=None,
                subject_count=len(strata),
                trial_count=trial_count,
            )
        denominator = sum(
            term * term / Decimal(len(values) - 1)
            for term, values in zip(variance_terms, strata, strict=True)
        )
        degrees_of_freedom = estimated_variance * estimated_variance / denominator
        critical_value = Decimal(
            format(
                _student_t_quantile(0.975, float(degrees_of_freedom)),
                ".15g",
            )
        )
        margin = critical_value * standard_error
        return QuestionScoreConfidenceInterval(
            confidence_level=CONFIDENCE_LEVEL,
            method=CONFIDENCE_METHOD,
            estimate=estimate,
            lower=estimate - margin,
            upper=estimate + margin,
            standard_error=standard_error,
            degrees_of_freedom=degrees_of_freedom,
            subject_count=len(strata),
            trial_count=trial_count,
        )
