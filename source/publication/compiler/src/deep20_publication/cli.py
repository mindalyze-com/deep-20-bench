from __future__ import annotations

import filecmp
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from html import escape
from pathlib import Path
from typing import Annotated

import typer
from pydantic import JsonValue

from .compiler import compile_publication
from .integrity import (
    PublicationInputError,
    parse_json_object,
    parse_yaml_object,
    sha256_text,
)
from .loader import (
    parse_completed_episode,
    parse_diagnostic_error_outputs,
    parse_guesser_violation_snapshot,
    parse_publication_config,
    parse_run,
    parse_subject_catalog,
)
from .models import (
    CompletedTrialSummary,
    DiagnosticErrorOutputRecord,
    EpisodeActionTurn,
    GuesserViolationDisclosure,
    GuesserViolationSnapshot,
    LoadedEpisode,
    LoadedRun,
    PublicationAppBuildDocument,
    PublicationDataBundle,
    PublicationManifestDocument,
    PublicRejectedOutput,
    PublishedDataset,
)
from .serialize import dataset_json, leaderboard_csv, publication_document_json
from .split import split_publication

app = typer.Typer(help="Compile and render the independent Deep20Bench publication site.")


@dataclass(frozen=True)
class _EditorialPage:
    route: str
    browser_title: str
    heading: str
    description: str


_EDITORIAL_PAGES = (
    _EditorialPage(
        route="results",
        browser_title="Results · Deep20Bench",
        heading="Deep20Bench results.",
        description="Compare official model scores, outcomes, costs, time, and stability.",
    ),
    _EditorialPage(
        route="results/reliability",
        browser_title="Stability results · Deep20Bench",
        heading="Stability results.",
        description="Compare repeated-trial stability and contract compliance by model.",
    ),
    _EditorialPage(
        route="results/cost",
        browser_title="Cost results · Deep20Bench",
        heading="Cost results.",
        description="Compare recorded benchmark costs by model and component.",
    ),
    _EditorialPage(
        route="results/time",
        browser_title="Time results · Deep20Bench",
        heading="Time results.",
        description="Compare tested-model response time and end-to-end benchmark runtime.",
    ),
    _EditorialPage(
        route="results/efficiency",
        browser_title="Efficiency results · Deep20Bench",
        heading="Efficiency results.",
        description="Compare question score and recorded Guesser cost across official runs.",
    ),
    _EditorialPage(
        route="methodology",
        browser_title="Method · Deep20Bench",
        heading="Deep20Bench method.",
        description="Read the protocol, scoring method, eligibility rules, and isolation boundary.",
    ),
    _EditorialPage(
        route="story",
        browser_title="Story · Deep20Bench",
        heading="Deep20Bench story.",
        description="Read about the benchmark's origin, scope, creators, and related work.",
    ),
    _EditorialPage(
        route="data",
        browser_title="Data · Deep20Bench",
        heading="Deep20Bench data.",
        description="Download the public dataset and inspect its contents and citation details.",
    ),
)
_EDITORIAL_ROUTES = tuple(page.route for page in _EDITORIAL_PAGES)
_CANONICAL_LINK_PATTERN = re.compile(r'<link rel="canonical" href="[^"]*" />')
_OPEN_GRAPH_URL_PATTERN = re.compile(r'<meta property="og:url" content="[^"]*" />')
_ROBOTS_META_PATTERN = re.compile(r'<meta name="robots" content="[^"]*" />')
_DESCRIPTION_META_PATTERN = re.compile(r'<meta\s+name="description"\s+content="[^"]*"\s*/>')
_OPEN_GRAPH_TITLE_PATTERN = re.compile(r'<meta property="og:title" content="[^"]*" />')
_OPEN_GRAPH_DESCRIPTION_PATTERN = re.compile(
    r'<meta\s+property="og:description"\s+content="[^"]*"\s*/>'
)
_TWITTER_TITLE_PATTERN = re.compile(r'<meta name="twitter:title" content="[^"]*" />')
_TWITTER_DESCRIPTION_PATTERN = re.compile(
    r'<meta\s+name="twitter:description"\s+content="[^"]*"\s*/>'
)
_TITLE_PATTERN = re.compile(r"<title>.*?</title>", re.DOTALL)
_STRUCTURED_DATA_PATTERN = re.compile(
    r'\s*<script type="application/ld\+json">.*?</script>',
    re.DOTALL,
)


