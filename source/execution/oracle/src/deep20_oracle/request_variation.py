"""Content variation for independent Oracle and Reviewer generations."""

import copy
import secrets
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .models import JsonObject
from .provider import ProviderRequest
from .search_budget import MAX_SERVER_TOOL_CALLS
from .util import canonical_json

QUESTION_ID_VERSION = "question-id-v1"


class QuestionMetadata(BaseModel):
    """Random metadata with no subject, role, execution, or retry information."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    instruction: Literal["Ignore question_id when answering; it is metadata only."] = (
        "Ignore question_id when answering; it is metadata only."
    )
    question_id: str = Field(pattern=r"^[0-9a-f]{8}$")

    def message(self) -> dict[str, str]:
        return {"role": "user", "content": canonical_json(self.model_dump(mode="json"))}


def with_fresh_question_id(request: ProviderRequest) -> ProviderRequest:
    """Append metadata initially, or replace only that metadata on a format retry."""

    messages = request.messages
    previous: QuestionMetadata | None = None
    if messages:
        try:
            previous = QuestionMetadata.model_validate_json(messages[-1]["content"])
        except ValidationError:
            pass
        if previous is not None and messages[-1] == previous.message():
            messages = messages[:-1]
        else:
            previous = None
    question_id = secrets.token_hex(4)
    while previous is not None and question_id == previous.question_id:
        question_id = secrets.token_hex(4)
    metadata = QuestionMetadata(question_id=question_id)
    return request.model_copy(update={"messages": (*messages, metadata.message())})


def requests_differ_only_in_question_id(prior: JsonObject, current: JsonObject) -> bool:
    """Allow only the canonical metadata tail to differ in recorded provider payloads."""

    def normalized(request: JsonObject) -> JsonObject | None:
        messages = request.get("messages")
        if not isinstance(messages, list) or not messages:
            return None
        tail = messages[-1]
        if not isinstance(tail, dict) or not isinstance(tail.get("content"), str):
            return None
        content = tail["content"]
        assert isinstance(content, str)
        try:
            metadata = QuestionMetadata.model_validate_json(content)
        except ValidationError:
            return None
        if tail != metadata.message():
            return None
        return {**request, "messages": messages[:-1]}

    before = normalized(prior)
    after = normalized(current)
    return before is not None and after is not None and before == after


def requests_match_bounded_research_retry(
    prior: JsonObject, current: JsonObject, *, searches_used: int,
) -> bool:
    """Permit exactly the consumed search allowance and optional question-ID change."""
    previous_limit = prior.get("max_tool_calls")
    if (type(previous_limit) is not int or not 1 <= previous_limit <= MAX_SERVER_TOOL_CALLS
            or type(searches_used) is not int or searches_used < 1):
        return False
    remaining = previous_limit - searches_used
    if remaining < 1 or type(current.get("max_tool_calls")) is not int:
        return False
    if current["max_tool_calls"] != remaining:
        return False

    def restored(request: JsonObject, expected: int) -> JsonObject | None:
        value = copy.deepcopy(request)
        tool_list = value.get("tools")
        if not isinstance(tool_list, list) or len(tool_list) != 1:
            return None
        tool = tool_list[0]
        if not isinstance(tool, dict) or tool.get("type") != "openrouter:web_search":
            return None
        parameters = tool.get("parameters")
        if not isinstance(parameters, dict) or parameters.get("engine") != "parallel":
            return None
        if type(parameters.get("max_uses")) is not int or parameters["max_uses"] != expected:
            return None
        parameters["max_uses"] = previous_limit
        value["max_tool_calls"] = previous_limit
        return value

    before = restored(prior, previous_limit)
    after = restored(current, remaining)
    return before is not None and after is not None and (
        before == after or requests_differ_only_in_question_id(before, after)
    )
