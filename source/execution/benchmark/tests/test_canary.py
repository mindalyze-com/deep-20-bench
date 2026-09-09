from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from deep20_benchmark.canary import (
    EchoCanaryExchange,
    EchoCanaryProviderError,
    EchoCanaryRequest,
    OpenRouterEchoCanaryProvider,
    run_startup_canaries,
)
from deep20_benchmark.catalog import (
    BenchmarkCatalogEntry,
    load_benchmark_catalog,
    load_model_catalog,
)
from deep20_benchmark.models import (
    BenchmarkId,
    BenchmarkLlmRole,
    BenchmarkModelId,
    BenchmarkModelSnapshot,
)
from deep20_oracle.config import EvidenceReviewConfig, ProviderRouting
from deep20_oracle.errors import OracleProviderError
from deep20_oracle.models import ProviderTrace, ProviderUsage
from deep20_oracle.provider import ProviderExchange, ProviderRequest


class RecordingEchoProvider:
    def __init__(
        self,
        *,
        outputs: dict[BenchmarkLlmRole, str] | None = None,
        failures: dict[BenchmarkLlmRole, str] | None = None,
    ) -> None:
        self.outputs = outputs or {}
        self.failures = failures or {}
        self.requests: list[EchoCanaryRequest] = []
        self.closed = False

    def complete(self, request: EchoCanaryRequest) -> EchoCanaryExchange:
        self.requests.append(request)
        failure = self.failures.get(request.role)
        if failure is not None:
            raise EchoCanaryProviderError(
                "synthetic provider failure",
                code=failure,
            )
        return EchoCanaryExchange(
            output=self.outputs.get(request.role, "Hi"),
            requested_model=request.model,
            resolved_model=request.model,
            requested_provider=request.provider,
            resolved_provider=(
                "Amazon Bedrock"
                if request.provider_routing is ProviderRouting.AUTOMATIC
                else (
                    "Google" if request.provider == "google-vertex" else request.provider
                )
            ),
            finish_reason="stop",
            latency_ms=12,
            usage=ProviderUsage(
                input_tokens=8,
                output_tokens=1,
                cost_usd=Decimal("0.000001"),
            ),
        )

    def close(self) -> None:
        self.closed = True


class RecordingEvidenceReviewProvider:
    def __init__(
        self,
        config: EvidenceReviewConfig,
        *,
        output: str | None = None,
        failure: str | None = None,
    ) -> None:
        self.config = config
        self.output = output or json.dumps(
            {
                "answer": "YES",
                "basis": "evidence",
                "evidence_indices": [1],
            },
            separators=(",", ":"),
        )
        self.failure = failure
        self.requests: list[ProviderRequest] = []
        self.closed = False

    def complete(self, request: ProviderRequest) -> ProviderExchange:
        self.requests.append(request)
        if self.failure is not None:
            raise OracleProviderError(
                "synthetic Judge provider failure",
                code=self.failure,
            )
        return ProviderExchange(
            raw_output=self.output,
            trace=ProviderTrace(
                requested_at="2026-08-05T12:00:00Z",
                completed_at="2026-08-05T12:00:00Z",
                latency_ms=18,
                response_id="judge-canary-response",
                finish_reason="stop",
                requested_model=self.config.model,
                resolved_model=self.config.model,
                requested_provider=self.config.provider,
                resolved_provider=(
                    "Amazon Bedrock"
                    if self.config.provider_routing is ProviderRouting.AUTOMATIC
                    else self.config.provider
                ),
                fallback_occurred=False,
                request={"canary": "judge"},
                response={"canary": "judge"},
                raw_output=self.output,
                usage=ProviderUsage(
                    input_tokens=90,
                    output_tokens=12,
                    search_count=0,
                    cost_usd=Decimal("0.00002"),
                ),
            ),
        )

    def close(self) -> None:
        self.closed = True


def _configuration() -> tuple[BenchmarkModelSnapshot, BenchmarkCatalogEntry]:
    root = Path(__file__).parents[4]
    model = load_model_catalog(root / "config" / "models.yaml").model(BenchmarkModelId("M-0004"))
    benchmark = load_benchmark_catalog(root / "config" / "benchmarks.yaml").entry(
        BenchmarkId("B-0001")
    )
    return model, benchmark