@app.callback()
def publication() -> None:
    """Prepare public Deep20Bench data and the static GitHub Pages site."""


def _repository_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() and (
            candidate / "source" / "publication" / "compiler"
        ).is_dir():
            return candidate
    raise FileNotFoundError("Deep20Bench repository root not found")


def _timestamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise PublicationInputError(f"cannot read {path}: {error}") from error


def _read_yaml(path: Path) -> dict[str, JsonValue]:
    return parse_yaml_object(_read_text(path), str(path))


def _read_json(path: Path) -> dict[str, JsonValue]:
    return parse_json_object(_read_text(path), str(path))


def _publication_build_time(repository: Path, *, check: bool) -> datetime:
    if not check:
        return datetime.now(UTC)
    manifest_path = repository / "docs" / "data" / "manifest.json"
    manifest = PublicationManifestDocument.model_validate(_read_json(manifest_path))
    return manifest.provenance.built_at


def _application_build_document(
    repository: Path,
    *,
    check: bool,
) -> PublicationAppBuildDocument:
    if not check:
        return PublicationAppBuildDocument(built_at=datetime.now(UTC))
    build_path = repository / "docs" / "data" / "app-build.json"
    return PublicationAppBuildDocument.model_validate(_read_json(build_path))


def _load_run(
    summary_path: Path,
    repository: Path,
    violation_snapshot: GuesserViolationSnapshot | None = None,
) -> LoadedRun:
    run_root = summary_path.parent
    manifest_path = run_root / "manifest.json"
    state_path = run_root / "state.yml"
    if not manifest_path.is_file() or not state_path.is_file():
        raise PublicationInputError(f"{summary_path} has no adjacent manifest or state")
    try:
        relative = summary_path.resolve().relative_to(repository.resolve()).as_posix()
    except ValueError as error:
        raise PublicationInputError(f"{summary_path} is outside repository") from error
    loaded = parse_run(
        summary=_read_yaml(summary_path),
        manifest=_read_json(manifest_path),
        state=_read_yaml(state_path),
        summary_label=str(summary_path),
        manifest_label=str(manifest_path),
        state_label=str(state_path),
        relative_summary_path=relative,
    )
    episodes = _load_episode_details(loaded, repository, violation_snapshot)
    return LoadedRun(
        summary=loaded.summary,
        manifest=loaded.manifest,
        state=loaded.state,
        episodes=episodes,
        summary_path=loaded.summary_path,
    )


def _load_episode_details(
    run: LoadedRun,
    repository: Path,
    violation_snapshot: GuesserViolationSnapshot | None = None,
) -> tuple[LoadedEpisode, ...]:
    episodes: list[LoadedEpisode] = []
    repository_root = repository.resolve()
    for subject in run.summary.subjects:
        for trial in subject.trials:
            if not isinstance(trial, CompletedTrialSummary):
                continue
            reference = trial.artifacts.trial_result
            source = (repository / reference.relative_path).resolve()
            try:
                relative = source.relative_to(repository_root).as_posix()
            except ValueError as error:
                raise PublicationInputError(
                    f"episode detail is outside repository: {reference.relative_path}"
                ) from error
            if not source.is_file():
                raise PublicationInputError(f"episode detail does not exist: {relative}")
            source_text = _read_text(source)
            episode = parse_completed_episode(
                value=parse_yaml_object(source_text, str(source)),
                label=str(source),
                relative_path=relative,
                actual_file_integrity_hash=sha256_text(source_text),
                expected_integrity_hash=reference.integrity_hash,
            )
            if violation_snapshot is not None:
                disclosures = tuple(
                    record
                    for record in violation_snapshot.records
                    if record.execution_id == episode.identity.execution_id
                    and record.target_id == episode.identity.target_id
                    and record.trial_id == episode.identity.trial_id
                )
                expected = {
                    (turn.turn_number, turn.violation_kind)
                    for turn in episode.result.turns
                    if not isinstance(turn, EpisodeActionTurn)
                }
                actual = {(record.turn_number, record.violation_kind) for record in disclosures}
                if actual != expected:
                    raise PublicationInputError(
                        f"{relative} Guesser violation disclosures do not match "
                        "its recorded contract violations"
                    )
                episode = episode.model_copy(update={"violation_disclosures": disclosures})
            episodes.append(episode)
    return tuple(episodes)


