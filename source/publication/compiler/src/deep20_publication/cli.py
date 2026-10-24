from __future__ import annotations

import filecmp
import json
import os
import shutil
import subprocess
import tempfile
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from itertools import repeat
from pathlib import Path
from typing import Annotated

import typer
from pydantic import JsonValue

from .comparison import build_comparison
from .compiler import compile_publication, superseded_qualified_runs
from .draft import load_draft, render_draft
from .edition_registry import EditionRegistry
from .integrity import (
    PublicationInputError,
    canonical_json,
    parse_json_object,
    parse_yaml_object,
    sha256_text,
)
from .legacy import legacy_dataset, legacy_dataset_schema_json
from .loader import (
    parse_completed_episode,
    parse_diagnostic_error_outputs,
    parse_guesser_violation_snapshot,
    parse_publication_config,
    parse_run,
    parse_subject_catalog,
)
from .model_pages import EditionModelPages, build_model_pages
from .models import (
    CompletedTrialSummary,
    DiagnosticErrorOutputRecord,
    EpisodeActionTurn,
    GuesserViolationDisclosure,
    GuesserViolationSnapshot,
    LoadedEpisode,
    LoadedRun,
    PublicationAppBuildDocument,
    PublicationConfig,
    PublicationDataBundle,
    PublicationDownload,
    PublicationDownloadPath,
    PublicationEditionsDocument,
    PublicationManifestDocument,
    PublicRejectedOutput,
    PublishedDataset,
    QualifiedEligibility,
    StaticRouteEntry,
    StaticRouteManifest,
)
from .serialize import (
    dataset_json,
    dataset_schema_json,
    leaderboard_csv,
    publication_document_json,
)
from .split import edition_index, split_publication

app = typer.Typer(help="Compile and render the independent Deep20Bench publication site.")


@app.command("preview-draft")
def preview_draft(
    model_id: Annotated[str, typer.Option("--model")],
    run_id: Annotated[str, typer.Option("--run-id")],
    edition_id: Annotated[str, typer.Option("--edition")],
    repository: Annotated[Path | None, typer.Option()] = None,
) -> None:
    """Render a local draft report under private/, without changing docs/."""
    try:
        root = _repository_root(repository or Path.cwd())
        report = load_draft(root, edition_id=edition_id, model_id=model_id, run_id=run_id)
        destination = root / "private" / "editions" / edition_id / "previews" / model_id / f"{run_id}.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(render_draft(report), encoding="utf-8")
        typer.echo(f"publication.draft_preview path={destination}")
    except (OSError, ValueError, PublicationInputError):
        typer.echo("publication.draft_preview_failed: invalid or missing local draft artifacts", err=True)
        raise typer.Exit(1) from None


@dataclass(frozen=True)
class _EditorialPage:
    route: str
    browser_title: str
    description: str


