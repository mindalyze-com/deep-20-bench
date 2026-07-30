from __future__ import annotations

from decimal import Decimal

from deep20_benchmark.aggregation import (
    SUMMARY_STATISTIC_QUANTUM,
    SUMMARY_USD_QUANTUM,
    distribution,
    summary_total,
)


def test_cost_distribution_removes_provider_precision_noise() -> None:
    summary = distribution(
        (
            Decimal("0.0461856500000000005"),
            Decimal("0.3584398500000000014"),
        ),
        quantum=SUMMARY_USD_QUANTUM,
    )

    assert summary.minimum == Decimal("0.04618565")
    assert summary.p25 == Decimal("0.1242492")
    assert summary.median == Decimal("0.20231275")
    assert summary.p75 == Decimal("0.2803763")
    assert summary.maximum == Decimal("0.35843985")
    assert summary.mean == Decimal("0.20231275")
    assert summary.sample_standard_deviation == Decimal("0.22079706")


def test_general_statistics_use_two_decimals_without_redundant_zeroes() -> None:
    summary = distribution(
        (Decimal(1), Decimal(2), Decimal(8)),
        quantum=SUMMARY_STATISTIC_QUANTUM,
    )

    assert summary.minimum == Decimal(1)
    assert summary.median == Decimal(2)
    assert summary.mean == Decimal("3.67")
    assert summary.sample_standard_deviation == Decimal("3.79")


def test_total_cost_rounds_the_exact_sum_instead_of_multiplying_the_rounded_mean() -> None:
    values = (Decimal("0.000000014"), Decimal("0.000000014"))
    summary = distribution(values, quantum=SUMMARY_USD_QUANTUM)

    assert summary.mean == Decimal("0.00000001")
    assert summary_total(
        values,
        quantum=SUMMARY_USD_QUANTUM,
    ) == Decimal("0.00000003")
