from __future__ import annotations

from pathlib import Path

from deep20_publication.models import (
    PublicationAppBuildDocument,
    PublicationDataBundle,
    PublicationEpisodeDocument,
    PublicationLeaderboardDocument,
    PublicationManifestDocument,
    PublicationRepeatAveragesDocument,
    PublicationRunDocument,
    PublicationSubjectDocument,
)

REPOSITORY = Path(__file__).resolve().parents[4]
DATA = REPOSITORY / "source" / "publication" / "site" / "tests" / "fixtures" / "publication" / "data"


def _load(model_type: type[PublicationAppBuildDocument], path: Path) -> PublicationAppBuildDocument:
    return model_type.model_validate_json(path.read_text(encoding="utf-8"))


def test_site_fixture_is_a_valid_publication_graph_with_required_edge_cases() -> None:
    manifest = PublicationManifestDocument.model_validate_json(
        (DATA / "manifest.json").read_text(encoding="utf-8")
    )
    leaderboard = PublicationLeaderboardDocument.model_validate_json(
        (DATA / "leaderboard.json").read_text(encoding="utf-8")
    )
    repeat_averages = PublicationRepeatAveragesDocument.model_validate_json(
        (DATA / "repeat-averages.json").read_text(encoding="utf-8")
    )
    _load(PublicationAppBuildDocument, DATA / "app-build.json")

    run_documents = {
        document.run.execution_id: document
        for path in (DATA / "runs").glob("*.json")
        for document in (PublicationRunDocument.model_validate_json(path.read_text()),)
    }
    subject_documents = {
        (document.execution_id, document.target_id): document
        for path in (DATA / "runs").glob("*/subjects/*.json")
        for document in (PublicationSubjectDocument.model_validate_json(path.read_text()),)
    }
    episode_documents = {
        (document.execution_id, document.target_id, document.trial_id): document
        for path in (DATA / "runs").glob("*/subjects/*/episodes/*.json")
        for document in (PublicationEpisodeDocument.model_validate_json(path.read_text()),)
    }
    references = (*manifest.official_runs, *manifest.lab_runs)
    runs = tuple(run_documents[reference.execution_id] for reference in references)
    subjects = tuple(
        subject_documents[(run.run.execution_id, subject.target_id)]
        for run in runs
        for subject in run.subjects
    )
    episodes = tuple(
        episode_documents[(subject.execution_id, subject.target_id, trial.trial_id)]
        for subject in subjects
        for trial in subject.trials
        if trial.status != "infrastructure_failure"
    )

    bundle = PublicationDataBundle(
        manifest=manifest,
        leaderboard=leaderboard,
        repeat_averages=repeat_averages,
        runs=runs,
        subjects=subjects,
        episodes=episodes,
    )

    assert len({run.run.model_id for run in bundle.runs}) >= 3
    assert any(row.question_score is None for row in bundle.leaderboard.leaderboard)
    assert any(
        trial.status == "success"
        for subject in bundle.subjects
        for trial in subject.trials
    )
    assert any(
        trial.status == "model_failure"
        for subject in bundle.subjects
        for trial in subject.trials
    )
    assert any(run.run.contract.violations > 0 for run in bundle.runs)
    assert any(len(model.display_name) > 50 for model in bundle.manifest.models)
    assert any(
        turn.question is not None and len(turn.question) > 120
        for episode in bundle.episodes
        for turn in episode.episode.turns
        if turn.turn_type == "action"
    )
    assert any(
        turn.recorded_output is not None and len(turn.recorded_output) > 150
        for episode in bundle.episodes
        for turn in episode.episode.turns
        if turn.turn_type == "action"
    )
