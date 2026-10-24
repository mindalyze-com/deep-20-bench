"""Compact comparison input projected from the existing typed publication graph."""

from __future__ import annotations

from .models import (
    PublicationComparisonDocument,
    PublicationDataBundle,
    PublicComparisonModel,
    PublicComparisonSubject,
    PublicTrialSummary,
)


def build_comparison(bundle: PublicationDataBundle) -> PublicationComparisonDocument:
    """Collect selected official results once; retain all existing scoring and units."""
    runs = {document.run.execution_id: document for document in bundle.runs}
    subjects = {
        (document.execution_id, document.target_id): document for document in bundle.subjects
    }
    official = {reference.execution_id for reference in bundle.manifest.official_runs}
    cohort = bundle.manifest.active_cohort
    return PublicationComparisonDocument(
        edition_id=bundle.manifest.edition_id,
        iterations=cohort.iterations,
        max_questions=cohort.max_questions,
        target_ids=cohort.target_ids,
        models=tuple(
            PublicComparisonModel(
                result=row,
                totals=runs[row.execution_id].run.totals,
                subjects=tuple(
                    PublicComparisonSubject(
                        target_id=summary.target_id,
                        display_name=summary.display_name,
                        entity_type=summary.entity_type,
                        success_rate=summary.success_rate,
                        average_questions=summary.average_questions,
                        successful=summary.successful,
                        model_failed=summary.model_failed,
                        infrastructure_failed=summary.infrastructure_failed,
                        contract=summary.contract,
                        rounds=tuple(
                            PublicTrialSummary(
                                trial_id=trial.trial_id,
                                trial_number=trial.trial_number,
                                status=trial.status,
                                counted_questions=trial.counted_questions,
                                penalized_questions=trial.penalized_questions,
                                cost_usd=trial.cost_usd,
                                duration_ms=trial.duration_ms,
                                contract=trial.contract,
                                failure_code=trial.failure_code,
                            )
                            for trial in sorted(
                                subjects[(row.execution_id, summary.target_id)].trials,
                                key=lambda trial: trial.trial_number,
                            )
                        ),
                    )
                    for summary in runs[row.execution_id].subjects
                ),
            )
            for row in bundle.leaderboard.leaderboard
            if row.status == "evaluated" and row.execution_id is not None
            and row.execution_id in official
        ),
    )
