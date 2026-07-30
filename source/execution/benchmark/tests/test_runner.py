from __future__ import annotations

import json
import logging
import re
import stat
from decimal import Decimal
from pathlib import Path

import deep20_benchmark.artifacts as artifacts_module
import pytest
import yaml
from deep20_benchmark.artifacts import (
    ArtifactIntegrityError,
    ArtifactStore,
    BenchmarkExecutionLocked,
    BenchmarkTrialSink,
    signed_trial_manifest,
)
from deep20_benchmark.catalog import (
    BenchmarkCatalog,
    BenchmarkCatalogEntry,
    ModelCatalog,
    ModelCatalogEntry,
)
from deep20_benchmark.logging import BLANK_LINE_BEFORE_ATTRIBUTE
from deep20_benchmark.models import (
    ERROR_OUTPUT_PREVIEW_MAX_CHARACTERS,
    BenchmarkEventId,
    BenchmarkExecutionId,
    BenchmarkId,
    BenchmarkManifest,
    BenchmarkModelId,
    BenchmarkRequest,
    BenchmarkStartedEvent,
    BenchmarkSummaryArtifact,
    CompletedTrialResult,
    EpisodeRunId,
    ExecutionResumedEvent,
    ExecutionStatus,
    InfrastructureCircuitBreaker,
    InfrastructureFailedTrialResult,
    ModelStartedEvent,
    SubjectId,
    SubjectStartedEvent,
    TrialId,
    TrialIdentity,
    TrialRepairPolicy,
)
from deep20_benchmark.runner import BenchmarkCircuitBreakerOpen, BenchmarkRunner
from deep20_benchmark.runtime import EpisodeExecutor, TrialExecutionContext
from deep20_game.config import (
    BenchmarkMode,
    CachePolicy,
    GamePolicy,
    ModelConfig,
    PromptCacheConfig,
)
from deep20_game.models import (
    ActionTurnResult,
    ActionType,
    CacheStatus,
    CallMetrics,
    ComponentCosts,
    ComponentTokens,
    ComponentTotals,
    ContractViolationKind,
    ContractViolationProgress,
    ContractViolationTurnResult,
    EpisodeFinishedEvent,
    EpisodeFinishedPayload,
    EpisodeLlmDetails,
    EpisodeModelVersions,
    EpisodeOutcome,
    EpisodeResult,
    EpisodeRun,
    EpisodeSummary,
    EpisodeTerminalFailure,
    FailedGameCallAudit,
    GameComponentFailure,
    GameLlmDetails,
    GuesserAction,
    GuesserFailureRecord,
    LlmVersion,
    OracleLlmDetails,
    OracleQualityTotals,
    TerminalReason,
    TurnAdjudication,
    TurnProgress,
    guesser_contract_reliability,
)
from deep20_game.sinks import ExecutionObserver
from deep20_oracle.catalog import SubjectCatalog
from deep20_oracle.config import OracleConfig
from deep20_oracle.models import (
    EvidenceDecisionBasis,
    EvidenceReviewResult,
    OracleAdjudication,
    OracleAnswer,
    OracleDecisionPath,
    OracleMetrics,
    OracleRoleMetrics,
    ProviderOutputCapture,
    ProviderTrace,
    ProviderUsage,
    RecoveryMetrics,
    RecoveryReason,
    RecoveryReasonCount,
    Subject,
)
from deep20_oracle.util import canonical_json, sha256_text
from pydantic import ValidationError


def assert_markdown_links_resolve(path: Path) -> None:
    targets = re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))
    assert targets
    for target in targets:
        assert (path.parent / target).resolve().is_file(), f"broken link {target} in {path}"


def model_config(configuration_id: str) -> ModelConfig:
    return ModelConfig(
        configuration_id=configuration_id,
        model=f"openai/{configuration_id.lower()}",
        provider="openai",
        reasoning_effort="medium",
        max_output_tokens=500,
        timeout_seconds=30,
        prompt_cache=PromptCacheConfig(
            policy=CachePolicy.BEST_EFFORT,
            minimum_cacheable_tokens=100,
            ttl_seconds=300,
            input_usd_per_million=Decimal(1),
            cached_input_usd_per_million=Decimal("0.1"),
            cache_write_multiplier=Decimal("1.25"),
        ),
    )


class FakeExecutor(EpisodeExecutor):
    def __init__(
        self,
        *,
        fail_first: bool = False,
        interrupt_call: int | None = None,
        emit_turn: ActionType | None = None,
        emit_contract_violation: bool = False,
        include_quality_costs: bool = False,
        include_turn_quality_costs: bool = False,
    ):
        self.fail_first = fail_first
        self.interrupt_call = interrupt_call
        self.emit_turn = emit_turn
        self.emit_contract_violation = emit_contract_violation
        self.include_quality_costs = include_quality_costs
        self.include_turn_quality_costs = include_turn_quality_costs
        self.calls: list[TrialExecutionContext] = []

    def execute(
        self,
        context: TrialExecutionContext,
        sink: BenchmarkTrialSink,
        observer: ExecutionObserver,
    ) -> EpisodeResult:
        self.calls.append(context)
        if self.interrupt_call == len(self.calls):
            raise KeyboardInterrupt
        if self.fail_first and len(self.calls) == 1:
            raise RuntimeError("temporary provider outage")
        episode_id = "EP-" + f"{len(self.calls):032x}"
        if self.emit_contract_violation:
            observer.observe(
                ContractViolationProgress(
                    run_id=str(context.identity.episode_run_id),
                    episode_id=episode_id,
                    turn=ContractViolationTurnResult(
                        turn_number=1,
                        violation_kind=ContractViolationKind.INVALID_ACTION,
                        feedback_event="FORMAT_ERROR",
                        counted=True,
                        counted_questions=1,
                        guesser_call_id="GC-" + f"{len(self.calls):032x}",
                    ),
                    guesser_metrics=CallMetrics(
                        cost_usd=Decimal("0.00123456"),
                        latency_ms=841,
                        input_tokens=50,
                        cached_input_tokens=20,
                        cache_write_tokens=0,
                        output_tokens=10,
                        reasoning_tokens=5,
                    ),
                )
            )
        if self.emit_turn is not None:
            is_question = self.emit_turn is ActionType.ASK
            observer.observe(
                TurnProgress(
                    run_id=str(context.identity.episode_run_id),
                    episode_id=episode_id,
                    turn=ActionTurnResult(
                        turn_number=1,
                        action=GuesserAction(
                            action=self.emit_turn,
                            question=(
                                "Was this person born before 1900?" if is_question else None
                            ),
                            name=None if is_question else "One",
                            description=None if is_question else "The first test subject.",
                        ),
                        adjudication=TurnAdjudication(
                            component="oracle" if is_question else "guess_validator",
                            call_id=("OC-" if is_question else "VC-")
                            + f"{len(self.calls):032x}",
                            answer=OracleAnswer.YES,
                            oracle_quality=(
                                OracleAdjudication(
                                    oracle_answer=OracleAnswer.YES,
                                    reviewer=EvidenceReviewResult(
                                        answer=OracleAnswer.YES,
                                        basis=EvidenceDecisionBasis.EVIDENCE,
                                        evidence_indices=(1,),
                                    ),
                                    disagreement=False,
                                    judge_invoked=False,
                                    final_answer=OracleAnswer.YES,
                                    decision_path=(
                                        OracleDecisionPath.REVIEWER_AGREEMENT
                                    ),
                                )
                                if is_question
                                else None
                            ),
                        ),
                        counted=is_question,
                        counted_questions=1 if is_question else 0,
                        guesser_call_id="GC-" + f"{len(self.calls):032x}",
                    ),
                    guesser_metrics=CallMetrics(
                        cost_usd=Decimal("0.00123456"),
                        latency_ms=841,
                        input_tokens=50,
                        cached_input_tokens=20,
                        cache_write_tokens=0,
                        output_tokens=10,
                        reasoning_tokens=5,
                    ),
                    adjudicator_metrics=(
                        OracleMetrics(
                            cost_usd=Decimal("0.0061318499999999995"),
                            latency_ms=1_842,
                            input_tokens=100,
                            cached_input_tokens=10,
                            cache_write_tokens=0,
                            output_tokens=20,
                            reasoning_tokens=5,
                            search_count=1,
                            reviewer=(
                                OracleRoleMetrics(
                                    cost_usd=Decimal("0.001"),
                                    latency_ms=200,
                                    input_tokens=10,
                                    output_tokens=2,
                                    reasoning_tokens=0,
                                    search_count=0,
                                )
                                if self.include_turn_quality_costs
                                else None
                            ),
                            judge=(
                                OracleRoleMetrics(
                                    cost_usd=Decimal("0.002"),
                                    latency_ms=300,
                                    input_tokens=12,
                                    output_tokens=3,
                                    reasoning_tokens=0,
                                    search_count=0,
                                )
                                if self.include_turn_quality_costs
                                else None
                            ),
                        )
                        if is_question
                        else CallMetrics(
                            cost_usd=Decimal("0.0007318499999999995"),
                            latency_ms=442,
                            input_tokens=40,
                            cached_input_tokens=4,
                            cache_write_tokens=3,
                            output_tokens=8,
                            reasoning_tokens=2,
                        )
                    ),
                )
            )
        zero = ComponentTotals()
        result = EpisodeResult(
            run=EpisodeRun(
                run_id=str(context.identity.episode_run_id),
                episode_id=episode_id,
                subject=context.subject,
                started_at="2026-07-26T10:00:00+00:00",
                completed_at="2026-07-26T10:00:01+00:00",
                duration_ms=1_000,
            ),
            outcome=EpisodeOutcome(
                success=True,
                terminal_reason=TerminalReason.SUCCESS,
                scoring_eligible=True,
                publication_eligible=False,
            ),
            summary=EpisodeSummary(
                total_turns=2 if self.emit_contract_violation else 1,
                counted_questions=context.identity.trial_number,
                guesser_call_count=2 if self.emit_contract_violation else 1,
                ask_count=0,
                guess_count=1,
                rejected_guess_count=0,
                oracle_unknown_count=0,
                oracle_quality=(
                    OracleQualityTotals(
                        reviewed_questions=1,
                        disagreements=1,
                        judge_invocations=1,
                        judge_yes_answers=1,
                        reviewer_cost_usd=Decimal("0.02"),
                        judge_cost_usd=Decimal("0.03"),
                        quality_control_cost_usd=Decimal("0.05"),
                    )
                    if self.include_quality_costs
                    else OracleQualityTotals()
                ),
                contract=(
                    guesser_contract_reliability(
                        evaluated_outputs=2,
                        violations=1,
                        counted_penalties=1,
                        affected_trials=1,
                    )
                    if self.emit_contract_violation
                    else guesser_contract_reliability(
                        evaluated_outputs=1,
                        violations=0,
                        counted_penalties=0,
                        affected_trials=0,
                    )
                ),
                cache_status=CacheStatus.NOT_APPLICABLE,
                costs_usd=(
                    ComponentCosts(
                        guesser=Decimal("0.01"),
                        oracle=Decimal("0.07"),
                        validator=Decimal("0.01"),
                        total=Decimal("0.09"),
                    )
                    if self.include_quality_costs
                    else ComponentCosts(
                        guesser=Decimal("0.01"),
                        oracle=Decimal(0),
                        validator=Decimal("0.01"),
                        total=Decimal("0.02"),
                    )
                ),
                tokens=ComponentTokens(
                    guesser=100,
                    oracle=0,
                    validator=100,
                    total=200,
                ),
            ),
            models=EpisodeModelVersions(
                under_test=LlmVersion(
                    role="guesser",
                    configuration_id=context.model.configuration.configuration_id,
                    requested_model=context.model.configuration.model,
                    requested_provider=context.model.configuration.provider,
                    resolved_models=(context.model.configuration.model,),
                    resolved_providers=("OpenAI",),
                    reasoning_effort="medium",
                    prompt_version="test-guesser",
                ),
                oracle=LlmVersion(
                    role="oracle",
                    configuration_id=None,
                    requested_model=context.definition.oracle_configuration.model,
                    requested_provider=context.definition.oracle_configuration.provider,
                    resolved_models=(),
                    resolved_providers=(),
                    reasoning_effort="medium",
                    prompt_version="test-oracle",
                ),
                validator=LlmVersion(
                    role="validator",
                    configuration_id=context.definition.validator_configuration.configuration_id,
                    requested_model=context.definition.validator_configuration.model,
                    requested_provider=context.definition.validator_configuration.provider,
                    resolved_models=(),
                    resolved_providers=(),
                    reasoning_effort="medium",
                    prompt_version="test-validator",
                ),
            ),
            turns=(),
            guesser_conversation=(),
            llm_details=EpisodeLlmDetails(
                guesser=GameLlmDetails(
                    configuration=context.model.configuration,
                    metrics=zero,
                ),
                oracle=OracleLlmDetails(
                    configuration=context.definition.oracle_configuration,
                    metrics=zero,
                ),
                validator=GameLlmDetails(
                    configuration=context.definition.validator_configuration,
                    metrics=zero,
                ),
            ),
        )
        sink.persist_episode_result(result)
        return result


