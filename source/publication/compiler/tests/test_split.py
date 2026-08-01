from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from pydantic import JsonValue

from deep20_publication.models import (
    PublicationDataBundle,
    PublicationEpisodeDocument,
    PublicationLeaderboardDocument,
    PublicationManifestDocument,
    PublicationRunDocument,
    PublicationSubjectDocument,
    PublicRun,
    PublicSubject,
    PublicTrial,
    PublishedDataset,
)
from deep20_publication.serialize import publication_document_json
from deep20_publication.split import split_publication

REPOSITORY = Path(__file__).resolve().parents[4]


def _dataset() -> PublishedDataset:
    path = REPOSITORY / "docs" / "data" / "deep20bench-v7.json"
    return PublishedDataset.model_validate_json(path.read_text(encoding="utf-8"))


def _reconstruct(bundle: PublicationDataBundle) -> PublishedDataset:
    subjects_by_run = {document.run.execution_id: document.subjects for document in bundle.runs}
    subject_documents = {
        (document.execution_id, document.target_id): document for document in bundle.subjects
    }
    episode_documents = {
        (document.execution_id, document.target_id, document.trial_id): document
        for document in bundle.episodes
    }

    def run_from_document(document: PublicationRunDocument) -> PublicRun:
        subjects = tuple(
            PublicSubject.model_validate(
                {
                    **subject_summary.model_dump(mode="python"),
                    "trials": tuple(
                        PublicTrial.model_validate(
                            {
                                **trial.model_dump(mode="python"),
                                "episode": (
                                    episode_documents[
                                        (
                                            document.run.execution_id,
                                            subject_summary.target_id,
                                            trial.trial_id,
                                        )
                                    ].episode
                                    if trial.status != "infrastructure_failure"
                                    else None
                                ),
                            }
                        )
                        for trial in subject_documents[
                            (document.run.execution_id, subject_summary.target_id)
                        ].trials
                    ),
                }
            )
            for subject_summary in subjects_by_run[document.run.execution_id]
        )
        return PublicRun.model_validate(
            {
                **document.run.model_dump(mode="python"),
                "subjects": subjects,
            }
        )

    run_documents = {document.run.execution_id: document for document in bundle.runs}
    official_runs = tuple(
        run_from_document(run_documents[reference.execution_id])
        for reference in bundle.manifest.official_runs
    )
    lab_runs = tuple(
        run_from_document(run_documents[reference.execution_id])
        for reference in bundle.manifest.lab_runs
    )
    return PublishedDataset(
        schema_version=bundle.manifest.dataset_schema_version,
        site=bundle.manifest.site,
        score_policy=bundle.manifest.score_policy,
        active_cohort=bundle.manifest.active_cohort,
        provenance=bundle.manifest.provenance,
        winner=bundle.manifest.winner,
        leaderboard=bundle.leaderboard.leaderboard,
        models=bundle.manifest.models,
        official_runs=official_runs,
        lab_runs=lab_runs,
    )


def _keys(value: JsonValue) -> set[str]:
    if isinstance(value, dict):
        object_keys = set(value)
        for child in value.values():
            object_keys.update(_keys(child))
        return object_keys
    if isinstance(value, list):
        list_keys: set[str] = set()
        for child in value:
            list_keys.update(_keys(child))
        return list_keys
    return set()


def test_split_documents_reconstruct_the_complete_public_dataset() -> None:
    dataset = _dataset()
    bundle = split_publication(dataset)

    assert _reconstruct(bundle) == dataset
    assert len(bundle.runs) == len(dataset.official_runs) + len(dataset.lab_runs)
    assert len(bundle.subjects) == sum(
        len(run.subjects) for run in (*dataset.official_runs, *dataset.lab_runs)
    )
    assert len(bundle.episodes) == sum(
        trial.episode is not None
        for run in (*dataset.official_runs, *dataset.lab_runs)
        for subject in run.subjects
        for trial in subject.trials
    )


def test_split_document_serialization_is_typed_deterministic_and_private_free() -> None:
    bundle = split_publication(_dataset())
    documents: tuple[
        PublicationManifestDocument
        | PublicationLeaderboardDocument
        | PublicationRunDocument
        | PublicationSubjectDocument
        | PublicationEpisodeDocument,
        ...,
    ] = (
        bundle.manifest,
        bundle.leaderboard,
        *bundle.runs,
        *bundle.subjects,
        *bundle.episodes,
    )
    forbidden = {
        "guesser_conversation",
        "subject_snapshot",
        "system_instructions",
        "variation_token",
        "raw_response",
        "provider_trace",
        "session_id",
        "cache_key",
        "error_output_preview",
        "error_outputs",
    }

    for document in documents:
        first = publication_document_json(document)
        second = publication_document_json(document)
        assert first == second
        assert first.endswith("\n")
        parsed = cast(JsonValue, json.loads(first))
        assert forbidden.isdisjoint(_keys(parsed))
