#!/usr/bin/env python3
"""Render live benchmark scores against the overall and partial leaders."""

from __future__ import annotations

import argparse
import re
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo
from decimal import ROUND_HALF_UP, Decimal, localcontext
from fractions import Fraction
from pathlib import Path
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

ReportFormat = Literal["markdown", "console"]


class ReportError(RuntimeError):
    """A report cannot be calculated from the available validated artifacts."""


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)


class ManifestRequest(FrozenModel):
    benchmark_id: str
    execution_id: str
    model_id: str
    benchmark_mode: str
    base_seed: int


class ManifestGamePolicy(FrozenModel):
    version: int
    max_questions: int = Field(ge=1)


class ManifestDefinition(FrozenModel):
    benchmark_id: str
    subject_ids: tuple[str, ...]
    iterations: int = Field(ge=1)
    game_policy: ManifestGamePolicy


class ManifestModel(FrozenModel):
    model_id: str
    display_name: str


class BenchmarkManifest(FrozenModel):
    schema_version: Literal[3]
    request: ManifestRequest
    definition: ManifestDefinition
    model: ManifestModel


class ScorePolicy(FrozenModel):
    version: Literal["average-then-average-v1"]
    failure_penalty_offset: int = Field(ge=1)


class ActiveCohort(FrozenModel):
    benchmark_id: str
    benchmark_version: int
    target_ids: tuple[str, ...]
    iterations: int = Field(ge=1)
    base_seed: int
    max_questions: int = Field(ge=1)


class PublicationManifest(FrozenModel):
    document_type: Literal["manifest"]
    schema_version: Literal[1]
    score_policy: ScorePolicy
    active_cohort: ActiveCohort


class PublicModel(FrozenModel):
    model_id: str
    display_name: str


class LeaderboardRow(FrozenModel):
    rank: int | None
    model: PublicModel
    status: Literal["evaluated", "awaiting_official_run"]
    execution_id: str | None
    question_score: Decimal | None


class LeaderboardDocument(FrozenModel):
    document_type: Literal["leaderboard"]
    schema_version: Literal[3]
    leaderboard: tuple[LeaderboardRow, ...]


class SubjectProfile(FrozenModel):
    subject_name: str


class TrialContract(FrozenModel):
    evaluated_outputs: int = Field(ge=0)
    violations: int = Field(ge=0)

    @model_validator(mode="after")
    def violations_do_not_exceed_outputs(self) -> TrialContract:
        if self.violations > self.evaluated_outputs:
            raise ValueError("contract violations exceed evaluated outputs")
        return self


class PublicTrial(FrozenModel):
    trial_id: str
    trial_number: int = Field(ge=1)
    penalized_questions: Decimal | None
    cost_usd: Decimal = Field(ge=0)
    duration_ms: int = Field(ge=0)
    contract: TrialContract


class PublicationSubject(FrozenModel):
    document_type: Literal["subject"]
    schema_version: Literal[1]
    execution_id: str
    target_id: str
    profile: SubjectProfile
    trials: tuple[PublicTrial, ...]

    @model_validator(mode="after")
    def unique_trial_numbers(self) -> PublicationSubject:
        numbers = tuple(trial.trial_number for trial in self.trials)
        if len(numbers) != len(set(numbers)):
            raise ValueError("publication subject contains duplicate trial numbers")
        return self


class TrialIdentity(FrozenModel):
    execution_id: str
    model_id: str
    target_id: str
    trial_id: str
    trial_number: int = Field(ge=1)


class EpisodeSubject(FrozenModel):
    canonical_name: str


class EpisodeRun(FrozenModel):
    subject: EpisodeSubject
    duration_ms: int = Field(ge=0)


class EpisodeOutcome(FrozenModel):
    success: bool
    scoring_eligible: bool


class EpisodeCosts(FrozenModel):
    total: Decimal = Field(ge=0)


class EpisodeSummary(FrozenModel):
    counted_questions: int = Field(ge=0)
    contract: TrialContract
    costs_usd: EpisodeCosts


class EpisodeResult(FrozenModel):
    run: EpisodeRun
    outcome: EpisodeOutcome
    summary: EpisodeSummary


class SupersededPartialMetrics(FrozenModel):
    cost_usd: Decimal = Field(ge=0)


class SupersededAttempt(FrozenModel):
    partial_metrics: SupersededPartialMetrics


class CompletedTrial(FrozenModel):
    status: Literal["completed"]
    identity: TrialIdentity
    result: EpisodeResult
    superseded_attempts: tuple[SupersededAttempt, ...] = ()


class InfrastructureFailedTrial(FrozenModel):
    status: Literal["infrastructure_failed"]
    identity: TrialIdentity


TrialPayload = Annotated[
    CompletedTrial | InfrastructureFailedTrial,
    Field(discriminator="status"),
]


class TrialEnvelope(FrozenModel):
    payload: TrialPayload


class StateFailure(FrozenModel):
    code: str


class BenchmarkState(FrozenModel):
    schema_version: Literal[1]
    execution_id: str
    model_id: str
    status: Literal["running", "completed", "failed"]
    scheduled_trials: int = Field(ge=0)
    started_trials: int = Field(ge=0)
    terminal_trials: int = Field(ge=0)
    current_target_id: str | None
    current_trial_id: str | None
    current_turn: int | None = Field(default=None, ge=1)
    last_failure: StateFailure | None
    updated_at: str


