from decimal import Decimal

import pytest

from deep20_publication.uncertainty import (
    _student_t_quantile,
    stratified_question_score_confidence_interval,
)


def _decimals(*values: int) -> tuple[Decimal, ...]:
    return tuple(Decimal(value) for value in values)


def test_student_t_quantile_matches_reference_values() -> None:
    assert _student_t_quantile(0.975, 4) == pytest.approx(2.7764451052)
    assert _student_t_quantile(0.975, 6) == pytest.approx(2.4469118511)
    assert _student_t_quantile(0.975, 34) == pytest.approx(2.0322445093)


def test_stratified_interval_uses_all_trials_without_random_subject_variance() -> None:
    interval = stratified_question_score_confidence_interval(
        (
            _decimals(14, 7, 10, 8, 9),
            _decimals(23, 24, 24, 25, 27),
            _decimals(13, 10, 12, 14, 12),
            _decimals(11, 23, 12, 11, 13),
            _decimals(7, 6, 7, 7, 7),
            _decimals(12, 11, 14, 14, 13),
            _decimals(6, 5, 8, 8, 5),
        ),
        estimate=Decimal(432) / Decimal(35),
    )

    assert interval is not None
    assert interval.method == "stratified-welch-t-v1"
    assert interval.confidence_level == Decimal("0.95")
    assert interval.subject_count == 7
    assert interval.trial_count == 35
    assert interval.estimate == Decimal(432) / Decimal(35)
    assert float(interval.standard_error) == pytest.approx(0.4140393356)
    assert float(interval.degrees_of_freedom or 0) == pytest.approx(9.4376972875)
    assert float(interval.lower) == pytest.approx(11.4128149952)
    assert float(interval.upper) == pytest.approx(13.2728992905)


def test_zero_trial_variance_produces_a_zero_width_interval() -> None:
    interval = stratified_question_score_confidence_interval(
        (_decimals(4, 4, 4), _decimals(20, 20, 20)),
        estimate=Decimal(12),
    )

    assert interval is not None
    assert interval.estimate == Decimal(12)
    assert interval.lower == interval.estimate
    assert interval.upper == interval.estimate
    assert interval.standard_error == 0
    assert interval.degrees_of_freedom is None


def test_interval_requires_two_trials_in_every_subject() -> None:
    assert (
        stratified_question_score_confidence_interval(
            (_decimals(1),),
            estimate=Decimal(1),
        )
        is None
    )