_EDITORIAL_PAGES = (
    _EditorialPage(
        route="results/compare",
        browser_title="Compare AI Models Side by Side | Deep20Bench",
        description=(
            "Compare up to five AI models side by side: question score, stability, cost, "
            "time, and results for each subject and round."
        ),
    ),
    _EditorialPage(
        route="results",
        browser_title="AI Model Leaderboard: LLM Benchmark Results | Deep20Bench",
        description=(
            "Compare official Twenty Questions AI benchmark scores for LLMs: outcomes, "
            "costs, runtime, and stability across rounds."
        ),
    ),
    _EditorialPage(
        route="results/reliability",
        browser_title="AI Benchmark Stability and Reliability | Deep20Bench",
        description=(
            "Compare how consistent AI model scores are across repeated rounds, their confidence "
            "intervals, and how often models use the required reply format."
        ),
    ),
    _EditorialPage(
        route="results/cost",
        browser_title="AI Benchmark Cost Comparison | Deep20Bench",
        description=(
            "Compare AI benchmark costs by tested model, answer-checking model, run, "
            "and round."
        ),
    ),
    _EditorialPage(
        route="results/time",
        browser_title="AI Benchmark Runtime and Response Time | Deep20Bench",
        description=(
            "Compare how long tested models take per round and per call, and total AI "
            "benchmark runtime."
        ),
    ),
    _EditorialPage(
        route="results/efficiency",
        browser_title="AI Benchmark Cost Efficiency | Deep20Bench",
        description=(
            "Compare question score and tested-model cost across official "
            "Twenty Questions AI benchmark runs."
        ),
    ),
    _EditorialPage(
        route="why",
        browser_title="Why Twenty Questions Is a Good AI Benchmark | Deep20Bench",
        description=(
            "Why Twenty Questions makes a simple, repeatable AI benchmark for LLMs: easy "
            "to play, hard to play well."
        ),
    ),
    _EditorialPage(
        route="methodology",
        browser_title="Twenty Questions AI Benchmark Method | Deep20Bench",
        description=(
            "How the Deep20Bench Twenty Questions AI benchmark works: the game, answer "
            "checks, scoring, and publication."
        ),
    ),
    _EditorialPage(
        route="about",
        browser_title="Deep20Bench Origin and Related LLM Research",
        description=(
            "How the Deep20Bench AI benchmark began, project news, and related Twenty "
            "Questions LLM research."
        ),
    ),
    _EditorialPage(
        route="data",
        browser_title="Deep20Bench Dataset, Results and Transcripts",
        description=(
            "Download the public Deep20Bench dataset, leaderboard, round transcripts, "
            "schema, and citation details."
        ),
    ),
)
_EDITORIAL_ALIASES: dict[str, str] = {"story": "about"}


def _round_label(trial_id: str) -> str:
    """Return the public round label for a validated `trial-NNN` identifier."""
    return f"Round {int(trial_id.removeprefix('trial-'))}"


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


