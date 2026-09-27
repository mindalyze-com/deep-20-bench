import json
import sqlite3
from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pytest
from deep20_backends.models import (
    BackendCapabilities,
    BackendError,
    BackendKind,
    BackendObservation,
    BackendUsage,
    Message,
    MessageRole,
    ModelRequest,
    ModelResponse,
    Role,
    ToolCall,
)
from deep20_backends.parallel import ParallelResearchTools
from deep20_backends.research import ExtractInput, ResearchPolicy, ResearchScope, SearchInput
from deep20_backends.research_backend import ResearchBackend
from deep20_benchmark.models import BenchmarkExecutionId, BenchmarkModelId, SubjectId, TrialId
from deep20_benchmark.parallel_credentials import load_parallel_api_key
from deep20_benchmark.research_journal import SqliteResearchJournal
from deep20_benchmark.spending import SqliteSpendingLedger
from deep20_benchmark.work_models import WorkIdentity, WorkSubmission
from deep20_benchmark.work_queue import MemoryWorkQueue


def inference(role=Role.ORACLE):
    return ModelRequest(role=role, messages=(Message(role=MessageRole.USER, content="current question"),),
                        output_schema={"type": "object"}, schema_name="oracle",
                        max_search_requests=2 if role is Role.ORACLE else None)


def setup_tools(handler, *, policy=None):
    connection = sqlite3.connect(":memory:")
    journal = SqliteResearchJournal(connection)
    ledger = SqliteSpendingLedger(sqlite3.connect(":memory:"), Decimal("0.1"))
    scope = ResearchScope(scope_id="RR-" + "a" * 32, search_limit=2, policy=policy or ResearchPolicy())
    tools = ParallelResearchTools("fake-secret", scope, ledger, journal,
                                   client=httpx.Client(transport=httpx.MockTransport(handler)))
    return tools, ledger, journal


def test_parallel_native_payloads_are_bounded_and_do_not_reuse_sessions():
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"results": [{"url": "https://example.com/", "title": "Evidence",
            "excerpts": ["An example excerpt."]}], "session_id": "must-not-be-reused", "errors": []})
    tools, ledger, _ = setup_tools(handler)
    search = tools.search(SearchInput(objective="Current factual question", search_queries=("example query",)))
    tools.extract(ExtractInput(url=search.sources[0].url, objective="Current factual question"))
    assert [request.url.path for request in requests] == ["/v1/search", "/v1/extract"]
    assert all(request.headers["x-api-key"] == "fake-secret" for request in requests)
    assert all("session_id" not in json.loads(request.content) for request in requests)
    assert json.loads(requests[1].content)["urls"] == ["https://example.com/"]
    assert tools.usage().search_requests == tools.usage().extract_requests == 1
    assert tools.usage().cost_usd is None
    assert ledger.snapshot().reserved_usd == Decimal("0.015")
    assert ledger.snapshot().reported_usd == 0


def test_failed_paid_research_keeps_reservation_and_cannot_be_silently_ignored():
    tools, ledger, journal = setup_tools(lambda request: httpx.Response(502, text="fake-secret and private body"))
    with pytest.raises(BackendError) as failure:
        tools.search(SearchInput(objective="question", search_queries=("query",)))
    assert "fake-secret" not in str(failure.value)
    assert ledger.snapshot().reserved_usd == Decimal("0.01")
    with pytest.raises(BackendError, match="failed or unresolved"):
        journal.usage(tools.scope.scope_id)


def test_research_limits_apply_before_a_third_http_call():
    seen = []
    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"results": []})
    tools, _, _ = setup_tools(handler)
    for _ in range(2):
        tools.search(SearchInput(objective="question", search_queries=("query",)))
    with pytest.raises(BackendError, match="allowance"):
        tools.search(SearchInput(objective="question", search_queries=("query",)))
    assert len(seen) == 2


