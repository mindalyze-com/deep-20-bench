from __future__ import annotations

import csv
import io

from .models import PublishedDataset


def dataset_json(dataset: PublishedDataset) -> str:
    return dataset.model_dump_json(indent=2) + "\n"


def leaderboard_csv(dataset: PublishedDataset) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(
        (
            "rank",
            "model_id",
            "model_name",
            "status",
            "execution_id",
            "b20_score",
            "penalized_score",
            "success_rate",
            "contract_status",
            "contract_compliance_rate",
            "contract_violations",
            "contract_affected_trials",
            "contract_counted_penalties",
            "successful",
            "terminal_trials",
            "total_cost_usd",
        )
    )
    for row in dataset.leaderboard:
        writer.writerow(
            (
                row.rank or "",
                row.model.model_id,
                row.model.display_name,
                row.status,
                row.execution_id or "",
                row.b20_score if row.b20_score is not None else "",
                row.penalized_score if row.penalized_score is not None else "",
                row.success_rate if row.success_rate is not None else "",
                row.contract.status if row.contract is not None else "",
                (
                    row.contract.compliance_rate
                    if row.contract is not None
                    and row.contract.compliance_rate is not None
                    else ""
                ),
                row.contract.violations if row.contract is not None else "",
                row.contract.affected_trials if row.contract is not None else "",
                row.contract.counted_penalties if row.contract is not None else "",
                row.successful,
                row.terminal_trials,
                row.total_cost_usd if row.total_cost_usd is not None else "",
            )
        )
    return buffer.getvalue()
