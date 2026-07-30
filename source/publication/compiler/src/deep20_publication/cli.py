from __future__ import annotations

import filecmp
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
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
    parse_publication_config,
    parse_run,
    parse_subject_catalog,
)
from .models import (
    CompletedTrialSummary,
    LoadedEpisode,
    LoadedRun,
    PublicationDataBundle,
    PublishedDataset,
)
from .serialize import dataset_json, leaderboard_csv, publication_document_json
from .split import split_publication

app = typer.Typer(help="Compile and render the independent Deep20Bench publication site.")


@app.callback()
def publication() -> None:
    """Prepare public Deep20Bench data and the static GitHub Pages site."""


def _repository_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (
            (candidate / ".git").exists()
            and (candidate / "source" / "publication" / "compiler").is_dir()
        ):
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


def _load_run(summary_path: Path, repository: Path) -> LoadedRun:
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
    episodes = _load_episode_details(loaded, repository)
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
            episodes.append(
                parse_completed_episode(
                    value=parse_yaml_object(source_text, str(source)),
                    label=str(source),
                    relative_path=relative,
                    actual_file_integrity_hash=sha256_text(source_text),
                    expected_integrity_hash=reference.integrity_hash,
                )
            )
    return tuple(episodes)


def _discover_runs(repository: Path) -> tuple[LoadedRun, ...]:
    candidates = sorted(
        (repository / "runs").glob("M-[0-9][0-9][0-9][0-9]/BX-*/summary.yml")
    )
    return tuple(_load_run(path, repository) for path in candidates)


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
    return all(
        _directories_equal(left / name, right / name)
        for name in comparison.common_dirs
    )


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


def _write_public_data(public_directory: Path, dataset: PublishedDataset) -> None:
    public_directory.mkdir(parents=True, exist_ok=True)
    data_directory = public_directory / "data"
    bundle = split_publication(dataset)
    staged_directory = Path(
        tempfile.mkdtemp(prefix=".deep20-data-", dir=public_directory)
    )
    backup_directory = public_directory / ".deep20-data-previous"
    try:
        (staged_directory / "deep20bench-v5.json").write_text(
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
        (staged_directory / "leaderboard.json").write_text(
            publication_document_json(bundle.leaderboard),
            encoding="utf-8",
        )
        for run_document in bundle.runs:
            path = (
                staged_directory
                / "runs"
                / f"{run_document.run.execution_id}.json"
            )
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
    editorial = (
        "results",
        "results/cost",
        "results/time",
        "results/efficiency",
        "methodology",
        "story",
        "data",
    )
    runs = tuple(f"runs/{document.run.execution_id}" for document in bundle.runs)
    subjects = tuple(
        f"runs/{document.execution_id}/subjects/{document.target_id}"
        for document in bundle.subjects
    )
    episodes = tuple(
        (
            f"runs/{document.execution_id}/subjects/{document.target_id}"
            f"/episodes/{document.trial_id}"
        )
        for document in bundle.episodes
    )
    return (*editorial, *runs, *subjects, *episodes)


def _write_route_shells(output_root: Path, bundle: PublicationDataBundle) -> None:
    entry = output_root / "index.html"
    entry_html = entry.read_text(encoding="utf-8")
    for route in _route_shells(bundle):
        shell = output_root / route / "index.html"
        shell.parent.mkdir(parents=True, exist_ok=True)
        shell.write_text(entry_html, encoding="utf-8")
    (output_root / "404.html").write_text(entry_html, encoding="utf-8")


def _build_site(
    site_root: Path,
    public_root: Path,
    output_root: Path,
    base_path: str,
    bundle: PublicationDataBundle,
) -> None:
    environment = dict(os.environ)
    environment["DEEP20_OUTPUT_DIR"] = str(output_root)
    environment["DEEP20_PUBLIC_DIR"] = str(public_root)
    environment["DEEP20_BASE_PATH"] = base_path
    subprocess.run(
        ["npm", "run", "build"],
        cwd=site_root,
        env=environment,
        check=True,
    )
    _write_route_shells(output_root, bundle)


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
        runs = _discover_runs(root)
        dataset = compile_publication(
            runs=runs,
            config=config,
            subject_catalog=subjects,
            subject_catalog_hash=subject_hash,
        )
        bundle = split_publication(dataset)
        _ensure_site_dependencies(site_root)
        with tempfile.TemporaryDirectory(prefix="deep20-publication-") as temporary:
            staging_root = Path(temporary)
            public_root = staging_root / "public"
            shutil.copytree(
                site_root / "public",
                public_root,
                ignore=shutil.ignore_patterns("data"),
            )
            _write_public_data(public_root, dataset)
            candidate = staging_root / "docs"
            _build_site(
                site_root,
                public_root,
                candidate,
                config.site.base_path,
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


if __name__ == "__main__":
    app()