class TerminalFailureExecutor(FakeExecutor):
    def execute(
        self,
        context: TrialExecutionContext,
        sink: BenchmarkTrialSink,
        observer: ExecutionObserver,
    ) -> EpisodeResult:
        completed = super().execute(context, sink, observer)
        failed = completed.model_copy(
            update={
                "outcome": EpisodeOutcome(
                    success=False,
                    terminal_reason=TerminalReason.INFRASTRUCTURE_FAILURE,
                    scoring_eligible=False,
                    publication_eligible=False,
                )
            }
        )
        index = len(self.calls)
        sink.persist_episode_event(
            EpisodeFinishedEvent(
                event_id="EV-" + f"{index:032x}",
                run_id=failed.run_id,
                episode_id=failed.episode_id,
                payload=EpisodeFinishedPayload(
                    result=failed,
                    failure=EpisodeTerminalFailure(
                        code="provider_request_failed",
                        type="GameProviderError",
                        message="OpenRouter request failed",
                        call_id="GC-" + f"{index:032x}",
                    ),
                ),
                recorded_at="2026-07-26T10:00:01+00:00",
            )
        )
        return failed


class ProtocolFailureExecutor(FakeExecutor):
    def execute(
        self,
        context: TrialExecutionContext,
        sink: BenchmarkTrialSink,
        observer: ExecutionObserver,
    ) -> EpisodeResult:
        completed = super().execute(context, sink, observer)
        failed = completed.model_copy(
            update={
                "outcome": EpisodeOutcome(
                    success=False,
                    terminal_reason=TerminalReason.GUESSER_PROTOCOL_FAILURE,
                    scoring_eligible=True,
                    publication_eligible=False,
                )
            }
        )
        index = len(self.calls)
        sink.persist_episode_event(
            EpisodeFinishedEvent(
                event_id="EV-" + f"{index:032x}",
                run_id=failed.run_id,
                episode_id=failed.episode_id,
                payload=EpisodeFinishedPayload(
                    result=failed,
                    failure=EpisodeTerminalFailure(
                        code="invalid_guesser_output",
                        type="GuesserProtocolError",
                        message="provider output did not match the Guesser action schema",
                        call_id="GC-" + f"{index:032x}",
                    ),
                ),
                recorded_at="2026-07-26T10:00:01+00:00",
            )
        )
        return failed


class OutputPreviewFailureExecutor(TerminalFailureExecutor):
    output = '{"result": {"action": "ASK", "question": "ERROR_OUTPUT_PREVIEW_MARKER?"' + (" " * 500)

    def __init__(self) -> None:
        super().__init__()
        self.visible_messages: tuple[dict[str, str], ...] = ()

    def execute(
        self,
        context: TrialExecutionContext,
        sink: BenchmarkTrialSink,
        observer: ExecutionObserver,
    ) -> EpisodeResult:
        index = len(self.calls) + 1
        call_id = "GC-" + f"{index:032x}"
        episode_id = "EP-" + f"{index:032x}"
        self.visible_messages = (
            {"role": "system", "content": "FIXED_GUESSER_INSTRUCTIONS"},
            {"role": "user", "content": "BEGIN"},
        )
        trace = ProviderTrace(
            requested_at="2026-07-27T20:00:00+00:00",
            completed_at="2026-07-27T20:04:00+00:00",
            latency_ms=240_000,
            http_status_code=200,
            response_id="response-final",
            finish_reason="length",
            requested_model=context.model.configuration.model,
            resolved_model=context.model.configuration.model,
            requested_provider=context.model.configuration.provider,
            resolved_provider="OpenAI",
            fallback_occurred=False,
            request={"messages": [{"role": "user", "content": "BEGIN"}]},
            response={
                "id": "response-final",
                "choices": [
                    {
                        "finish_reason": "length",
                        "message": {"content": self.output},
                    }
                ],
            },
            raw_output=self.output,
            usage=ProviderUsage(output_tokens=16_384),
        )
        sink.persist_guesser_failure(
            GuesserFailureRecord(
                call_id=call_id,
                run_id=str(context.identity.episode_run_id),
                episode_id=episode_id,
                metrics=None,
                audit=FailedGameCallAudit(
                    prompt_version="test",
                    prompt_hash="a" * 64,
                    messages=self.visible_messages,
                    session_id="test-session",
                    prompt_cache_key="test-cache",
                    provider=trace,
                ),
                failure=GameComponentFailure(
                    code="provider_output_limit_exceeded",
                    type="GameProviderError",
                    message="OpenRouter did not return a completed choice",
                    details={},
                ),
                recorded_at="2026-07-27T20:04:00+00:00",
            )
        )
        return super().execute(context, sink, observer)


def fixtures() -> tuple[ModelCatalog, BenchmarkCatalog, SubjectCatalog]:
    first = model_config("M-0001")
    second = model_config("M-0002")
    validator = model_config("validator")
    models = ModelCatalog(
        version=3,
        models={
            "M-0001": ModelCatalogEntry(
                model_id=BenchmarkModelId("M-0001"),
                display_name="First",
                configuration=first,
            ),
            "M-0002": ModelCatalogEntry(
                model_id=BenchmarkModelId("M-0002"),
                display_name="Second",
                configuration=second,
            ),
        },
    )
    benchmark = BenchmarkCatalog(
        version=2,
        benchmarks={
            "B-0001": BenchmarkCatalogEntry(
                benchmark_id=BenchmarkId("B-0001"),
                display_name="Test suite",
                default_iterations=2,
                game_policy=GamePolicy(),
                oracle_configuration=OracleConfig(
                    model="openai/oracle",
                    provider="openai",
                ),
                validator_configuration=validator,
            )
        },
    )
    subjects = SubjectCatalog(
        version=1,
        subjects={
            "T-0001": Subject(
                target_id="T-0001",
                canonical_name="One",
                entity_type="person",
                description="First test subject.",
            ),
            "T-0002": Subject(
                target_id="T-0002",
                canonical_name="Two",
                entity_type="person",
                description="Second test subject.",
            ),
        },
    )
    return models, benchmark, subjects


