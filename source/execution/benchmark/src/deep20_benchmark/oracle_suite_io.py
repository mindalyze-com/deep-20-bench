"""Private suite input, checkpoints and review reports."""

from __future__ import annotations

import html
import os
from pathlib import Path

import yaml
from deep20_oracle.models import StrictModel
from deep20_oracle.util import canonical_json, load_yaml_unique, sha256_text
from pydantic import Field

from .oracle_replay import ReplayFailure, ReplayInputError, ReplaySuccess
from .oracle_replay_io import render_oracle_decisions, render_oracle_evidence
from .oracle_review_files import PrivateReviewFiles
from .oracle_suite import QuestionSuite, SuiteReport, summarize_suite


class SuiteEnvelope(StrictModel):
    payload: SuiteReport
    integrity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


def load_question_suite(path: Path) -> QuestionSuite:
    return QuestionSuite.model_validate_json(canonical_json(load_yaml_unique(path)))


def write_question_suite(path: Path, suite: QuestionSuite) -> None:
    # Export is an explicit composition-root action, never a model call.
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(yaml.safe_dump(suite.model_dump(mode="json", exclude_none=True),
                                    sort_keys=False, allow_unicode=True))


class SuiteStore(PrivateReviewFiles):
    def load(self) -> SuiteReport | None:
        path = self.directory / "result.yml"
        if not path.exists():
            if self.directory.exists():
                raise ReplayInputError("suite directory exists without a checkpoint; use a new run ID")
            return None
        value = load_yaml_unique(path)
        envelope = SuiteEnvelope.model_validate_json(canonical_json(value))
        if not isinstance(value, dict):
            raise ReplayInputError("invalid suite envelope")
        if sha256_text(canonical_json(value["payload"])) != envelope.integrity_hash:
            raise ReplayInputError("suite result integrity mismatch")
        return envelope.payload

    def save(self, report: SuiteReport) -> None:
        report = SuiteReport.model_validate_json(report.model_dump_json())
        payload = report.model_dump(mode="json")
        self._write("result.yml", yaml.safe_dump(
            {"payload": payload, "integrity_hash": sha256_text(canonical_json(payload))},
            sort_keys=False, allow_unicode=True,
        ))
        if self.artifact_policy.permits("review.md"):
            self._write("review.md", render_suite_review(report))


def expectation_status(report: SuiteReport, outcome: ReplaySuccess) -> str:
    expected = report.plan.case_at(outcome.case_number).expected_answers
    if not expected:
        return "unscored"
    return "match" if outcome.adjudication.final_answer in expected else "mismatch"


def render_suite_review(report: SuiteReport) -> str:
    summary = summarize_suite(report)
    lines = [
        "# Oracle question suite\n",
        f"Suite: {html.escape(report.plan.suite.name)}. Run: `{report.plan.run_id}`.\n",
        (f"State: {report.status}. Succeeded: {summary.succeeded}/{summary.selected}; "
        f"failed: {summary.failed}; pending: {summary.selected - len(report.outcomes)}.\n"),
        (f"Expectation matches: {summary.matched}/{summary.assessed}; mismatches: {summary.mismatched}. "
        f"Cases with varying final answers: {summary.unstable_cases}.\n"),
        (f"Known successful-call cost: ${summary.known_cost_usd}. Failed calls and missing cost "
        "telemetry can incur additional charges.\n"),
        ("Each repetition uses a fresh production Oracle call. No Guesser, Validator, answer cache, "
        "or prior-answer feedback is used. Expected answers and notes are report-only. Matches "
        "measure agreement with the supplied expectations, not independently verified accuracy. "
        "A stable answer can still be wrong. Source excerpts are model-reported.\n"),
        ("| Case | Repeat | Oracle | Reviewer | Judge | Final | Expectation |\n"
        "| --- | --- | --- | --- | --- | --- | --- |\n"),
    ]
    for outcome in report.outcomes:
        number = outcome.case_number
        case = report.plan.case_at(number)
        repetition = report.plan.repetition_at(number)
        if isinstance(outcome, ReplayFailure):
            values = "- | - | - | FAILURE | n/a"
        else:
            a = outcome.adjudication
            values = f"{a.oracle_answer} | {a.reviewer.answer if a.reviewer else '-'} | " \
                f"{a.judge.answer if a.judge else '-'} | {a.final_answer} | " \
                + expectation_status(report, outcome)
        lines.append(f"| [{case.id}](#q{number}) | {repetition} | {values} |")
    for outcome in report.outcomes:
        number = outcome.case_number
        case = report.plan.case_at(number)
        assert case.subject is not None
        lines.append(f'\n<a id="q{number}"></a>\n\n## {case.id}, repeat '
                     f'{report.plan.repetition_at(number)}\n')
        lines.append(f"<p>{html.escape(case.subject.canonical_name)}</p>\n"
                     f"<pre>{html.escape(case.question)}</pre>\n")
        lines.append("Expected: " + (", ".join(case.expected_answers) or "not specified") + ".\n")
        if case.notes:
            lines.append(f"<pre>{html.escape(case.notes)}</pre>\n")
        if isinstance(outcome, ReplayFailure):
            lines.append(f"Failure: `{html.escape(outcome.code)}`. No final answer.\n")
            continue
        lines.append(render_oracle_decisions(outcome.adjudication))
        if outcome.result.supporting_statement:
            lines.append("Oracle support: <pre>" + html.escape(outcome.result.supporting_statement)
                         + "</pre>\n")
        lines.append(render_oracle_evidence(outcome.result.evidence))
        for role in outcome.roles:
            lines.append(f"{role.role}: `{role.prompt_version}`; prompt hash `{role.prompt_hash}`.\n")
        lines.append(f"Cost: {outcome.metrics.cost_usd} USD; latency: {outcome.metrics.latency_ms} ms; "
                     f"cached input tokens: {outcome.metrics.cached_input_tokens}.\n")
    return "\n".join(lines)
