from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCRIPT = PROJECT_ROOT / "scripts" / "benchmark-progress-report.py"


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _manifest() -> dict[str, object]:
    return {
        "schema_version": 3,
        "request": {
            "benchmark_id": "B-0001",
            "execution_id": "BX-test",
            "model_id": "M-9000",
            "benchmark_mode": "official",
            "base_seed": 0,
        },
        "definition": {
            "benchmark_id": "B-0001",
            "subject_ids": ["T-0001"],
            "iterations": 3,
            "game_policy": {"version": 9, "max_questions": 50},
        },
        "model": {"model_id": "M-9000", "display_name": "Candidate (high)"},
    }


def _trial(
    trial_number: int,
    *,
    questions: int,
    cost: str,
    success: bool = True,
    violations: int = 0,
    duration_ms: int = 10_000,
    superseded_costs: tuple[str, ...] = (),
) -> dict[str, object]:
    return {
        "payload": {
            "status": "completed",
            "identity": {
                "execution_id": "BX-test",
                "model_id": "M-9000",
                "target_id": "T-0001",
                "trial_id": f"trial-{trial_number:03d}",
                "trial_number": trial_number,
            },
            "result": {
                "run": {
                    "subject": {"canonical_name": "Example Subject"},
                    "duration_ms": duration_ms,
                },
                "outcome": {"success": success, "scoring_eligible": True},
                "summary": {
                    "counted_questions": questions,
                    "contract": {
                        "evaluated_outputs": questions + 1,
                        "violations": violations,
                    },
                    "costs_usd": {"total": cost},
                },
            },
            "superseded_attempts": [
                {"partial_metrics": {"cost_usd": superseded_cost}}
                for superseded_cost in superseded_costs
            ],
        }
    }


def _infrastructure_failure(trial_number: int) -> dict[str, object]:
    return {
        "payload": {
            "status": "infrastructure_failed",
            "identity": {
                "execution_id": "BX-test",
                "model_id": "M-9000",
                "target_id": "T-0001",
                "trial_id": f"trial-{trial_number:03d}",
                "trial_number": trial_number,
            },
        }
    }


def _published_subject(
    execution_id: str,
    scores: tuple[int, int, int],
    costs: tuple[str, str, str],
    violations: tuple[int, int, int] = (0, 0, 0),
    durations_ms: tuple[int, int, int] = (10_000, 10_000, 10_000),
) -> dict[str, object]:
    return {
        "document_type": "subject",
        "schema_version": 1,
        "execution_id": execution_id,
        "target_id": "T-0001",
        "profile": {"subject_name": "Example Subject"},
        "trials": [
            {
                "trial_id": f"trial-{number:03d}",
                "trial_number": number,
                "penalized_questions": str(score),
                "cost_usd": cost,
                "duration_ms": duration_ms,
                "contract": {
                    "evaluated_outputs": score + 1,
                    "violations": violation_count,
                },
            }
            for number, (score, cost, violation_count, duration_ms) in enumerate(
                zip(scores, costs, violations, durations_ms, strict=True), start=1
            )
        ],
    }


