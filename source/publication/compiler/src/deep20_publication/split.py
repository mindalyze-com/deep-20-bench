from __future__ import annotations

from decimal import Decimal

from .models import (
    EditionRunReference,
    PublicationConfig,
    PublicationDataBundle,
    PublicationEditionReference,
    PublicationEditionsDocument,
    PublicationEpisodeDocument,
    PublicationLeaderboardDocument,
    PublicationManifestDocument,
    PublicationRepeatAveragesDocument,
    PublicationRunDocument,
    PublicationRunReference,
    PublicationSubjectDocument,
    PublicationSubjectProfile,
    PublicRepeatAverage,
    PublicRun,
    PublicRunSummary,
    PublicSubject,
    PublicSubjectSummary,
    PublicTrialSummary,
    PublishedDataset,
)


def _run_reference(run: PublicRun) -> PublicationRunReference:
    return PublicationRunReference(
        execution_id=run.execution_id,
        model_id=run.model_id,
        model_name=run.model_name,
        classification=run.classification,
    )


def _subject_document(
    run: PublicRun,
    subject: PublicSubject,
    edition_id: str,
) -> PublicationSubjectDocument:
    episodes = tuple(trial.episode for trial in subject.trials if trial.episode is not None)
    if not episodes:
        raise ValueError(
            f"published subject {run.execution_id}/{subject.target_id} has no episode detail"
        )
    profiles = {
        (
            episode.subject_name,
            episode.subject_description,
            episode.subject_reference_url,
        )
        for episode in episodes
    }
    if len(profiles) != 1:
        raise ValueError(
            f"published subject {run.execution_id}/{subject.target_id} has inconsistent profiles"
        )
    subject_name, subject_description, subject_reference_url = profiles.pop()
    if subject_name != subject.display_name:
        raise ValueError(
            f"published subject {run.execution_id}/{subject.target_id} has inconsistent names"
        )
    return PublicationSubjectDocument(
        edition_id=edition_id,
        execution_id=run.execution_id,
        target_id=subject.target_id,
        profile=PublicationSubjectProfile(
            subject_name=subject_name,
            subject_description=subject_description,
            subject_reference_url=subject_reference_url,
        ),
        trials=tuple(
            PublicTrialSummary.model_validate(trial, from_attributes=True)
            for trial in subject.trials
        ),
    )


def _repeat_averages(run: PublicRun) -> tuple[PublicRepeatAverage, ...]:
    if run.question_score is None:
        return ()
    averages: list[PublicRepeatAverage] = []
    for trial_number in range(1, run.iterations + 1):
        trials = tuple(
            trial
            for subject in run.subjects
            for trial in subject.trials
            if trial.trial_number == trial_number
        )
        scores = tuple(
            trial.penalized_questions for trial in trials if trial.penalized_questions is not None
        )
        if len(trials) != len(run.subjects) or len(scores) != len(run.subjects):
            raise ValueError("scored official repeats must include every subject")
        averages.append(
            PublicRepeatAverage(
                execution_id=run.execution_id,
                model_id=run.model_id,
                trial_number=trial_number,
                average_questions=sum(scores, start=Decimal(0)) / Decimal(len(scores)),
                subject_count=len(scores),
                successful=sum(trial.status == "success" for trial in trials),
                model_failed=sum(trial.status == "model_failure" for trial in trials),
            )
        )
    reproduced_score = sum(
        (average.average_questions for average in averages),
        start=Decimal(0),
    ) / Decimal(len(averages))
    if abs(reproduced_score - run.question_score) > Decimal("1e-24"):
        raise ValueError("repeat averages must reproduce the official question score")
    return tuple(averages)


def split_publication(dataset: PublishedDataset) -> PublicationDataBundle:
    ordered_runs = (*dataset.official_runs, *dataset.lab_runs)
    edition_id = dataset.active_cohort.edition_id
    return PublicationDataBundle(
        manifest=PublicationManifestDocument(
            edition_id=edition_id,
            dataset_schema_version=dataset.schema_version,
            site=dataset.site,
            score_policy=dataset.score_policy,
            active_cohort=dataset.active_cohort,
            provenance=dataset.provenance,
            winner=dataset.winner,
            models=dataset.models,
            official_runs=tuple(_run_reference(run) for run in dataset.official_runs),
            lab_runs=tuple(_run_reference(run) for run in dataset.lab_runs),
        ),
        leaderboard=PublicationLeaderboardDocument(
            edition_id=edition_id,
            leaderboard=dataset.leaderboard,
        ),
        repeat_averages=PublicationRepeatAveragesDocument(
            edition_id=edition_id,
            averages=tuple(
                average for run in dataset.official_runs for average in _repeat_averages(run)
            ),
        ),
        runs=tuple(
            PublicationRunDocument(
            edition_id=edition_id,
                run=PublicRunSummary.model_validate(run, from_attributes=True),
                subjects=tuple(
                    PublicSubjectSummary.model_validate(subject, from_attributes=True)
                    for subject in run.subjects
                ),
            )
            for run in ordered_runs
        ),
        subjects=tuple(
            _subject_document(run, subject, edition_id) for run in ordered_runs for subject in run.subjects
        ),
        episodes=tuple(
            PublicationEpisodeDocument(
            edition_id=edition_id,
                execution_id=run.execution_id,
                target_id=subject.target_id,
                trial_id=trial.trial_id,
                episode=trial.episode,
            )
            for run in ordered_runs
            for subject in run.subjects
            for trial in subject.trials
            if trial.episode is not None
        ),
    )


def edition_index(
    config: PublicationConfig, datasets: tuple[PublishedDataset, ...],
) -> PublicationEditionsDocument:
    return PublicationEditionsDocument(
        default_edition_id=config.default_edition_id,
        built_at=datasets[0].provenance.built_at,
        editions=tuple(
            PublicationEditionReference(
                edition_id=dataset.active_cohort.edition_id,
                label=dataset.active_cohort.edition_label,
                status=dataset.active_cohort.edition_status,
                manifest_path=f"editions/{dataset.active_cohort.edition_id}/manifest.json",
                leaderboard_path=f"editions/{dataset.active_cohort.edition_id}/leaderboard.json",
                repeat_averages_path=f"editions/{dataset.active_cohort.edition_id}/repeat-averages.json",
                runs=tuple(
                    EditionRunReference(
                        execution_id=run.execution_id,
                        model_id=run.model_id,
                        model_name=run.model_name,
                        classification=run.classification,
                        target_ids=run.target_ids,
                    ) for run in dataset.official_runs
                ),
            ) for dataset in datasets
        ),
    )
