from __future__ import annotations

import re

from .models import OracleQuestionType

_COMPARISON_PATTERN = re.compile(
    r"\b(?:"
    r"before|after|earlier|later|older|younger|"
    r"more|less|fewer|greater|smaller|larger|"
    r"at\s+least|at\s+most|no\s+earlier|no\s+later|"
    r"over|under|above|below|between"
    r")\b",
    flags=re.IGNORECASE,
)
_TEMPORAL_PATTERN = re.compile(
    r"\b(?:"
    r"year|date|century|decade|era|period|"
    r"born|birth|died|death|founded|established|published"
    r")\b|\b(?:1[0-9]{3}|20[0-9]{2}|2100)\b",
    flags=re.IGNORECASE,
)
_QUANTITATIVE_PATTERN = re.compile(
    r"\b[0-9]+(?:\.[0-9]+)?\b|\b(?:"
    r"amount|count|distance|height|length|population|price|quantity|"
    r"score|size|weight"
    r")\b",
    flags=re.IGNORECASE,
)
_NEGATION_PATTERN = re.compile(
    r"\b(?:not|never|neither|nor|without|except)\b|n['’]t\b",
    flags=re.IGNORECASE,
)


def classify_oracle_question(question: str) -> OracleQuestionType:
    """Classify question shapes that are especially prone to polarity mistakes."""

    comparison = _COMPARISON_PATTERN.search(question) is not None
    if comparison and _TEMPORAL_PATTERN.search(question) is not None:
        return OracleQuestionType.TEMPORAL_COMPARISON
    if comparison and _QUANTITATIVE_PATTERN.search(question) is not None:
        return OracleQuestionType.QUANTITATIVE_COMPARISON
    if _NEGATION_PATTERN.search(question) is not None:
        return OracleQuestionType.NEGATION
    return OracleQuestionType.OTHER