def test_benchmark_retains_full_error_outputs_in_private_artifact(
    tmp_path: Path,
) -> None:
    models, benchmark, subjects = fixtures()
    model = models.model(BenchmarkModelId("M-0001"))
    definition = benchmark.benchmark(
        BenchmarkId("B-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        subject_ids=(SubjectId("T-0001"),),
        iterations_override=1,
    )
    identity = TrialIdentity(
        execution_id=BenchmarkExecutionId("BX-error-output-001"),
        model_id=model.model_id,
        target_id=SubjectId("T-0001"),
        trial_id=TrialId("trial-001"),
        trial_number=1,
        episode_run_id=EpisodeRunId("BR-" + "1" * 40),
    )
    sink = BenchmarkTrialSink(
        ArtifactStore(tmp_path),
        signed_trial_manifest(
            identity=identity,
            subject_catalog_hash=subjects.content_hash(),
            subject=subjects.subject("T-0001"),
            model=model,
            game_policy=definition.game_policy,
            oracle_configuration=definition.oracle_configuration,
            validator_configuration=definition.validator_configuration,
        ),
    )
    sink.prepare_run(str(identity.episode_run_id))
    first_output = "RUNAWAY-FIRST-" * 2_000
    final_output = " \nRUNAWAY-FINAL-" * 2_000
    recovery = RecoveryMetrics(
        request_attempts=2,
        retried_calls=1,
        recovered_calls=0,
        exhausted_retries=1,
        reasons=(
            RecoveryReasonCount(
                reason=RecoveryReason.OUTPUT_LIMIT_EXCEEDED,
                count=2,
            ),
        ),
        retry_usage=ProviderUsage(output_tokens=16_384),
    )
    trace = ProviderTrace(
        requested_at="2026-07-27T20:00:00+00:00",
        completed_at="2026-07-27T20:04:00+00:00",
        latency_ms=240_000,
        http_status_code=200,
        response_id="response-final",
        finish_reason="length",
        request_attempts=2,
        recovery=recovery,
        requested_model=model.configuration.model,
        resolved_model=model.configuration.model,
        requested_provider=model.configuration.provider,
        resolved_provider=model.configuration.provider,
        fallback_occurred=False,
        request={
            "messages": [{"role": "user", "content": "PRIVATE_PROMPT_MARKER"}],
        },
        response={
            "id": "response-final",
            "private_subject": "PRIVATE_SUBJECT_MARKER",
            "choices": [
                {
                    "finish_reason": "length",
                    "message": {"content": final_output},
                }
            ],
        },
        raw_output=final_output,
        discarded_error_outputs=(
            ProviderOutputCapture(
                attempt_number=1,
                response_id="response-first",
                finish_reason="length",
                output=first_output,
            ),
        ),
        usage=ProviderUsage(output_tokens=32_768),
    )
    sink.persist_guesser_failure(
        GuesserFailureRecord(
            call_id="GC-" + "2" * 32,
            run_id=str(identity.episode_run_id),
            episode_id="EP-" + "3" * 32,
            metrics=None,
            audit=FailedGameCallAudit(
                prompt_version="test",
                prompt_hash="a" * 64,
                messages=(
                    {"role": "system", "content": "PRIVATE_SYSTEM_MARKER"},
                    {"role": "user", "content": "BEGIN"},
                ),
                session_id="test-session",
                prompt_cache_key="test-cache",
                provider=trace,
            ),
            failure=GameComponentFailure(
                code="provider_output_limit_exceeded",
                type="GameProviderError",
                message="OpenRouter did not return a completed choice",
                details={"provider_trace": trace.model_dump(mode="json")},
            ),
            recorded_at="2026-07-27T20:04:00+00:00",
        )
    )

    references = sink.references()
    assert references.error_outputs is not None
    assert references.error_outputs.record_count == 1
    assert references.error_outputs.integrity_hash
    path = tmp_path / references.error_outputs.relative_path
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    raw_artifact = path.read_text(encoding="utf-8")
    record = json.loads(raw_artifact)
    assert record["component"] == "guesser"
    assert record["failure_code"] == "provider_output_limit_exceeded"
    assert record["recovered"] is False
    assert [output["output"] for output in record["outputs"]] == [
        first_output,
        final_output,
    ]
    assert [output["attempt_number"] for output in record["outputs"]] == [1, 2]
    assert "PRIVATE_PROMPT_MARKER" not in raw_artifact
    assert "PRIVATE_SYSTEM_MARKER" not in raw_artifact
    assert "PRIVATE_SUBJECT_MARKER" not in raw_artifact
    assert sink.latest_error_output_preview is not None
    assert (
        sink.latest_error_output_preview.text == final_output[:ERROR_OUTPUT_PREVIEW_MAX_CHARACTERS]
    )
    assert len(sink.latest_error_output_preview.text) == ERROR_OUTPUT_PREVIEW_MAX_CHARACTERS
    assert sink.latest_error_output_preview.original_characters == len(final_output)
    assert sink.latest_error_output_preview.truncated is True


def test_runner_writes_bounded_error_output_preview_only_to_results(
    tmp_path: Path,
    caplog,
) -> None:
    models, benchmark, subjects = fixtures()
    executor = OutputPreviewFailureExecutor()
    store = ArtifactStore(tmp_path)
    store._git = lambda arguments: (  # type: ignore[method-assign]
        "abc123" if arguments == ["rev-parse", "HEAD"] else ""
    )
    with caplog.at_level(logging.INFO, logger="deep20.benchmark"):
        result = BenchmarkRunner(
            store=store,
            model_catalog=models,
            benchmark_catalog=benchmark,
            subject_catalog=subjects,
            executor=executor,
        ).run(
            BenchmarkRequest(
                benchmark_id=BenchmarkId("B-0001"),
                execution_id=BenchmarkExecutionId("BX-error-preview-001"),
                model_id=BenchmarkModelId("M-0001"),
                benchmark_mode=BenchmarkMode.EXPERIMENTAL,
                target_ids=(SubjectId("T-0001"),),
                iterations_override=1,
            )
        )

    trial = result.subjects[0].trials[0]
    assert isinstance(trial, InfrastructureFailedTrialResult)
    preview = trial.error_output_preview
    assert preview is not None
    assert preview.component == "guesser"
    assert preview.attempt_number == 1
    assert preview.finish_reason == "length"
    assert preview.text == executor.output[:ERROR_OUTPUT_PREVIEW_MAX_CHARACTERS]
    assert len(preview.text) == ERROR_OUTPUT_PREVIEW_MAX_CHARACTERS
    assert preview.original_characters == len(executor.output)
    assert preview.trailing_whitespace_characters == 500
    assert preview.truncated is True

    run_root = tmp_path / "runs/M-0001/BX-error-preview-001"
    loaded_trial = store.load_trial_result(trial.identity)
    assert loaded_trial == trial
    loaded_result = store.load_benchmark_result(
        BenchmarkModelId("M-0001"),
        BenchmarkExecutionId("BX-error-preview-001"),
    )
    assert loaded_result == result
    leaf_result = (run_root / "subjects/T-0001/trials/trial-001/result.yml").read_text(
        encoding="utf-8"
    )
    benchmark_result = (run_root / "result.yml").read_text(encoding="utf-8")
    for result_text in (leaf_result, benchmark_result):
        assert "error_output_preview:" in result_text
        assert "ERROR_OUTPUT_PREVIEW_MARKER" in result_text
        assert executor.output not in result_text

    for non_result_path in (
        run_root / "state.yml",
        run_root / "benchmark-events.jsonl",
        run_root / "summary.yml",
        run_root / "summary.md",
    ):
        non_result = non_result_path.read_text(encoding="utf-8")
        assert "ERROR_OUTPUT_PREVIEW_MARKER" not in non_result
        assert "error_output_preview" not in non_result

    visible_conversation = canonical_json(executor.visible_messages)
    assert "ERROR_OUTPUT_PREVIEW_MARKER" not in visible_conversation
    assert preview.text not in visible_conversation
    assert all(
        "ERROR_OUTPUT_PREVIEW_MARKER" not in record.getMessage()
        and "error_output_preview" not in record.getMessage()
        for record in caplog.records
    )


def test_runner_returns_nested_typed_result_and_hierarchy(tmp_path: Path) -> None:
    models, benchmark, subjects = fixtures()
    executor = FakeExecutor()
    store = ArtifactStore(tmp_path)
    store._git = lambda arguments: "abc123" if arguments == ["rev-parse", "HEAD"] else ""  # type: ignore[method-assign]
    runner = BenchmarkRunner(
        store=store,
        model_catalog=models,
        benchmark_catalog=benchmark,
        subject_catalog=subjects,
        executor=executor,
    )
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-test-001"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        base_seed=42,
    )

    result = runner.run(request)

    assert result.run.model.model_id == BenchmarkModelId("M-0001")
    assert "models" not in result.model_dump(mode="json")
    assert len(result.subjects) == 2
    assert len(result.subjects[0].trials) == 2
    assert all(
        isinstance(trial, CompletedTrialResult)
        for subject in result.subjects
        for trial in subject.trials
    )
    assert result.summary.counts.scheduled == 4
    assert result.summary.success_rate == Decimal(1)
    assert result.summary.questions_all_eligible.median == Decimal("1.5")
    assert result.summary.guesser_cost_usd.mean == Decimal("0.01")
    assert result.summary.oracle_cost_usd.mean == Decimal(0)
    assert result.summary.validator_cost_usd.mean == Decimal("0.01")
    assert result.summary.cost_usd.mean == Decimal("0.02")
    assert result.summary.total_cost_usd == Decimal("0.08")
    assert result.summary.cached_input_tokens.count == 4
    assert result.summary.cache_write_tokens.count == 4
    assert len(result.integrity_hash) == 64
    assert result.artifacts.result.integrity_hash == result.integrity_hash
    assert len(executor.calls) == 4
    assert result.run.base_seed == 42
    assert all(context.base_seed == 42 for context in executor.calls)
    assert {
        (context.subject.target_id, context.identity.trial_number) for context in executor.calls
    } == {
        ("T-0001", 1),
        ("T-0001", 2),
        ("T-0002", 1),
        ("T-0002", 2),
    }
    assert (
        tmp_path / "runs/M-0001/BX-test-001/subjects/T-0001/trials/trial-001/result.yml"
    ).is_file()
    assert not (tmp_path / "runs/M-0002").exists()
    assert not (tmp_path / "reports").exists()
    manifest = json.loads(
        (tmp_path / "runs/M-0001/BX-test-001/manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["model"]["model_id"] == "M-0001"
    assert manifest["request"]["benchmark_mode"] == "experimental"
    assert manifest["definition"]["game_policy"]["benchmark_mode"] == "experimental"
    assert "models" not in manifest
    assert not tuple(tmp_path.glob("runs/**/trials/*/audit"))
    assert (tmp_path / "runs/M-0001/BX-test-001/result.yml").is_file()
    benchmark_summary_path = tmp_path / "runs/M-0001/BX-test-001/summary.yml"
    assert benchmark_summary_path.is_file()
    benchmark_summary = store.load_benchmark_summary(
        BenchmarkModelId("M-0001"), BenchmarkExecutionId("BX-test-001")
    )
    assert isinstance(benchmark_summary, BenchmarkSummaryArtifact)
    assert benchmark_summary.summary == result.summary
    assert benchmark_summary.model == result.run.model
    assert len(benchmark_summary.subjects) == 2
    assert len(benchmark_summary.subjects[0].trials) == 2
    assert benchmark_summary.subjects[0].trials[0].artifacts.trial_result.integrity_hash
    assert result.artifacts.summary_yaml.relative_path == "runs/M-0001/BX-test-001/summary.yml"
    subject_summary = (tmp_path / "runs/M-0001/BX-test-001/subjects/T-0001/summary.md").read_text()
    assert "audit/" not in subject_summary
    assert "- Counted questions by run: trial-001=1, trial-002=2" in subject_summary
    assert (
        "- Counted questions (scoring-eligible): average `1.5` · minimum `1` · "
        "median `1.5` · maximum `2`"
    ) in subject_summary
    average_cost_line = (
        "- Average cost per terminal run (USD): Guesser `0.0100` · "
        "Oracle `0.0000` · Verifier `0.0100` · Total `0.0200`"
    )
    assert average_cost_line in subject_summary
    benchmark_report_path = tmp_path / "runs/M-0001/BX-test-001/summary.md"
    benchmark_report = benchmark_report_path.read_text(encoding="utf-8")
    assert "## Overall metrics" in benchmark_report
    assert "## Subjects" in benchmark_report
    assert average_cost_line in benchmark_report
    assert "- Total execution cost (USD): `0.0800`" in benchmark_report
    assert "| Guesser cost (USD) | 0.0100 | 0.0100 | 0.0100–0.0100 |" in benchmark_report
    assert "Each subject report links to every individual typed trial" in benchmark_report
    assert_markdown_links_resolve(benchmark_report_path)
    benchmark_summary_payload = yaml.safe_load(benchmark_summary_path.read_text(encoding="utf-8"))[
        "payload"
    ]
    with pytest.raises(ValidationError):
        BenchmarkSummaryArtifact.model_validate({**benchmark_summary_payload, "unexpected": True})
    missing_summary = dict(benchmark_summary_payload)
    missing_summary.pop("summary")
    with pytest.raises(ValidationError):
        BenchmarkSummaryArtifact.model_validate(missing_summary)
    assert store.load_benchmark_result(request.model_id, request.execution_id) == result
    assert (
        store.load_state(request.model_id, request.execution_id).terminal_trials == 4  # type: ignore[union-attr]
    )

    replacement_executor = FakeExecutor()
    resumed = BenchmarkRunner(
        store=store,
        model_catalog=models,
        benchmark_catalog=benchmark,
        subject_catalog=subjects,
        executor=replacement_executor,
    ).run(request)
    assert resumed == result
    assert replacement_executor.calls == []


def test_manifest_without_request_mode_is_rejected(
    tmp_path: Path,
) -> None:
    models, benchmark, subjects = fixtures()
    store = ArtifactStore(tmp_path)
    store._git = lambda arguments: "abc123" if arguments == ["rev-parse", "HEAD"] else ""  # type: ignore[method-assign]
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-legacy-mode-001"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        target_ids=(SubjectId("T-0001"),),
        iterations_override=1,
    )
    definition = benchmark.benchmark(
        request.benchmark_id,
        benchmark_mode=request.benchmark_mode,
        subject_ids=request.target_ids,
        iterations_override=request.iterations_override,
    )
    manifest = store.execution_manifest(
        request=request,
        definition=definition,
        model=models.model(request.model_id),
        subject_catalog_hash=subjects.content_hash(),
    )
    legacy_value = manifest.model_dump(mode="json")
    legacy_request = dict(legacy_value["request"])
    legacy_request.pop("benchmark_mode")
    legacy_value["request"] = legacy_request

    with pytest.raises(ValidationError):
        BenchmarkManifest.model_validate(legacy_value)


def test_manifest_omits_worktree_state_and_rejects_retired_metadata(
    tmp_path: Path,
) -> None:
    models, benchmark, subjects = fixtures()
    store = ArtifactStore(tmp_path)
    git_calls: list[list[str]] = []

    def git(arguments: list[str]) -> str:
        git_calls.append(arguments)
        return "abc123"

    store._git = git  # type: ignore[method-assign]
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-no-worktree-001"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.OFFICIAL,
        target_ids=(SubjectId("T-0001"),),
        iterations_override=1,
    )
    definition = benchmark.benchmark(
        request.benchmark_id,
        benchmark_mode=request.benchmark_mode,
        subject_ids=request.target_ids,
        iterations_override=request.iterations_override,
    )

    manifest = store.execution_manifest(
        request=request,
        definition=definition,
        model=models.model(request.model_id),
        subject_catalog_hash=subjects.content_hash(),
    )
    serialized = manifest.model_dump(mode="json")

    assert git_calls == [["rev-parse", "HEAD"]]
    assert "working_tree_dirty_before_run" not in serialized

    retired = {
        **serialized,
        "working_tree_dirty_before_run": True,
    }
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        BenchmarkManifest.model_validate(retired)


