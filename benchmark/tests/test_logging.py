from __future__ import annotations

import io
import logging
import re

from deep20_benchmark.logging import (
    BLANK_LINE_BEFORE_ATTRIBUTE,
    LocalMillisecondFormatter,
)


def test_trial_context_formatter_inserts_a_genuinely_empty_separator() -> None:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(
        LocalMillisecondFormatter("%(asctime)s %(levelname)s %(message)s")
    )
    test_logger = logging.getLogger("deep20.benchmark.formatter-test")
    test_logger.handlers.clear()
    test_logger.propagate = False
    test_logger.setLevel(logging.INFO)
    test_logger.addHandler(handler)

    test_logger.info("benchmark.run execution=BX-test")
    test_logger.info(
        'benchmark.trial_context trial=trial-002 target=T-0004 name="Garfield"',
        extra={BLANK_LINE_BEFORE_ATTRIBUTE: True},
    )

    lines = stream.getvalue().splitlines()
    assert len(lines) == 3
    assert lines[1] == ""
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} INFO "
        r"benchmark\.run execution=BX-test",
        lines[0],
    )
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} INFO "
        r'benchmark\.trial_context trial=trial-002 target=T-0004 name="Garfield"',
        lines[2],
    )
    assert all(
        re.match(r"\d{4}-\d{2}-\d{2} ", line) is not None
        for line in lines
        if line
    )
