"""One request-scoped tool loop; only its final content crosses the research role port."""

from collections.abc import Callable
from datetime import UTC, datetime
from time import monotonic

from pydantic import ValidationError

from .models import (
    BackendCapabilities,
    BackendError,
    BackendUsage,
    Message,
    MessageRole,
    ModelRequest,
    ModelResponse,
    Role,
)
from .ports import ModelBackend
from .research import ExtractInput, ResearchPolicy, ResearchTools, SearchInput, tool_definitions


def _sum_known(values: tuple[int | None, ...]) -> int | None:
    return sum(v for v in values if v is not None) if all(v is not None for v in values) else None


class ResearchBackend:
    def __init__(self, backend: ModelBackend, policy: ResearchPolicy,
                 tools: Callable[[ModelRequest], ResearchTools]):
        self.backend = backend
        self.policy = policy
        self.tools = tools

    @property
    def capabilities(self) -> BackendCapabilities:
        return self.backend.capabilities

    def complete(self, request: ModelRequest) -> ModelResponse:
        if request.role is not Role.ORACLE or request.max_search_requests is None:
            raise BackendError("research_role_required", "research is restricted to an Oracle request")
        tools = self.tools(request)
        started = monotonic()
        messages = request.messages
        responses: list[ModelResponse] = []
        try:
            for round_number in range(self.policy.max_model_rounds):
                if monotonic() - started >= self.policy.deadline_seconds:
                    raise BackendError("research_deadline", "research deadline elapsed")
                final_round = round_number == self.policy.max_model_rounds - 1
                current = ModelRequest.model_validate({**request.model_dump(), "messages": messages,
                    "tools": () if final_round else tool_definitions()})
                result = self.backend.complete(current)
                responses.append(result)
                if monotonic() - started >= self.policy.deadline_seconds:
                    raise BackendError("research_deadline", "research deadline elapsed")
                if not result.tool_calls:
                    if not final_round:
                        # A separate schema-constrained pass validates the final wire
                        # shape. The Oracle service still performs semantic validation.
                        messages += (Message(role=MessageRole.ASSISTANT, content=result.content),
                                     Message(role=MessageRole.USER, content="Return the final answer using the required JSON schema."))
                        final = self.backend.complete(ModelRequest.model_validate({
                            **request.model_dump(), "messages": messages, "tools": (),
                        }))
                        responses.append(final)
                    else:
                        final = result
                    if final.tool_calls or monotonic() - started >= self.policy.deadline_seconds:
                        raise BackendError("research_incomplete", "research did not produce a final response within its limit")
                    usage = tools.usage()
                    observations = tuple(r.observation for r in responses)
                    merged = BackendUsage(
                        input_tokens=_sum_known(tuple(o.usage.input_tokens for o in observations)),
                        output_tokens=_sum_known(tuple(o.usage.output_tokens for o in observations)),
                        cached_input_tokens=_sum_known(tuple(o.usage.cached_input_tokens for o in observations)),
                        reasoning_tokens=_sum_known(tuple(o.usage.reasoning_tokens for o in observations)),
                        search_requests=usage.search_requests, extract_requests=usage.extract_requests,
                        cost_usd=None,
                    )
                    return final.model_copy(update={
                        "requested_at": responses[0].requested_at, "completed_at": datetime.now(UTC).isoformat(),
                        "latency_ms": max(0, round((monotonic() - started) * 1000)),
                        "observation": final.observation.model_copy(update={"usage": merged,
                            "inference_requests": sum(o.inference_requests for o in observations),
                            "research_workflow": self.policy.workflow}),
                        "native_record": {"inference_rounds": [r.model_dump(mode="json") for r in responses]},
                    })
                if final_round:
                    raise BackendError("research_round_limit", "research exceeded its model round limit")
                messages += (Message(role=MessageRole.ASSISTANT, content=result.content, tool_calls=result.tool_calls),)
                for call in result.tool_calls:
                    try:
                        if call.name == "search":
                            output = tools.search(SearchInput.model_validate(call.arguments))
                        elif call.name == "fetch":
                            output = tools.extract(ExtractInput.model_validate(call.arguments))
                        else:
                            raise BackendError("research_tool_unknown", "Oracle requested an unsupported research tool")
                    except ValidationError:
                        raise BackendError("research_tool_invalid", "Oracle supplied invalid research arguments") from None
                    messages += (Message(role=MessageRole.TOOL, tool_name=call.name, content=output.model_dump_json()),)
            raise BackendError("research_round_limit", "research exceeded its model round limit")
        finally:
            tools.close()

    def close(self) -> None:
        self.backend.close()
