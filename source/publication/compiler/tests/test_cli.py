from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree

from deep20_publication.cli import (
    _application_build_document,
    _canonical_route_url,
    _publication_build_time,
    _route_shells,
    _sitemap_routes,
    _write_public_data,
    _write_route_shells,
    _write_search_files,
)
from deep20_publication.models import PublicationAppBuildDocument, PublishedDataset
from deep20_publication.split import split_publication

REPOSITORY = Path(__file__).resolve().parents[4]
CANONICAL_URL = "https://mindalyze-com.github.io/deep-20-bench/"


def test_generated_data_is_not_stored_in_site_source() -> None:
    source_data = REPOSITORY / "source" / "publication" / "site" / "public" / "data"

    assert not source_data.exists()
    assert (REPOSITORY / "docs" / "data" / "manifest.json").is_file()


def test_search_files_are_generated_from_the_editorial_route_policy(
    tmp_path: Path,
) -> None:
    _write_search_files(tmp_path, CANONICAL_URL)

    sitemap = tmp_path / "sitemap.xml"
    document = ElementTree.parse(sitemap)
    locations = tuple(
        element.text
        for element in document.findall(
            ".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
        )
    )
    assert locations == tuple(
        _canonical_route_url(CANONICAL_URL, route) for route in _sitemap_routes()
    )
    assert all("/runs/" not in location for location in locations if location is not None)
    assert (tmp_path / "robots.txt").read_text(encoding="utf-8") == (
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {CANONICAL_URL}sitemap.xml\n"
    )


def test_search_files_are_not_handwritten_site_assets() -> None:
    public = REPOSITORY / "source" / "publication" / "site" / "public"

    assert not (public / "sitemap.xml").exists()
    assert not (public / "robots.txt").exists()


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


def test_file_scheme_entry_explains_how_to_start_the_preview() -> None:
    entry = (REPOSITORY / "source" / "publication" / "site" / "index.html").read_text(
        encoding="utf-8"
    )

    assert 'window.location.protocol === "file:"' in entry
    assert "Open this publication through HTTP." in entry
    assert "npm run --prefix source/publication/site dev" in entry
    assert "http://127.0.0.1:4173/deep-20-bench/" in entry


def test_generated_homepage_has_a_static_executive_summary() -> None:
    entry = (REPOSITORY / "docs" / "index.html").read_text(encoding="utf-8")
    entry_copy = " ".join(entry.split())

    assert '<main class="static-home" id="static-home">' in entry
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
    assert "What it does not claim" in entry
    assert "The model under test sees only the game." in entry
    assert "Deep20Bench needs JavaScript" not in entry
    assert '<script type="application/ld+json">' in entry
    assert '"alternateName":["Deep20 Bench","D20B"]' in entry
    assert '"keywords":["Deep20Bench","Deep20 Bench"' in entry
    assert 'rel="canonical" href="https://mindalyze-com.github.io/deep-20-bench/"' in entry
    assert "deep20-static-home" not in entry
    assert "deep20-structured-data" not in entry
    assert 'classList.add("app-loading")' in entry
    assert 'classList.remove("app-loading")' in entry


def _published_dataset() -> PublishedDataset:
    source = REPOSITORY / "docs" / "data" / "deep20bench-v9.json"
    return PublishedDataset.model_validate_json(source.read_text(encoding="utf-8"))


def test_route_shells_cover_every_known_static_route(tmp_path: Path) -> None:
    bundle = split_publication(_published_dataset())
    output = tmp_path / "docs"
    output.mkdir()
    entry = '<!doctype html><div id="app"></div>'
    (output / "index.html").write_text(entry, encoding="utf-8")

    _write_route_shells(output, bundle, CANONICAL_URL)

    routes = _route_shells(bundle)
    assert "results" in routes
    assert "results/reliability" in routes
    assert "results/efficiency" in routes
    assert "methodology" in routes
    assert "story" in routes
    assert len(routes) == (9 + len(bundle.runs) + len(bundle.subjects) + len(bundle.episodes))
    assert set(_sitemap_routes()[1:]).issubset(routes)
    for route in routes:
        assert (output / route / "index.html").read_text(encoding="utf-8") == entry
    assert (output / "404.html").read_text(encoding="utf-8") == entry


