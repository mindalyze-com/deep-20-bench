from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree

from deep20_publication.cli import (
    _application_build_document,
    _publication_build_time,
    _static_route_manifest,
    _write_public_data,
)
from deep20_publication.models import PublicationAppBuildDocument, PublishedDataset
from deep20_publication.split import split_publication

REPOSITORY = Path(__file__).resolve().parents[4]
CANONICAL_URL = "https://mindalyze-com.github.io/deep-20-bench/"


def test_generated_data_is_not_stored_in_site_source() -> None:
    source_data = REPOSITORY / "source" / "publication" / "site" / "public" / "data"

    assert not source_data.exists()
    assert (REPOSITORY / "docs" / "data" / "manifest.json").is_file()


def test_search_files_follow_the_static_route_manifest() -> None:
    bundle = split_publication(_published_dataset())
    route_manifest = _static_route_manifest(bundle)
    sitemap = REPOSITORY / "docs" / "sitemap.xml"
    document = ElementTree.parse(sitemap)
    locations = tuple(
        element.text
        for element in document.findall(
            ".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
        )
    )
    expected = tuple(
        CANONICAL_URL if route.canonical_route == "" else (
            f"{CANONICAL_URL}{route.canonical_route}/"
        )
        for route in route_manifest.routes
        if route.sitemap_included
    )
    assert locations == expected
    assert len(locations) == len(expected)
    assert sum(
        "/runs/" in location for location in locations if location is not None
    ) == len(bundle.runs)
    assert not (REPOSITORY / "docs" / "robots.txt").exists()


def test_sitemap_contains_editorial_and_official_run_routes() -> None:
    bundle = split_publication(_published_dataset())
    routes = _static_route_manifest(bundle).routes
    sitemap_routes = {entry.route for entry in routes if entry.sitemap_included}
    editorial_routes = {
        entry.route for entry in routes if entry.kind in {"home", "editorial"}
    }
    run_routes = {
        f"runs/{run.run.execution_id}" for run in bundle.runs
    }

    assert sitemap_routes == editorial_routes | run_routes
    assert len(sitemap_routes) == len(editorial_routes) + len(bundle.runs)


def test_search_files_are_not_handwritten_site_assets() -> None:
    public = REPOSITORY / "source" / "publication" / "site" / "public"
    prerender = (
        REPOSITORY / "source" / "publication" / "site" / "scripts" / "prerender.mjs"
    ).read_text(encoding="utf-8")

    assert not (public / "sitemap.xml").exists()
    assert not (public / "robots.txt").exists()
    assert 'join(outputRoot, "robots.txt")' not in prerender


def test_execution_components_do_not_import_publication_outputs() -> None:
    execution_root = REPOSITORY / "source" / "execution"

    for source in execution_root.rglob("*.py"):
        assert "deep20_publication" not in source.read_text(encoding="utf-8")


def test_publication_build_time_is_fresh_or_reused_for_verification() -> None:
    before = datetime.now(UTC)
    fresh = _publication_build_time(REPOSITORY, check=False)
    after = datetime.now(UTC)
    committed = _publication_build_time(REPOSITORY, check=True)
    manifest = json.loads(
        (REPOSITORY / "docs" / "data" / "manifest.json").read_text(encoding="utf-8")
    )

    assert before <= fresh <= after
    assert committed == datetime.fromisoformat(manifest["provenance"]["built_at"])


def test_application_build_time_is_fresh_or_reused_for_verification() -> None:
    before = datetime.now(UTC)
    fresh = _application_build_document(REPOSITORY, check=False)
    after = datetime.now(UTC)
    committed = _application_build_document(REPOSITORY, check=True)
    document = PublicationAppBuildDocument.model_validate_json(
        (REPOSITORY / "docs" / "data" / "app-build.json").read_text(encoding="utf-8")
    )

    assert before <= fresh.built_at <= after
    assert committed == document


def test_source_entry_has_no_production_preview_or_duplicate_fallback() -> None:
    entry = (REPOSITORY / "source" / "publication" / "site" / "index.html").read_text(
        encoding="utf-8"
    )

    assert '<div id="app"></div>' in entry
    assert "Local preview" not in entry
    assert "app-loading" not in entry
    assert "static-home" not in entry


