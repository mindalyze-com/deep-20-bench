import shutil
from pathlib import Path

import pytest

from deep20_publication.cli import _load_run, _repository_relative_path
from deep20_publication.integrity import PublicationInputError

REPOSITORY = Path(__file__).resolve().parents[4]


def test_external_run_link_preserves_signed_reads_and_tamper_rejection(tmp_path: Path) -> None:
    execution = "BX-20260728-official-M0001-010"
    source = REPOSITORY / "runs/M-0001" / execution
    destination = tmp_path / "storage" / execution
    shutil.copytree(source, destination)
    repository = tmp_path / "repository"
    link = repository / "runs/M-0001" / execution
    link.parent.mkdir(parents=True)
    link.symlink_to(destination, target_is_directory=True)

    loaded = _load_run(link / "summary.yml", repository)
    assert loaded.summary.execution_id == execution
    assert loaded.summary_path == f"runs/M-0001/{execution}/summary.yml"
    assert len(loaded.episodes) == 35

    reference = loaded.summary.subjects[0].trials[0].artifacts.trial_result
    trial_path = repository / reference.relative_path
    trial_path.write_text(trial_path.read_text() + "\n")
    with pytest.raises(PublicationInputError, match="summary integrity reference"):
        _load_run(link / "summary.yml", repository)


def test_publication_rejects_direct_external_paths_and_traversal(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    for path in (tmp_path / "storage/summary.yml", repository / "../storage/summary.yml"):
        with pytest.raises(ValueError):
            _repository_relative_path(path, repository)