def test_echo_payload_contains_only_plain_request_and_route_controls() -> None:
    request = EchoCanaryRequest(
        role=BenchmarkLlmRole.GUESSER,
        model="google/gemini-3.6-flash",
        provider="google-vertex",
        session_id="isolated-session",
        prompt_cache_key="isolated-cache",
    )

    payload = OpenRouterEchoCanaryProvider._request_payload(request)

    assert payload == {
        "model": "google/gemini-3.6-flash",
        "messages": [{"role": "user", "content": "Reply with exactly: Hi"}],
        "max_tokens": 512,
        "provider": {
            "only": ["google-vertex"],
            "allow_fallbacks": False,
            "require_parameters": True,
        },
        "session_id": "isolated-session",
        "prompt_cache_key": "isolated-cache",
        "x_open_router_metadata": "enabled",
        "stream": False,
    }


def test_echo_payload_allows_automatic_provider_selection() -> None:
    request = EchoCanaryRequest(
        role=BenchmarkLlmRole.JUDGE,
        model="anthropic/claude-opus-5",
        provider="openrouter-auto",
        provider_routing=ProviderRouting.AUTOMATIC,
        session_id="isolated-session",
        prompt_cache_key="isolated-cache",
    )

    payload = OpenRouterEchoCanaryProvider._request_payload(request)

    assert payload["provider"] == {
        "allow_fallbacks": True,
        "require_parameters": True,
    }


def test_concise_canaries_use_selected_instructions_and_separate_cache_keys() -> None:
    from deep20_benchmark.canary import (
        _STRUCTURED_CANARY_REVIEW,
        _evidence_review_canary_request,
    )
    from deep20_oracle.config import PromptProfile
    from deep20_oracle.models import OracleRole
    from deep20_oracle.prompt import render_evidence_review_messages

    for role in (OracleRole.REVIEWER, OracleRole.JUDGE):
        baseline = _evidence_review_canary_request("test", role=role)
        revised = _evidence_review_canary_request(
            "test", role=role, profile=PromptProfile.CONCISE_V1,
        )
        assert revised.messages == render_evidence_review_messages(
            _STRUCTURED_CANARY_REVIEW, role=role, profile=PromptProfile.CONCISE_V1,
        )
        assert revised.messages[1] == baseline.messages[1]
        assert revised.messages[0] != baseline.messages[0]
        assert revised.prompt_cache_key != baseline.prompt_cache_key
        assert revised.output_schema == baseline.output_schema


@pytest.mark.parametrize("judge_uses_knowledge", (False, True))
def test_judge_policy_reaches_startup_canary_without_changing_reviewer(
    judge_uses_knowledge: bool,
) -> None:
    from deep20_benchmark.canary import _evidence_review_canary_request
    from deep20_oracle.config import AdjudicationPolicy, PromptProfile
    from deep20_oracle.models import OracleRole

    model, benchmark = _configuration()
    oracle = benchmark.oracle_configuration.model_copy(update={
        "prompt_profile": PromptProfile.QUALIFIED_V1,
        "adjudication_policy": AdjudicationPolicy.JUDGE_STABLE_KNOWLEDGE_V1,
    })
    benchmark = benchmark.model_copy(update={"oracle_configuration": oracle})
    reviewer = RecordingEvidenceReviewProvider(oracle.reviewer)
    judge = RecordingEvidenceReviewProvider(
        oracle.judge,
        output=(json.dumps({"answer": "YES", "basis": "model_knowledge", "evidence_indices": []})
                if judge_uses_knowledge else None),
    )
    result = run_startup_canaries(
        model, benchmark, api_key="unused", provider=RecordingEchoProvider(),
        reviewer_provider=reviewer, judge_provider=judge,
    )
    # This canary supplies decisive evidence, so a knowledge-based answer fails the check.
    assert result.valid is not judge_uses_knowledge
    for role, provider in ((OracleRole.REVIEWER, reviewer), (OracleRole.JUDGE, judge)):
        baseline = _evidence_review_canary_request("old", role=role, profile=oracle.prompt_profile)
        revised = provider.requests[0]
        assert revised.messages[1] == baseline.messages[1]
        if role is OracleRole.REVIEWER:
            assert revised.messages == baseline.messages
            assert revised.output_schema == baseline.output_schema
            assert revised.prompt_cache_key == baseline.prompt_cache_key
        else:
            assert revised.messages[0] != baseline.messages[0]
            assert revised.output_schema != baseline.output_schema
            assert revised.prompt_cache_key != baseline.prompt_cache_key


