"""Replay recorded ASK actions through an injected Oracle, without a game or Guesser."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal, Protocol

from deep20_game.models import ActionTurnResult, TurnAdjudication
from deep20_oracle.cache_contract import oracle_contract_hash
from deep20_oracle.config import OracleConfig, validate_prompt_profiles
from deep20_oracle.errors import AuditWriteError, OracleError
from deep20_oracle.models import (
    RUN_ID_PATTERN,
    OracleAdjudication,
    OracleAnswer,
    OracleCall,
    OracleMetrics,
    OracleRequest,
    OracleResult,
    OracleRole,
    ProviderResultAudit,
    StrictModel,
    Subject,
)
from deep20_oracle.result_audit import provider_result_audit
from deep20_oracle.util import canonical_json, sha256_text, timestamp
from pydantic import ConfigDict, Field, model_validator

from .models import (
    BenchmarkExecutionId,
    BenchmarkId,
    BenchmarkModelId,
    BenchmarkResult,
    SubjectId,
    TrialId,
    TrialIdentity,
)


class ReplayInputError(ValueError):
    """A fixed, console-safe explanation of an invalid replay context."""


class ReplaySelection(StrictModel):
    targets: tuple[SubjectId, ...] = ()
    trials: tuple[TrialId, ...] = ()
    turns: tuple[int, ...] = ()
    limit: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def valid_filters(self) -> ReplaySelection:
        if any(number < 1 for number in self.turns):
            raise ReplayInputError("turns must be positive")
        for values in (self.targets, self.trials, self.turns):
            if len(values) != len(set(values)):
                raise ReplayInputError("replay filters must be unique")
        return self


class ReplayCase(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=False)
    identity: TrialIdentity
    turn_number: int = Field(ge=1)
    subject: Subject
    question: str = Field(min_length=1, max_length=1_000)
    previous: TurnAdjudication

    @model_validator(mode="after")
    def matching_subject(self) -> ReplayCase:
        if self.subject.target_id != str(self.identity.target_id):
            raise ReplayInputError("replay subject must match trial identity")
        if self.previous.component != "oracle":
            raise ReplayInputError("replay baseline must be an Oracle adjudication")
        return self


class ReplayPlan(StrictModel):
    schema_version: Literal[1] = 1
    run_id: str = Field(pattern=RUN_ID_PATTERN)
    source_execution_id: BenchmarkExecutionId
    source_model_id: BenchmarkModelId
    source_benchmark_id: BenchmarkId
    source_integrity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_oracle_configuration: OracleConfig
    oracle_configuration: OracleConfig
    oracle_contract_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    selection: ReplaySelection
    source_ask_count: int = Field(ge=0)
    source_trials_without_transcript: int = Field(ge=0)
    cases: tuple[ReplayCase, ...] = Field(min_length=1)

    def content_hash(self) -> str:
        return sha256_text(canonical_json(self.model_dump(mode="json")))


def build_replay_plan(
    source: BenchmarkResult,
    config: OracleConfig,
    *,
    run_id: str,
    selection: ReplaySelection,
) -> ReplayPlan:
    """Select exact recorded ASK occurrences; never synthesize or deduplicate questions."""
    validate_prompt_profiles(source.run.definition.game_policy.prompt_profile, config.prompt_profile)
    cases: list[ReplayCase] = []
    missing = 0
    for subject_result in source.subjects:
        for trial in subject_result.trials:
            if trial.status != "completed":
                missing += 1
                continue
            if trial.result.run.run_id != str(trial.identity.episode_run_id):
                raise ReplayInputError("source episode identity mismatch")
            for turn in trial.result.turns:
                if not isinstance(turn, ActionTurnResult) or turn.action.action != "ASK":
                    continue
                if turn.action.question is None:
                    raise ReplayInputError("recorded ASK is missing its question")
                cases.append(ReplayCase(
                    identity=trial.identity,
                    turn_number=turn.turn_number,
                    subject=trial.result.run.subject,
                    question=turn.action.question,
                    previous=turn.adjudication,
                ))
    keys = [(case.identity, case.turn_number) for case in cases]
    if len(keys) != len(set(keys)):
        raise ReplayInputError("duplicate source ASK position")
    if any(case.identity.execution_id != source.run.execution_id
           or case.identity.model_id != source.run.model.model_id for case in cases):
        raise ReplayInputError("source trial context mismatch")
    if set(selection.targets) - {case.identity.target_id for case in cases}:
        raise ReplayInputError("selected target has no recorded ASK actions")
    if set(selection.trials) - {case.identity.trial_id for case in cases}:
        raise ReplayInputError("selected trial has no recorded ASK actions")
    selected = [case for case in cases if (
        (not selection.targets or case.identity.target_id in selection.targets)
        and (not selection.trials or case.identity.trial_id in selection.trials)
        and (not selection.turns or case.turn_number in selection.turns)
    )]
    if set(selection.turns) - {case.turn_number for case in selected}:
        raise ReplayInputError("selected turn has no recorded ASK actions")
    return ReplayPlan(
        run_id=run_id,
        source_execution_id=source.run.execution_id,
        source_model_id=source.run.model.model_id,
        source_benchmark_id=source.run.definition.benchmark_id,
        source_integrity_hash=source.integrity_hash,
        source_oracle_configuration=source.run.definition.oracle_configuration,
        oracle_configuration=config,
        oracle_contract_hash=oracle_contract_hash(config),
        selection=selection,
        source_ask_count=len(cases),
        source_trials_without_transcript=missing,
        cases=tuple(selected[:selection.limit]),
    )


class ReplayRoleAudit(StrictModel):
    role: OracleRole
    prompt_version: str
    prompt_hash: str
    provider: ProviderResultAudit


class ReplaySuccess(StrictModel):
    status: Literal["success"] = "success"
    case_number: int = Field(ge=1)
    recorded_at: str
    result: OracleResult
    adjudication: OracleAdjudication
    metrics: OracleMetrics
    roles: tuple[ReplayRoleAudit, ...]


class ReplayFailure(StrictModel):
    status: Literal["failure"] = "failure"
    case_number: int = Field(ge=1)
    recorded_at: str
    code: str = Field(min_length=1, max_length=160)


ReplayOutcome = Annotated[ReplaySuccess | ReplayFailure, Field(discriminator="status")]


class ReplayStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"


class ReplayReport(StrictModel):
    schema_version: Literal[1] = 1
    plan: ReplayPlan
    plan_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    started_at: str
    updated_at: str
    status: ReplayStatus = ReplayStatus.RUNNING
    in_flight: int | None = Field(default=None, ge=1)
    outcomes: tuple[ReplayOutcome, ...] = ()

    @model_validator(mode="after")
    def consistent_checkpoint(self) -> ReplayReport:
        if self.plan_hash != self.plan.content_hash():
            raise ReplayInputError("replay plan hash mismatch")
        numbers = tuple(outcome.case_number for outcome in self.outcomes)
        if numbers != tuple(range(1, len(numbers) + 1)) or len(numbers) > len(self.plan.cases):
            raise ReplayInputError("replay outcomes must be an ordered prefix of the plan")
        if self.in_flight is not None and (
            self.in_flight != len(numbers) + 1 or self.in_flight > len(self.plan.cases)
            or self.status is not ReplayStatus.RUNNING
        ):
            raise ReplayInputError("invalid in-flight replay position")
        if self.status is ReplayStatus.COMPLETED and len(numbers) != len(self.plan.cases):
            raise ReplayInputError("completed replay must account for every case")
        return self


class ReplaySummary(StrictModel):
    selected: int
    completed: int
    failed: int
    changed: int
    unchanged: int
    final_unknown: int
    known_cost_usd: Decimal
    calls_without_cost: int
    failure_cost_unavailable: bool
    cached_input_tokens: int
    cache_write_tokens: int


def summarize_replay(report: ReplayReport) -> ReplaySummary:
    successes = [outcome for outcome in report.outcomes if isinstance(outcome, ReplaySuccess)]
    failed = len(report.outcomes) - len(successes)
    changed = sum(
        outcome.adjudication.final_answer != report.plan.cases[outcome.case_number - 1].previous.answer
        for outcome in successes
    )
    return ReplaySummary(
        selected=len(report.plan.cases), completed=len(successes), failed=failed,
        changed=changed, unchanged=len(successes) - changed,
        final_unknown=sum(o.adjudication.final_answer is OracleAnswer.UNKNOWN for o in successes),
        known_cost_usd=sum((o.metrics.cost_usd or Decimal(0) for o in successes), Decimal(0)),
        calls_without_cost=sum(o.metrics.cost_usd is None for o in successes),
        failure_cost_unavailable=bool(failed),
        cached_input_tokens=sum(o.metrics.cached_input_tokens for o in successes),
        cache_write_tokens=sum(o.metrics.cache_write_tokens for o in successes),
    )


class ReplayOracle(Protocol):
    def ask(self, request: OracleRequest) -> OracleCall: ...


class ReplaySink(Protocol):
    def save(self, report: ReplayReport) -> None: ...


class ReplayObserver(Protocol):
    def completed(self, outcome: ReplayOutcome, total: int) -> None: ...


def capture_oracle_call(case_number: int, call: OracleCall) -> ReplaySuccess:
    audit = call.audit
    roles: list[ReplayRoleAudit] = []
    if audit.research is not None:
        for attempt in audit.research.attempts:
            roles.append(ReplayRoleAudit(
                role=OracleRole.ORACLE, prompt_version=attempt.prompt_version,
                prompt_hash=attempt.prompt_hash, provider=provider_result_audit(attempt.provider),
            ))
    else:
        roles.append(ReplayRoleAudit(
            role=OracleRole.ORACLE, prompt_version=audit.prompt_version,
            prompt_hash=audit.prompt_hash, provider=provider_result_audit(audit.provider),
        ))
    for role, review in ((OracleRole.REVIEWER, audit.reviewer), (OracleRole.JUDGE, audit.judge)):
        if review is not None:
            roles.append(ReplayRoleAudit(
                role=role, prompt_version=review.prompt_version, prompt_hash=review.prompt_hash,
                provider=provider_result_audit(review.provider),
            ))
    return ReplaySuccess(
        case_number=case_number, recorded_at=call.recorded_at, result=call.result,
        adjudication=call.adjudication, metrics=call.metrics, roles=tuple(roles),
    )


def run_replay(
    report: ReplayReport,
    oracle: ReplayOracle,
    sink: ReplaySink,
    observer: ReplayObserver,
    *,
    max_consecutive_failures: int = 5,
) -> ReplayReport:
    """Checkpoint each call. Interrupted calls are accounted for, never silently re-billed."""
    if max_consecutive_failures < 1:
        raise ReplayInputError("failure limit must be positive")
    if report.status is ReplayStatus.COMPLETED:
        return report
    outcomes = list(report.outcomes)
    if report.in_flight is not None:
        outcomes.append(ReplayFailure(
            case_number=report.in_flight, recorded_at=timestamp(), code="replay_interrupted",
        ))
    failures = 0
    report = report.model_copy(update={
        "outcomes": tuple(outcomes), "in_flight": None, "status": ReplayStatus.RUNNING,
        "updated_at": timestamp(),
    })
    sink.save(report)
    for index in range(len(outcomes), len(report.plan.cases)):
        case = report.plan.cases[index]
        report = report.model_copy(update={"in_flight": index + 1, "updated_at": timestamp()})
        sink.save(report)
        # This is the complete input projection. Baselines and other cases stay report-only.
        request = OracleRequest(
            run_id=report.plan.run_id, subject=case.subject, question=case.question,
        )
        outcome: ReplayOutcome
        try:
            call = oracle.ask(request)
            if call.request != request:
                raise ReplayInputError("Oracle returned a different request")
            outcome = capture_oracle_call(index + 1, call)
        except AuditWriteError:
            raise
        except OracleError as error:
            outcome = ReplayFailure(case_number=index + 1, recorded_at=timestamp(), code=error.code)
        outcomes.append(outcome)
        failures = failures + 1 if isinstance(outcome, ReplayFailure) else 0
        report = report.model_copy(update={
            "in_flight": None, "outcomes": tuple(outcomes), "updated_at": timestamp(),
        })
        sink.save(report)
        observer.completed(outcome, len(report.plan.cases))
        if failures >= max_consecutive_failures:
            break
    report = report.model_copy(update={
        "status": (ReplayStatus.COMPLETED if len(outcomes) == len(report.plan.cases)
                   else ReplayStatus.STOPPED),
        "updated_at": timestamp(),
    })
    sink.save(report)
    return report