def test_summary_yaml_integrity_detects_tampering(tmp_path: Path) -> None:
    models, benchmark, subjects = fixtures()
    store = ArtifactStore(tmp_path)
    store._git = lambda arguments: "abc123" if arguments == ["rev-parse", "HEAD"] else ""  # type: ignore[method-assign]
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-summary-integrity-001"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        target_ids=(SubjectId("T-0001"),),
        iterations_override=1,
    )
    BenchmarkRunner(
        store=store,
        model_catalog=models,
        benchmark_catalog=benchmark,
        subject_catalog=subjects,
        executor=FakeExecutor(),
    ).run(request)
    path = tmp_path / "runs/M-0001/BX-summary-integrity-001/summary.yml"
    envelope = yaml.safe_load(path.read_text(encoding="utf-8"))
    envelope["payload"]["display_name"] = "tampered"
    path.write_text(yaml.safe_dump(envelope), encoding="utf-8")

    with pytest.raises(ArtifactIntegrityError, match="integrity hash mismatch"):
        store.load_benchmark_summary(request.model_id, request.execution_id)


def test_result_integrity_uses_validated_raw_payload_across_schema_defaults(
    tmp_path: Path,
) -> None:
    models, benchmark, subjects = fixtures()
    store = ArtifactStore(tmp_path)
    store._git = lambda arguments: (  # type: ignore[method-assign]
        "abc123" if arguments == ["rev-parse", "HEAD"] else ""
    )
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-result-schema-evolution-001"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        target_ids=(SubjectId("T-0001"),),
        iterations_override=1,
    )
    BenchmarkRunner(
        store=store,
        model_catalog=models,
        benchmark_catalog=benchmark,
        subject_catalog=subjects,
        executor=FakeExecutor(),
    ).run(request)
    path = tmp_path / "runs/M-0001/BX-result-schema-evolution-001/result.yml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["run"]["model"]["configuration"]["reasoning_control"] = "effort"
    unsigned = dict(payload)
    unsigned.pop("integrity_hash")
    unsigned["artifacts"] = dict(unsigned["artifacts"])
    unsigned["artifacts"]["result"] = dict(unsigned["artifacts"]["result"])
    unsigned["artifacts"]["result"]["integrity_hash"] = None
    integrity_hash = sha256_text(canonical_json(unsigned))
    payload["integrity_hash"] = integrity_hash
    payload["artifacts"]["result"]["integrity_hash"] = integrity_hash
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    loaded = store.load_benchmark_result(request.model_id, request.execution_id)

    assert loaded is not None
    assert loaded.integrity_hash == integrity_hash
    assert loaded.run.model.configuration.reasoning_control == "effort"


def test_runner_records_failure_and_continues(tmp_path: Path) -> None:
    models, benchmark, subjects = fixtures()
    executor = FakeExecutor(fail_first=True)
    store = ArtifactStore(tmp_path)
    store._git = lambda arguments: "abc123" if arguments == ["rev-parse", "HEAD"] else ""  # type: ignore[method-assign]
    runner = BenchmarkRunner(
        store=store,
        model_catalog=models,
        benchmark_catalog=benchmark,
        subject_catalog=subjects,
        executor=executor,
    )

    result = runner.run(
        BenchmarkRequest(
            benchmark_id=BenchmarkId("B-0001"),
            execution_id=BenchmarkExecutionId("BX-failure-001"),
            model_id=BenchmarkModelId("M-0001"),
            benchmark_mode=BenchmarkMode.EXPERIMENTAL,
            iterations_override=1,
        )
    )

    trials = tuple(subject.trials[0] for subject in result.subjects)
    assert isinstance(trials[0], InfrastructureFailedTrialResult)
    assert isinstance(trials[1], CompletedTrialResult)
    assert trials[0].failure.diagnostics is not None
    assert trials[0].failure.diagnostics.causes[0].exception_type == "RuntimeError"
    assert trials[0].failure.diagnostics.causes[0].message == "temporary provider outage"
    assert any(
        frame.module == "test_runner" and frame.function == "execute"
        for frame in trials[0].failure.diagnostics.frames
    )
    assert result.summary.counts.infrastructure_failed == 1
    assert len(executor.calls) == 2


def test_runner_preserves_typed_episode_component_failure(
    tmp_path: Path,
    caplog,
) -> None:
    models, benchmark, subjects = fixtures()
    store = ArtifactStore(tmp_path)
    store._git = lambda arguments: "abc123" if arguments == ["rev-parse", "HEAD"] else ""  # type: ignore[method-assign]
    runner = BenchmarkRunner(
        store=store,
        model_catalog=models,
        benchmark_catalog=benchmark,
        subject_catalog=subjects,
        executor=TerminalFailureExecutor(),
    )

    with caplog.at_level(logging.INFO, logger="deep20.benchmark"):
        result = runner.run(
            BenchmarkRequest(
                benchmark_id=BenchmarkId("B-0001"),
                execution_id=BenchmarkExecutionId("BX-component-failure-001"),
                model_id=BenchmarkModelId("M-0001"),
                benchmark_mode=BenchmarkMode.EXPERIMENTAL,
                target_ids=(SubjectId("T-0001"),),
                iterations_override=1,
            )
        )

    trial = result.subjects[0].trials[0]
    assert isinstance(trial, InfrastructureFailedTrialResult)
    assert trial.failure.code == "provider_request_failed"
    assert trial.failure.type == "GameProviderError"
    assert trial.failure.message == "OpenRouter request failed"
    assert str(trial.failure.call_id) == "GC-" + f"{1:032x}"
    assert result.summary.total_cost_usd == Decimal("0.02")
    assert any(
        "benchmark.failed " in record.getMessage()
        and "code=provider_request_failed" in record.getMessage()
        for record in caplog.records
    )


def test_runner_preserves_and_logs_completed_protocol_failure(
    tmp_path: Path,
    caplog,
) -> None:
    models, benchmark, subjects = fixtures()
    store = ArtifactStore(tmp_path)
    store._git = lambda arguments: "abc123" if arguments == ["rev-parse", "HEAD"] else ""  # type: ignore[method-assign]
    runner = BenchmarkRunner(
        store=store,
        model_catalog=models,
        benchmark_catalog=benchmark,
        subject_catalog=subjects,
        executor=ProtocolFailureExecutor(),
    )

    with caplog.at_level(logging.INFO, logger="deep20.benchmark"):
        result = runner.run(
            BenchmarkRequest(
                benchmark_id=BenchmarkId("B-0001"),
                execution_id=BenchmarkExecutionId("BX-protocol-failure-001"),
                model_id=BenchmarkModelId("M-0001"),
                benchmark_mode=BenchmarkMode.EXPERIMENTAL,
                target_ids=(SubjectId("T-0001"),),
                iterations_override=1,
            )
        )

    trial = result.subjects[0].trials[0]
    assert isinstance(trial, CompletedTrialResult)
    assert trial.failure is not None
    assert trial.failure.code == "invalid_guesser_output"
    assert trial.failure.type == "GuesserProtocolError"
    assert str(trial.failure.call_id) == "GC-" + f"{1:032x}"
    assert result.summary.counts.model_failed == 1
    summary = store.load_benchmark_summary(
        BenchmarkModelId("M-0001"),
        BenchmarkExecutionId("BX-protocol-failure-001"),
    )
    assert summary is not None
    assert summary.subjects[0].trials[0].failure == trial.failure
    state = store.load_state(
        BenchmarkModelId("M-0001"),
        BenchmarkExecutionId("BX-protocol-failure-001"),
    )
    assert state is not None
    assert state.last_failure == trial.failure
    messages = tuple(record.getMessage() for record in caplog.records)
    assert any(
        "benchmark.failed " in message
        and "code=invalid_guesser_output" in message
        and "latency_ms=0" in message
        for message in messages
    )
    assert any(
        "benchmark.trial " in message and "reason=guesser_protocol_failure" in message
        for message in messages
    )
    assert all("provider output did not match" not in message for message in messages)


