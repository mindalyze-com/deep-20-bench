from __future__ import annotations

import re

from .models import OracleQuestionType, OracleResearchQuestionClass

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

_TEMPORAL_STATUS_PATTERN = re.compile(
    r"\b(?:currently\s+alive|alive\s+today|still\s+alive|living\s+today|"
    r"alive|living|dead|deceased)\b",
    flags=re.IGNORECASE,
)
_PRIMARY_RECOGNITION_PATTERN = re.compile(
    r"\b(?:primarily|principally|mainly|chiefly|best)\s+(?:known|recognized)\b|"
    r"\bprimary\s+(?:role|occupation|profession)\b",
    flags=re.IGNORECASE,
)
_OPEN_WORLD_EVER_PATTERN = re.compile(
    r"\b(?:ever|at\s+any\s+time|at\s+some\s+point)\b|"
    r"\b(?:has|had|did)\b.{0,80}\b(?:appeared|visited|worked|served|held|joined)\b",
    flags=re.IGNORECASE,
)
_ABSENCE_EXCLUSIVITY_PATTERN = re.compile(
    r"\b(?:never|only|sole|solely|exclusively|none|no\s+other|exactly\s+one)\b",
    flags=re.IGNORECASE,
)
_ROLE_OR_OCCUPATION_PATTERN = re.compile(
    r"\b(?:actor|actress|author|writer|artist|musician|singer|composer|director|"
    r"producer|scientist|physicist|chemist|mathematician|physician|doctor|"
    r"engineer|inventor|politician|leader|lawyer|teacher|professor|journalist|"
    r"occupation|profession|professionally)\b",
    flags=re.IGNORECASE,
)
_CLOSED_FACT_PATTERN = re.compile(
    r"\b(?:born|birthplace|died|death|founded|established|published|authored|"
    r"wrote|written|created|invented|capital|located)\b",
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


def classify_oracle_research_question(question: str) -> OracleResearchQuestionClass:
    """Select a deterministic evidence-acquisition strategy from question wording."""

    if _TEMPORAL_STATUS_PATTERN.search(question) is not None:
        return OracleResearchQuestionClass.TEMPORAL_STATUS
    if _PRIMARY_RECOGNITION_PATTERN.search(question) is not None:
        return OracleResearchQuestionClass.PRIMARY_RECOGNITION
    if _OPEN_WORLD_EVER_PATTERN.search(question) is not None:
        return OracleResearchQuestionClass.OPEN_WORLD_EVER
    if _ABSENCE_EXCLUSIVITY_PATTERN.search(question) is not None:
        return OracleResearchQuestionClass.ABSENCE_OR_EXCLUSIVITY
    if _ROLE_OR_OCCUPATION_PATTERN.search(question) is not None:
        return OracleResearchQuestionClass.ROLE_OR_OCCUPATION
    if (
        _COMPARISON_PATTERN.search(question) is not None
        and _TEMPORAL_PATTERN.search(question) is not None
    ):
        return OracleResearchQuestionClass.CLOSED_FACT
    if _COMPARISON_PATTERN.search(question) is not None or (
        _QUANTITATIVE_PATTERN.search(question) is not None
        and re.search(r"\b(?:how\s+many|number|total|exactly)\b", question, re.IGNORECASE)
        is not None
    ):
        return OracleResearchQuestionClass.COUNT_OR_COMPARISON
    if _CLOSED_FACT_PATTERN.search(question) is not None:
        return OracleResearchQuestionClass.CLOSED_FACT
    return OracleResearchQuestionClass.OTHER