class StateEnvelope(FrozenModel):
    payload: BenchmarkState


class EventIdentity(FrozenModel):
    target_id: str
    trial_id: str
    trial_number: int = Field(ge=1)


class EventEvidence(FrozenModel):
    excerpt: str
    source_url: str


class EventAdjudication(FrozenModel):
    answer: str
    evidence: tuple[EventEvidence, ...] = ()


class EventAction(FrozenModel):
    action: str
    question: str | None = None


class EventTurn(FrozenModel):
    turn_number: int = Field(ge=1)
    action: EventAction | None = None
    adjudication: EventAdjudication | None = None


class EventProgress(FrozenModel):
    turn: EventTurn | None = None


class BenchmarkEvent(FrozenModel):
    event_type: str
    status: str | None = None
    recorded_at: str
    identity: EventIdentity | None = None
    progress: EventProgress | None = None


@dataclass(frozen=True)
class TrialPoint:
    target_id: str
    trial_number: int
    subject_name: str
    score: Fraction
    cost_usd: Decimal
    contract_breaks: int
    duration_ms: int
    evaluated_outputs: int


@dataclass(frozen=True)
class CurrentRunProgress:
    """Scored trials and the contiguous terminal schedule prefix."""

    trials: tuple[TrialPoint, ...]
    terminal_positions: int


@dataclass(frozen=True)
class ComparisonRun:
    model_id: str
    display_name: str
    rank: int
    overall_score: Decimal
    trials: tuple[TrialPoint, ...]


@dataclass(frozen=True)
class TableRow:
    cells: tuple[str, ...]
    emphasized: bool = False


@dataclass(frozen=True)
class QuestionContext:
    turn_number: int
    question: str
    answer: str
    evidence: tuple[EventEvidence, ...]


@dataclass(frozen=True)
class RoundContext:
    label: str
    position: int
    target_id: str
    trial_number: int
    subject_name: str
    questions: tuple[QuestionContext, ...]


