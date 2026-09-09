"""Private artifact ownership and human review rendering for the replay composition root."""

from __future__ import annotations

import html

import yaml
from deep20_oracle.models import Evidence, OracleAdjudication, StrictModel
from deep20_oracle.util import canonical_json, load_yaml_unique, sha256_text
from pydantic import Field

from .oracle_replay import ReplayFailure, ReplayInputError, ReplayReport, summarize_replay
from .oracle_review_files import PrivateReviewFiles


class ReplayEnvelope(StrictModel):
    payload: ReplayReport
    integrity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class ReplayStore(PrivateReviewFiles):
    def load(self) -> ReplayReport | None:
        path = self.directory / "result.yml"
        if not path.exists():
            if self.directory.exists():
                raise ReplayInputError("replay directory exists without a checkpoint; use a new run ID")
            return None
        value = load_yaml_unique(path)
        envelope = ReplayEnvelope.model_validate(value)
        if not isinstance(value, dict):
            raise TypeError("invalid replay envelope")
        if sha256_text(canonical_json(value["payload"])) != envelope.integrity_hash:
            raise ReplayInputError("replay result integrity mismatch")
        return envelope.payload

    def save(self, report: ReplayReport) -> None:
        # Validate updated copies before acknowledging a checkpoint.
        report = ReplayReport.model_validate_json(report.model_dump_json())
        payload = report.model_dump(mode="json")
        envelope = {"payload": payload, "integrity_hash": sha256_text(canonical_json(payload))}
        self._write("result.yml", yaml.safe_dump(envelope, allow_unicode=True, sort_keys=False))
        if self.artifact_policy.permits("review.md"):
            self._write("review.md", render_replay_review(report))



def _text(value: object) -> str:
    return html.escape(str(value), quote=True)


def render_oracle_decisions(adjudication: OracleAdjudication) -> str:
    rows = [f"Oracle: {adjudication.oracle_answer}"]
    for name, decision in (("Reviewer", adjudication.reviewer), ("Judge", adjudication.judge)):
        if decision is None:
            rows.append(f"{name}: not invoked")
        else:
            rows.append(
                f"{name}: {decision.answer}; basis={decision.basis}; "
                f"evidence={list(decision.evidence_indices)}"
            )
            if decision.supporting_statement is not None:
                rows.append(f"Support: {decision.supporting_statement}")
    rows.append(f"Final: {adjudication.final_answer}; path={adjudication.decision_path}")
    return "<pre>" + _text("\n".join(rows)) + "</pre>\n"


def render_oracle_evidence(items: tuple[Evidence, ...]) -> str:
    if not items:
        return "<p>No retained evidence.</p>\n"
    return "".join(
        f'<p>Evidence {index}: <a href="{_text(item.source_url)}">'
        f'{_text(item.source_url)}</a></p>\n<pre>{_text(item.excerpt)}</pre>\n'
        for index, item in enumerate(items, 1)
    )


def render_replay_review(report: ReplayReport) -> str:
    summary = summarize_replay(report)
    lines = [
        "# Oracle question replay\n",
        f"Source: `{report.plan.source_execution_id}`. Replay: `{report.plan.run_id}`.\n",
        (f"State: {report.status}. Selected: {summary.selected}. "
        f"Succeeded: {summary.completed}. Failed: {summary.failed}. "
        f"Pending: {summary.selected - summary.completed - summary.failed}.\n"),
        (f"Changed final answers: {summary.changed}. Unchanged: {summary.unchanged}. "
        f"New UNKNOWN answers: {summary.final_unknown}.\n"),
        (f"Known successful-call cost: ${summary.known_cost_usd}. "
        f"Successful calls without reported cost: {summary.calls_without_cost}. "
        "Failed or interrupted calls may incur additional cost; this is not a total bill.\n"),
        (f"Cached input tokens: {summary.cached_input_tokens}. "
        f"Cache-write tokens: {summary.cache_write_tokens}.\n"),
        ("These are fixed historical questions, not a new game or an accuracy score. "
        "Historical answers are comparison data, not ground truth. Changes can reflect prompts, "
        "retrieval, source changes, or model variation. Inspect unchanged answers too. "
        "Source excerpts are model-reported and have not been independently verified.\n"),
        (f"Source ASK actions: {report.plan.source_ask_count}. "
        f"Trials without a retained transcript: {report.plan.source_trials_without_transcript}. "
        "GUESS actions and contract violations are excluded. Repeated ASK actions remain separate.\n"),
        ("| Case | Target | Trial | Turn | Old | New | Changed |\n"
        "| --- | --- | --- | --- | --- | --- | --- |\n"),
    ]
    for outcome in report.outcomes:
        case = report.plan.cases[outcome.case_number - 1]
        answer = outcome.adjudication.final_answer if outcome.status == "success" else "FAILURE"
        changed = ("yes" if answer != case.previous.answer else "no")
        if outcome.status == "failure":
            changed = "n/a"
        lines.append(
            f"| [Q{outcome.case_number}](#q{outcome.case_number}) | {case.identity.target_id} | "
            f"{case.identity.trial_id} | {case.turn_number} | {case.previous.answer} | "
            f"{answer} | {changed} |\n"
        )
    for outcome in report.outcomes:
        case = report.plan.cases[outcome.case_number - 1]
        lines.append(
            f'\n<a id="q{outcome.case_number}"></a>\n\n'
            f"## Q{outcome.case_number}\n\n"
            f"<p>{_text(case.subject.canonical_name)}; {_text(case.identity.target_id)}; "
            f"{_text(case.identity.trial_id)}; turn {case.turn_number}</p>\n"
            f"<pre>{_text(case.question)}</pre>\n\n"
            "### Historical answer\n\n"
        )
        if case.previous.oracle_quality is not None:
            lines.append(render_oracle_decisions(case.previous.oracle_quality))
        if case.previous.cache_source is not None:
            lines.append("<p>The historical answer was reused from the benchmark ASK cache.</p>\n")
        lines.append(render_oracle_evidence(case.previous.evidence))
        lines.append("\n### Replayed answer\n\n")
        if isinstance(outcome, ReplayFailure):
            lines.append(f"<p>Infrastructure failure: {_text(outcome.code)}. No final answer.</p>\n")
        else:
            lines.append(render_oracle_decisions(outcome.adjudication))
            lines.append(render_oracle_evidence(outcome.result.evidence))
            # Optional typed support fields evolve with the Oracle's selected factual policy.
            lines.append("<details><summary>Validated research result</summary>\n\n<pre>"
                         + _text(outcome.result.model_dump_json(indent=2)) + "</pre>\n</details>\n")
            for role in outcome.roles:
                lines.append(
                    f"<p>{role.role}: {_text(role.prompt_version)}; "
                    f"prompt hash {_text(role.prompt_hash)}</p>\n"
                )
            lines.append(f"<p>Reported cost: {_text(outcome.metrics.cost_usd)} USD; "
                         f"latency: {outcome.metrics.latency_ms} ms.</p>\n")
        lines.append("\nManual assessment: pending.\n\nNotes:\n")
    return "\n".join(lines)