def test_startup_canaries_use_the_structured_contract_for_reviewer_and_judge() -> None:
    model, benchmark = _configuration()
    provider = RecordingEchoProvider()
    reviewer_provider = RecordingEvidenceReviewProvider(
        benchmark.oracle_configuration.reviewer
    )
    judge_provider = RecordingEvidenceReviewProvider(
        benchmark.oracle_configuration.judge
    )

    result = run_startup_canaries(
        model,
        benchmark,
        api_key="unused",
        provider=provider,
        reviewer_provider=reviewer_provider,
        judge_provider=judge_provider,
    )

    assert result.valid is True
    assert tuple(role.role for role in result.roles) == tuple(BenchmarkLlmRole)
    assert all(role.valid for role in result.roles)
    assert all(
        role.answer == "Hi"
        for role in result.roles
        if role.role
        not in {BenchmarkLlmRole.REVIEWER, BenchmarkLlmRole.JUDGE}
    )
    assert provider.closed is True
    assert reviewer_provider.closed is True
    assert judge_provider.closed is True
    assert len(provider.requests) == 3
    assert all(
        request.role
        not in {BenchmarkLlmRole.REVIEWER, BenchmarkLlmRole.JUDGE}
        for request in provider.requests
    )
    assert len(reviewer_provider.requests) == 1
    assert len(judge_provider.requests) == 1
    reviewer_request = reviewer_provider.requests[0]
    judge_request = judge_provider.requests[0]
    reviewer_result = next(
        role for role in result.roles if role.role is BenchmarkLlmRole.REVIEWER
    )
    judge_result = next(
        role for role in result.roles if role.role is BenchmarkLlmRole.JUDGE
    )
    assert reviewer_request.response_schema_name == "reviewer_canary_result"
    assert reviewer_request.session_id is not None
    assert "startup-reviewer-canary-v1" in reviewer_request.session_id
    assert reviewer_request.prompt_cache_key == "deep20-startup-reviewer-canary-v1"
    assert judge_request.response_schema_name == "judge_canary_result"
    assert judge_request.session_id is not None
    assert "startup-judge-canary-v1" in judge_request.session_id
    assert judge_request.prompt_cache_key == "deep20-startup-judge-canary-v1"
    for structured_request in (reviewer_request, judge_request):
        payload = json.loads(
            structured_request.messages[1]["content"].split("\n", 1)[1]
        )
        assert set(payload) == {
            "subject",
            "current_yes_no_question",
            "numbered_evidence_excerpts",
        }
        assert set(payload["numbered_evidence_excerpts"][0]) == {
            "number",
            "excerpt",
        }
        assert "oracle_answer" not in payload
        assert "reviewer_answer" not in payload
        assert "episode_history" not in payload
        assert "britannica.com" not in json.dumps(payload)
    assert reviewer_request.session_id != judge_request.session_id
    assert reviewer_request.prompt_cache_key != judge_request.prompt_cache_key
    assert reviewer_result.provider_routing is ProviderRouting.EXACT
    assert reviewer_result.resolved_provider == "google-ai-studio"
    assert reviewer_result.answer == "YES"
    assert reviewer_result.evidence_count == 1
    assert reviewer_result.search_count == 0
    assert judge_result.provider_routing is ProviderRouting.AUTOMATIC
    assert judge_result.resolved_provider == "Amazon Bedrock"
    assert judge_result.answer == "YES"
    assert judge_result.evidence_count == 1
    assert judge_result.search_count == 0
    assert len({request.session_id for request in provider.requests}) == 3
    assert len({request.prompt_cache_key for request in provider.requests}) == 3
    assert all("startup-echo-canary-v1" in request.session_id for request in provider.requests)
    assert all(
        "startup-echo-canary-v1" in request.prompt_cache_key for request in provider.requests
    )
    serialized_result = result.model_dump_json()
    assert "Reply with exactly" not in serialized_result
    assert "synthetic_entity" not in serialized_result
    assert "Example Domain" not in serialized_result
    assert "Ada Lovelace" not in serialized_result
    assert "December 10, 1815" not in serialized_result