def _repository_relative_path(path: Path, repository: Path) -> str:
    """Retain operator-created storage symlinks and reject lexical path escapes."""
    return Path(os.path.abspath(path)).relative_to(repository.resolve()).as_posix()


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
        relative = _repository_relative_path(summary_path, repository)
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
    for subject in run.summary.subjects:
        for trial in subject.trials:
            if not isinstance(trial, CompletedTrialSummary):
                continue
            reference = trial.artifacts.trial_result
            source = repository / reference.relative_path
            try:
                relative = _repository_relative_path(source, repository)
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
                if not actual.issubset(expected):
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
    workers = min(len(candidates), os.cpu_count() or 1)
    if workers <= 1:
        runs = tuple(_load_run(path, repository, violation_snapshot) for path in candidates)
    else:
        # YAML construction dominates build time; runs are independent, and map keeps their
        # order and re-raises the first failing run's error, exactly like a sequential load.
        with ProcessPoolExecutor(max_workers=workers) as pool:
            runs = tuple(pool.map(
                _load_run,
                candidates,
                repeat(repository),
                repeat(violation_snapshot),
            ))
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
    source = repository / reference.relative_path
    try:
        _repository_relative_path(source, repository)
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
    *,
    datasets: tuple[PublishedDataset, ...] | None = None,
    editions: PublicationEditionsDocument | None = None,
    model_pages: tuple[EditionModelPages, ...] = (),
) -> None:
    public_directory.mkdir(parents=True, exist_ok=True)
    data_directory = public_directory / "data"
    datasets = datasets or (dataset,)
    staged = Path(tempfile.mkdtemp(prefix=".deep20-data-", dir=public_directory))
    backup = public_directory / ".deep20-data-previous"

    def write(path: str, content: str) -> None:
        destination = staged / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    try:
        historical = next(item for item in datasets if item.active_cohort.edition_id == "1.0")
        write("deep20bench-v9.json", legacy_dataset(historical).model_dump_json(indent=2) + "\n")
        write("deep20bench-v9.schema.json", legacy_dataset_schema_json())
        # Unversioned data URLs retain the historical dataset's comparison meaning.
        write("leaderboard.csv", leaderboard_csv(historical))
        write("app-build.json", publication_document_json(app_build))
        if editions is not None:
            write("editions.json", publication_document_json(editions))
        for item in datasets:
            bundle = split_publication(item)
            prefix = f"editions/{item.active_cohort.edition_id}/"
            write(prefix + "compare.json", build_comparison(bundle).model_dump_json() + "\n")
            downloads: tuple[tuple[PublicationDownloadPath, str], ...] = (
                ("deep20bench-v10.json", dataset_json(item)),
                ("deep20bench-v10.schema.json", dataset_schema_json()),
                ("leaderboard.csv", leaderboard_csv(item)),
            )
            for download_path, content in downloads:
                write(prefix + download_path, content)
            manifest = bundle.manifest.model_copy(
                update={
                    "downloads": tuple(
                        PublicationDownload(path=path, size_bytes=len(text.encode()))
                        for path, text in downloads
                    )
                }
            )
            for filename, document in (("manifest.json", manifest),
                                       ("leaderboard.json", bundle.leaderboard),
                                       ("repeat-averages.json", bundle.repeat_averages)):
                write(prefix + filename, publication_document_json(document))
                if item.active_cohort.edition_id == "1.0":
                    write(filename, publication_document_json(document))
            for run in bundle.runs:
                write(f"runs/{run.run.execution_id}.json", publication_document_json(run))
            for pages in model_pages:
                if pages.edition_id != item.active_cohort.edition_id:
                    continue
                write(prefix + "models.json", publication_document_json(pages.index))
                for model in pages.models:
                    write(prefix + f"models/{model.slug}.json", publication_document_json(model))
            for subject in bundle.subjects:
                write(f"runs/{subject.execution_id}/subjects/{subject.target_id}.json",
                      publication_document_json(subject))
            for episode in bundle.episodes:
                write(f"runs/{episode.execution_id}/subjects/{episode.target_id}/episodes/"
                      f"{episode.trial_id}.json", publication_document_json(episode))
        if backup.exists():
            shutil.rmtree(backup)
        if data_directory.exists():
            data_directory.rename(backup)
        try:
            staged.rename(data_directory)
        except BaseException:
            if backup.exists() and not data_directory.exists():
                backup.rename(data_directory)
            raise
        if backup.exists():
            shutil.rmtree(backup)
    finally:
        if staged.exists():
            shutil.rmtree(staged)


def _decimal_text(value: Decimal) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _percent_text(value: Decimal) -> str:
    return f"{value * Decimal(100):.1f}".rstrip("0").rstrip(".")


def _content_modified(bundle: PublicationDataBundle) -> datetime:
    """Return when the edition's published results last changed: its newest run completion."""
    return max(
        (document.run.completed_at for document in bundle.runs),
        default=bundle.manifest.provenance.built_at,
    )