def test_operator_cannot_submit_during_research_or_use_another_role():
    queue = MemoryWorkQueue()
    identity = WorkIdentity(execution_id=BenchmarkExecutionId("BX-research"), model_id=BenchmarkModelId("M-0001"),
                            target_id=SubjectId("T-0001"), trial_id=TrialId("trial-001"), attempt_number=1,
                            role=Role.ORACLE)
    work = queue.enqueue(identity, "operator", inference())
    claim = queue.claim(work.request_id, operator="operator", role=Role.ORACLE)
    journal = SqliteResearchJournal(queue.connection, claim=claim)
    scope = ResearchScope(scope_id=work.request_id, search_limit=2, policy=ResearchPolicy())
    ticket = journal.begin(scope, "search")
    submission = WorkSubmission(request_id=work.request_id, request_hash=work.request_hash,
                                claim_id=claim.claim_id, content="  raw response\n")
    with pytest.raises(BackendError, match="complete research"):
        queue.submit(submission)
    journal.finish(ticket, succeeded=True)
    queue.submit(submission)
    assert queue.reply(work).content == "  raw response\n"
    with pytest.raises(BackendError, match="stale"):
        journal.begin(scope, "search")


def test_research_deadline_survives_journal_recreation():
    connection = sqlite3.connect(":memory:")
    now = [10.0]
    journal = SqliteResearchJournal(connection, clock=lambda: now[0])
    scope = ResearchScope(scope_id="RR-" + "d" * 32, search_limit=2,
                          policy=ResearchPolicy(deadline_seconds=10))
    ticket = journal.begin(scope, "search")
    journal.finish(ticket, succeeded=True)
    now[0] = 21.0
    journal = SqliteResearchJournal(connection, clock=lambda: now[0])
    with pytest.raises(BackendError, match="deadline"):
        journal.begin(scope, "search")


def test_local_research_uses_a_fresh_bounded_loop_and_final_schema():
    class Local:
        capabilities = BackendCapabilities(tool_calls=True)
        def __init__(self):
            self.requests = []
        def complete(self, request):
            self.requests.append(request)
            now = datetime.now(UTC).isoformat()
            first = len(self.requests) == 1
            return ModelResponse(content="" if first else '{"answer":"UNKNOWN"}',
                tool_calls=(ToolCall(name="search", arguments={"objective": "question", "search_queries": ["query"]}),) if first else (),
                finish_reason="stop", requested_at=now, completed_at=now, latency_ms=1,
                observation=BackendObservation(kind=BackendKind.OLLAMA, model="local", inference_requests=1,
                    usage=BackendUsage(input_tokens=20, output_tokens=5)))
        def close(self):
            pass
    local = Local()
    tools, _, _ = setup_tools(lambda request: httpx.Response(200, json={"results": []}))
    driver = ResearchBackend(local, ResearchPolicy(), lambda _: tools)
    response = driver.complete(inference())
    assert len(local.requests) == 3
    assert local.requests[0].tools
    assert not local.requests[-1].tools
    assert any(message.role is MessageRole.TOOL for message in local.requests[-1].messages)
    assert response.observation.inference_requests == 3
    assert response.observation.usage.search_requests == 1
    assert response.observation.usage.input_tokens == 60
    assert response.observation.usage.cost_usd is None
    assert response.observation.research_workflow == "parallel-tools-v1"
    with pytest.raises(BackendError, match="restricted"):
        driver.complete(inference(Role.REVIEWER))


def test_parallel_credentials_are_separate_and_environment_has_priority(tmp_path):
    private = tmp_path / "private"
    private.mkdir()
    (private / "parallel.yml").write_text("api:\n  api_key: separate-file-key\n")
    assert load_parallel_api_key(tmp_path, environ={}) == "separate-file-key"
    assert load_parallel_api_key(tmp_path, environ={"PARALLEL_API_KEY": "env-key", "OPENROUTER_API_KEY": "wrong"}) == "env-key"