def test_startup_canaries_report_failures_without_retaining_bad_output() -> None:
    model, benchmark = _configuration()
    provider = RecordingEchoProvider(
        failures={BenchmarkLlmRole.ORACLE: "provider_http_503"},
    )
    reviewer_provider = RecordingEvidenceReviewProvider(
        benchmark.oracle_configuration.reviewer,
        failure="provider_http_503",
    )
    judge_provider = RecordingEvidenceReviewProvider(
        benchmark.oracle_configuration.judge,
        output="Hello",
    )

    result = run_startup_canaries(
        model,
        benchmark,
        api_key="unused",
        provider=provider,
        reviewer_provider=reviewer_provider,
        judge_provider=judge_provider,
    )

    failures = {role.role: role for role in result.roles if not role.valid}
    assert result.valid is False
    assert failures[BenchmarkLlmRole.ORACLE].error_code == "provider_http_503"
    assert failures[BenchmarkLlmRole.REVIEWER].error_code == "provider_http_503"
    assert failures[BenchmarkLlmRole.JUDGE].error_code == "invalid_judge_canary_output"
    assert failures[BenchmarkLlmRole.JUDGE].answer is None
    assert "Hello" not in result.model_dump_json()
    assert len(provider.requests) == 3
    assert len(reviewer_provider.requests) == 1
    assert len(judge_provider.requests) == 1
    assert provider.closed is True
    assert reviewer_provider.closed is True
    assert judge_provider.closed is True


def test_startup_canary_reports_live_judge_provider_failure() -> None:
    model, benchmark = _configuration()
    provider = RecordingEchoProvider()
    reviewer_provider = RecordingEvidenceReviewProvider(
        benchmark.oracle_configuration.reviewer
    )
    judge_provider = RecordingEvidenceReviewProvider(
        benchmark.oracle_configuration.judge,
        failure="provider_invalid_request",
    )

    result = run_startup_canaries(
        model,
        benchmark,
        api_key="unused",
        provider=provider,
        reviewer_provider=reviewer_provider,
        judge_provider=judge_provider,
    )

    judge_result = next(
        role for role in result.roles if role.role is BenchmarkLlmRole.JUDGE
    )
    assert result.valid is False
    assert judge_result.valid is False
    assert judge_result.error_code == "provider_invalid_request"
    assert judge_result.answer is None
    assert reviewer_provider.closed is True
    assert judge_provider.closed is True


def test_startup_canaries_require_paired_provider_injection() -> None:
    model, benchmark = _configuration()

    with pytest.raises(ValueError, match="inject echo, Reviewer, and Judge"):
        run_startup_canaries(
            model,
            benchmark,
            api_key="unused",
            provider=RecordingEchoProvider(),
        )


def test_echo_exchange_reads_openrouter_provider_metadata() -> None:
    request = EchoCanaryRequest(
        role=BenchmarkLlmRole.GUESSER,
        model="google/gemini-3.6-flash",
        provider="google-vertex",
        session_id="isolated-session",
        prompt_cache_key="isolated-cache",
    )

    exchange = OpenRouterEchoCanaryProvider._exchange(
        request,
        {
            "model": request.model,
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"content": "Hi"},
                }
            ],
            "openrouter_metadata": {
                "attempts": [{"provider_name": "Google"}],
            },
            "usage": {
                "prompt_tokens": 8,
                "completion_tokens": 1,
                "cost": 0.000001,
            },
        },
        response_cache_status=None,
        latency_ms=12,
    )

    assert exchange.output == "Hi"
    assert exchange.resolved_provider == "Google"
    assert exchange.usage.input_tokens == 8
    assert exchange.usage.output_tokens == 1


def test_concise_policy_reaches_both_structured_startup_canaries() -> None:
    from deep20_oracle.config import AdjudicationPolicy, PromptProfile

    model, benchmark = _configuration()
    oracle = benchmark.oracle_configuration.model_copy(update={
        "prompt_profile": PromptProfile.QUALIFIED_V1,
        "adjudication_policy": AdjudicationPolicy.CONCISE_KNOWLEDGE_V1,
    })
    benchmark = benchmark.model_copy(update={"oracle_configuration": oracle})
    output = json.dumps({"answer": "YES", "basis": "evidence", "evidence_indices": [1],
                         "supporting_statement": "The supplied excerpt establishes the claim."})
    reviewer = RecordingEvidenceReviewProvider(oracle.reviewer, output=output)
    judge = RecordingEvidenceReviewProvider(oracle.judge, output=output)
    result = run_startup_canaries(
        model, benchmark, api_key="unused", provider=RecordingEchoProvider(),
        reviewer_provider=reviewer, judge_provider=judge,
    )
    assert result.valid
    for provider in (reviewer, judge):
        request = provider.requests[0]
        assert request.output_schema["$defs"]["EvidenceDecisionBasis"]["enum"] == ["evidence", "other"]
        assert "supporting_statement" in request.output_schema["required"]
