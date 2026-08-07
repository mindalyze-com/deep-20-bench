from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import cast

from deep20_publication.models import (
    PublicationAppBuildDocument,
    PublicationDataBundle,
    PublishedDataset,
)
from deep20_publication.serialize import publication_document_json
from deep20_publication.split import split_publication
from pydantic import JsonValue

REPOSITORY = Path(__file__).resolve().parents[4]
OUTPUT = REPOSITORY / "source" / "publication" / "site" / "tests" / "fixtures" / "publication"
RUN_IDS = (
    "BX-20260805-official-M0014-011",
    "BX-20260728-official-M0006-010",
    "BX-20260728-official-M0001-010",
)


def _synthetic_bundle(dataset: PublishedDataset) -> PublicationDataBundle:
    runs_by_id = {run.execution_id: run for run in dataset.official_runs}
    selected_runs = tuple(runs_by_id[execution_id] for execution_id in RUN_IDS)
    leaderboard = list(dataset.leaderboard)
    awaiting_index = next(
        index for index, row in enumerate(leaderboard) if row.model.model_id == "M-0012"
    )
    awaiting = leaderboard[awaiting_index]
    leaderboard[awaiting_index] = awaiting.model_copy(
        update={
            "rank": None,
            "efficiency_rank": None,
            "ideal_distance_rank": None,
            "product_efficiency_rank": None,
            "pareto_efficient": False,
            "status": "awaiting_official_run",
            "execution_id": None,
            "completed_at": None,
            "question_score": None,
            "question_score_confidence_interval": None,
            "success_rate": None,
            "total_cost_usd": None,
            "guesser_cost_per_episode_usd": None,
            "full_cost_per_episode_usd": None,
            "runtime_per_episode_ms": None,
            "guesser_think_time_per_episode_ms": None,
            "guesser_latency_per_call_ms": None,
            "ideal_distance_score": None,
            "normalized_question_score": None,
            "normalized_guesser_cost": None,
            "cost_adjusted_question_score": None,
            "efficiency_status": "question_score_unavailable",
            "successful": 0,
            "terminal_trials": 0,
            "contract": None,
        }
    )
    subset = dataset.model_copy(
        update={
            "leaderboard": tuple(leaderboard),
            "official_runs": selected_runs,
            "lab_runs": (),
        }
    )
    payload = cast(dict[str, JsonValue], split_publication(subset).model_dump(mode="json"))

    model_names = {
        model.model_id: f"Synthetic Model {index:02d} ({model.reasoning_effort})"
        for index, model in enumerate(dataset.models, start=1)
    }
    model_names["M-0012"] = (
        "Synthetic Model 11 With An Intentionally Long Display Name (high)"
    )
    manifest = cast(dict[str, JsonValue], payload["manifest"])
    for model_value in cast(list[JsonValue], manifest["models"]):
        model = cast(dict[str, JsonValue], model_value)
        model["display_name"] = model_names[cast(str, model["model_id"])]
    winner = cast(dict[str, JsonValue] | None, manifest["winner"])
    if winner is not None:
        winner["display_names"] = [
            model_names[model_id]
            for model_id in cast(list[str], winner["model_ids"])
        ]

    leaderboard_document = cast(dict[str, JsonValue], payload["leaderboard"])
    for row_value in cast(list[JsonValue], leaderboard_document["leaderboard"]):
        row = cast(dict[str, JsonValue], row_value)
        model = cast(dict[str, JsonValue], row["model"])
        model["display_name"] = model_names[cast(str, model["model_id"])]

    for run_value in cast(list[JsonValue], payload["runs"]):
        run_document = cast(dict[str, JsonValue], run_value)
        run = cast(dict[str, JsonValue], run_document["run"])
        run["model_name"] = model_names[cast(str, run["model_id"])]
        for subject_value in cast(list[JsonValue], run_document["subjects"]):
            subject = cast(dict[str, JsonValue], subject_value)
            subject["display_name"] = f"Synthetic Subject {subject['target_id']}"

    for subject_value in cast(list[JsonValue], payload["subjects"]):
        subject = cast(dict[str, JsonValue], subject_value)
        profile = cast(dict[str, JsonValue], subject["profile"])
        target_id = cast(str, subject["target_id"])
        profile["subject_name"] = f"Synthetic Subject {target_id}"
        profile["subject_description"] = "A synthetic subject used for publication UI tests."
        profile["subject_reference_url"] = f"https://example.com/subjects/{target_id}"

    for episode_value in cast(list[JsonValue], payload["episodes"]):
        episode_document = cast(dict[str, JsonValue], episode_value)
        episode = cast(dict[str, JsonValue], episode_document["episode"])
        target_id = cast(str, episode_document["target_id"])
        episode["subject_name"] = f"Synthetic Subject {target_id}"
        episode["subject_description"] = "A synthetic subject used for publication UI tests."
        episode["subject_reference_url"] = f"https://example.com/subjects/{target_id}"
        for turn_value in cast(list[JsonValue], episode["turns"]):
            turn = cast(dict[str, JsonValue], turn_value)
            turn_number = cast(int, turn["turn_number"])
            if turn.get("question") is not None:
                turn["question"] = f"Synthetic question {turn_number}?"
            if turn.get("guess_name") is not None:
                turn["guess_name"] = f"Synthetic Subject {target_id}"
            if turn.get("guess_description") is not None:
                turn["guess_description"] = "Synthetic final guess."
            if turn.get("validator_explanation") is not None:
                turn["validator_explanation"] = "Synthetic validator explanation."
            if turn.get("recorded_output") is not None:
                turn["recorded_output"] = "Synthetic recorded output."
            for evidence_value in cast(list[JsonValue], turn.get("evidence", [])):
                evidence = cast(dict[str, JsonValue], evidence_value)
                evidence["source_url"] = "https://example.com/evidence"
                evidence["excerpt"] = "Synthetic public evidence excerpt."
            for rejected_value in cast(list[JsonValue], turn.get("rejected_outputs", [])):
                rejected = cast(dict[str, JsonValue], rejected_value)
                rejected["text"] = "Synthetic rejected output."

    episodes = cast(list[JsonValue], payload["episodes"])
    long_episode = cast(dict[str, JsonValue], episodes[-1])
    long_detail = cast(dict[str, JsonValue], long_episode["episode"])
    long_turn = cast(dict[str, JsonValue], cast(list[JsonValue], long_detail["turns"])[0])
    long_turn["question"] = (
        "Is this the intentionally long synthetic question used to verify that episode "
        "content wraps without clipping across narrow and wide publication layouts?"
    )
    long_turn["recorded_output"] = (
        "This intentionally long synthetic episode answer verifies that detailed model output "
        "wraps without clipping, overlapping adjacent controls, or escaping its transcript "
        "container on narrow and wide publication layouts."
    )

    return PublicationDataBundle.model_validate(payload)