def _discover_runs(
    repository: Path,
    violation_snapshot: GuesserViolationSnapshot | None = None,
) -> tuple[LoadedRun, ...]:
    candidates = sorted((repository / "runs").glob("M-[0-9][0-9][0-9][0-9]/BX-*/summary.yml"))
    runs = tuple(_load_run(path, repository, violation_snapshot) for path in candidates)
    if violation_snapshot is not None:
        attached = sum(
            len(episode.violation_disclosures) for run in runs for episode in run.episodes
        )
        if attached != len(violation_snapshot.records):
            raise PublicationInputError(
                "Guesser violation disclosure snapshot contains unknown episode records"
            )
    return runs


def _guesser_violation_snapshot_path(repository: Path) -> Path:
    return repository / "source" / "publication" / "data" / "guesser-violation-outputs-v1.json"


def _episode_diagnostic_records(
    episode: LoadedEpisode,
    repository: Path,
) -> tuple[DiagnosticErrorOutputRecord, ...]:
    reference = episode.artifacts.error_outputs
    if reference is None:
        return ()
    source = (repository / reference.relative_path).resolve()
    try:
        source.relative_to(repository.resolve())
    except ValueError as error:
        raise PublicationInputError(
            f"error-output diagnostic is outside repository: {reference.relative_path}"
        ) from error
    if not source.is_file():
        raise PublicationInputError(
            f"error-output diagnostic does not exist: {reference.relative_path}"
        )
    if source.stat().st_mode & 0o077:
        raise PublicationInputError(
            f"error-output diagnostic is not owner-only: {reference.relative_path}"
        )
    return parse_diagnostic_error_outputs(
        text=_read_text(source),
        label=str(source),
        expected_record_count=reference.record_count,
        expected_integrity_hash=reference.integrity_hash,
    )


def _capture_guesser_violation_snapshot(
    runs: tuple[LoadedRun, ...],
    repository: Path,
) -> GuesserViolationSnapshot:
    disclosures: list[GuesserViolationDisclosure] = []
    for run in runs:
        for episode in run.episodes:
            diagnostics = {
                record.call_id: record
                for record in _episode_diagnostic_records(episode, repository)
                if record.component == "guesser"
            }
            for turn in episode.result.turns:
                if isinstance(turn, EpisodeActionTurn):
                    continue
                diagnostic = diagnostics.get(turn.guesser_call_id)
                if diagnostic is not None and diagnostic.recovered:
                    raise PublicationInputError(
                        f"{episode.relative_path} maps a recovered diagnostic "
                        f"to rejected turn {turn.turn_number}"
                    )
                rejected_outputs = (
                    tuple(
                        PublicRejectedOutput(
                            attempt_number=output.attempt_number,
                            finish_reason=output.finish_reason,
                            text=output.output,
                        )
                        for output in diagnostic.outputs
                    )
                    if diagnostic is not None
                    else ()
                )
                disclosures.append(
                    GuesserViolationDisclosure(
                        execution_id=episode.identity.execution_id,
                        target_id=episode.identity.target_id,
                        trial_id=episode.identity.trial_id,
                        turn_number=turn.turn_number,
                        violation_kind=turn.violation_kind,
                        rejected_outputs=rejected_outputs,
                    )
                )
    return GuesserViolationSnapshot(
        records=tuple(
            sorted(
                disclosures,
                key=lambda record: (
                    record.execution_id,
                    record.target_id,
                    record.trial_id,
                    record.turn_number,
                ),
            )
        )
    )


def _directories_equal(left: Path, right: Path) -> bool:
    if not left.is_dir() or not right.is_dir():
        return False
    comparison = filecmp.dircmp(left, right)
    if comparison.left_only or comparison.right_only or comparison.funny_files:
        return False
    if any(
        not filecmp.cmp(left / name, right / name, shallow=False)
        for name in comparison.common_files
    ):
        return False
    return all(_directories_equal(left / name, right / name) for name in comparison.common_dirs)