def test_omitted_targets_expand_to_subject_catalog_order(
    tmp_path: Path,
) -> None:
    models, benchmark, subjects = fixtures()
    executor = FakeExecutor()
    store = ArtifactStore(tmp_path)
    store._git = lambda arguments: "abc123" if arguments == ["rev-parse", "HEAD"] else ""  # type: ignore[method-assign]

    result = BenchmarkRunner(
        store=store,
        model_catalog=models,
        benchmark_catalog=benchmark,
        subject_catalog=subjects,
        executor=executor,
    ).run(
        BenchmarkRequest(
            benchmark_id=BenchmarkId("B-0001"),
            execution_id=BenchmarkExecutionId("BX-all-defaults-001"),
            model_id=BenchmarkModelId("M-0001"),
            benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        )
    )

    assert result.run.model.model_id == BenchmarkModelId("M-0001")
    assert result.run.definition.subject_ids == (
        SubjectId("T-0001"),
        SubjectId("T-0002"),
    )
    assert result.run.definition.iterations == 2
    assert result.summary.counts.scheduled == 4
    assert [
        (
            str(context.identity.model_id),
            str(context.identity.target_id),
            context.identity.trial_number,
        )
        for context in executor.calls
    ] == [
        (model_id, target_id, trial)
        for model_id in ("M-0001",)
        for target_id in ("T-0001", "T-0002")
        for trial in (1, 2)
    ]


def test_model_target_and_iteration_are_bound_to_one_run(tmp_path: Path) -> None:
    models, benchmark, subjects = fixtures()
    executor = FakeExecutor()
    store = ArtifactStore(tmp_path)
    store._git = lambda arguments: "abc123" if arguments == ["rev-parse", "HEAD"] else ""  # type: ignore[method-assign]

    result = BenchmarkRunner(
        store=store,
        model_catalog=models,
        benchmark_catalog=benchmark,
        subject_catalog=subjects,
        executor=executor,
    ).run(
        BenchmarkRequest(
            benchmark_id=BenchmarkId("B-0001"),
            execution_id=BenchmarkExecutionId("BX-selected-001"),
            model_id=BenchmarkModelId("M-0002"),
            benchmark_mode=BenchmarkMode.EXPERIMENTAL,
            target_ids=(SubjectId("T-0002"),),
            iterations_override=3,
        )
    )

    assert result.run.model.model_id == BenchmarkModelId("M-0002")
    assert tuple(subject.subject.target_id for subject in result.subjects) == ("T-0002",)
    assert len(result.subjects[0].trials) == 3
    assert result.summary.counts.scheduled == 3


def test_benchmark_logs_one_combined_line_per_resolved_turn(
    tmp_path: Path,
    caplog,
) -> None:
    models, benchmark, subjects = fixtures()
    subjects = SubjectCatalog(
        version=subjects.version,
        subjects={
            "T-0001": subjects.subject("T-0001"),
            "T-0002": subjects.subject("T-0002").model_copy(
                update={"canonical_name": 'Two\n"Quoted"'}
            ),
        },
    )
    store = ArtifactStore(tmp_path)
    store._git = lambda arguments: "abc123" if arguments == ["rev-parse", "HEAD"] else ""  # type: ignore[method-assign]
    runner = BenchmarkRunner(
        store=store,
        model_catalog=models,
        benchmark_catalog=benchmark,
        subject_catalog=subjects,
        executor=FakeExecutor(emit_turn=ActionType.ASK),
    )

    with caplog.at_level(logging.INFO, logger="deep20.benchmark"):
        runner.run(
            BenchmarkRequest(
                benchmark_id=BenchmarkId("B-0001"),
                execution_id=BenchmarkExecutionId("BX-logging-001"),
                model_id=BenchmarkModelId("M-0001"),
                benchmark_mode=BenchmarkMode.EXPERIMENTAL,
                iterations_override=2,
            )
        )

    run_lines = [
        record.getMessage()
        for record in caplog.records
        if record.getMessage().startswith("benchmark.run ")
    ]
    assert len(run_lines) == 1
    assert (
        "benchmark.run execution=BX-logging-001 benchmark=B-0001 "
        'guesser_id=M-0001 guesser="First" model=openai/m-0001 provider=openai '
        in run_lines[0]
    )
    assert "model_id=" not in run_lines[0]
    turn_lines = [
        record.getMessage()
        for record in caplog.records
        if record.getMessage().startswith("benchmark.turn ")
    ]
    assert len(turn_lines) == 4
    assert turn_lines == [
        (
            'benchmark.turn turn=1 question="Was this person born before 1900?" answer=YES '
                "guesser_ms=841 guesser_cost=0.00123 oracle_ms=1842 oracle_cost=0.00613 "
                "searches=1 evidence=0 cache=30/0 attempts=2 recovered=0 exhausted=0"
        )
    ] * 4
    removed_turn_fields = (
        "trial=",
        "_cost_usd=",
        "adjudicator=",
        "adjudicator_ms=",
        "web_searches=",
        "cache_read=",
        "cache_write=",
    )
    assert all(
        removed_field not in line
        for line in turn_lines
        for removed_field in removed_turn_fields
    )
    assert runner.state.accumulated_cost_usd == Decimal("0.02") * 4
    trial_lines = [
        record.getMessage()
        for record in caplog.records
        if record.getMessage().startswith("benchmark.trial ")
    ]
    assert len(trial_lines) == 4
    assert all("cost_usd=0.0200" in line for line in trial_lines)
    assert all(not line.endswith("\n") for line in trial_lines)
    result_lines = [
        record.getMessage()
        for record in caplog.records
        if record.getMessage().startswith("benchmark.result ")
    ]
    assert len(result_lines) == 1
    assert "cost_usd=0.0800" in result_lines[0]
    context_records = [
        record
        for record in caplog.records
        if record.getMessage().startswith("benchmark.trial_context ")
    ]
    assert [record.getMessage() for record in context_records] == [
        'benchmark.trial_context trial=trial-001 target=T-0001 name="One"',
        'benchmark.trial_context trial=trial-002 target=T-0001 name="One"',
        'benchmark.trial_context trial=trial-001 target=T-0002 name="Two\\n\\"Quoted\\""',
        'benchmark.trial_context trial=trial-002 target=T-0002 name="Two\\n\\"Quoted\\""',
    ]
    assert all(
        getattr(record, BLANK_LINE_BEFORE_ATTRIBUTE, False) is True
        for record in context_records
    )
    assert all("\n" not in record.getMessage() for record in context_records)
    block_lines = [
        record.getMessage()
        for record in caplog.records
        if record.getMessage().startswith(
            ("benchmark.trial_context ", "benchmark.turn ", "benchmark.trial ")
        )
    ]
    assert [
        line.split(" ", maxsplit=1)[0] for line in block_lines
    ] == ["benchmark.trial_context", "benchmark.turn", "benchmark.trial"] * 4
    assert not any(
        record.getMessage().startswith("benchmark.subject ") for record in caplog.records
    )
    assert not any(
        record.getMessage().startswith(
            ("oracle.call ", "guesser.call ", "validator.call ", "game.result ")
        )
        for record in caplog.records
    )


def test_benchmark_trial_log_reports_cumulative_progress_costs_and_questions(
    tmp_path: Path,
    caplog,
) -> None:
    models, benchmark, subjects = fixtures()
    store = ArtifactStore(tmp_path)
    store._git = lambda arguments: "abc123" if arguments == ["rev-parse", "HEAD"] else ""  # type: ignore[method-assign]
    executor = FakeExecutor(include_quality_costs=True)
    runner = BenchmarkRunner(
        store=store,
        model_catalog=models,
        benchmark_catalog=benchmark,
        subject_catalog=subjects,
        executor=executor,
    )

    with caplog.at_level(logging.INFO, logger="deep20.benchmark"):
        result = runner.run(
            BenchmarkRequest(
                benchmark_id=BenchmarkId("B-0001"),
                execution_id=BenchmarkExecutionId("BX-progress-logging-001"),
                model_id=BenchmarkModelId("M-0001"),
                benchmark_mode=BenchmarkMode.EXPERIMENTAL,
                iterations_override=2,
            )
        )

    trial_lines = [
        record.getMessage()
        for record in caplog.records
        if record.getMessage().startswith("benchmark.trial ")
    ]
    assert len(trial_lines) == 4
    expected_progress = (
        (
            "progress=25.00%",
            "total_cost_usd=0.0900",
            "oracle_cost_usd=0.0200",
            "guesser_cost_usd=0.0100",
            "judge_cost_usd=0.0300",
            "reviewer_cost_usd=0.0200",
            "total_questions=1",
            "avg_questions_per_trial=1.0",
        ),
        (
            "progress=50.00%",
            "total_cost_usd=0.1800",
            "oracle_cost_usd=0.0400",
            "guesser_cost_usd=0.0200",
            "judge_cost_usd=0.0600",
            "reviewer_cost_usd=0.0400",
            "total_questions=3",
            "avg_questions_per_trial=1.5",
        ),
        (
            "progress=75.00%",
            "total_cost_usd=0.2700",
            "oracle_cost_usd=0.0600",
            "guesser_cost_usd=0.0300",
            "judge_cost_usd=0.0900",
            "reviewer_cost_usd=0.0600",
            "total_questions=4",
            "avg_questions_per_trial=1.3",
        ),
        (
            "progress=100.00%",
            "total_cost_usd=0.3600",
            "oracle_cost_usd=0.0800",
            "guesser_cost_usd=0.0400",
            "judge_cost_usd=0.1200",
            "reviewer_cost_usd=0.0800",
            "total_questions=6",
            "avg_questions_per_trial=1.5",
        ),
    )
    for line, expected_fields in zip(trial_lines, expected_progress, strict=True):
        assert all(field in line for field in expected_fields)
        assert re.search(r" elapsed=(?:\d+d)?\d{2}:\d{2}:\d{2} ", line)
        assert re.search(
            r' eta="\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [^"]+"$',
            line,
        )

    # Progress reporting is post-trial control-plane data. It is not executor input
    # and therefore cannot enter a later Guesser request or cache namespace.
    executor_inputs = canonical_json(
        [context.model_dump(mode="json") for context in executor.calls]
    )
    for private_progress_field in (
        "progress",
        "total_cost_usd",
        "oracle_cost_usd",
        "guesser_cost_usd",
        "judge_cost_usd",
        "reviewer_cost_usd",
        "total_questions",
        "avg_questions_per_trial",
        "eta",
    ):
        assert f'"{private_progress_field}":' not in executor_inputs
    guesser_conversations = canonical_json(
        [
            message.model_dump(mode="json")
            for subject_result in result.subjects
            for trial in subject_result.trials
            if isinstance(trial, CompletedTrialResult)
            for message in trial.result.guesser_conversation
        ]
    )
    assert all(
        f'"{field}":' not in guesser_conversations
        for field in ("total_cost_usd", "total_questions", "avg_questions_per_trial", "eta")
    )