def _write_json(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def main() -> None:
    dataset_path = REPOSITORY / "docs" / "data" / "deep20bench-v9.json"
    dataset = PublishedDataset.model_validate_json(dataset_path.read_text(encoding="utf-8"))
    bundle = _synthetic_bundle(dataset)
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    data = OUTPUT / "data"
    _write_json(
        data / "app-build.json",
        publication_document_json(
            PublicationAppBuildDocument(built_at=dataset.provenance.built_at)
        ),
    )
    _write_json(data / "manifest.json", publication_document_json(bundle.manifest))
    _write_json(data / "leaderboard.json", publication_document_json(bundle.leaderboard))
    _write_json(
        data / "repeat-averages.json",
        publication_document_json(bundle.repeat_averages),
    )
    for document in bundle.runs:
        _write_json(
            data / "runs" / f"{document.run.execution_id}.json",
            publication_document_json(document),
        )
    for document in bundle.subjects:
        _write_json(
            data
            / "runs"
            / document.execution_id
            / "subjects"
            / f"{document.target_id}.json",
            publication_document_json(document),
        )
    for document in bundle.episodes:
        _write_json(
            data
            / "runs"
            / document.execution_id
            / "subjects"
            / document.target_id
            / "episodes"
            / f"{document.trial_id}.json",
            publication_document_json(document),
        )
    metadata = {
        "fixture_version": 1,
        "source_schema_version": dataset.schema_version,
        "run_ids": list(RUN_IDS),
    }
    _write_json(OUTPUT / "fixture.json", json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