def _model_routes(
    bundle: PublicationDataBundle, pages: EditionModelPages,
) -> tuple[StaticRouteEntry, ...]:
    """Return the edition's model index and one stable summary route per model."""
    # Subject ranks on a model page compare every model, so any new run can change them.
    last_modified = _content_modified(bundle)
    subject_names = {
        subject.target_id: subject.display_name
        for document in bundle.runs
        for subject in document.subjects
    }
    index = StaticRouteEntry(
        route="models",
        kind="model-index",
        indexable=True,
        sitemap_included=True,
        canonical_route="models",
        browser_title="Models Tested on Twenty Questions | Deep20Bench",
        description=(
            f"All {len(pages.models)} models with an official Deep20Bench result, with rank, "
            "question score, and rounds solved. Each links to a model summary."
        ),
        last_modified=last_modified,
    )
    models: list[StaticRouteEntry] = []
    for document in pages.models:
        result = document.result
        name = result.model.display_name
        score = (
            _decimal_text(result.question_score)
            if result.question_score is not None
            else "unavailable"
        )
        standing = (
            f"ranks {result.rank} of {document.ranked_models} models"
            if result.rank is not None
            else "has no ranked result"
        )
        strongest = next(
            (
                subject_names[observation.target_id]
                for observation in document.observations
                if observation.kind == "strongest_subject" and observation.target_id is not None
            ),
            None,
        )
        models.append(StaticRouteEntry(
            route=f"models/{document.slug}",
            kind="model",
            indexable=True,
            sitemap_included=True,
            canonical_route=f"models/{document.slug}",
            browser_title=f"{name} Twenty Questions Results | Deep20Bench",
            description=(
                f"{name} {standing} on Deep20Bench with a {score} question score "
                f"(lower is better) and solved {result.successful} of "
                f"{result.terminal_trials} rounds."
                + (f" Strongest subject: {strongest}." if strongest is not None else "")
                + " See every round."
            ),
            last_modified=last_modified,
            model_id=result.model.model_id,
        ))
    return (index, *models)