def test_active_elapsed_time_excludes_downtime_before_resume() -> None:
    execution_id = BenchmarkExecutionId("BX-active-time-001")
    model_id = BenchmarkModelId("M-0001")
    events = (
        BenchmarkStartedEvent(
            event_id=BenchmarkEventId("BE-" + ("1" * 32)),
            execution_id=execution_id,
            recorded_at="2026-07-27T10:00:00+00:00",
        ),
        ModelStartedEvent(
            event_id=BenchmarkEventId("BE-" + ("2" * 32)),
            execution_id=execution_id,
            model_id=model_id,
            recorded_at="2026-07-27T10:05:00+00:00",
        ),
        ExecutionResumedEvent(
            event_id=BenchmarkEventId("BE-" + ("3" * 32)),
            execution_id=execution_id,
            model_id=model_id,
            operation="repair",
            git_commit="def456",
            repair_policy=TrialRepairPolicy(),
            recorded_at="2026-07-28T10:00:00+00:00",
        ),
        ModelStartedEvent(
            event_id=BenchmarkEventId("BE-" + ("4" * 32)),
            execution_id=execution_id,
            model_id=model_id,
            recorded_at="2026-07-28T10:02:00+00:00",
        ),
    )

    assert (
        BenchmarkRunner._active_elapsed_ms(
            events,
            "2026-07-28T10:03:00+00:00",
        )
        == 8 * 60 * 1_000
    )


def test_benchmark_turn_log_names_guess_validator_metrics(
    tmp_path: Path,
    caplog,
) -> None:
    models, benchmark, subjects = fixtures()
    store = ArtifactStore(tmp_path)
    store._git = lambda arguments: "abc123" if arguments == ["rev-parse", "HEAD"] else ""  # type: ignore[method-assign]
    runner = BenchmarkRunner(
        store=store,
        model_catalog=models,
        benchmark_catalog=benchmark,
        subject_catalog=subjects,
        executor=FakeExecutor(emit_turn=ActionType.GUESS),
    )

    with caplog.at_level(logging.INFO, logger="deep20.benchmark"):
        runner.run(
            BenchmarkRequest(
                benchmark_id=BenchmarkId("B-0001"),
                execution_id=BenchmarkExecutionId("BX-guess-logging-001"),
                model_id=BenchmarkModelId("M-0001"),
                benchmark_mode=BenchmarkMode.EXPERIMENTAL,
                target_ids=(SubjectId("T-0001"),),
                iterations_override=1,
            )
        )

    turn_lines = [
        record.getMessage()
        for record in caplog.records
        if record.getMessage().startswith("benchmark.turn ")
    ]
    assert turn_lines == [
        (
                'benchmark.turn turn=1 guess="One" answer=YES guesser_ms=841 '
                "guesser_cost=0.00123 validator_ms=442 validator_cost=0.00073 "
                "searches=0 evidence=0 cache=24/3 attempts=2 recovered=0 exhausted=0"
        )
    ]
    assert "oracle_ms=" not in turn_lines[0]
    assert "oracle_cost=" not in turn_lines[0]


def test_benchmark_persists_and_reports_recovered_contract_violation(
    tmp_path: Path,
    caplog,
) -> None:
    models, benchmark, subjects = fixtures()
    store = ArtifactStore(tmp_path)
    store._git = lambda arguments: "abc123" if arguments == ["rev-parse", "HEAD"] else ""  # type: ignore[method-assign]
    runner = BenchmarkRunner(
        store=store,
        model_catalog=models,
        benchmark_catalog=benchmark,
        subject_catalog=subjects,
        executor=FakeExecutor(emit_contract_violation=True),
    )

    with caplog.at_level(logging.INFO, logger="deep20.benchmark"):
        result = runner.run(
            BenchmarkRequest(
                benchmark_id=BenchmarkId("B-0001"),
                execution_id=BenchmarkExecutionId("BX-contract-logging-001"),
                model_id=BenchmarkModelId("M-0001"),
                benchmark_mode=BenchmarkMode.EXPERIMENTAL,
                target_ids=(SubjectId("T-0001"),),
                iterations_override=1,
            )
        )

    assert result.summary.contract.status == "breached"
    assert result.summary.contract.violations == 1
    assert result.summary.contract.counted_penalties == 1
    turn_lines = [
        record.getMessage()
        for record in caplog.records
        if record.getMessage().startswith("benchmark.turn ")
    ]
    assert turn_lines == [
        (
            "benchmark.turn turn=1 contract_violation=invalid_action counted=True "
            "questions=1 guesser_ms=841 guesser_cost=0.00123 cache=20/0 attempts=1"
        )
    ]
    events = [
        json.loads(line)
        for line in (
            tmp_path
            / "runs/M-0001/BX-contract-logging-001/benchmark-events.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert sum(event["event_type"] == "contract_violation" for event in events) == 1
    report = (
        tmp_path / "runs/M-0001/BX-contract-logging-001/summary.md"
    ).read_text(encoding="utf-8")
    assert "Output-contract reliability: `breached`" in report
    assert "1 violation(s) across 1 trial(s)" in report


def test_resume_marks_started_trial_interrupted_and_runs_only_unstarted_trials(
    tmp_path: Path,
    caplog,
) -> None:
    models, benchmark, subjects = fixtures()
    store = ArtifactStore(tmp_path)
    store._git = lambda arguments: "abc123" if arguments == ["rev-parse", "HEAD"] else ""  # type: ignore[method-assign]
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-resume-001"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        iterations_override=2,
    )

    with pytest.raises(KeyboardInterrupt):
        BenchmarkRunner(
            store=store,
            model_catalog=models,
            benchmark_catalog=benchmark,
            subject_catalog=subjects,
            executor=FakeExecutor(interrupt_call=2),
        ).run(request)

    resumed_executor = FakeExecutor()
    caplog.clear()
    with caplog.at_level(logging.INFO, logger="deep20.benchmark"):
        result = BenchmarkRunner(
            store=store,
            model_catalog=models,
            benchmark_catalog=benchmark,
            subject_catalog=subjects,
            executor=resumed_executor,
        ).run(request)

    completed_before_resume = result.subjects[0].trials[0]
    interrupted_on_resume = result.subjects[0].trials[1]
    assert isinstance(completed_before_resume, CompletedTrialResult)
    assert isinstance(interrupted_on_resume, InfrastructureFailedTrialResult)
    assert interrupted_on_resume.failure.code == "interrupted_trial"
    assert all(
        isinstance(trial, CompletedTrialResult) for trial in result.subjects[1].trials
    )
    assert len(resumed_executor.calls) == 2
    context_lines = [
        record.getMessage()
        for record in caplog.records
        if record.getMessage().startswith("benchmark.trial_context ")
    ]
    assert context_lines == [
        'benchmark.trial_context trial=trial-002 target=T-0001 name="One"',
        'benchmark.trial_context trial=trial-001 target=T-0002 name="Two"',
        'benchmark.trial_context trial=trial-002 target=T-0002 name="Two"',
    ]
    state = store.load_state(request.model_id, request.execution_id)
    assert state is not None
    assert state.started_trials == 4
    assert state.terminal_trials == 4
    events = [
        json.loads(line)
        for line in (tmp_path / "runs/M-0001/BX-resume-001/benchmark-events.jsonl")
        .read_text()
        .splitlines()
    ]
    first_trial_starts = [
        event
        for event in events
        if event["event_type"] == "trial_started"
        and event["identity"]["target_id"] == "T-0001"
        and event["identity"]["trial_id"] == "trial-002"
    ]
    assert len(first_trial_starts) == 1


class AlwaysFailingExecutor(FakeExecutor):
    def execute(
        self,
        context: TrialExecutionContext,
        sink: BenchmarkTrialSink,
        observer: ExecutionObserver,
    ) -> EpisodeResult:
        self.calls.append(context)
        raise RuntimeError("persistent provider outage")


class SucceedOnceThenAlwaysFailExecutor(TerminalFailureExecutor):
    def execute(
        self,
        context: TrialExecutionContext,
        sink: BenchmarkTrialSink,
        observer: ExecutionObserver,
    ) -> EpisodeResult:
        if not self.calls:
            return FakeExecutor.execute(self, context, sink, observer)
        return TerminalFailureExecutor.execute(self, context, sink, observer)


class StateCheckingExecutor(FakeExecutor):
    def __init__(
        self,
        model_id: BenchmarkModelId,
        execution_id: BenchmarkExecutionId,
    ) -> None:
        super().__init__()
        self.model_id = model_id
        self.execution_id = execution_id
        self.store: ArtifactStore | None = None
        self.observed_statuses: list[str] = []
        self.observed_summary_statuses: list[str] = []

    def execute(
        self,
        context: TrialExecutionContext,
        sink: BenchmarkTrialSink,
        observer: ExecutionObserver,
    ) -> EpisodeResult:
        assert self.store is not None
        state = self.store.load_state(self.model_id, self.execution_id)
        assert state is not None
        self.observed_statuses.append(state.status.value)
        summary = (
            self.store.run_root(self.model_id, self.execution_id) / "summary.md"
        ).read_text(encoding="utf-8")
        summary_status = re.search(r"^- Status: `([^`]+)`$", summary, re.MULTILINE)
        assert summary_status is not None
        self.observed_summary_statuses.append(summary_status.group(1))
        return super().execute(context, sink, observer)


class TurnThenInterruptExecutor(FakeExecutor):
    def __init__(self) -> None:
        super().__init__(
            emit_turn=ActionType.ASK,
            include_turn_quality_costs=True,
        )

    def execute(
        self,
        context: TrialExecutionContext,
        sink: BenchmarkTrialSink,
        observer: ExecutionObserver,
    ) -> EpisodeResult:
        super().execute(context, sink, observer)
        raise KeyboardInterrupt


def _runner(tmp_path: Path, executor: FakeExecutor) -> tuple[BenchmarkRunner, ArtifactStore]:
    models, benchmark, subjects = fixtures()
    store = ArtifactStore(tmp_path)
    store._git = lambda arguments: "abc123" if arguments == ["rev-parse", "HEAD"] else ""  # type: ignore[method-assign]
    runner = BenchmarkRunner(
        store=store,
        model_catalog=models,
        benchmark_catalog=benchmark,
        subject_catalog=subjects,
        executor=executor,
    )
    return runner, store


def test_repair_reruns_only_infrastructure_failed_trials(tmp_path: Path) -> None:
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-repair-001"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        iterations_override=1,
    )
    runner, store = _runner(tmp_path, FakeExecutor(fail_first=True))
    first = runner.run(request)
    assert first.outcome.has_infrastructure_failures is True
    failed_trial = first.subjects[0].trials[0]
    assert isinstance(failed_trial, InfrastructureFailedTrialResult)
    failed_state = store.load_state(request.model_id, request.execution_id)
    assert failed_state is not None
    assert failed_state.status is ExecutionStatus.FAILED

    repair_executor = FakeExecutor()
    repaired_runner, _ = _runner(tmp_path, repair_executor)
    repaired = repaired_runner.run(request, repair=TrialRepairPolicy())

    assert repaired.outcome.has_infrastructure_failures is False
    assert all(
        isinstance(trial, CompletedTrialResult)
        for subject in repaired.subjects
        for trial in subject.trials
    )
    assert len(repair_executor.calls) == 1
    assert repair_executor.calls[0].subject.target_id == "T-0001"
    assert (
        repair_executor.calls[0].identity.episode_run_id == failed_trial.identity.episode_run_id
    )
    state = store.load_state(request.model_id, request.execution_id)
    assert state is not None
    assert state.started_trials == 2
    assert state.terminal_trials == 2