def test_generated_homepage_has_prerendered_vue_content() -> None:
    entry = (REPOSITORY / "docs" / "index.html").read_text(encoding="utf-8")
    entry_copy = " ".join(entry.split())

    assert '<html lang="en" data-prerendered="true">' in entry
    assert 'id="route-content" class="page home-page"' in entry
    assert 'content="https://mindalyze-com.github.io/deep-20-bench/og.webp"' in entry
    assert "og.png" not in entry
    assert "How well can AI models play Twenty Questions?" in entry
    assert "What this pilot tests" in entry
    assert "more than the traditional twenty" in entry_copy
    assert "The concept works and the first step is complete." in entry_copy
    assert "cost is the main constraint." in entry_copy
    assert "small first step" not in entry
    assert "not a definitive ranking" not in entry
    assert "https://github.com/mindalyze-com/deep-20-bench/discussions" in entry
    assert "Join discussion" in entry
    assert "How to read the pilot" in entry
    assert "Comparable runs, limited conclusions." in entry
    assert "The Guesser is isolated from this process" in entry
    assert "Deep20Bench needs JavaScript" not in entry
    assert '<script type="application/ld+json">' in entry
    assert '"alternateName":["Deep20 Bench","D20B"]' in entry
    assert '"keywords":["Deep20Bench","Deep20 Bench","Deep20 benchmark"' in entry
    assert 'rel="canonical" href="https://mindalyze-com.github.io/deep-20-bench/"' in entry
    assert "deep20-static-home" not in entry
    assert "deep20-structured-data" not in entry
    assert 'id="deep20-page-state" type="application/json"' in entry
    assert "app-loading" not in entry
    assert "Local preview" not in entry


def _published_dataset() -> PublishedDataset:
    source = REPOSITORY / "docs" / "data" / "deep20bench-v9.json"
    return PublishedDataset.model_validate_json(source.read_text(encoding="utf-8"))


def test_static_route_manifest_covers_sitemap_and_evidence_routes() -> None:
    bundle = split_publication(_published_dataset())
    manifest = _static_route_manifest(bundle)
    routes = {entry.route: entry for entry in manifest.routes}
    editorial_routes = {
        entry.route
        for entry in manifest.routes
        if entry.kind in {"home", "editorial"}
    }
    run_routes = {
        f"runs/{run.run.execution_id}" for run in bundle.runs
    }

    assert len(routes) == (10 + len(bundle.runs) + len(bundle.subjects) + len(bundle.episodes))
    assert {
        entry.route for entry in routes.values() if entry.sitemap_included
    } == editorial_routes | run_routes
    assert all(routes[page].sitemap_included for page in (
        "", "results", "results/reliability", "results/cost", "results/time",
        "results/efficiency", "methodology", "about", "data",
    ))
    assert all(
        routes[f"runs/{run.run.execution_id}"].sitemap_included
        for run in bundle.runs
    )
    assert routes["story"].canonical_route == "about"
    assert not routes["story"].sitemap_included
    assert all(
        not entry.sitemap_included
        for entry in routes.values()
        if entry.kind in {"subject", "episode"}
    )
    assert len({entry.browser_title for entry in routes.values() if entry.kind == "run"}) == len(
        bundle.runs
    )
    assert len({entry.description for entry in routes.values() if entry.kind == "run"}) == len(
        bundle.runs
    )


def test_generated_run_is_prerendered_and_evidence_has_no_robots_block() -> None:
    bundle = split_publication(_published_dataset())
    run = bundle.runs[0]
    run_route = f"runs/{run.run.execution_id}"
    entry = (REPOSITORY / "docs" / run_route / "index.html").read_text(encoding="utf-8")

    assert '<html lang="en" data-prerendered="true">' in entry
    assert 'class="run-overview-pane pane-scroll"' in entry
    assert run.run.model_name in entry
    assert "Question score" in entry
    assert "95% CI" in entry
    assert "Success" in entry
    assert "Contract compliance" in entry
    assert "Guesser cost" in entry
    assert "Wall-clock runtime" in entry
    assert 'name="robots"' not in entry
    for subject_summary in run.subjects:
        assert (
            f'href="/deep-20-bench/{run_route}/subjects/{subject_summary.target_id}/"'
            in entry
        )

    subject_document = bundle.subjects[0]
    subject_route = (
        f"runs/{subject_document.execution_id}/subjects/{subject_document.target_id}"
    )
    subject_entry = (REPOSITORY / "docs" / subject_route / "index.html").read_text(
        encoding="utf-8"
    )
    assert 'name="robots"' not in subject_entry
    assert 'data-prerendered="true"' not in subject_entry
    assert f"{CANONICAL_URL}{subject_route}/" not in {
        element.text
        for element in ElementTree.parse(REPOSITORY / "docs" / "sitemap.xml").findall(
            ".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
        )
    }

    not_found = (REPOSITORY / "docs" / "404.html").read_text(encoding="utf-8")
    assert 'rel="canonical"' not in not_found
    assert 'name="robots" content="noindex, follow"' in not_found