def test_route_shells_do_not_duplicate_the_static_homepage(tmp_path: Path) -> None:
    bundle = split_publication(_published_dataset())
    output = tmp_path / "docs"
    output.mkdir()
    entry = """<!doctype html>
<head>
  <title>Deep20Bench · Twenty Questions Benchmark for LLMs</title>
  <meta name="description" content="Deep20Bench benchmark publication." />
  <meta name="robots" content="index, follow, max-image-preview:large" />
  <meta property="og:title" content="Deep20Bench" />
  <meta property="og:description" content="Deep20Bench benchmark publication." />
  <meta property="og:url" content="https://mindalyze-com.github.io/deep-20-bench/" />
  <meta name="twitter:title" content="Deep20Bench" />
  <meta name="twitter:description" content="Deep20Bench benchmark publication." />
  <link rel="canonical" href="https://mindalyze-com.github.io/deep-20-bench/" />
  <script type="application/ld+json">{"@type":"Dataset"}</script>
</head>
<div id="app">
  <main class="static-home" id="static-home"><h1>Executive summary</h1></main>
</div>
"""
    (output / "index.html").write_text(entry, encoding="utf-8")

    _write_route_shells(output, bundle, CANONICAL_URL)

    assert (output / "index.html").read_text(encoding="utf-8") == entry
    route = (output / "results" / "index.html").read_text(encoding="utf-8")
    assert 'class="static-home"' not in route
    assert 'class="static-route-fallback static-route-fallback--editorial"' in route
    assert "Deep20Bench results." in route
    assert "This detailed view uses JavaScript." not in route
    assert "The current leader has a question score of" in route
    assert "Top three official model results" in route
    assert bundle.manifest.winner is not None
    assert bundle.manifest.winner.display_names[0] in route
    assert f'href="{bundle.manifest.site.base_path}"' in route
    assert f'href="{bundle.manifest.site.base_path}data/"' in route
    assert f'rel="canonical" href="{CANONICAL_URL}results/"' in route
    assert f'property="og:url" content="{CANONICAL_URL}results/"' in route
    assert "<title>Results · Deep20Bench</title>" in route
    assert 'name="description" content="Compare official model scores' in route
    assert 'name="robots" content="index, follow, max-image-preview:large"' in route
    assert 'type="application/ld+json"' not in route
    method_route = (output / "methodology" / "index.html").read_text(encoding="utf-8")
    assert "From one round to a comparable score." in method_route
    assert (
        "Follow one Twenty Questions round through answer checks, repeated trials, "
        "scoring, official comparison, and publication."
    ) in method_route
    about_route = (output / "about" / "index.html").read_text(encoding="utf-8")
    assert "A shared idea, built into a benchmark." in about_route
    assert (
        "Read how Deep20Bench began, see project news, and review related research."
        in about_route
    )
    story_route = (output / "story" / "index.html").read_text(encoding="utf-8")
    assert "A shared idea, built into a benchmark." in story_route
    assert f'rel="canonical" href="{CANONICAL_URL}about/"' in story_route
    assert 'name="robots" content="noindex, follow"' in story_route
    run_route = next(route for route in _route_shells(bundle) if route.startswith("runs/"))
    run_shell = (output / run_route / "index.html").read_text(encoding="utf-8")
    assert "This detailed view uses JavaScript." in run_shell
    assert f'rel="canonical" href="{CANONICAL_URL}{run_route}/"' in run_shell
    assert 'name="robots" content="noindex, follow"' in run_shell
    not_found = (output / "404.html").read_text(encoding="utf-8")
    assert 'rel="canonical"' not in not_found
    assert 'name="robots" content="noindex, follow"' in not_found


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