def _load_json[ModelT: BaseModel](path: Path, model: type[ModelT]) -> ModelT:
    try:
        return model.model_validate_json(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ReportError(f"cannot read {path}") from error
    except ValidationError as error:
        raise ReportError(f"invalid data in {path}: {error}") from error


def _load_trial(path: Path) -> TrialEnvelope:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return TrialEnvelope.model_validate(data)
    except OSError as error:
        raise ReportError(f"cannot read {path}") from error
    except (ValidationError, yaml.YAMLError) as error:
        raise ReportError(f"invalid data in {path}: {error}") from error


def _load_state(path: Path) -> BenchmarkState:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return StateEnvelope.model_validate(data).payload
    except OSError as error:
        raise ReportError(f"cannot read {path}") from error
    except (ValidationError, yaml.YAMLError) as error:
        raise ReportError(f"invalid data in {path}: {error}") from error


def _load_events(path: Path) -> tuple[BenchmarkEvent, ...]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ReportError(f"cannot read {path}") from error
    events: list[BenchmarkEvent] = []
    for line_number, line in enumerate(lines, start=1):
        try:
            events.append(BenchmarkEvent.model_validate_json(line))
        except ValidationError as error:
            raise ReportError(f"invalid event at {path}:{line_number}: {error}") from error
    return tuple(events)


def _validate_compatible_cohort(
    manifest: BenchmarkManifest,
    publication: PublicationManifest,
) -> None:
    definition = manifest.definition
    cohort = publication.active_cohort
    checks = (
        (definition.benchmark_id, cohort.benchmark_id, "benchmark ID"),
        (definition.game_policy.version, cohort.benchmark_version, "benchmark version"),
        (definition.subject_ids, cohort.target_ids, "subject order"),
        (definition.iterations, cohort.iterations, "iteration count"),
        (manifest.request.base_seed, cohort.base_seed, "base seed"),
        (definition.game_policy.max_questions, cohort.max_questions, "question limit"),
    )
    mismatches = tuple(label for actual, expected, label in checks if actual != expected)
    if mismatches:
        raise ReportError(
            "run is incompatible with the active published cohort: " + ", ".join(mismatches)
        )


def _positions(manifest: BenchmarkManifest) -> tuple[tuple[str, int], ...]:
    return tuple(
        (target_id, trial_number)
        for target_id in manifest.definition.subject_ids
        for trial_number in range(1, manifest.definition.iterations + 1)
    )


def _trial_path(
    run_root: Path,
    target_id: str,
    trial_number: int,
) -> Path:
    return run_root / "subjects" / target_id / "trials" / f"trial-{trial_number:03d}" / "result.yml"


def _current_trials(
    run_root: Path,
    manifest: BenchmarkManifest,
    positions: tuple[tuple[str, int], ...],
    *,
    failure_penalty_offset: int,
) -> CurrentRunProgress:
    completed: list[TrialPoint] = []
    first_missing: int | None = None
    failure_penalty = Fraction(
        manifest.definition.game_policy.max_questions + failure_penalty_offset
    )

    for position, (target_id, trial_number) in enumerate(positions, start=1):
        path = _trial_path(run_root, target_id, trial_number)
        if not path.exists():
            first_missing = position
            break
        envelope = _load_trial(path)
        payload = envelope.payload
        expected_trial_id = f"trial-{trial_number:03d}"
        expected_identity = (
            manifest.request.execution_id,
            manifest.request.model_id,
            target_id,
            expected_trial_id,
            trial_number,
        )
        actual_identity = (
            payload.identity.execution_id,
            payload.identity.model_id,
            payload.identity.target_id,
            payload.identity.trial_id,
            payload.identity.trial_number,
        )
        if actual_identity != expected_identity:
            raise ReportError(f"trial identity mismatch in {path}")
        if isinstance(payload, InfrastructureFailedTrial):
            continue
        if not payload.result.outcome.scoring_eligible:
            raise ReportError(f"position {position} is not scoring eligible")
        score = (
            Fraction(payload.result.summary.counted_questions)
            if payload.result.outcome.success
            else failure_penalty
        )
        completed.append(
            TrialPoint(
                target_id=target_id,
                trial_number=trial_number,
                subject_name=payload.result.run.subject.canonical_name,
                score=score,
                cost_usd=(
                    payload.result.summary.costs_usd.total
                    + sum(
                        (
                            attempt.partial_metrics.cost_usd
                            for attempt in payload.superseded_attempts
                        ),
                        start=Decimal(0),
                    )
                ),
                contract_breaks=payload.result.summary.contract.violations,
                duration_ms=payload.result.run.duration_ms,
                evaluated_outputs=payload.result.summary.contract.evaluated_outputs,
            )
        )

    if first_missing is not None:
        later_paths = (
            _trial_path(run_root, target_id, trial_number)
            for target_id, trial_number in positions[first_missing:]
        )
        if any(path.exists() for path in later_paths):
            raise ReportError("completed trial artifacts are not a contiguous benchmark prefix")
    terminal_positions = len(positions) if first_missing is None else first_missing - 1
    return CurrentRunProgress(tuple(completed), terminal_positions)


def _publication_trials(
    data_root: Path,
    row: LeaderboardRow,
    positions: tuple[tuple[str, int], ...],
) -> tuple[TrialPoint, ...]:
    if row.execution_id is None or row.question_score is None or row.rank is None:
        raise ReportError(f"evaluated model {row.model.model_id} lacks leaderboard data")
    subjects: dict[str, PublicationSubject] = {}
    for target_id, _ in positions:
        if target_id in subjects:
            continue
        path = data_root / "runs" / row.execution_id / "subjects" / f"{target_id}.json"
        subject = _load_json(path, PublicationSubject)
        if subject.execution_id != row.execution_id or subject.target_id != target_id:
            raise ReportError(f"publication subject identity mismatch in {path}")
        subjects[target_id] = subject

    points: list[TrialPoint] = []
    for target_id, trial_number in positions:
        subject = subjects[target_id]
        matches = tuple(trial for trial in subject.trials if trial.trial_number == trial_number)
        if len(matches) != 1:
            raise ReportError(
                f"expected one trial {trial_number} for {row.execution_id}/{target_id}"
            )
        trial = matches[0]
        if trial.trial_id != f"trial-{trial_number:03d}":
            raise ReportError(
                f"trial ID mismatch for {row.execution_id}/{target_id}/{trial_number}"
            )
        if trial.penalized_questions is None:
            raise ReportError(
                f"published trial is not scored: {row.execution_id}/{target_id}/{trial_number}"
            )
        points.append(
            TrialPoint(
                target_id=target_id,
                trial_number=trial_number,
                subject_name=subject.profile.subject_name,
                score=Fraction(trial.penalized_questions),
                cost_usd=trial.cost_usd,
                contract_breaks=trial.contract.violations,
                duration_ms=trial.duration_ms,
                evaluated_outputs=trial.contract.evaluated_outputs,
            )
        )
    return tuple(points)


def _comparison_runs(
    data_root: Path,
    leaderboard: LeaderboardDocument,
    positions: tuple[tuple[str, int], ...],
) -> tuple[ComparisonRun, ...]:
    runs: list[ComparisonRun] = []
    for row in leaderboard.leaderboard:
        if row.status != "evaluated":
            continue
        trials = _publication_trials(data_root, row, positions)
        assert row.rank is not None
        assert row.question_score is not None
        calculated_score = sum(
            (trial.score for trial in trials),
            start=Fraction(0),
        ) / len(trials)
        with localcontext() as context:
            context.prec = 40
            calculated_decimal = Decimal(calculated_score.numerator) / Decimal(
                calculated_score.denominator
            )
        if abs(calculated_decimal - row.question_score) > Decimal("1e-24"):
            raise ReportError(
                f"published score mismatch for {row.model.model_id}: "
                f"{calculated_decimal} != {row.question_score}"
            )
        runs.append(
            ComparisonRun(
                model_id=row.model.model_id,
                display_name=row.model.display_name,
                rank=row.rank,
                overall_score=row.question_score,
                trials=trials,
            )
        )
    if not runs:
        raise ReportError("published leaderboard has no evaluated models")
    return tuple(runs)


def _short_name(display_name: str) -> str:
    return re.sub(r" \([^()]+\)$", "", display_name)


def _markdown(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def _heading(value: str, output_format: ReportFormat) -> str:
    return f"**{value}**" if output_format == "markdown" else value


def _render_grid(
    headers: tuple[str, ...],
    rows: tuple[TableRow, ...],
    *,
    right_columns: frozenset[int],
    output_format: ReportFormat,
) -> str:
    if any(len(row.cells) != len(headers) for row in rows):
        raise ReportError("table row width does not match its header")
    if output_format == "markdown":
        header = "| " + " | ".join(_markdown(value) for value in headers) + " |"
        alignment = (
            "|"
            + "|".join("---:" if index in right_columns else "---" for index in range(len(headers)))
            + "|"
        )
        rendered_rows = []
        for row in rows:
            cells = tuple(_markdown(value) for value in row.cells)
            if row.emphasized:
                cells = tuple(f"**{value}**" if value else "" for value in cells)
            rendered_rows.append("| " + " | ".join(cells) + " |")
        return "\n".join((header, alignment, *rendered_rows))

    widths = tuple(
        max(len(headers[index]), *(len(row.cells[index]) for row in rows))
        for index in range(len(headers))
    )

    def separator(character: str) -> str:
        return "+" + "+".join(character * (width + 2) for width in widths) + "+"

    def render_cells(cells: tuple[str, ...]) -> str:
        values = []
        for index, (value, width) in enumerate(zip(cells, widths, strict=True)):
            padded = value.rjust(width) if index in right_columns else value.ljust(width)
            values.append(f" {padded} ")
        return "|" + "|".join(values) + "|"

    return "\n".join(
        (
            separator("-"),
            render_cells(headers),
            separator("="),
            *(render_cells(row.cells) for row in rows),
            separator("-"),
        )
    )


def _question_contexts(
    events: tuple[BenchmarkEvent, ...],
    target_id: str,
    trial_number: int,
    limit: int,
) -> tuple[QuestionContext, ...]:
    matches: list[QuestionContext] = []
    expected_trial_id = f"trial-{trial_number:03d}"
    for event in events:
        if event.event_type != "turn_resolved" or event.identity is None:
            continue
        if (
            event.identity.target_id != target_id
            or event.identity.trial_id != expected_trial_id
            or event.identity.trial_number != trial_number
            or event.progress is None
            or event.progress.turn is None
        ):
            continue
        turn = event.progress.turn
        if (
            turn.action is None
            or turn.action.action != "ASK"
            or turn.action.question is None
            or turn.adjudication is None
        ):
            continue
        matches.append(
            QuestionContext(
                turn_number=turn.turn_number,
                question=turn.action.question,
                answer=turn.adjudication.answer,
                evidence=turn.adjudication.evidence,
            )
        )
    return tuple(matches[-limit:])


def _recent_context(
    state: BenchmarkState,
    manifest: BenchmarkManifest,
    comparison_runs: tuple[ComparisonRun, ...],
    events: tuple[BenchmarkEvent, ...],
    current: CurrentRunProgress,
    limit: int,
) -> tuple[RoundContext, ...]:
    positions = _positions(manifest)
    current_index: int | None = None
    if (
        state.status == "running"
        and state.current_target_id is not None
        and state.current_trial_id is not None
    ):
        match = re.fullmatch(r"trial-(\d{3})", state.current_trial_id)
        if match is None:
            raise ReportError("state has an invalid current trial ID")
        key = (state.current_target_id, int(match.group(1)))
        try:
            current_index = positions.index(key)
        except ValueError as error:
            raise ReportError("current context round is outside the schedule") from error
    elif current.trials:
        key = (current.trials[-1].target_id, current.trials[-1].trial_number)
        current_index = positions.index(key)

    if current_index is None:
        return ()
    requested = (("Current round", current_index), ("Last round", current_index - 1))
    contexts: list[RoundContext] = []
    for label, index in requested:
        if index < 0:
            continue
        target_id, trial_number = positions[index]
        subject_name = next(
            trial.subject_name
            for trial in comparison_runs[0].trials
            if trial.target_id == target_id
        )
        contexts.append(
            RoundContext(
                label=label,
                position=index + 1,
                target_id=target_id,
                trial_number=trial_number,
                subject_name=subject_name,
                questions=_question_contexts(events, target_id, trial_number, limit),
            )
        )
    return tuple(contexts)


def _console_text(value: str) -> str:
    return " ".join(value.split())


def _wrapped_console_line(prefix: str, value: str) -> str:
    return textwrap.fill(
        _console_text(value),
        width=120,
        initial_indent=prefix,
        subsequent_indent=" " * len(prefix),
        break_long_words=False,
        break_on_hyphens=False,
    )


def _render_context(
    contexts: tuple[RoundContext, ...],
    manifest: BenchmarkManifest,
    output_format: ReportFormat,
) -> str:
    heading = _heading("Recent context", output_format)
    if not contexts:
        return f"{heading}\n\nNo current or completed round is available."
    lines = [heading]
    for context in contexts:
        title = (
            f"{context.label} - {context.subject_name} - "
            f"position {context.position}/{len(_positions(manifest))} - "
            f"trial {context.trial_number}/{manifest.definition.iterations}"
        )
        lines.extend(("", _heading(title, output_format)))
        if not context.questions:
            lines.append(
                "No resolved question is available."
                if output_format == "markdown"
                else "  No resolved question is available."
            )
            continue
        for question_index, question in enumerate(context.questions, start=1):
            if output_format == "markdown":
                lines.append(
                    f"{question_index}. **Question (turn {question.turn_number}):** "
                    f"{_markdown(question.question)}"
                )
                lines.append(f"   - **Answer:** {_markdown(question.answer)}")
                if question.evidence:
                    lines.append("   - **Oracle evidence:**")
                    for evidence_index, evidence in enumerate(question.evidence, start=1):
                        lines.append(f"     {evidence_index}. {_markdown(evidence.excerpt)}")
                        lines.append(f"        Source: {_markdown(evidence.source_url)}")
                else:
                    lines.append("   - **Oracle evidence:** none")
                continue
            lines.append(
                _wrapped_console_line(
                    f"  Question {question_index} (turn {question.turn_number}): ",
                    question.question,
                )
            )
            lines.append(_wrapped_console_line("    Answer: ", question.answer))
            if question.evidence:
                lines.append("    Oracle evidence:")
                for evidence_index, evidence in enumerate(question.evidence, start=1):
                    lines.append(
                        _wrapped_console_line(f"      {evidence_index}. ", evidence.excerpt)
                    )
                    lines.append(_wrapped_console_line("         Source: ", evidence.source_url))
            else:
                lines.append("    Oracle evidence: none")
    return "\n".join(lines)


def _score(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _average(total: Fraction, count: int) -> str:
    value = total / count
    with localcontext() as context:
        context.prec = 40
        decimal = Decimal(value.numerator) / Decimal(value.denominator)
    return _two_decimals(decimal)


def _two_decimals(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{rounded:.2f}"


def _money(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"${rounded:.2f}"


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ReportError(f"invalid timestamp: {value}") from error
    if parsed.tzinfo is None:
        raise ReportError(f"timestamp lacks a timezone: {value}")
    return parsed


def _milliseconds(started_at: str, completed_at: str) -> int:
    delta = _timestamp(completed_at) - _timestamp(started_at)
    return max(round(delta.total_seconds() * 1_000), 0)


def _active_elapsed_ms(
    events: tuple[BenchmarkEvent, ...],
    current_time: str,
) -> int:
    elapsed_ms = 0
    segment_started_at: str | None = None
    segment_last_event_at: str | None = None
    for event in events:
        if event.event_type in {"benchmark_started", "execution_resumed"}:
            if segment_started_at is not None and segment_last_event_at is not None:
                elapsed_ms += _milliseconds(segment_started_at, segment_last_event_at)
            segment_started_at = event.recorded_at
            segment_last_event_at = event.recorded_at
            continue
        if segment_started_at is None:
            continue
        segment_last_event_at = event.recorded_at
        if event.event_type == "benchmark_finished":
            elapsed_ms += _milliseconds(segment_started_at, event.recorded_at)
            segment_started_at = None
            segment_last_event_at = None
    if segment_started_at is not None:
        elapsed_ms += _milliseconds(segment_started_at, current_time)
    return elapsed_ms


def _duration(duration_ms: int) -> str:
    total_seconds = max((duration_ms + 500) // 1_000, 0)
    days, remainder = divmod(total_seconds, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes, seconds = divmod(remainder, 60)
    if days:
        return f"{days}d {hours}h {minutes}m"
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def _paired_trials(
    current: tuple[TrialPoint, ...],
    comparison: ComparisonRun,
) -> tuple[tuple[int, TrialPoint, TrialPoint], ...]:
    comparison_by_identity = {
        (trial.target_id, trial.trial_number): (position, trial)
        for position, trial in enumerate(comparison.trials, start=1)
    }
    if len(comparison_by_identity) != len(comparison.trials):
        raise ReportError(f"comparison run has duplicate trial identities: {comparison.model_id}")
    pairs: list[tuple[int, TrialPoint, TrialPoint]] = []
    for candidate in current:
        key = (candidate.target_id, candidate.trial_number)
        try:
            position, baseline = comparison_by_identity[key]
        except KeyError as error:
            raise ReportError(
                "comparison run lacks candidate trial "
                f"{candidate.target_id}/{candidate.trial_number}"
            ) from error
        pairs.append((position, candidate, baseline))
    return tuple(pairs)


def _comparison_score(
    current: tuple[TrialPoint, ...],
    comparison: ComparisonRun,
) -> Fraction:
    pairs = _paired_trials(current, comparison)
    if not pairs:
        raise ReportError("cannot calculate a comparison score without scored trials")
    return sum((baseline.score for _, _, baseline in pairs), start=Fraction(0)) / len(pairs)


def _render_table(
    current_name: str,
    comparison: ComparisonRun,
    current: tuple[TrialPoint, ...],
    output_format: ReportFormat,
) -> str:
    candidate_label = _short_name(current_name)
    comparison_label = _short_name(comparison.display_name)
    headers = (
        "Position",
        "Subject",
        candidate_label,
        comparison_label,
        f"Cumulative cost: {candidate_label} / {comparison_label}",
        f"Contract breaks: {candidate_label} / {comparison_label}",
    )
    rows: list[TableRow] = []
    current_cost = Decimal(0)
    comparison_cost = Decimal(0)
    current_total = Fraction(0)
    comparison_total = Fraction(0)
    paired = _paired_trials(current, comparison)
    subject_current_total = Fraction(0)
    subject_comparison_total = Fraction(0)
    subject_current_contract_breaks = 0
    subject_comparison_contract_breaks = 0
    subject_position_count = 0
    for pair_index, (position, candidate, baseline) in enumerate(paired):
        current_cost += candidate.cost_usd
        comparison_cost += baseline.cost_usd
        current_total += candidate.score
        comparison_total += baseline.score
        subject_current_total += candidate.score
        subject_comparison_total += baseline.score
        subject_current_contract_breaks += candidate.contract_breaks
        subject_comparison_contract_breaks += baseline.contract_breaks
        subject_position_count += 1
        rows.append(
            TableRow(
                cells=(
                    str(position),
                    candidate.subject_name,
                    _score(candidate.score),
                    _score(baseline.score),
                    f"{_money(current_cost)} / {_money(comparison_cost)}",
                    f"{candidate.contract_breaks} / {baseline.contract_breaks}",
                )
            )
        )
        next_candidate = paired[pair_index + 1][1] if pair_index + 1 < len(paired) else None
        if next_candidate is None or next_candidate.target_id != candidate.target_id:
            subject_size = sum(
                trial.target_id == candidate.target_id for trial in comparison.trials
            )
            rows.append(
                TableRow(
                    cells=(
                        f"Subject average ({subject_position_count}/{subject_size})",
                        candidate.subject_name,
                        _average(subject_current_total, subject_position_count),
                        _average(subject_comparison_total, subject_position_count),
                        f"{_money(current_cost)} / {_money(comparison_cost)}",
                        (
                            f"{subject_current_contract_breaks} / "
                            f"{subject_comparison_contract_breaks}"
                        ),
                    ),
                    emphasized=True,
                )
            )
            subject_current_total = Fraction(0)
            subject_comparison_total = Fraction(0)
            subject_current_contract_breaks = 0
            subject_comparison_contract_breaks = 0
            subject_position_count = 0
    rows.append(
        TableRow(
            cells=(
                "Average",
                "",
                _average(current_total, len(current)),
                _average(comparison_total, len(current)),
                f"{_money(current_cost)} / {_money(comparison_cost)}",
                (
                    f"{sum(trial.contract_breaks for trial in current)} / "
                    f"{sum(baseline.contract_breaks for _, _, baseline in paired)}"
                ),
            ),
            emphasized=True,
        )
    )
    return _render_grid(
        headers,
        tuple(rows),
        right_columns=frozenset({0, 2, 3, 4, 5}),
        output_format=output_format,
    )


def _status_block(
    state: BenchmarkState,
    manifest: BenchmarkManifest,
    comparison_runs: tuple[ComparisonRun, ...],
    events: tuple[BenchmarkEvent, ...],
    output_format: ReportFormat,
) -> str:
    if (
        state.execution_id != manifest.request.execution_id
        or state.model_id != manifest.model.model_id
    ):
        raise ReportError("state identity does not match the run manifest")
    if state.scheduled_trials != len(_positions(manifest)):
        raise ReportError("state trial count does not match the run manifest")
    infrastructure_failures = sum(
        event.event_type == "trial_finished" and event.status == "infrastructure_failed"
        for event in events
    )
    if infrastructure_failures:
        noun = "failure" if infrastructure_failures == 1 else "failures"
        if state.status == "completed" and state.last_failure is None:
            exceptions = f"{infrastructure_failures} repaired infrastructure {noun}"
        else:
            exceptions = f"{infrastructure_failures} infrastructure {noun}"
        if state.last_failure is not None:
            exceptions += f"; latest code: {state.last_failure.code}"
    elif state.last_failure is not None:
        exceptions = f"latest code: {state.last_failure.code}"
    else:
        exceptions = "none"

    current = "finished"
    if state.status == "running":
        if state.current_target_id is None or state.current_trial_id is None:
            current = "awaiting the first trial"
        else:
            match = re.fullmatch(r"trial-(\d{3})", state.current_trial_id)
            if match is None:
                raise ReportError("state has an invalid current trial ID")
            trial_number = int(match.group(1))
            try:
                subject_index = manifest.definition.subject_ids.index(state.current_target_id)
            except ValueError as error:
                raise ReportError("state has an unknown current target ID") from error
            position = subject_index * manifest.definition.iterations + trial_number
            subject_name = next(
                trial.subject_name
                for trial in comparison_runs[0].trials
                if trial.target_id == state.current_target_id
            )
            turn = str(state.current_turn) if state.current_turn is not None else "pending"
            current = (
                f"position {position}/{state.scheduled_trials}, {subject_name}, "
                f"trial {trial_number}/{manifest.definition.iterations}, turn {turn}"
            )
    table = _render_grid(
        ("Metric", "Value"),
        (
            TableRow(("State", state.status)),
            TableRow(("Completed", f"{state.terminal_trials}/{state.scheduled_trials} terminal")),
            TableRow(("Current", current)),
            TableRow(("Exceptions", exceptions)),
        ),
        right_columns=frozenset(),
        output_format=output_format,
    )
    return f"{_heading('Run status', output_format)}\n\n{table}"


def _finish_time(current_time: str, remaining_ms: int, timezone: tzinfo) -> str:
    rounded_seconds = (remaining_ms + 500) // 1_000
    finish = (_timestamp(current_time) + timedelta(seconds=rounded_seconds)).astimezone(timezone)
    return finish.strftime("%Y-%m-%d %H:%M:%S %Z")


def _timing_block(
    state: BenchmarkState,
    manifest: BenchmarkManifest,
    events: tuple[BenchmarkEvent, ...],
    current: CurrentRunProgress,
    overall_leader: ComparisonRun,
    timezone: tzinfo,
    output_format: ReportFormat,
) -> str:
    elapsed_ms = _active_elapsed_ms(events, state.updated_at)
    runtime = _duration(elapsed_ms)
    if state.status == "completed":
        table = _render_grid(
            ("Metric", "Value", "Basis"),
            (
                TableRow(("Active runtime", runtime, "Active benchmark time")),
                TableRow(("Linear ETA", "Complete", "All positions completed")),
                TableRow(("Leader-adjusted ETA", "Complete", "All positions completed")),
            ),
            right_columns=frozenset(),
            output_format=output_format,
        )
        return f"{_heading('Timing and ETA', output_format)}\n\n{table}"
    if state.status == "failed":
        table = _render_grid(
            ("Metric", "Value", "Basis"),
            (
                TableRow(("Active runtime", runtime, "Active benchmark time")),
                TableRow(("Linear ETA", "Stopped", "Run failed")),
                TableRow(("Leader-adjusted ETA", "Stopped", "Run failed")),
            ),
            right_columns=frozenset(),
            output_format=output_format,
        )
        return f"{_heading('Timing and ETA', output_format)}\n\n{table}"

    completed_positions = current.terminal_positions
    if completed_positions:
        linear_remaining_ms = round(
            Fraction(
                elapsed_ms * (len(overall_leader.trials) - completed_positions),
                completed_positions,
            )
        )
        linear_value = (
            f"{_duration(linear_remaining_ms)} remaining; finish "
            f"{_finish_time(state.updated_at, linear_remaining_ms, timezone)}"
        )
        linear_basis = (
            f"{completed_positions}/{len(overall_leader.trials)} completed positions; "
            f"{manifest.model.display_name}'s elapsed speed"
        )
    else:
        linear_value = "Unavailable"
        linear_basis = "No completed position"

    leader_total_ms = sum(trial.duration_ms for trial in overall_leader.trials)
    leader_progress_ms = Fraction(
        sum(trial.duration_ms for trial in overall_leader.trials[:completed_positions])
    )
    progress_description = f"{completed_positions} completed positions"
    positions = _positions(manifest)
    if (
        completed_positions < len(positions)
        and state.current_target_id is not None
        and state.current_trial_id is not None
        and state.current_turn is not None
    ):
        current_target_id, current_trial_number = positions[completed_positions]
        if state.current_target_id != current_target_id:
            raise ReportError("current timing target does not match the next position")
        if state.current_trial_id != f"trial-{current_trial_number:03d}":
            raise ReportError("current timing trial does not match the next position")
        leader_trial = overall_leader.trials[completed_positions]
        if leader_trial.evaluated_outputs > 0:
            comparable_turn = min(state.current_turn, leader_trial.evaluated_outputs)
            leader_progress_ms += Fraction(
                leader_trial.duration_ms * comparable_turn,
                leader_trial.evaluated_outputs,
            )
        progress_description = f"position {completed_positions + 1}, turn {state.current_turn}"

    if leader_total_ms <= 0 or leader_progress_ms <= 0 or elapsed_ms <= 0:
        adjusted_value = "Unavailable"
        adjusted_basis = "No comparable leader progress"
    else:
        projected_total_ms = round(Fraction(elapsed_ms * leader_total_ms, 1) / leader_progress_ms)
        remaining_ms = max(projected_total_ms - elapsed_ms, 0)
        with localcontext() as context:
            context.prec = 40
            progress_percent = (
                Decimal(leader_progress_ms.numerator)
                * Decimal(100)
                / Decimal(leader_progress_ms.denominator * leader_total_ms)
            )
        progress = progress_percent.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        adjusted_value = (
            f"{_duration(remaining_ms)} remaining; finish "
            f"{_finish_time(state.updated_at, remaining_ms, timezone)}"
        )
        adjusted_basis = (
            f"{progress:.1f}% of {overall_leader.display_name}'s actual timing through "
            f"{progress_description}; {manifest.model.display_name}'s elapsed speed"
        )
    table = _render_grid(
        ("Metric", "Value", "Basis"),
        (
            TableRow(("Active runtime", runtime, "Active benchmark time")),
            TableRow(("Linear ETA", linear_value, linear_basis)),
            TableRow(("Leader-adjusted ETA", adjusted_value, adjusted_basis)),
        ),
        right_columns=frozenset(),
        output_format=output_format,
    )
    return f"{_heading('Timing and ETA', output_format)}\n\n{table}"


def render_report(
    project_root: Path,
    model_id: str,
    execution_id: str,
    *,
    timezone: tzinfo | None = None,
    output_format: ReportFormat = "markdown",
    context_count: int = 0,
) -> str:
    if context_count < 0:
        raise ReportError("context count cannot be negative")
    report_timezone = timezone or datetime.now().astimezone().tzinfo
    if report_timezone is None:
        raise ReportError("cannot determine the report timezone")
    run_root = project_root / "runs" / model_id / execution_id
    manifest = _load_json(run_root / "manifest.json", BenchmarkManifest)
    if manifest.request.model_id != model_id or manifest.model.model_id != model_id:
        raise ReportError("model ID does not match the run manifest")
    if manifest.request.execution_id != execution_id:
        raise ReportError("execution ID does not match the run manifest")

    data_root = project_root / "docs" / "data"
    state = _load_state(run_root / "state.yml")
    events = _load_events(run_root / "benchmark-events.jsonl")
    publication = _load_json(data_root / "manifest.json", PublicationManifest)
    leaderboard = _load_json(data_root / "leaderboard.json", LeaderboardDocument)
    _validate_compatible_cohort(manifest, publication)
    positions = _positions(manifest)
    current = _current_trials(
        run_root,
        manifest,
        positions,
        failure_penalty_offset=publication.score_policy.failure_penalty_offset,
    )
    comparison_runs = _comparison_runs(data_root, leaderboard, positions)
    overall_leader = min(
        comparison_runs,
        key=lambda run: (run.overall_score, run.rank, run.display_name),
    )
    context_section = (
        _render_context(
            _recent_context(
                state,
                manifest,
                comparison_runs,
                events,
                current,
                context_count,
            ),
            manifest,
            output_format,
        )
        if context_count
        else None
    )
    scored_trials = current.trials
    scored_count = len(scored_trials)
    if scored_count == current.terminal_positions:
        snapshot = f"Current snapshot: {scored_count}/{len(positions)} completed."
    else:
        snapshot = (
            f"Current snapshot: {scored_count}/{len(positions)} scored; "
            f"{current.terminal_positions}/{len(positions)} terminal."
        )
    if not scored_trials:
        sections = [f"{snapshot} No scores are available yet."]
        if context_section is not None:
            sections.append(context_section)
        sections.extend(
            (
                _status_block(
                    state,
                    manifest,
                    comparison_runs,
                    events,
                    output_format,
                ),
                _timing_block(
                    state,
                    manifest,
                    events,
                    current,
                    overall_leader,
                    report_timezone,
                    output_format,
                ),
            )
        )
        return "\n\n".join(sections) + "\n"
    completed_count = len(scored_trials)
    current_leader = min(
        comparison_runs,
        key=lambda run: (
            _comparison_score(scored_trials, run),
            run.rank,
            run.display_name,
        ),
    )
    sections = [f"{snapshot} Lower is better."]
    if context_section is not None:
        sections.append(context_section)
    sections.extend(
        (
            _heading(f"Overall leader - {overall_leader.display_name}", output_format),
            _render_table(
                manifest.model.display_name,
                overall_leader,
                scored_trials,
                output_format,
            ),
            (
                f"{overall_leader.display_name}'s overall {len(positions)}-trial score: "
                + (
                    f"**{_two_decimals(overall_leader.overall_score)}**."
                    if output_format == "markdown"
                    else f"{_two_decimals(overall_leader.overall_score)}."
                )
            ),
            _heading(
                f"Current {completed_count}-position leader - {current_leader.display_name}",
                output_format,
            ),
            _render_table(
                manifest.model.display_name,
                current_leader,
                scored_trials,
                output_format,
            ),
            _status_block(state, manifest, comparison_runs, events, output_format),
            _timing_block(
                state,
                manifest,
                events,
                current,
                overall_leader,
                report_timezone,
                output_format,
            ),
        )
    )
    return "\n\n".join(sections) + "\n"


def _positive_integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare a running benchmark's completed positions with the published overall "
            "leader and the leader over the same position prefix."
        )
    )
    parser.add_argument("model_id", help="Benchmark model ID, for example M-0022")
    parser.add_argument("execution_id", help="Benchmark execution ID")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (defaults to the script's parent repository)",
    )
    parser.add_argument(
        "--timezone",
        help="IANA timezone for ETA finish times (defaults to the system timezone)",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "console"),
        nargs="?",
        const="console",
        default="markdown",
        help="Output format; providing the flag without a value selects console",
    )
    parser.add_argument(
        "--context",
        nargs="?",
        const=1,
        default=0,
        type=_positive_integer,
        metavar="COUNT",
        help=(
            "Show the latest question, answer, and Oracle evidence from the current and "
            "previous rounds; optionally set the number per round"
        ),
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        report_timezone = ZoneInfo(args.timezone) if args.timezone else None
        report = render_report(
            args.project_root.resolve(),
            args.model_id,
            args.execution_id,
            timezone=report_timezone,
            output_format=args.format,
            context_count=args.context,
        )
    except ZoneInfoNotFoundError as error:
        print(f"benchmark progress report failed: unknown timezone {error}", file=sys.stderr)
        return 1
    except ReportError as error:
        print(f"benchmark progress report failed: {error}", file=sys.stderr)
        return 1
    print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