def test_all_sitemap_pages_have_unique_metadata_and_a_static_referrer() -> None:
    manifest = _static_route_manifest(split_publication(_published_dataset()))
    sitemap_routes = tuple(
        entry for entry in manifest.routes if entry.sitemap_included
    )
    html_by_route = {
        entry.route: (
            REPOSITORY / "docs" / entry.route / "index.html"
            if entry.route
            else REPOSITORY / "docs" / "index.html"
        ).read_text(encoding="utf-8")
        for entry in sitemap_routes
    }
    titles: list[str] = []
    descriptions: list[str] = []
    canonicals: list[str] = []

    for entry in sitemap_routes:
        html = html_by_route[entry.route]
        title = re.search(r"<title>(.*?)</title>", html)
        description = re.search(r'<meta name="description" content="([^"]+)" />', html)
        canonical = re.search(r'<link rel="canonical" href="([^"]+)" />', html)
        assert title is not None
        assert description is not None
        assert canonical is not None
        titles.append(title.group(1))
        descriptions.append(description.group(1))
        canonicals.append(canonical.group(1))
        expected_url = CANONICAL_URL if entry.route == "" else f"{CANONICAL_URL}{entry.route}/"
        expected_href = (
            "/deep-20-bench/" if entry.route == "" else f"/deep-20-bench/{entry.route}/"
        )
        assert canonical.group(1) == expected_url
        assert 'name="robots"' not in html
        assert 'id="route-content"' in html
        assert any(
            f'href="{expected_href}"' in referring_html
            for route, referring_html in html_by_route.items()
            if route != entry.route
        )

    assert len(titles) == len(set(titles)) == len(sitemap_routes)
    assert len(descriptions) == len(set(descriptions)) == len(sitemap_routes)
    assert len(canonicals) == len(set(canonicals)) == len(sitemap_routes)


def test_split_public_data_is_complete_and_removes_stale_files(
    tmp_path: Path,
) -> None:
    dataset = _published_dataset()
    public = tmp_path / "public"
    stale = public / "data" / "runs" / "stale.json"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale", encoding="utf-8")

    app_build = PublicationAppBuildDocument(built_at=datetime(2026, 8, 1, 18, 0, tzinfo=UTC))
    _write_public_data(public, dataset, app_build)

    data = public / "data"
    assert not stale.exists()
    assert (data / "deep20bench-v9.json").is_file()
    assert (data / "deep20bench-v9.schema.json").is_file()
    assert (data / "leaderboard.csv").is_file()
    public_schema = json.loads(
        (data / "deep20bench-v9.schema.json").read_text(encoding="utf-8")
    )
    assert public_schema.pop("$schema") == "https://json-schema.org/draft/2020-12/schema"
    assert public_schema == PublishedDataset.model_json_schema(mode="serialization")
    serialized_schema = json.dumps(public_schema, sort_keys=True)
    for forbidden_field in (
        "call_id",
        "guesser_conversation",
        "subject_snapshot",
        "system_instructions",
        "variation_token",
        "raw_response",
        "oracle_raw_response",
        "oracle_search_results",
        "reviewer_answer",
        "judge_answer",
        "provider_trace",
        "response_id",
        "session_id",
        "cache_key",
        "error_output_preview",
        "error_outputs",
    ):
        assert forbidden_field not in serialized_schema
    manifest = json.loads((data / "manifest.json").read_text(encoding="utf-8"))
    application = json.loads((data / "app-build.json").read_text(encoding="utf-8"))
    leaderboard = json.loads((data / "leaderboard.json").read_text(encoding="utf-8"))
    repeat_averages = json.loads((data / "repeat-averages.json").read_text(encoding="utf-8"))
    assert manifest["document_type"] == "manifest"
    assert manifest["dataset_schema_version"] == 9
    assert application == {
        "document_type": "app_build",
        "schema_version": 1,
        "built_at": "2026-08-01T18:00:00Z",
    }
    assert leaderboard["document_type"] == "leaderboard"
    assert leaderboard["schema_version"] == 3
    first_row = leaderboard["leaderboard"][0]
    assert first_row["ideal_distance_rank"] is not None
    assert first_row["ideal_distance_score"] is not None
    assert first_row["normalized_question_score"] is not None
    assert first_row["normalized_guesser_cost"] is not None
    assert first_row["product_efficiency_rank"] is not None
    csv_header = (data / "leaderboard.csv").read_text(encoding="utf-8").splitlines()[0]
    assert "ideal_distance_rank" in csv_header
    assert "ideal_distance_score" in csv_header
    assert "normalized_question_score" in csv_header
    assert "normalized_guesser_cost" in csv_header
    assert "product_efficiency_rank" in csv_header
    assert repeat_averages["document_type"] == "repeat_averages"
    assert repeat_averages["schema_version"] == 1
    assert len(repeat_averages["averages"]) == sum(
        run.iterations for run in dataset.official_runs if run.question_score is not None
    )
    assert (
        leaderboard["leaderboard"]
        == json.loads((data / "deep20bench-v9.json").read_text(encoding="utf-8"))["leaderboard"]
    )

    run = dataset.official_runs[0]
    first = data / "runs" / run.execution_id / "subjects" / "T-0001"
    second = data / "runs" / run.execution_id / "subjects" / "T-0002"
    assert (first / "episodes" / "trial-001.json").is_file()
    assert (second / "episodes" / "trial-001.json").is_file()
    assert (first / "episodes" / "trial-001.json").read_text(encoding="utf-8") != (
        second / "episodes" / "trial-001.json"
    ).read_text(encoding="utf-8")
