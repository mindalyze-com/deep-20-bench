from __future__ import annotations

import logging

from deep20_oracle import console


def test_console_logging_configures_one_global_pattern(monkeypatch) -> None:
    configured = {}
    monkeypatch.setattr(
        console.logging,
        "basicConfig",
        lambda **kwargs: configured.update(kwargs),
    )

    console.configure_console_logging()

    assert configured == {
        "level": logging.INFO,
        "format": "%(asctime)s.%(msecs)03d %(levelname)s %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S",
    }