def _static_route_manifest(
    bundle: PublicationDataBundle, pages: EditionModelPages | None = None,
) -> StaticRouteManifest:
    last_modified = _content_modified(bundle)
    evaluated_count = sum(
        row.status == "evaluated" for row in bundle.leaderboard.leaderboard
    )
    home = StaticRouteEntry(
        route="",
        kind="home",
        indexable=True,
        sitemap_included=True,
        canonical_route="",
        browser_title="Deep20Bench: A Twenty Questions AI Benchmark for LLMs",
        description=(
            f"Compare {evaluated_count} AI models playing Twenty Questions: how they choose "
            "questions, use earlier answers, follow the rules, and compare on score, cost, and time."
        ),
        last_modified=last_modified,
    )
    editorial = tuple(
        StaticRouteEntry(
            route=page.route,
            kind="editorial",
            indexable=True,
            sitemap_included=True,
            canonical_route=page.route,
            browser_title=page.browser_title,
            description=page.description,
            last_modified=last_modified,
        )
        for page in _EDITORIAL_PAGES
    )
    editorial_by_route = {entry.route: entry for entry in editorial}
    aliases = tuple(
        editorial_by_route[canonical_route].model_copy(
            update={"route": route, "kind": "alias", "sitemap_included": False},
        )
        for route, canonical_route in _EDITORIAL_ALIASES.items()
    )
    leaderboard_by_execution = {
        row.execution_id: row
        for row in bundle.leaderboard.leaderboard
        if row.execution_id is not None
    }
    # Model pages own "<model> Twenty Questions Results"; a run page names its date instead of
    # its opaque execution ID, which keeps titles short. Same-day runs keep the ID to stay unique.
    run_dates = Counter(
        (document.run.model_name, document.run.completed_at.date()) for document in bundle.runs
    )
    runs: list[StaticRouteEntry] = []
    for run_document in bundle.runs:
        run = run_document.run
        run_label = (
            f"{run.completed_at.day} {run.completed_at:%b %Y}"
            if run_dates[(run.model_name, run.completed_at.date())] == 1
            else run.execution_id
        )
        row = leaderboard_by_execution.get(run.execution_id)
        score = (
            _decimal_text(run.question_score)
            if run.question_score is not None
            else "unavailable"
        )
        success = (
            f"{_percent_text(run.success_rate)}%"
            if run.success_rate is not None
            else "unavailable"
        )
        rank = f"rank {row.rank}, " if row is not None and row.rank is not None else ""
        runs.append(
            StaticRouteEntry(
                route=f"runs/{run.execution_id}",
                kind="run",
                indexable=True,
                sitemap_included=True,
                canonical_route=f"runs/{run.execution_id}",
                browser_title=f"{run.model_name} Run, {run_label} | Deep20Bench",
                description=(
                    f"Official Twenty Questions AI benchmark results for {run.model_name}: "
                    f"{rank}"
                    f"{score} question score across {run.terminal_trials} rounds with "
                    f"{success} success."
                ),
                last_modified=run.completed_at,
                execution_id=run.execution_id,
            )
        )
    runs_by_execution = {document.run.execution_id: document for document in bundle.runs}
    subjects: list[StaticRouteEntry] = []
    for subject_document in bundle.subjects:
        run_document = runs_by_execution[subject_document.execution_id]
        run = run_document.run
        subject = next(
            summary
            for summary in run_document.subjects
            if summary.target_id == subject_document.target_id
        )
        score = (
            _decimal_text(subject.average_questions)
            if subject.average_questions is not None
            else "unavailable"
        )
        route = (
            f"runs/{subject_document.execution_id}/subjects/{subject_document.target_id}"
        )
        subjects.append(
            StaticRouteEntry(
                route=route,
                kind="subject",
                indexable=True,
                sitemap_included=True,
                canonical_route=route,
                browser_title=(
                    f"{run.model_name} on {subject.display_name} | Deep20Bench"
                ),
                description=(
                    f"{run.model_name} scored {score} questions on {subject.display_name} "
                    f"across {len(subject_document.trials)} Deep20Bench rounds, solving "
                    f"{subject.successful} of {len(subject_document.trials)}. "
                    "See every question, answer, and source."
                ),
                last_modified=run.completed_at,
                execution_id=subject_document.execution_id,
                target_id=subject_document.target_id,
            )
        )
    episodes = tuple(
        StaticRouteEntry(
            route=(
                f"runs/{episode_document.execution_id}/subjects/{episode_document.target_id}/"
                f"episodes/{episode_document.trial_id}"
            ),
            kind="episode",
            indexable=True,
            sitemap_included=True,
            canonical_route=(
                f"runs/{episode_document.execution_id}/subjects/{episode_document.target_id}/"
                f"episodes/{episode_document.trial_id}"
            ),
            browser_title=(
                f"{runs_by_execution[episode_document.execution_id].run.model_name} on "
                f"{episode_document.episode.subject_name} - "
                f"{_round_label(episode_document.trial_id)} | Deep20Bench"
            ),
            description=(
                "Questions, final answers, and Oracle evidence for "
                f"{runs_by_execution[episode_document.execution_id].run.model_name} finding "
                f"{episode_document.episode.subject_name} in "
                f"{_round_label(episode_document.trial_id).lower()}."
            ),
            last_modified=runs_by_execution[episode_document.execution_id].run.completed_at,
            execution_id=episode_document.execution_id,
            target_id=episode_document.target_id,
            trial_id=episode_document.trial_id,
        )
        for episode_document in bundle.episodes
    )
    models = () if pages is None else _model_routes(bundle, pages)
    return StaticRouteManifest(
        routes=(home, *editorial, *models, *runs, *aliases, *subjects, *episodes),
    )


def _edition_title(title: str, edition_label: str) -> str:
    """Attach the edition to the brand, keeping titles short enough for search results."""
    brand = "Deep20Bench"
    if title.startswith((f"{brand}: ", f"{brand} ")):
        return f"{brand} {edition_label}{title.removeprefix(brand)}"
    if title.endswith(f" | {brand}"):
        return f"{title} {edition_label}"
    raise ValueError(f"edition page title must name {brand}: {title}")