def test_repair_retains_superseded_failure_metrics_in_execution_cost(
    tmp_path: Path,
) -> None:
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-repair-accounting-001"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        target_ids=(SubjectId("T-0001"),),
        iterations_override=1,
    )
    runner, _store = _runner(tmp_path, TerminalFailureExecutor())
    original = runner.run(request)
    assert original.summary.total_cost_usd == Decimal("0.02")

    repair_executor = StateCheckingExecutor(request.model_id, request.execution_id)
    repaired_runner, repaired_store = _runner(tmp_path, repair_executor)
    repair_executor.store = repaired_store
    repaired_store._git = (  # type: ignore[method-assign]
        lambda arguments: "def456" if arguments == ["rev-parse", "HEAD"] else ""
    )
    repaired = repaired_runner.run(request, repair=TrialRepairPolicy())

    trial = repaired.subjects[0].trials[0]
    assert isinstance(trial, CompletedTrialResult)
    assert len(trial.superseded_attempts) == 1
    attempt = trial.superseded_attempts[0]
    assert attempt.attempt_number == 1
    assert attempt.failure.code == "provider_request_failed"
    assert attempt.partial_metrics.cost_usd == Decimal("0.02")
    assert attempt.partial_metrics.tokens == 200
    assert repaired.summary.repair.superseded_attempts == 1
    assert repaired.summary.repair.affected_trials == 1
    assert repaired.summary.repair.partial_metrics.cost_usd == Decimal("0.02")
    assert repaired.summary.repair.partial_metrics.tokens == 200
    assert repaired.summary.total_cost_usd == Decimal("0.04")
    assert repaired.run.git_commits == ("abc123", "def456")
    reloaded = repaired_store.load_benchmark_result(
        request.model_id,
        request.execution_id,
    )
    assert reloaded == repaired
    report = (
        tmp_path / "runs/M-0001/BX-repair-accounting-001/summary.md"
    ).read_text(encoding="utf-8")
    assert (
        "- Superseded infrastructure attempts: 1 across 1 trial(s) · "
        "cost `0.0200` USD"
    ) in report
    assert "- Total execution cost (USD): `0.0400`" in report


def test_repair_recovers_legacy_superseded_quality_costs_from_signed_events(
    tmp_path: Path,
) -> None:
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-repair-legacy-quality-001"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        target_ids=(SubjectId("T-0001"),),
        iterations_override=1,
    )
    original_runner, store = _runner(
        tmp_path,
        TerminalFailureExecutor(
            emit_turn=ActionType.ASK,
            include_quality_costs=True,
            include_turn_quality_costs=True,
        ),
    )
    original = original_runner.run(request)
    original_trial = original.subjects[0].trials[0]
    assert isinstance(original_trial, InfrastructureFailedTrialResult)
    store.write_trial_result(
        original_trial.model_copy(
            update={
                "partial_metrics": original_trial.partial_metrics.model_copy(
                    update={
                        "reviewer_cost_usd": Decimal(0),
                        "judge_cost_usd": Decimal(0),
                    }
                )
            }
        )
    )
    events_path = (
        tmp_path
        / "runs/M-0001/BX-repair-legacy-quality-001/benchmark-events.jsonl"
    )
    legacy_lines = [
        line
        for line in events_path.read_text(encoding="utf-8").splitlines()
        if json.loads(line)["event_type"] != "trial_metrics_resolved"
    ]
    events_path.write_text("\n".join(legacy_lines) + "\n", encoding="utf-8")

    repair_executor = FakeExecutor()
    repaired_runner, _ = _runner(tmp_path, repair_executor)
    repaired = repaired_runner.run(request, repair=TrialRepairPolicy())
    repaired_trial = repaired.subjects[0].trials[0]

    assert isinstance(repaired_trial, CompletedTrialResult)
    superseded = repaired_trial.superseded_attempts[0]
    assert superseded.partial_metrics.oracle_cost_usd == Decimal("0.07")
    assert superseded.partial_metrics.reviewer_cost_usd == Decimal("0.001")
    assert superseded.partial_metrics.judge_cost_usd == Decimal("0.002")
    assert repaired.summary.repair.partial_metrics.reviewer_cost_usd == Decimal(
        "0.001"
    )
    assert repaired.summary.repair.partial_metrics.judge_cost_usd == Decimal("0.002")
    visible_context = canonical_json(repair_executor.calls[0].model_dump(mode="json"))
    assert "reviewer_cost_usd" not in visible_context
    assert "judge_cost_usd" not in visible_context


def test_interrupted_repair_retains_each_attempt_and_its_metrics(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-repair-interrupted-001"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        target_ids=(SubjectId("T-0001"),),
        iterations_override=1,
    )
    original_runner, store = _runner(tmp_path, TerminalFailureExecutor())
    original = original_runner.run(request)
    identity = original.subjects[0].trials[0].identity

    interrupted_runner, _ = _runner(tmp_path, TurnThenInterruptExecutor())
    with pytest.raises(KeyboardInterrupt):
        interrupted_runner.run(request, repair=TrialRepairPolicy())

    final_executor = FakeExecutor()
    final_runner, _ = _runner(tmp_path, final_executor)
    caplog.clear()
    with caplog.at_level(logging.INFO, logger="deep20.benchmark"):
        final = final_runner.run(request, repair=TrialRepairPolicy())
    trial = final.subjects[0].trials[0]

    assert isinstance(trial, CompletedTrialResult)
    assert trial.attempt_number == 3
    assert [attempt.attempt_number for attempt in trial.superseded_attempts] == [1, 2]
    assert [attempt.failure.code for attempt in trial.superseded_attempts] == [
        "provider_request_failed",
        "interrupted_trial",
    ]
    assert [attempt.partial_metrics.cost_usd for attempt in trial.superseded_attempts] == [
        Decimal("0.02"),
        Decimal("0.0073664099999999995"),
    ]
    assert [
        attempt.partial_metrics.reviewer_cost_usd
        for attempt in trial.superseded_attempts
    ] == [Decimal(0), Decimal("0.001")]
    assert [
        attempt.partial_metrics.judge_cost_usd
        for attempt in trial.superseded_attempts
    ] == [Decimal(0), Decimal("0.002")]
    assert store.trial_event_count(identity, "trial_started") == 3
    assert store.trial_event_count(identity, "trial_finished") == 3
    assert final.summary.repair.superseded_attempts == 2
    assert final.summary.repair.partial_metrics.reviewer_cost_usd == Decimal("0.001")
    assert final.summary.repair.partial_metrics.judge_cost_usd == Decimal("0.002")
    assert final.summary.total_cost_usd == Decimal("0.04736641")
    state = store.load_state(request.model_id, request.execution_id)
    assert state is not None
    assert state.accumulated_cost_usd == Decimal("0.0473664099999999995")
    repair_trial_line = next(
        record.getMessage()
        for record in caplog.records
        if record.getMessage().startswith("benchmark.trial ")
    )
    assert "oracle_cost_usd=0.0031" in repair_trial_line
    assert "reviewer_cost_usd=0.0010" in repair_trial_line
    assert "judge_cost_usd=0.0020" in repair_trial_line
    visible_context = canonical_json(final_executor.calls[0].model_dump(mode="json"))
    for private_repair_value in (
        "provider_request_failed",
        "interrupted_trial",
        "superseded_attempts",
        "reviewer_cost_usd",
        "judge_cost_usd",
    ):
        assert private_repair_value not in visible_context


def test_repair_rejects_a_result_without_its_start_event_before_writing(
    tmp_path: Path,
) -> None:
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-repair-missing-start-001"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        target_ids=(SubjectId("T-0001"),),
        iterations_override=1,
    )
    runner, _ = _runner(tmp_path, TerminalFailureExecutor())
    runner.run(request)
    events_path = (
        tmp_path
        / "runs/M-0001/BX-repair-missing-start-001/benchmark-events.jsonl"
    )
    retained_lines = [
        line
        for line in events_path.read_text(encoding="utf-8").splitlines()
        if json.loads(line)["event_type"] != "trial_started"
    ]
    events_path.write_text("\n".join(retained_lines) + "\n", encoding="utf-8")
    before_repair = events_path.read_text(encoding="utf-8")

    repair_runner, _ = _runner(tmp_path, FakeExecutor())
    with pytest.raises(
        ArtifactIntegrityError,
        match="trial result attempt has no durable start event",
    ):
        repair_runner.run(request, repair=TrialRepairPolicy())

    assert events_path.read_text(encoding="utf-8") == before_repair