def _ensure_site_dependencies(site_root: Path) -> None:
    required = (
        site_root / "node_modules" / ".bin" / "vite",
        site_root / "node_modules" / ".bin" / "vue-tsc",
        site_root / "node_modules" / "vue",
        site_root / "node_modules" / "vue-router",
    )
    if all(path.exists() for path in required):
        return
    subprocess.run(["npm", "ci"], cwd=site_root, check=True)


def _write_public_data(
    public_directory: Path,
    dataset: PublishedDataset,
    app_build: PublicationAppBuildDocument,
) -> None:
    public_directory.mkdir(parents=True, exist_ok=True)
    data_directory = public_directory / "data"
    bundle = split_publication(dataset)
    staged_directory = Path(tempfile.mkdtemp(prefix=".deep20-data-", dir=public_directory))
    backup_directory = public_directory / ".deep20-data-previous"
    try:
        (staged_directory / "deep20bench-v7.json").write_text(
            dataset_json(dataset),
            encoding="utf-8",
        )
        (staged_directory / "leaderboard.csv").write_text(
            leaderboard_csv(dataset),
            encoding="utf-8",
        )
        (staged_directory / "manifest.json").write_text(
            publication_document_json(bundle.manifest),
            encoding="utf-8",
        )
        (staged_directory / "app-build.json").write_text(
            publication_document_json(app_build),
            encoding="utf-8",
        )
        (staged_directory / "leaderboard.json").write_text(
            publication_document_json(bundle.leaderboard),
            encoding="utf-8",
        )
        (staged_directory / "repeat-averages.json").write_text(
            publication_document_json(bundle.repeat_averages),
            encoding="utf-8",
        )
        for run_document in bundle.runs:
            path = staged_directory / "runs" / f"{run_document.run.execution_id}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                publication_document_json(run_document),
                encoding="utf-8",
            )
        for subject_document in bundle.subjects:
            path = (
                staged_directory
                / "runs"
                / subject_document.execution_id
                / "subjects"
                / f"{subject_document.target_id}.json"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                publication_document_json(subject_document),
                encoding="utf-8",
            )
        for episode_document in bundle.episodes:
            path = (
                staged_directory
                / "runs"
                / episode_document.execution_id
                / "subjects"
                / episode_document.target_id
                / "episodes"
                / f"{episode_document.trial_id}.json"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                publication_document_json(episode_document),
                encoding="utf-8",
            )

        if backup_directory.exists():
            shutil.rmtree(backup_directory)
        if data_directory.exists():
            data_directory.rename(backup_directory)
        try:
            staged_directory.rename(data_directory)
        except BaseException:
            if backup_directory.exists() and not data_directory.exists():
                backup_directory.rename(data_directory)
            raise
        if backup_directory.exists():
            shutil.rmtree(backup_directory)
    finally:
        if staged_directory.exists():
            shutil.rmtree(staged_directory)


def _route_shells(bundle: PublicationDataBundle) -> tuple[str, ...]:
    runs = tuple(f"runs/{document.run.execution_id}" for document in bundle.runs)
    subjects = tuple(
        f"runs/{document.execution_id}/subjects/{document.target_id}"
        for document in bundle.subjects
    )
    episodes = tuple(
        (f"runs/{document.execution_id}/subjects/{document.target_id}/episodes/{document.trial_id}")
        for document in bundle.episodes
    )
    return (*_EDITORIAL_ROUTES, *runs, *subjects, *episodes)


def _canonical_route_url(canonical_url: str, route: str) -> str:
    return canonical_url if route == "" else f"{canonical_url}{route}/"


def _sitemap_routes() -> tuple[str, ...]:
    return ("", *_EDITORIAL_ROUTES)


def _editorial_page(route: str) -> _EditorialPage | None:
    return next((page for page in _EDITORIAL_PAGES if page.route == route), None)


