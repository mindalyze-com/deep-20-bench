"""Comparison eligibility is separate from any measured performance difference."""

from .models import BenchmarkManifest


def require_comparable(left: BenchmarkManifest, right: BenchmarkManifest) -> None:
    a, b = left.request.edition, right.request.edition
    if a is None or b is None:
        raise ValueError("historical run lacks an edition preflight; inspect its recorded contract explicitly")
    if ((a.edition_id, a.profile_hash, a.comparison_hash, a.classification)
            != (b.edition_id, b.profile_hash, b.comparison_hash, b.classification)):
        raise ValueError("comparison_contract_mismatch: editions, rules, subjects, prompts or trial schedules differ")
