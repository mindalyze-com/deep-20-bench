from __future__ import annotations

import logging
from datetime import datetime

BLANK_LINE_BEFORE_ATTRIBUTE = "deep20_blank_line_before"


class LocalMillisecondFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        rendered = super().format(record)
        if getattr(record, BLANK_LINE_BEFORE_ATTRIBUTE, False) is True:
            return f"\n{rendered}"
        return rendered

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        del datefmt
        value = datetime.fromtimestamp(record.created).astimezone()
        return value.strftime("%Y-%m-%d %H:%M:%S.") + f"{value.microsecond // 1_000:03d}"


def configure_benchmark_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise TypeError(f"unknown log level {level!r}")
    handler = logging.StreamHandler()
    handler.setFormatter(
        LocalMillisecondFormatter("%(asctime)s %(levelname)s %(message)s")
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(numeric_level)
    logging.getLogger("deep20.benchmark").setLevel(numeric_level)
    for name in (
        "deep20.oracle",
        "deep20.oracle.game",
        "deep20.oracle.guesser",
        "deep20.oracle.validator",
        "httpx",
        "httpcore",
    ):
        logging.getLogger(name).setLevel(logging.WARNING)