def _fixture(tmp_path: Path) -> None:
    _write_json(tmp_path / "runs/M-9000/BX-test/manifest.json", _manifest())
    _write_json(
        tmp_path / "runs/M-9000/BX-test/state.yml",
        {
            "payload": {
                "schema_version": 1,
                "execution_id": "BX-test",
                "model_id": "M-9000",
                "status": "running",
                "scheduled_trials": 3,
                "started_trials": 3,
                "terminal_trials": 2,
                "current_target_id": "T-0001",
                "current_trial_id": "trial-003",
                "current_turn": 4,
                "last_failure": None,
                "updated_at": "2026-01-01T00:00:24+00:00",
            }
        },
    )
    events_path = tmp_path / "runs/M-9000/BX-test/benchmark-events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    events_path.write_text(
        json.dumps(
            {
                "event_type": "benchmark_started",
                "recorded_at": "2026-01-01T00:00:00+00:00",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    _write_json(
        tmp_path / "runs/M-9000/BX-test/subjects/T-0001/trials/trial-001/result.yml",
        _trial(1, questions=8, cost="0.17"),
    )
    _write_json(
        tmp_path / "runs/M-9000/BX-test/subjects/T-0001/trials/trial-002/result.yml",
        _trial(2, questions=10, cost="0.22"),
    )
    _write_json(
        tmp_path / "docs/data/manifest.json",
        {
            "document_type": "manifest",
            "schema_version": 1,
            "score_policy": {
                "version": "average-then-average-v1",
                "failure_penalty_offset": 1,
            },
            "active_cohort": {
                "benchmark_id": "B-0001",
                "benchmark_version": 9,
                "target_ids": ["T-0001"],
                "iterations": 3,
                "base_seed": 0,
                "max_questions": 50,
            },
        },
    )
    _write_json(
        tmp_path / "docs/data/leaderboard.json",
        {
            "document_type": "leaderboard",
            "schema_version": 3,
            "leaderboard": [
                {
                    "rank": 1,
                    "model": {"model_id": "M-0001", "display_name": "Overall (high)"},
                    "status": "evaluated",
                    "execution_id": "BX-overall",
                    "question_score": "10",
                },
                {
                    "rank": 2,
                    "model": {"model_id": "M-0002", "display_name": "Prefix (medium)"},
                    "status": "evaluated",
                    "execution_id": "BX-prefix",
                    "question_score": "18.66666666666666666666666667",
                },
            ],
        },
    )
    _write_json(
        tmp_path / "docs/data/runs/BX-overall/subjects/T-0001.json",
        _published_subject("BX-overall", (10, 10, 10), ("0.40", "0.60", "0.50")),
    )
    _write_json(
        tmp_path / "docs/data/runs/BX-prefix/subjects/T-0001.json",
        _published_subject("BX-prefix", (2, 4, 50), ("0.01", "0.02", "0.03")),
    )


def _turn_event(
    *,
    trial_number: int,
    turn_number: int,
    question: str,
    answer: str,
    excerpt: str,
    source_url: str,
    recorded_at: str,
) -> dict[str, object]:
    return {
        "event_type": "turn_resolved",
        "recorded_at": recorded_at,
        "identity": {
            "target_id": "T-0001",
            "trial_id": f"trial-{trial_number:03d}",
            "trial_number": trial_number,
        },
        "progress": {
            "turn": {
                "turn_number": turn_number,
                "action": {"action": "ASK", "question": question},
                "adjudication": {
                    "answer": answer,
                    "evidence": [
                        {
                            "excerpt": excerpt,
                            "source_url": source_url,
                        }
                    ],
                },
            }
        },
    }


def _add_context_events(tmp_path: Path) -> None:
    events_path = tmp_path / "runs/M-9000/BX-test/benchmark-events.jsonl"
    events = (
        _turn_event(
            trial_number=2,
            turn_number=10,
            question="Was this the previous question?",
            answer="NO",
            excerpt="Previous evidence excerpt.",
            source_url="https://example.com/previous",
            recorded_at="2026-01-01T00:00:10+00:00",
        ),
        _turn_event(
            trial_number=3,
            turn_number=2,
            question="Should this older question be omitted?",
            answer="UNKNOWN",
            excerpt="Older evidence excerpt.",
            source_url="https://example.com/older",
            recorded_at="2026-01-01T00:00:18+00:00",
        ),
        _turn_event(
            trial_number=3,
            turn_number=4,
            question="Is this the current question?",
            answer="YES",
            excerpt="Current evidence excerpt.",
            source_url="https://example.com/current",
            recorded_at="2026-01-01T00:00:24+00:00",
        ),
    )
    with events_path.open("a", encoding="utf-8") as stream:
        for event in events:
            stream.write(json.dumps(event) + "\n")


def test_report_renders_both_leaders_scores_subjects_averages_and_costs(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "M-9000",
            "BX-test",
            "--project-root",
            str(tmp_path),
            "--timezone",
            "UTC",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (
        result.stdout
        == """Current snapshot: 2/3 completed. Lower is better.

**Overall leader - Overall (high)**

| Position | Subject | Candidate | Overall | Cumulative cost: Candidate / Overall | Contract breaks: Candidate / Overall |
|---:|---|---:|---:|---:|---:|
| 1 | Example Subject | 8 | 10 | $0.17 / $0.40 | 0 / 0 |
| 2 | Example Subject | 10 | 10 | $0.39 / $1.00 | 0 / 0 |
| **Subject average (2/3)** | **Example Subject** | **9.00** | **10.00** | **$0.39 / $1.00** | **0 / 0** |
| **Average** |  | **9.00** | **10.00** | **$0.39 / $1.00** | **0 / 0** |

Overall (high)'s overall 3-trial score: **10.00**.

**Current 2-position leader - Prefix (medium)**

| Position | Subject | Candidate | Prefix | Cumulative cost: Candidate / Prefix | Contract breaks: Candidate / Prefix |
|---:|---|---:|---:|---:|---:|
| 1 | Example Subject | 8 | 2 | $0.17 / $0.01 | 0 / 0 |
| 2 | Example Subject | 10 | 4 | $0.39 / $0.03 | 0 / 0 |
| **Subject average (2/3)** | **Example Subject** | **9.00** | **3.00** | **$0.39 / $0.03** | **0 / 0** |
| **Average** |  | **9.00** | **3.00** | **$0.39 / $0.03** | **0 / 0** |

**Run status**

| Metric | Value |
|---|---|
| State | running |
| Completed | 2/3 terminal |
| Current | position 3/3, Example Subject, trial 3/3, turn 4 |
| Exceptions | none |

**Timing and ETA**

| Metric | Value | Basis |
|---|---|---|
| Active runtime | 24s | Active benchmark time |
| Linear ETA | 12s remaining; finish 2026-01-01 00:00:36 UTC | 2/3 completed positions; Candidate (high)'s elapsed speed |
| Leader-adjusted ETA | 6s remaining; finish 2026-01-01 00:00:30 UTC | 78.8% of Overall (high)'s actual timing through position 3, turn 4; Candidate (high)'s elapsed speed |
"""
    )


def test_report_uses_the_publication_penalty_for_model_failures(tmp_path: Path) -> None:
    _fixture(tmp_path)
    _write_json(
        tmp_path / "runs/M-9000/BX-test/subjects/T-0001/trials/trial-002/result.yml",
        _trial(2, questions=10, cost="0.22", success=False),
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "M-9000",
            "BX-test",
            "--project-root",
            str(tmp_path),
            "--timezone",
            "UTC",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "| 2 | Example Subject | 51 | 10 | $0.39 / $1.00 | 0 / 0 |" in result.stdout
    assert "| **Average** |  | **29.50** | **10.00** | **$0.39 / $1.00** |" in result.stdout


def test_report_includes_superseded_repair_attempt_costs(tmp_path: Path) -> None:
    _fixture(tmp_path)
    _write_json(
        tmp_path / "runs/M-9000/BX-test/subjects/T-0001/trials/trial-002/result.yml",
        _trial(
            2,
            questions=10,
            cost="0.22",
            superseded_costs=("1.11", "2.22"),
        ),
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "M-9000",
            "BX-test",
            "--project-root",
            str(tmp_path),
            "--timezone",
            "UTC",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "| 2 | Example Subject | 10 | 10 | $3.72 / $1.00 | 0 / 0 |" in result.stdout


def test_report_skips_infrastructure_failures_without_losing_schedule_alignment(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    _write_json(
        tmp_path / "runs/M-9000/BX-test/subjects/T-0001/trials/trial-002/result.yml",
        _infrastructure_failure(2),
    )

    active_result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "M-9000",
            "BX-test",
            "--project-root",
            str(tmp_path),
            "--timezone",
            "UTC",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert active_result.returncode == 0, active_result.stderr
    assert "Current snapshot: 1/3 scored; 2/3 terminal. Lower is better." in active_result.stdout
    assert "**Current 1-position leader - Prefix (medium)**" in active_result.stdout
    assert "position 3, turn 4; Candidate (high)'s elapsed speed" in active_result.stdout

    _write_json(
        tmp_path / "runs/M-9000/BX-test/subjects/T-0001/trials/trial-003/result.yml",
        _trial(3, questions=12, cost="0.25"),
    )
    _write_json(
        tmp_path / "runs/M-9000/BX-test/state.yml",
        {
            "payload": {
                "schema_version": 1,
                "execution_id": "BX-test",
                "model_id": "M-9000",
                "status": "completed",
                "scheduled_trials": 3,
                "started_trials": 3,
                "terminal_trials": 3,
                "current_target_id": None,
                "current_trial_id": None,
                "current_turn": None,
                "last_failure": None,
                "updated_at": "2026-01-01T00:00:30+00:00",
            }
        },
    )

    completed_result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "M-9000",
            "BX-test",
            "--project-root",
            str(tmp_path),
            "--timezone",
            "UTC",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed_result.returncode == 0, completed_result.stderr
    assert "Current snapshot: 2/3 scored; 3/3 terminal. Lower is better." in completed_result.stdout
    assert "| 3 | Example Subject | 12 | 10 | $0.42 / $0.90 | 0 / 0 |" in (completed_result.stdout)
    assert "**Current 2-position leader - Overall (high)**" in completed_result.stdout


def test_report_counts_trial_and_summary_contract_breaks(tmp_path: Path) -> None:
    _fixture(tmp_path)
    _write_json(
        tmp_path / "runs/M-9000/BX-test/subjects/T-0001/trials/trial-002/result.yml",
        _trial(2, questions=10, cost="0.22", violations=2),
    )
    _write_json(
        tmp_path / "docs/data/runs/BX-overall/subjects/T-0001.json",
        _published_subject(
            "BX-overall",
            (10, 10, 10),
            ("0.40", "0.60", "0.50"),
            violations=(1, 0, 0),
        ),
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "M-9000",
            "BX-test",
            "--project-root",
            str(tmp_path),
            "--timezone",
            "UTC",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "| 1 | Example Subject | 8 | 10 | $0.17 / $0.40 | 0 / 1 |" in result.stdout
    assert "| 2 | Example Subject | 10 | 10 | $0.39 / $1.00 | 2 / 0 |" in result.stdout
    assert (
        "| **Subject average (2/3)** | **Example Subject** | **9.00** | "
        "**10.00** | **$0.39 / $1.00** | **2 / 1** |" in result.stdout
    )
    assert (
        "| **Average** |  | **9.00** | **10.00** | **$0.39 / $1.00** | **2 / 1** |" in result.stdout
    )


def test_report_optional_format_flag_renders_padded_console_tables(tmp_path: Path) -> None:
    _fixture(tmp_path)
    _add_context_events(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "M-9000",
            "BX-test",
            "--project-root",
            str(tmp_path),
            "--timezone",
            "UTC",
            "--format",
            "--context",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "**" not in result.stdout
    assert "|---" not in result.stdout
    assert "Overall leader - Overall (high)" in result.stdout
    assert "Recent context" in result.stdout
    assert "Current evidence excerpt." in result.stdout
    assert "https://example.com/previous" in result.stdout
    assert "Should this older question be omitted?" not in result.stdout
    assert re.search(
        r"\|\s+1 \| Example Subject\s+\|\s+8 \|\s+10 \|",
        result.stdout,
    )
    assert re.search(
        r"\| Linear ETA\s+\| 12s remaining; finish 2026-01-01 00:00:36 UTC\s+\|",
        result.stdout,
    )
    assert "+=======================+" in result.stdout


def test_context_count_adds_recent_questions_answers_and_oracle_evidence(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    _add_context_events(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "M-9000",
            "BX-test",
            "--project-root",
            str(tmp_path),
            "--timezone",
            "UTC",
            "--context",
            "2",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.index("**Recent context**") < result.stdout.index(
        "**Overall leader - Overall (high)**"
    )
    assert "**Current round - Example Subject - position 3/3 - trial 3/3**" in result.stdout
    assert "Should this older question be omitted?" in result.stdout
    assert "Is this the current question?" in result.stdout
    assert "**Answer:** YES" in result.stdout
    assert "Current evidence excerpt." in result.stdout
    assert "Source: https://example.com/current" in result.stdout
    assert "**Last round - Example Subject - position 2/3 - trial 2/3**" in result.stdout
    assert "Was this the previous question?" in result.stdout
    assert "**Answer:** NO" in result.stdout
    assert "Previous evidence excerpt." in result.stdout
    assert "Source: https://example.com/previous" in result.stdout


def test_report_status_includes_recorded_infrastructure_exceptions(tmp_path: Path) -> None:
    _fixture(tmp_path)
    _write_json(
        tmp_path / "runs/M-9000/BX-test/state.yml",
        {
            "payload": {
                "schema_version": 1,
                "execution_id": "BX-test",
                "model_id": "M-9000",
                "status": "running",
                "scheduled_trials": 3,
                "started_trials": 3,
                "terminal_trials": 2,
                "current_target_id": "T-0001",
                "current_trial_id": "trial-003",
                "current_turn": 4,
                "last_failure": {"code": "provider_unavailable"},
                "updated_at": "2026-01-01T00:00:24+00:00",
            }
        },
    )
    events_path = tmp_path / "runs/M-9000/BX-test/benchmark-events.jsonl"
    events_path.write_text(
        json.dumps(
            {
                "event_type": "benchmark_started",
                "recorded_at": "2026-01-01T00:00:00+00:00",
            }
        )
        + "\n"
        + json.dumps(
            {
                "event_type": "trial_finished",
                "status": "infrastructure_failed",
                "recorded_at": "2026-01-01T00:00:10+00:00",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "M-9000",
            "BX-test",
            "--project-root",
            str(tmp_path),
            "--timezone",
            "UTC",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (
        "| Exceptions | 1 infrastructure failure; latest code: provider_unavailable |"
        in result.stdout
    )


def test_report_status_marks_historical_infrastructure_failures_as_repaired(
    tmp_path: Path,
) -> None:
    _fixture(tmp_path)
    _write_json(
        tmp_path / "runs/M-9000/BX-test/subjects/T-0001/trials/trial-003/result.yml",
        _trial(3, questions=6, cost="0.12"),
    )
    _write_json(
        tmp_path / "runs/M-9000/BX-test/state.yml",
        {
            "payload": {
                "schema_version": 1,
                "execution_id": "BX-test",
                "model_id": "M-9000",
                "status": "completed",
                "scheduled_trials": 3,
                "started_trials": 3,
                "terminal_trials": 3,
                "current_target_id": None,
                "current_trial_id": None,
                "current_turn": None,
                "last_failure": None,
                "updated_at": "2026-01-01T00:00:30+00:00",
            }
        },
    )
    events_path = tmp_path / "runs/M-9000/BX-test/benchmark-events.jsonl"
    events_path.write_text(
        "\n".join(
            json.dumps(event)
            for event in (
                {
                    "event_type": "benchmark_started",
                    "recorded_at": "2026-01-01T00:00:00+00:00",
                },
                {
                    "event_type": "trial_finished",
                    "status": "infrastructure_failed",
                    "recorded_at": "2026-01-01T00:00:10+00:00",
                },
                {
                    "event_type": "benchmark_finished",
                    "recorded_at": "2026-01-01T00:00:30+00:00",
                },
            )
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "M-9000",
            "BX-test",
            "--project-root",
            str(tmp_path),
            "--timezone",
            "UTC",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "| Exceptions | 1 repaired infrastructure failure |" in result.stdout