def test_run_reconciles_stale_state_from_events_and_results(tmp_path: Path) -> None:
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-reconcile-state-001"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        target_ids=(SubjectId("T-0001"),),
        iterations_override=1,
    )
    runner, store = _runner(tmp_path, FakeExecutor())
    result = runner.run(request)
    state = store.load_state(request.model_id, request.execution_id)
    assert state is not None
    store.write_state(
        state.model_copy(
            update={
                "status": ExecutionStatus.RUNNING,
                "started_trials": 0,
                "terminal_trials": 0,
                "accumulated_cost_usd": Decimal(0),
            }
        )
    )

    resumed_runner, _ = _runner(tmp_path, FakeExecutor())
    assert resumed_runner.run(request) == result
    reconciled = store.load_state(request.model_id, request.execution_id)
    assert reconciled is not None
    assert reconciled.status.value == "completed"
    assert reconciled.started_trials == 1
    assert reconciled.terminal_trials == 1
    assert reconciled.accumulated_cost_usd == Decimal("0.02")


def test_execution_lock_rejects_a_second_writer(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    with (
        store.execution_lock("M-0001", "BX-locked-001"),
        pytest.raises(BenchmarkExecutionLocked),
        store.execution_lock("M-0001", "BX-locked-001"),
    ):
        pass


def test_event_queries_and_appends_reuse_one_verified_log(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-event-cache-001"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        target_ids=(SubjectId("T-0001"),),
        iterations_override=1,
    )
    runner, _ = _runner(tmp_path, FakeExecutor())
    result = runner.run(request)
    identity = result.subjects[0].trials[0].identity
    store = ArtifactStore(tmp_path)
    verification_calls = 0
    verify_signed = artifacts_module._verify_signed

    def counting_verify(payload: dict[str, object], label: str) -> None:
        nonlocal verification_calls
        verification_calls += 1
        verify_signed(payload, label)

    monkeypatch.setattr(artifacts_module, "_verify_signed", counting_verify)
    existing_events = store.load_events(request.model_id, request.execution_id)
    initial_verification_calls = verification_calls
    assert initial_verification_calls == len(existing_events)

    assert store.trial_event_count(identity, "trial_started") == 1
    assert store.trial_attempt_event_recorded(
        identity,
        "trial_finished",
        1,
    )
    store.append_event(
        request.model_id,
        request.execution_id,
        SubjectStartedEvent(
            event_id=BenchmarkEventId("BE-" + ("f" * 32)),
            execution_id=request.execution_id,
            model_id=request.model_id,
            target_id=SubjectId("T-0001"),
            recorded_at="2026-07-28T10:00:00+00:00",
        ),
    )
    assert len(store.load_events(request.model_id, request.execution_id)) == (
        len(existing_events) + 1
    )
    assert verification_calls == initial_verification_calls


def test_repair_without_infrastructure_failures_returns_existing_result(
    tmp_path: Path,
) -> None:
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-repair-002"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        iterations_override=1,
    )
    runner, _store = _runner(tmp_path, FakeExecutor())
    original = runner.run(request)

    repair_executor = FakeExecutor()
    repaired_runner, _ = _runner(tmp_path, repair_executor)
    repaired = repaired_runner.run(request, repair=TrialRepairPolicy())

    assert repaired == original
    assert repair_executor.calls == []


def test_repair_respects_the_per_trial_attempt_cap(tmp_path: Path) -> None:
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-repair-003"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        target_ids=(SubjectId("T-0001"),),
        iterations_override=1,
    )
    runner, _store = _runner(tmp_path, AlwaysFailingExecutor())
    first = runner.run(request)
    assert first.outcome.has_infrastructure_failures is True

    capped_executor = FakeExecutor()
    capped_runner, _ = _runner(tmp_path, capped_executor)
    capped = capped_runner.run(
        request,
        repair=TrialRepairPolicy(max_attempts_per_trial=1),
    )

    assert capped_executor.calls == []
    assert capped.outcome.has_infrastructure_failures is True

    second_executor = AlwaysFailingExecutor()
    second_runner, _ = _runner(tmp_path, second_executor)
    second = second_runner.run(request, repair=TrialRepairPolicy(max_attempts_per_trial=2))
    assert len(second_executor.calls) == 1
    assert second.outcome.has_infrastructure_failures is True

    third_executor = FakeExecutor()
    third_runner, _ = _runner(tmp_path, third_executor)
    third_runner.run(request, repair=TrialRepairPolicy(max_attempts_per_trial=2))
    assert third_executor.calls == []


def test_circuit_breaker_aborts_after_consecutive_infrastructure_failures(
    tmp_path: Path,
) -> None:
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-breaker-001"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        iterations_override=2,
    )
    executor = AlwaysFailingExecutor()
    runner, store = _runner(tmp_path, executor)

    with pytest.raises(BenchmarkCircuitBreakerOpen) as excinfo:
        runner.run(
            request,
            circuit_breaker=InfrastructureCircuitBreaker(
                max_consecutive_infrastructure_failures=2,
            ),
        )

    assert excinfo.value.code == "infrastructure_circuit_breaker_open"
    assert len(executor.calls) == 2
    state = store.load_state(request.model_id, request.execution_id)
    assert state is not None
    assert state.status.value == "failed"
    assert state.terminal_trials == 2
    assert store.load_benchmark_result(request.model_id, request.execution_id) is None
    summary = (
        tmp_path / "runs/M-0001/BX-breaker-001/summary.md"
    ).read_text(encoding="utf-8")
    assert "- Status: `failed`" in summary
    assert "- Progress: 2/4 terminal trials" in summary


def test_repair_completes_an_execution_aborted_by_the_circuit_breaker(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-breaker-repair-001"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        iterations_override=2,
    )
    failing_executor = SucceedOnceThenAlwaysFailExecutor()
    runner, store = _runner(tmp_path, failing_executor)
    with pytest.raises(BenchmarkCircuitBreakerOpen):
        runner.run(
            request,
            circuit_breaker=InfrastructureCircuitBreaker(
                max_consecutive_infrastructure_failures=2,
            ),
        )
    assert len(failing_executor.calls) == 3
    completed_identity = failing_executor.calls[0].identity
    failed_identities = [context.identity for context in failing_executor.calls[1:]]
    assert store.load_benchmark_result(request.model_id, request.execution_id) is None

    repair_executor = StateCheckingExecutor(request.model_id, request.execution_id)
    repaired_runner, repaired_store = _runner(tmp_path, repair_executor)
    repair_executor.store = repaired_store
    repaired_store._git = (  # type: ignore[method-assign]
        lambda arguments: "def456" if arguments == ["rev-parse", "HEAD"] else ""
    )
    caplog.clear()
    with caplog.at_level(logging.INFO, logger="deep20.benchmark"):
        repaired = repaired_runner.run(
            request,
            repair=TrialRepairPolicy(),
            circuit_breaker=InfrastructureCircuitBreaker(),
        )

    assert repaired.outcome.complete is True
    assert repaired.outcome.has_infrastructure_failures is False
    assert all(
        isinstance(trial, CompletedTrialResult)
        for subject in repaired.subjects
        for trial in subject.trials
    )
    assert len(repair_executor.calls) == 3
    assert repair_executor.observed_statuses == ["running", "running", "running"]
    assert repair_executor.observed_summary_statuses == [
        "running",
        "running",
        "running",
    ]
    repaired_identities = [context.identity for context in repair_executor.calls]
    assert repaired_identities[:2] == failed_identities
    assert completed_identity not in repaired_identities
    assert len(set(repaired_identities)) == 3
    for context in repair_executor.calls:
        visible_context = canonical_json(context.model_dump(mode="json"))
        assert "OpenRouter request failed" not in visible_context
        assert "superseded_attempts" not in visible_context
    assert repaired.run.git_commits == ("abc123", "def456")
    repaired_failures = tuple(
        attempt
        for subject in repaired.subjects
        for trial in subject.trials
        for attempt in trial.superseded_attempts
    )
    assert len(repaired_failures) == 2
    assert all(attempt.attempt_number == 1 for attempt in repaired_failures)
    assert all(
        attempt.failure.message == "OpenRouter request failed"
        for attempt in repaired_failures
    )
    assert repaired.summary.repair.superseded_attempts == 2
    assert repaired.summary.repair.affected_trials == 2
    repaired_trial_lines = [
        record.getMessage()
        for record in caplog.records
        if record.getMessage().startswith("benchmark.trial ")
    ]
    assert len(repaired_trial_lines) == 3
    assert "progress=75.00%" in repaired_trial_lines[0]
    assert "total_cost_usd=0.0800" in repaired_trial_lines[0]
    assert "progress=75.00%" in repaired_trial_lines[1]
    assert "total_cost_usd=0.1000" in repaired_trial_lines[1]
    assert "progress=100.00%" in repaired_trial_lines[2]
    assert "total_cost_usd=0.1200" in repaired_trial_lines[2]
    state = repaired_store.load_state(request.model_id, request.execution_id)
    assert state is not None
    assert state.status.value == "completed"
    assert state.started_trials == 4
    assert state.terminal_trials == 4
    assert state.accumulated_cost_usd == Decimal("0.12")
    assert state.last_failure is None
    for identity in failed_identities:
        assert repaired_store.trial_event_count(identity, "trial_started") == 2
    assert repaired_store.trial_event_count(completed_identity, "trial_started") == 1
    events = [
        json.loads(line)
        for line in (
            tmp_path
            / "runs/M-0001/BX-breaker-repair-001/benchmark-events.jsonl"
        ).read_text(encoding="utf-8").splitlines()
    ]
    resume_events = [
        event for event in events if event["event_type"] == "execution_resumed"
    ]
    assert len(resume_events) == 1
    assert resume_events[0]["operation"] == "repair"
    assert resume_events[0]["git_commit"] == "def456"


def test_circuit_breaker_resets_on_a_scoring_eligible_trial(tmp_path: Path) -> None:
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-breaker-002"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        iterations_override=1,
    )
    runner, store = _runner(tmp_path, FakeExecutor(fail_first=True))

    result = runner.run(
        request,
        circuit_breaker=InfrastructureCircuitBreaker(
            max_consecutive_infrastructure_failures=2,
        ),
    )

    assert result.summary.counts.infrastructure_failed == 1
    assert result.summary.counts.successful == 1
    state = store.load_state(request.model_id, request.execution_id)
    assert state is not None
    assert state.status is ExecutionStatus.FAILED
