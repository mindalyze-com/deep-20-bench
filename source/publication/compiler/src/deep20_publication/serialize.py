from __future__ import annotations

import csv
import io

from .models import PublicationDocument, PublishedDataset


def dataset_json(dataset: PublishedDataset) -> str:
    return dataset.model_dump_json(indent=2) + "\n"


def publication_document_json(document: PublicationDocument) -> str:
    return document.model_dump_json(indent=2) + "\n"


def leaderboard_csv(dataset: PublishedDataset) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(
        (
            "rank",
            "efficiency_rank",
            "ideal_distance_rank",
            "product_efficiency_rank",
            "pareto_efficient",
            "model_id",
            "model_name",
            "status",
            "execution_id",
            "question_score",
            "question_score_ci_lower",
            "question_score_ci_upper",
            "question_score_ci_method",
            "success_rate",
            "contract_status",
            "contract_compliance_rate",
            "contract_violations",
            "contract_affected_trials",
            "contract_counted_penalties",
            "successful",
            "terminal_trials",
            "total_cost_usd",
            "guesser_cost_per_episode_usd",
            "full_cost_per_episode_usd",
            "runtime_per_episode_ms",
            "guesser_think_time_per_episode_ms",
            "guesser_latency_per_call_ms",
            "ideal_distance_score",
            "normalized_question_score",
            "normalized_guesser_cost",
            "cost_adjusted_question_score",
            "efficiency_status",
        )
    )
    for row in dataset.leaderboard:
        writer.writerow(
            (
                row.rank or "",
                row.efficiency_rank or "",
                row.ideal_distance_rank or "",
                row.product_efficiency_rank or "",
                row.pareto_efficient,
                row.model.model_id,
                row.model.display_name,
                row.status,
                row.execution_id or "",
                row.question_score if row.question_score is not None else "",
                (
                    row.question_score_confidence_interval.lower
                    if row.question_score_confidence_interval is not None
                    else ""
                ),
                (
                    row.question_score_confidence_interval.upper
                    if row.question_score_confidence_interval is not None
                    else ""
                ),
                (
                    row.question_score_confidence_interval.method
                    if row.question_score_confidence_interval is not None
                    else ""
                ),
                row.success_rate if row.success_rate is not None else "",
                row.contract.status if row.contract is not None else "",
                (
                    row.contract.compliance_rate
                    if row.contract is not None and row.contract.compliance_rate is not None
                    else ""
                ),
                row.contract.violations if row.contract is not None else "",
                row.contract.affected_trials if row.contract is not None else "",
                row.contract.counted_penalties if row.contract is not None else "",
                row.successful,
                row.terminal_trials,
                row.total_cost_usd if row.total_cost_usd is not None else "",
                (
                    row.guesser_cost_per_episode_usd
                    if row.guesser_cost_per_episode_usd is not None
                    else ""
                ),
                (
                    row.full_cost_per_episode_usd
                    if row.full_cost_per_episode_usd is not None
                    else ""
                ),
                (row.runtime_per_episode_ms if row.runtime_per_episode_ms is not None else ""),
                (
                    row.guesser_think_time_per_episode_ms
                    if row.guesser_think_time_per_episode_ms is not None
                    else ""
                ),
                (
                    row.guesser_latency_per_call_ms
                    if row.guesser_latency_per_call_ms is not None
                    else ""
                ),
                row.ideal_distance_score if row.ideal_distance_score is not None else "",
                (
                    row.normalized_question_score
                    if row.normalized_question_score is not None
                    else ""
                ),
                (
                    row.normalized_guesser_cost
                    if row.normalized_guesser_cost is not None
                    else ""
                ),
                (
                    row.cost_adjusted_question_score
                    if row.cost_adjusted_question_score is not None
                    else ""
                ),
                row.efficiency_status,
            )
        )
    return buffer.getvalue()