def _decimal_text(value: Decimal) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _current_results_html(bundle: PublicationDataBundle, safe_base: str) -> str:
    winner = bundle.manifest.winner
    evaluated = tuple(
        row
        for row in bundle.leaderboard.leaderboard
        if row.status == "evaluated"
        and row.execution_id is not None
        and row.rank is not None
        and row.question_score is not None
    )
    if winner is None or not evaluated:
        return """<section class="static-route-result">
            <h2>Official results are in progress.</h2>
            <p>Scores appear after a complete, integrity-checked run covers every subject.</p>
          </section>"""

    leader_rows: list[str] = []
    for row in evaluated[:3]:
        execution_id = row.execution_id
        rank = row.rank
        question_score = row.question_score
        if execution_id is None or rank is None or question_score is None:
            raise PublicationInputError("evaluated leaderboard row is incomplete")
        leader_rows.append(
            f"""<li>
              <span>{rank}</span>
              <a href="{safe_base}runs/{escape(execution_id, quote=True)}/">
                {escape(row.model.display_name)}
              </a>
              <strong>{_decimal_text(question_score)} questions</strong>
            </li>"""
        )
    leaders = "\n".join(leader_rows)
    leader_label = "Joint official leaders" if winner.joint else "Official leader"
    return f"""<section class="static-route-result" aria-labelledby="static-result-title">
            <p>{leader_label}</p>
            <h2 id="static-result-title">{escape(" · ".join(winner.display_names))}</h2>
            <p>
              The current leader has a question score of
              <strong>{_decimal_text(winner.question_score)}</strong>. Lower is better.
            </p>
            <ol aria-label="Top three official model results">
              {leaders}
            </ol>
          </section>"""


def _editorial_fallback_html(
    page: _EditorialPage,
    bundle: PublicationDataBundle,
    safe_base: str,
) -> str:
    results = _current_results_html(bundle, safe_base) if page.route == "results" else ""
    return f"""<main class="static-route-fallback static-route-fallback--editorial">
        <div>
          <p>Deep20Bench · Static publication summary</p>
          <h1>{escape(page.heading)}</h1>
          <p>{escape(page.description)}</p>
          {results}
          <nav aria-label="Publication navigation">
            <a href="{safe_base}">Overview</a>
            <a href="{safe_base}results/">Results</a>
            <a href="{safe_base}methodology/">Method</a>
            <a href="{safe_base}data/">Data</a>
          </nav>
        </div>
      </main>"""


def _write_search_files(output_root: Path, canonical_url: str) -> None:
    locations = "\n".join(
        "  <url>\n"
        f"    <loc>{escape(_canonical_route_url(canonical_url, route), quote=False)}</loc>\n"
        "  </url>"
        for route in _sitemap_routes()
    )
    (output_root / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{locations}\n"
        "</urlset>\n",
        encoding="utf-8",
    )
    (output_root / "robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {canonical_url}sitemap.xml\n",
        encoding="utf-8",
    )


def _replace_required_tag(
    html: str,
    pattern: re.Pattern[str],
    replacement: str,
    label: str,
) -> str:
    updated, count = pattern.subn(replacement, html)
    if count != 1:
        raise PublicationInputError(f"generated HTML must contain exactly one {label} tag")
    return updated


def _route_metadata_html(
    html: str,
    *,
    canonical_url: str | None,
    indexable: bool,
    editorial_page: _EditorialPage | None,
) -> str:
    if canonical_url is None:
        html, count = _CANONICAL_LINK_PATTERN.subn("", html)
        if count != 1:
            raise PublicationInputError(
                "generated HTML must contain exactly one canonical URL tag"
            )
    else:
        safe_url = escape(canonical_url, quote=True)
        html = _replace_required_tag(
            html,
            _CANONICAL_LINK_PATTERN,
            f'<link rel="canonical" href="{safe_url}" />',
            "canonical URL",
        )
        html = _replace_required_tag(
            html,
            _OPEN_GRAPH_URL_PATTERN,
            f'<meta property="og:url" content="{safe_url}" />',
            "Open Graph URL",
        )
    if editorial_page is not None:
        safe_title = escape(editorial_page.browser_title)
        safe_description = escape(editorial_page.description, quote=True)
        html = _replace_required_tag(
            html,
            _TITLE_PATTERN,
            f"<title>{safe_title}</title>",
            "document title",
        )
        html = _replace_required_tag(
            html,
            _DESCRIPTION_META_PATTERN,
            f'<meta name="description" content="{safe_description}" />',
            "description",
        )
        html = _replace_required_tag(
            html,
            _OPEN_GRAPH_TITLE_PATTERN,
            f'<meta property="og:title" content="{safe_title}" />',
            "Open Graph title",
        )
        html = _replace_required_tag(
            html,
            _OPEN_GRAPH_DESCRIPTION_PATTERN,
            f'<meta property="og:description" content="{safe_description}" />',
            "Open Graph description",
        )
        html = _replace_required_tag(
            html,
            _TWITTER_TITLE_PATTERN,
            f'<meta name="twitter:title" content="{safe_title}" />',
            "Twitter title",
        )
        html = _replace_required_tag(
            html,
            _TWITTER_DESCRIPTION_PATTERN,
            f'<meta name="twitter:description" content="{safe_description}" />',
            "Twitter description",
        )
    robots = (
        "index, follow, max-image-preview:large" if indexable else "noindex, follow"
    )
    html = _replace_required_tag(
        html,
        _ROBOTS_META_PATTERN,
        f'<meta name="robots" content="{robots}" />',
        "robots",
    )
    html, structured_count = _STRUCTURED_DATA_PATTERN.subn("", html)
    if structured_count != 1:
        raise PublicationInputError(
            "generated HTML must contain exactly one Dataset structured-data block"
        )
    return re.sub(r"[ \t]+$", "", html, flags=re.MULTILINE)


