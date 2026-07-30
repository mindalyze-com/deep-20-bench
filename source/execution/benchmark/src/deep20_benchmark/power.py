from __future__ import annotations

import logging
import os
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger("deep20.benchmark")

_CAFFEINATE_PATH = Path("/usr/bin/caffeinate")
_CAFFEINATE_ENV = "DEEP20BENCH_CAFFEINATE"


@contextmanager
def prevent_idle_system_sleep() -> Iterator[None]:
    """Prevent macOS idle sleep while the guarded benchmark operation runs."""

    process: subprocess.Popen[bytes] | None = None
    if sys.platform == "darwin" and os.environ.get(_CAFFEINATE_ENV, "1") != "0":
        if not _CAFFEINATE_PATH.is_file():
            logger.warning(
                "benchmark.power_assertion status=unavailable "
                "error_code=caffeinate_not_found"
            )
        else:
            try:
                process = subprocess.Popen(
                    (
                        str(_CAFFEINATE_PATH),
                        "-i",
                        "-w",
                        str(os.getpid()),
                    ),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except OSError as error:
                logger.warning(
                    "benchmark.power_assertion status=unavailable "
                    "error_code=caffeinate_start_failed error_type=%s",
                    type(error).__name__,
                )
            else:
                logger.info(
                    "benchmark.power_assertion status=enabled "
                    "idle_sleep=prevented display_sleep=allowed"
                )

    try:
        yield
    finally:
        try:
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        except OSError as error:
            logger.debug(
                "benchmark.power_assertion status=cleanup_failed "
                "error_code=caffeinate_stop_failed error_type=%s",
                type(error).__name__,
            )
