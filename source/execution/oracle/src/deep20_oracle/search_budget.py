"""Requested research queries and the additional API search allowance."""

DEFAULT_RESEARCH_QUERY_TARGET = 3
SEARCH_CALL_BONUS = 2
MAX_SERVER_TOOL_CALLS = 30
STANDARD_MAX_RESEARCH_QUERIES = 8


def research_search_limit(requested_queries: int) -> int:
    return requested_queries + SEARCH_CALL_BONUS
