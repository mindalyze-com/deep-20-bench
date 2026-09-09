"""Atomic, private file ownership shared by Oracle review composition roots."""

from __future__ import annotations

import fcntl
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from deep20_oracle.artifacts import RunArtifactPolicy
from deep20_oracle.util import sha256_text

from .oracle_replay import ReplayInputError


class PrivateReviewFiles:
    def __init__(self, directory: Path, artifact_policy: RunArtifactPolicy):
        self.directory = directory
        self.artifact_policy = artifact_policy

    @contextmanager
    def locked(self) -> Iterator[None]:
        lock_path = Path(tempfile.gettempdir()) / (
            f"deep20-replay-{sha256_text(str(self.directory.resolve()))}.lock"
        )
        with lock_path.open("a", encoding="utf-8") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ReplayInputError("review is already running") from error
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def _write(self, name: str, content: str) -> None:
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{name}.", dir=self.directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.directory / name)
            directory_fd = os.open(self.directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
