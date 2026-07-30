from __future__ import annotations

import logging

CONSOLE_LOG_FORMAT = "%(asctime)s.%(msecs)03d %(levelname)s %(message)s"
CONSOLE_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_console_logging() -> None:
    """Configure the CLI's root logger; library loggers inherit this format."""
    logging.basicConfig(
        level=logging.INFO,
        format=CONSOLE_LOG_FORMAT,
        datefmt=CONSOLE_DATE_FORMAT,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