def _write_route_shells(
    output_root: Path,
    bundle: PublicationDataBundle,
    canonical_url: str,
) -> None:
    entry = output_root / "index.html"
    entry_html = entry.read_text(encoding="utf-8")
    for route in _route_shells(bundle):
        shell = output_root / route / "index.html"
        shell.parent.mkdir(parents=True, exist_ok=True)
        editorial_page = _editorial_page(route)
        route_html = _route_shell_html(
            entry_html,
            bundle.manifest.site.base_path,
            route=route,
            bundle=bundle,
            canonical_url=_canonical_route_url(canonical_url, route),
            indexable=editorial_page is not None,
        )
        shell.write_text(route_html, encoding="utf-8")
    not_found_html = _route_shell_html(
        entry_html,
        bundle.manifest.site.base_path,
        route=None,
        bundle=bundle,
        canonical_url=None,
        indexable=False,
    )
    (output_root / "404.html").write_text(not_found_html, encoding="utf-8")


def _route_shell_html(
    entry_html: str,
    base_path: str,
    *,
    route: str | None,
    bundle: PublicationDataBundle,
    canonical_url: str | None,
    indexable: bool,
) -> str:
    static_home_start = '<main class="static-home" id="static-home">'
    start = entry_html.find(static_home_start)
    if start < 0:
        return entry_html
    end = entry_html.find("</main>", start)
    if end < 0:
        raise PublicationInputError("generated static homepage has no closing main tag")
    end += len("</main>")
    safe_base = escape(base_path, quote=True)
    editorial_page = None if route is None else _editorial_page(route)
    fallback = (
        _editorial_fallback_html(editorial_page, bundle, safe_base)
        if editorial_page is not None
        else f"""<main class="static-route-fallback">
        <div>
          <p>Deep20Bench · Interactive publication</p>
          <h1>This detailed view uses JavaScript.</h1>
          <p>The complete executive summary and public data remain available without it.</p>
          <nav aria-label="Non-JavaScript options">
            <a href="{safe_base}">Read the executive summary</a>
            <a href="{safe_base}data/leaderboard.csv">Download the leaderboard</a>
          </nav>
        </div>
      </main>"""
    )
    route_html = f"{entry_html[:start]}{fallback}{entry_html[end:]}"
    return _route_metadata_html(
        route_html,
        canonical_url=canonical_url,
        indexable=indexable,
        editorial_page=editorial_page,
    )


def _build_site(
    site_root: Path,
    public_root: Path,
    output_root: Path,
    base_path: str,
    canonical_url: str,
    bundle: PublicationDataBundle,
) -> None:
    environment = dict(os.environ)
    environment["DEEP20_OUTPUT_DIR"] = str(output_root)
    environment["DEEP20_PUBLIC_DIR"] = str(public_root)
    environment["DEEP20_BASE_PATH"] = base_path
    environment["DEEP20_CANONICAL_URL"] = canonical_url
    subprocess.run(
        ["npm", "run", "build"],
        cwd=site_root,
        env=environment,
        check=True,
    )
    _write_route_shells(output_root, bundle, canonical_url)
    _write_search_files(output_root, canonical_url)


