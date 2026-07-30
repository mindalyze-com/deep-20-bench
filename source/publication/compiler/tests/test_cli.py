from __future__ import annotations

import json
from pathlib import Path

from deep20_publication.cli import (
    _route_shells,
    _write_public_data,
    _write_route_shells,
)
from deep20_publication.models import PublishedDataset
from deep20_publication.split import split_publication

REPOSITORY = Path(__file__).resolve().parents[4]


def test_generated_data_is_not_stored_in_site_source() -> None:
    source_data = (
        REPOSITORY / "source" / "publication" / "site" / "public" / "data"
    )

    assert not source_data.exists()
    assert (REPOSITORY / "docs" / "data" / "manifest.json").is_file()


def test_file_scheme_entry_explains_how_to_start_the_preview() -> None:
    entry = (
        REPOSITORY / "source" / "publication" / "site" / "index.html"
    ).read_text(encoding="utf-8")

    assert 'window.location.protocol === "file:"' in entry
    assert "Open this publication through HTTP." in entry
    assert "npm run --prefix source/publication/site dev" in entry
    assert "http://127.0.0.1:4173/deep-20-bench/" in entry


def _published_dataset() -> PublishedDataset:
    source = REPOSITORY / "docs" / "data" / "deep20bench-v5.json"
    return PublishedDataset.model_validate_json(source.read_text(encoding="utf-8"))


def test_route_shells_cover_every_known_static_route(tmp_path: Path) -> None:
    bundle = split_publication(_published_dataset())
    output = tmp_path / "docs"
    output.mkdir()
    entry = "<!doctype html><div id=\"app\"></div>"
    (output / "index.html").write_text(entry, encoding="utf-8")

    _write_route_shells(output, bundle)

    routes = _route_shells(bundle)
    assert "results" in routes
    assert "results/efficiency" in routes
    assert "methodology" in routes
    assert len(routes) == (
        7 + len(bundle.runs) + len(bundle.subjects) + len(bundle.episodes)
    )
    for route in routes:
        assert (output / route / "index.html").read_text(encoding="utf-8") == entry
    assert (output / "404.html").read_text(encoding="utf-8") == entry


def test_split_public_data_is_complete_and_removes_stale_files(
    tmp_path: Path,
) -> None:
    dataset = _published_dataset()
    public = tmp_path / "public"
    stale = public / "data" / "runs" / "stale.json"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale", encoding="utf-8")

    _write_public_data(public, dataset)

    data = public / "data"
    assert not stale.exists()
    assert (data / "deep20bench-v5.json").is_file()
    assert (data / "leaderboard.csv").is_file()
    manifest = json.loads((data / "manifest.json").read_text(encoding="utf-8"))
    leaderboard = json.loads(
        (data / "leaderboard.json").read_text(encoding="utf-8")
    )
    assert manifest["document_type"] == "manifest"
    assert manifest["dataset_schema_version"] == 5
    assert leaderboard["document_type"] == "leaderboard"
    assert leaderboard["leaderboard"] == json.loads(
        (data / "deep20bench-v5.json").read_text(encoding="utf-8")
    )["leaderboard"]

    run = dataset.official_runs[0]
    first = data / "runs" / run.execution_id / "subjects" / "T-0001"
    second = data / "runs" / run.execution_id / "subjects" / "T-0002"
    assert (first / "episodes" / "trial-001.json").is_file()
    assert (second / "episodes" / "trial-001.json").is_file()
    assert (first / "episodes" / "trial-001.json").read_text(
        encoding="utf-8"
    ) != (second / "episodes" / "trial-001.json").read_text(encoding="utf-8")
