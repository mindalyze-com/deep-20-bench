from __future__ import annotations

from .models import (
    PublicationDataBundle,
    PublicationEpisodeDocument,
    PublicationLeaderboardDocument,
    PublicationManifestDocument,
    PublicationRunDocument,
    PublicationRunReference,
    PublicationSubjectDocument,
    PublicationSubjectProfile,
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


def split_publication(dataset: PublishedDataset) -> PublicationDataBundle:
    ordered_runs = (*dataset.official_runs, *dataset.lab_runs)
    return PublicationDataBundle(
        manifest=PublicationManifestDocument(
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
            leaderboard=dataset.leaderboard,
        ),
        runs=tuple(
            PublicationRunDocument(
                run=PublicRunSummary.model_validate(run, from_attributes=True),
                subjects=tuple(
                    PublicSubjectSummary.model_validate(subject, from_attributes=True)
                    for subject in run.subjects
                ),
            )
            for run in ordered_runs
        ),
        subjects=tuple(
            _subject_document(run, subject) for run in ordered_runs for subject in run.subjects
        ),
        episodes=tuple(
            PublicationEpisodeDocument(
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