def _edition_route_manifest(
    config: PublicationConfig,
    datasets: tuple[PublishedDataset, ...],
    model_pages: tuple[EditionModelPages, ...] = (),
) -> StaticRouteManifest:
    entries: list[StaticRouteEntry] = []
    bundles = tuple(split_publication(dataset) for dataset in datasets)
    pages_by_edition = {pages.edition_id: pages for pages in model_pages}
    # The shared About page carries project news, which follows the newest published run.
    about_modified = max(_content_modified(bundle) for bundle in bundles)
    for dataset, bundle in zip(datasets, bundles, strict=True):
        cohort = dataset.active_cohort
        prefix = f"editions/{cohort.edition_id}"
        pages = pages_by_edition.get(cohort.edition_id)
        for entry in _static_route_manifest(bundle, pages).routes:
            if entry.route in {"about", "story"}:
                entry = entry.model_copy(update={"last_modified": about_modified})
                if cohort.edition_id == config.default_edition_id:
                    entries.append(entry.model_copy(update={"edition_id": cohort.edition_id}))
                if entry.route == "about":
                    entries.append(entry.model_copy(update={
                        "route": f"{prefix}/about",
                        "canonical_route": "about",
                        "sitemap_included": False,
                        "edition_id": cohort.edition_id,
                    }))
                continue
            scoped = entry.kind not in {"run", "subject", "episode"}
            route = (prefix + (f"/{entry.route}" if entry.route else "")) if scoped else entry.route
            canonical = route
            updated = entry.model_copy(update={
                "route": route,
                "canonical_route": canonical,
                "edition_id": cohort.edition_id,
                "browser_title": _edition_title(entry.browser_title, cohort.edition_label),
                "description": f"{entry.description} Edition {cohort.edition_label}.",
            })
            entries.append(updated)
            if scoped and cohort.edition_id == config.default_edition_id:
                entries.append(updated.model_copy(update={
                    "route": entry.route, "sitemap_included": False,
                }))
        if pages is not None:
            entries.extend(_model_aliases(entries, pages, prefix,
                                          cohort.edition_id == config.default_edition_id))
    return StaticRouteManifest(routes=tuple(entries))


def _model_aliases(
    entries: list[StaticRouteEntry],
    pages: EditionModelPages,
    prefix: str,
    default_edition: bool,
) -> tuple[StaticRouteEntry, ...]:
    """Keep retired model slugs and replaced run URLs pointing at the stable model page."""
    model_entries = {
        entry.route: entry for entry in entries
        if entry.kind == "model" and entry.route.startswith(f"{prefix}/models/")
    }
    aliases: list[StaticRouteEntry] = []

    def alias(route: str, slug: str) -> StaticRouteEntry:
        return model_entries[f"{prefix}/models/{slug}"].model_copy(
            update={"route": route, "kind": "alias", "sitemap_included": False},
        )

    for previous, slug in sorted(pages.slug_aliases.items()):
        aliases.append(alias(f"{prefix}/models/{previous}", slug))
        if default_edition:
            aliases.append(alias(f"models/{previous}", slug))
    for document in pages.models:
        for run in document.superseded_runs:
            aliases.append(alias(f"runs/{run.execution_id}", document.slug))
    return tuple(aliases)


def _build_site(
    site_root: Path,
    public_root: Path,
    output_root: Path,
    route_manifest_path: Path,
    server_output_root: Path,
    base_path: str,
    canonical_url: str,
) -> None:
    environment = dict(os.environ)
    environment["DEEP20_OUTPUT_DIR"] = str(output_root)
    environment["DEEP20_PUBLIC_DIR"] = str(public_root)
    environment["DEEP20_ROUTE_MANIFEST"] = str(route_manifest_path)
    environment["DEEP20_SSR_OUTPUT_DIR"] = str(server_output_root)
    environment["DEEP20_BASE_PATH"] = base_path
    environment["DEEP20_CANONICAL_URL"] = canonical_url
    subprocess.run(
        ["npm", "run", "build"],
        cwd=site_root,
        env=environment,
        check=True,
    )


