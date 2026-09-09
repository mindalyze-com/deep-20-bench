"""Direct, repeatable Oracle question suites with report-only expectations."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal, Protocol

from deep20_oracle.cache_contract import oracle_contract_hash
from deep20_oracle.catalog import SubjectCatalog
from deep20_oracle.config import OracleConfig
from deep20_oracle.errors import AuditWriteError, OracleError
from deep20_oracle.models import RUN_ID_PATTERN, OracleAnswer, OracleRequest, StrictModel, Subject
from deep20_oracle.util import canonical_json, sha256_text, timestamp
from pydantic import ConfigDict, Field, model_validator

from .models import SubjectId
from .oracle_replay import (
    ReplayFailure,
    ReplayInputError,
    ReplayObserver,
    ReplayOracle,
    ReplayOutcome,
    ReplayStatus,
    ReplaySuccess,
    capture_oracle_call,
)


class QuestionCase(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=False)
    id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
    target_id: SubjectId | None = None
    subject: Subject | None = None
    question: str = Field(min_length=1, max_length=1_000)
    expected_answers: tuple[OracleAnswer, ...] = Field(default=(), max_length=5)
    notes: str | None = Field(default=None, max_length=2_000)

    @model_validator(mode="after")
    def valid_case(self) -> QuestionCase:
        if (self.target_id is None) == (self.subject is None):
            raise ReplayInputError("each case needs exactly one of target_id or subject")
        if not self.question.strip():
            raise ReplayInputError("question must not be blank")
        if len(set(self.expected_answers)) != len(self.expected_answers):
            raise ReplayInputError("expected answers must be unique")
        return self


class QuestionSuite(StrictModel):
    schema_version: Literal[1] = 1
    name: str = Field(min_length=1, max_length=160)
    cases: tuple[QuestionCase, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_cases(self) -> QuestionSuite:
        if len({case.id for case in self.cases}) != len(self.cases):
            raise ReplayInputError("suite case IDs must be unique")
        return self


class SuitePlan(StrictModel):
    run_id: str = Field(pattern=RUN_ID_PATTERN)
    suite: QuestionSuite
    repetitions: int = Field(ge=1, le=100)
    oracle_configuration: OracleConfig
    oracle_contract_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def resolved_subjects(self) -> SuitePlan:
        if any(case.subject is None for case in self.suite.cases):
            raise ReplayInputError("saved suites must contain resolved subject snapshots")
        return self

    @property
    def total(self) -> int:
        return len(self.suite.cases) * self.repetitions

    def case_at(self, position: int) -> QuestionCase:
        if not 1 <= position <= self.total:
            raise ReplayInputError("suite position is out of range")
        return self.suite.cases[(position - 1) // self.repetitions]

    def repetition_at(self, position: int) -> int:
        self.case_at(position)
        return (position - 1) % self.repetitions + 1

    def content_hash(self) -> str:
        return sha256_text(canonical_json(self.model_dump(mode="json")))


def build_suite_plan(
    suite: QuestionSuite, config: OracleConfig, *, run_id: str, repetitions: int = 1,
    case_ids: tuple[str, ...] = (), catalog: SubjectCatalog | None = None,
) -> SuitePlan:
    if len(set(case_ids)) != len(case_ids) or set(case_ids) - {case.id for case in suite.cases}:
        raise ReplayInputError("case selection contains duplicate or unknown IDs")
    cases: list[QuestionCase] = []
    for case in suite.cases:
        if case_ids and case.id not in case_ids:
            continue
        subject = case.subject
        if subject is None:
            if catalog is None or case.target_id is None:
                raise ReplayInputError("catalog is required to resolve target IDs")
            subject = catalog.subject(str(case.target_id))
        cases.append(case.model_copy(update={"subject": subject, "target_id": None}))
    return SuitePlan(
        run_id=run_id, suite=QuestionSuite(name=suite.name, cases=tuple(cases)),
        repetitions=repetitions, oracle_configuration=config,
        oracle_contract_hash=oracle_contract_hash(config),
    )


class SuiteReport(StrictModel):
    schema_version: Literal[1] = 1
    plan: SuitePlan
    plan_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    started_at: str
    updated_at: str
    status: ReplayStatus = ReplayStatus.RUNNING
    in_flight: int | None = Field(default=None, ge=1)
    outcomes: tuple[ReplayOutcome, ...] = ()

    @model_validator(mode="after")
    def valid_checkpoint(self) -> SuiteReport:
        if self.plan.content_hash() != self.plan_hash:
            raise ReplayInputError("suite plan hash mismatch")
        if tuple(o.case_number for o in self.outcomes) != tuple(range(1, len(self.outcomes) + 1)):
            raise ReplayInputError("suite outcomes must be an ordered prefix")
        if len(self.outcomes) > self.plan.total:
            raise ReplayInputError("too many suite outcomes")
        if self.in_flight is not None and (
            self.in_flight != len(self.outcomes) + 1 or self.in_flight > self.plan.total
            or self.status is not ReplayStatus.RUNNING
        ):
            raise ReplayInputError("invalid in-flight suite position")
        if self.status is ReplayStatus.COMPLETED and len(self.outcomes) != self.plan.total:
            raise ReplayInputError("completed suite has pending questions")
        return self


class SuiteSink(Protocol):
    def save(self, report: SuiteReport) -> None: ...


def run_oracle_suite(
    report: SuiteReport, oracle: ReplayOracle, sink: SuiteSink, observer: ReplayObserver,
    *, max_consecutive_failures: int = 1,
) -> SuiteReport:
    if max_consecutive_failures < 1:
        raise ReplayInputError("failure limit must be positive")
    if report.status is ReplayStatus.COMPLETED:
        return report
    outcomes = list(report.outcomes)
    if report.in_flight is not None:
        outcomes.append(ReplayFailure(case_number=report.in_flight, recorded_at=timestamp(),
                                      code="suite_interrupted"))
    report = report.model_copy(update={"outcomes": tuple(outcomes), "in_flight": None,
                                       "status": ReplayStatus.RUNNING, "updated_at": timestamp()})
    sink.save(report)
    failures = 0
    for number in range(len(outcomes) + 1, report.plan.total + 1):
        case = report.plan.case_at(number)
        assert case.subject is not None
        report = report.model_copy(update={"in_flight": number, "updated_at": timestamp()})
        sink.save(report)
        # IDs, repetition, expectations, notes and earlier outcomes stay outside this projection.
        request = OracleRequest(run_id=report.plan.run_id, subject=case.subject, question=case.question)
        outcome: ReplayOutcome
        try:
            call = oracle.ask(request)
            if call.request != request:
                raise ReplayInputError("Oracle returned a different request")
            outcome = capture_oracle_call(number, call)
        except AuditWriteError:
            raise
        except OracleError as error:
            outcome = ReplayFailure(case_number=number, recorded_at=timestamp(), code=error.code)
        outcomes.append(outcome)
        failures = failures + 1 if isinstance(outcome, ReplayFailure) else 0
        report = report.model_copy(update={"outcomes": tuple(outcomes), "in_flight": None,
                                           "updated_at": timestamp()})
        sink.save(report)
        observer.completed(outcome, report.plan.total)
        if failures >= max_consecutive_failures:
            break
    report = report.model_copy(update={
        "status": ReplayStatus.COMPLETED if len(outcomes) == report.plan.total else ReplayStatus.STOPPED,
        "updated_at": timestamp(),
    })
    sink.save(report)
    return report


class SuiteSummary(StrictModel):
    selected: int
    succeeded: int
    failed: int
    assessed: int
    matched: int
    mismatched: int
    unstable_cases: int
    known_cost_usd: Decimal


def summarize_suite(report: SuiteReport) -> SuiteSummary:
    successes = [o for o in report.outcomes if isinstance(o, ReplaySuccess)]
    assessed = [o for o in successes if report.plan.case_at(o.case_number).expected_answers]
    matched = sum(o.adjudication.final_answer in report.plan.case_at(o.case_number).expected_answers
                  for o in assessed)
    unstable = sum(len({o.adjudication.final_answer for o in successes
                         if report.plan.case_at(o.case_number).id == case.id}) > 1
                   for case in report.plan.suite.cases)
    return SuiteSummary(selected=report.plan.total, succeeded=len(successes),
        failed=len(report.outcomes) - len(successes), assessed=len(assessed), matched=matched,
        mismatched=len(assessed) - matched, unstable_cases=unstable,
        known_cost_usd=sum((o.metrics.cost_usd or Decimal(0) for o in successes), Decimal(0)))