@app.command("build")
def build(
    repository: Annotated[
        Path | None,
        typer.Option(help="Deep20Bench repository root; discovered by default."),
    ] = None,
    check: Annotated[
        bool,
        typer.Option("--check", help="Verify that committed output is current."),
    ] = False,
) -> None:
    try:
        root = _repository_root(repository or Path.cwd())
        publication_root = root / "source" / "publication"
        site_root = publication_root / "site"
        publication_path = root / "config" / "publication.yml"
        subject_path = root / "config" / "subjects.yaml"
        config = parse_publication_config(_read_yaml(publication_path), str(publication_path))
        subjects, subject_hash = parse_subject_catalog(
            _read_yaml(subject_path),
            str(subject_path),
        )
        violation_snapshot_path = _guesser_violation_snapshot_path(root)
        violation_snapshot = parse_guesser_violation_snapshot(
            _read_json(violation_snapshot_path),
            str(violation_snapshot_path),
        )
        runs = _discover_runs(root, violation_snapshot)
        built_at = _publication_build_time(root, check=check)
        dataset = compile_publication(
            runs=runs,
            config=config,
            subject_catalog=subjects,
            subject_catalog_hash=subject_hash,
            built_at=built_at,
        )
        bundle = split_publication(dataset)
        _ensure_site_dependencies(site_root)
        app_build = _application_build_document(root, check=check)
        with tempfile.TemporaryDirectory(prefix="deep20-publication-") as temporary:
            staging_root = Path(temporary)
            public_root = staging_root / "public"
            shutil.copytree(
                site_root / "public",
                public_root,
                ignore=shutil.ignore_patterns("data"),
            )
            _write_public_data(public_root, dataset, app_build)
            candidate = staging_root / "docs"
            _build_site(
                site_root,
                public_root,
                candidate,
                config.site.base_path,
                str(config.site.canonical_url),
                bundle,
            )
            if check:
                if not _directories_equal(candidate, root / "docs"):
                    raise PublicationInputError("committed docs output is stale")
            else:
                output = root / "docs"
                backup = staging_root / "previous-docs"
                if output.exists():
                    output.rename(backup)
                try:
                    shutil.copytree(candidate, output)
                except BaseException:
                    if output.exists():
                        shutil.rmtree(output)
                    if backup.exists():
                        backup.rename(output)
                    raise
        typer.echo(
            f"{_timestamp()} INFO publication.result runs={len(runs)} "
            f"official={dataset.provenance.official_run_count} "
            f"lab={dataset.provenance.lab_run_count} output=docs"
        )
    except (OSError, PublicationInputError, subprocess.CalledProcessError, ValueError) as error:
        typer.echo(
            f"{_timestamp()} ERROR publication.failed code=publication_build_failed "
            f"message={str(error)!r}",
            err=True,
        )
        raise typer.Exit(1) from error


@app.command("capture-guesser-outputs")
def capture_guesser_outputs(
    repository: Annotated[
        Path | None,
        typer.Option(help="Deep20Bench repository root; discovered by default."),
    ] = None,
) -> None:
    """Create the public-safe Guesser violation snapshot from owner-only diagnostics."""

    try:
        root = _repository_root(repository or Path.cwd())
        runs = _discover_runs(root)
        snapshot = _capture_guesser_violation_snapshot(runs, root)
        output = _guesser_violation_snapshot_path(root)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(
                snapshot.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        retained = sum(len(record.rejected_outputs) for record in snapshot.records)
        typer.echo(
            f"{_timestamp()} INFO publication.guesser_outputs "
            f"violations={len(snapshot.records)} retained_outputs={retained} "
            f"output={output.relative_to(root).as_posix()}"
        )
    except (OSError, PublicationInputError, ValueError) as error:
        typer.echo(
            f"{_timestamp()} ERROR publication.failed "
            f"code=guesser_output_capture_failed message={str(error)!r}",
            err=True,
        )
        raise typer.Exit(1) from error


if __name__ == "__main__":
    app()