def read_publication_config(path: Path) -> PublicationConfig:
    """Compose site settings with the same released profiles used before execution."""
    from .models import PublicationSettings, ReleasedEditionProfile

    value = _read_yaml(path)
    if value.get("version") != 3:
        return parse_publication_config(value, str(path))
    settings = PublicationSettings.model_validate(value)
    registry = EditionRegistry.model_validate(_read_yaml(path.parent / "editions.yaml"))
    profiles = []
    for edition in registry.editions:
        if edition.status == "draft":
            continue
        if edition.profile_path is None:
            raise ValueError("released edition has no shared profile")
        profile = ReleasedEditionProfile.model_validate(_read_yaml(path.parent / edition.profile_path))
        release = profile.cohort.eligibility
        if (profile.oracle_configuration is not None and isinstance(release, QualifiedEligibility)
            and (sha256_text(canonical_json(profile.oracle_configuration.model_dump(mode="json")))
                != release.oracle_configuration_hash
                or profile.validator_configuration is None
                or sha256_text(canonical_json(profile.validator_configuration.model_dump(mode="json")))
                != release.validator_configuration_hash)):
            raise ValueError("edition configurations differ from their release pins")
        profiles.append(profile)
    if not profiles or any(p.score != profiles[0].score for p in profiles):
        raise ValueError("released editions must declare the same score policy")
    profiles.sort(key=lambda profile: profile.cohort.edition_id != registry.default_edition_id)
    config = PublicationConfig(site=settings.site, score=profiles[0].score,
                               model_slugs=settings.model_slugs,
                               default_edition_id=registry.default_edition_id,
                               cohorts=tuple(p.cohort for p in profiles))
    registry.validate_publication(config)
    return config


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
        config = read_publication_config(publication_path)
        registry_path = root / "config" / "editions.yaml"
        if registry_path.exists():
            EditionRegistry.model_validate(_read_yaml(registry_path)).validate_publication(config)
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
        datasets = tuple(
            compile_publication(
                runs=runs, config=config, cohort=cohort, subject_catalog=subjects,
                subject_catalog_hash=subject_hash, built_at=built_at,
            ) for cohort in config.cohorts
        )
        dataset = next(item for item in datasets
                       if item.active_cohort.edition_id == config.default_edition_id)
        model_pages = build_model_pages(
            tuple(split_publication(item) for item in datasets),
            config.model_slugs,
            {cohort.edition_id: superseded_qualified_runs(runs, cohort) for cohort in config.cohorts},
        )
        editions = edition_index(config, datasets, model_pages)
        selected_ids = {run.execution_id for item in datasets for run in item.official_runs}
        for run in runs:
            if run.summary.execution_id not in selected_ids:
                continue
            for episode in run.episodes:
                expected = {turn.turn_number for turn in episode.result.turns
                            if not isinstance(turn, EpisodeActionTurn)}
                actual = {record.turn_number for record in episode.violation_disclosures}
                if actual != expected:
                    raise PublicationInputError(
                        "selected runs require capture-guesser-outputs before publication"
                    )
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
            _write_public_data(
                public_root, dataset, app_build,
                datasets=datasets, editions=editions, model_pages=model_pages,
            )
            candidate = staging_root / "docs"
            route_manifest_path = public_root / "data" / "routes.json"
            route_manifest_path.write_text(
                _edition_route_manifest(config, datasets, model_pages).model_dump_json(indent=2)
                + "\n",
                encoding="utf-8",
            )
            _build_site(
                site_root,
                public_root,
                candidate,
                route_manifest_path,
                staging_root / "ssr",
                config.site.base_path,
                str(config.site.canonical_url),
            )
            if check:
                if not _directories_equal(candidate, root / "docs"):
                    raise PublicationInputError("committed docs output is stale")
            else:
                output = root / "docs"
                backup = staging_root / "previous-docs"
                if output.exists():
                    shutil.move(output, backup)
                try:
                    shutil.copytree(candidate, output)
                except BaseException:
                    if output.exists():
                        shutil.rmtree(output)
                    if backup.exists():
                        shutil.move(backup, output)
                    raise
        typer.echo(
            f"{_timestamp()} INFO publication.result runs={len(runs)} "
            f"official={sum(item.provenance.official_run_count for item in datasets)} "
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
