"""Canonical research outcome vocabulary shared by schemas and prompt instructions."""

from enum import StrEnum


class OracleResearchOutcome(StrEnum):
    ANSWERED = "answered"
    NO_RESULTS = "no_results"
    IRRELEVANT_RESULTS = "irrelevant_results"
    INSUFFICIENT_COVERAGE = "insufficient_coverage"
    CONFLICTING_SOURCES = "conflicting_sources"
    AMBIGUOUS_QUESTION = "ambiguous_question"
    OPEN_WORLD_NOT_PROVABLE = "open_world_not_provable"
