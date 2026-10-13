"""Repository-relative references for operator-selected artifact storage."""

import os
from pathlib import Path


def repository_relative_path(repository: Path, path: Path) -> str:
    """Keep repository symlinks in references while rejecting lexical escapes."""
    return Path(os.path.abspath(path)).relative_to(repository.resolve()).as_posix()
