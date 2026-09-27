"""Verify the retained September 2026 records offline; never calls a provider."""

import hashlib
import json
import re
import zipfile
from collections import Counter
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from urllib.parse import unquote, urlsplit

BASE = Path(__file__).resolve().parent
BUTTONS = {
    "YES": "Yes",
    "NO": "No",
    "UNKNOWN": "Don't know",
    "RATHER_YES": "Probably",
    "RATHER_NO": "Probably not",
}


def main() -> None:
    catalog = json.loads((BASE / "oracle/subject-catalog.json").read_text())
    active = {k for k, v in catalog["subjects"].items() if v["status"] == "active"}
    assert len(active) == 10
    totals = {}
    for arm in ("oracle", "self-answered"):
        games = [
            json.loads(path.read_text()) for path in sorted((BASE / arm / "games").glob("*.json"))
        ]
        complete = [g for g in games if g["status"] == "completed"]
        expected_events = []
        assert {g["target_id"] for g in games} == active
        assert len({(g["target_id"], g["iteration"]) for g in games}) == len(games)
        for g in games:
            asks = [e for e in g["events"] if e["kind"] == "ASK"]
            assert [e["question_number"] for e in asks] == list(range(1, len(asks) + 1))
            assert all(e["answer"] in BUTTONS for e in g["events"] if e["kind"] != "CONTINUE")
            verified = sum(e["submission_verified"] for e in asks)
            wrong = sum(e["kind"] == "GUESS" and e["answer"] == "NO" for e in g["events"])
            assert g["answered_questions"] == verified
            assert g["rejected_guesses"] == wrong
            if g["status"] == "completed":
                assert all(e["submission_verified"] for e in g["events"])
                assert verified + wrong <= 40
                assert g["identified_within_20_questions"] == (g["success"] and verified <= 20)
                forty_key = (
                    "identified_within_40_counted_turns"
                    if arm == "oracle"
                    else "identified_within_40_counted_actions"
                )
                assert g[forty_key] == (g["success"] and verified + wrong <= 40)
                assert (
                    bool(any(e["kind"] == "GUESS" and e["answer"] == "YES" for e in g["events"]))
                    == g["success"]
                )
                if not g["success"]:
                    assert verified + wrong == 40
            else:
                assert g["success"] is None and g["identified_within_20_questions"] is None
            if arm == "self-answered":
                assert g["iteration"] == 1 and g["answering_arm"] == "self"
                assert g["api_cost_usd"] == "0"
                assert g["counted_actions"] == verified + wrong
                assert all(e["submission_verified"] for e in g["events"][:-1])
                if g["status"] == "infrastructure_failure":
                    assert g["target_id"] == "T-0002" and len(asks) == 19 and verified == 18
                    assert not asks[-1]["submission_verified"]
                    assert g["scoring_eligible"] is False
            else:
                assert all(e["submission_verified"] for e in g["events"])
            for i, e in enumerate(g["events"], 1):
                record = {
                    "answering_arm": "oracle" if arm == "oracle" else "self",
                    "target_id": g["target_id"],
                    "canonical_name": g["canonical_name"],
                    "iteration": g["iteration"],
                    "game_status": g["status"],
                    "event_number": i,
                    **e,
                }
                if arm == "self-answered":
                    record["button"] = BUTTONS[e["answer"]]
                expected_events.append(record)
        raw = [
            json.loads(line)
            for line in (BASE / arm / "raw-web-events.jsonl").read_text().splitlines()
        ]
        assert raw == expected_events
        totals[arm] = {
            "starts": len(games),
            "scored": len(complete),
            "wins40": sum(g["success"] for g in complete),
            "wins20": sum(g["identified_within_20_questions"] for g in complete),
            "confirmed_questions": sum(g["answered_questions"] for g in games),
            "completed_questions": sum(g["answered_questions"] for g in complete),
        }
        if arm == "oracle":
            cost = sum(Decimal(g["known_api_cost_usd"]) for g in games)
            ledger = json.loads((BASE / arm / "budget.json").read_text())
            assert cost == Decimal(ledger["known_spent_usd"]) == Decimal("3.7221445200000000011")
            assert cost < Decimal(ledger["cap_usd"]) == Decimal(7)
            partial = next(g for g in games if g["status"] != "completed")
            assert partial["target_id"] == "T-0011" and partial["answered_questions"] == 23
            assert partial["status"] == "stopped_by_user" and partial["scoring_eligible"] is False
            unsubmitted = [
                json.loads(line)
                for line in (BASE / arm / "unsubmitted-adjudications.jsonl")
                .read_text()
                .splitlines()
            ]
            assert len(unsubmitted) == 1 and unsubmitted[0]["question_number"] == 24
            assert unsubmitted[0]["submitted"] is False
        else:
            questions = [e for e in raw if e["kind"] == "ASK"]
            qraw = [
                json.loads(line)
                for line in (BASE / arm / "raw-questions-and-answers.jsonl")
                .read_text()
                .splitlines()
            ]
            assert qraw == questions and len(questions) == 231
            distribution = Counter(e["answer"] for e in questions if e["submission_verified"])
            metrics = json.loads((BASE / arm / "results.json").read_text())
            assert metrics["confirmed_answer_distribution"] == distribution
            assert metrics["confirmed_factual_answers"] == 230
            assert metrics["rejected_guesses"] == 2
            assert metrics["mean_questions_successful_games"] == 21.75
            assert metrics["mean_questions_completed_games"] == 212 / 9
    assert totals == {
        "oracle": {
            "starts": 19,
            "scored": 18,
            "wins40": 8,
            "wins20": 2,
            "confirmed_questions": 607,
            "completed_questions": 584,
        },
        "self-answered": {
            "starts": 10,
            "scored": 9,
            "wins40": 8,
            "wins20": 4,
            "confirmed_questions": 230,
            "completed_questions": 212,
        },
    }
    llm = json.loads((BASE / "llm-question-counts.json").read_text())
    assert llm["metric"] == "actual_factual_ASK_count" and llm["new_provider_calls"] == 0
    assert len(llm["models"]) == llm["model_count"] == 12
    assert len(llm["trials"]) == llm["included_game_count"] == 359
    assert len(llm["excluded_trials"]) == llm["excluded_infrastructure_game_count"] == 1
    assert {s["target_id"] for s in llm["subjects"]} == active
    assert len({m["model_id"] for m in llm["models"]}) == 12
    assert len({(t["model_id"], t["target_id"], t["trial_number"]) for t in llm["trials"]}) == 359
    repo = BASE.parents[2]
    checked_hashes = {}
    for model in llm["models"]:
        assert model["max_counted_actions"] == 40 and model["prompt_profile"] == "qualified_v1"
        own = [t for t in llm["trials"] if t["model_id"] == model["model_id"]]
        assert len(own) == model["included_trials"]
        assert all(t["execution_id"] == model["execution_id"] for t in own)
        for key in ("manifest", "source"):
            relative_path = model[f"{key}_path"]
            if relative_path not in checked_hashes:
                checked_hashes[relative_path] = hashlib.sha256(
                    (repo / relative_path).read_bytes()
                ).hexdigest()
            assert checked_hashes[relative_path] == model[f"{key}_sha256"]
    llm_subject_means = []
    for subject in llm["subjects"]:
        model_means = []
        assert subject["model_count"] == len(subject["per_model"]) == 12
        assert {m["model_id"] for m in subject["per_model"]} == {
            m["model_id"] for m in llm["models"]
        }
        for model in subject["per_model"]:
            counts = [
                t["ask_count"]
                for t in llm["trials"]
                if t["model_id"] == model["model_id"] and t["target_id"] == subject["target_id"]
            ]
            assert counts == model["question_counts"] and len(counts) == model["trial_count"]
            mean = Fraction(sum(counts), len(counts))
            assert mean == Fraction(model["mean_questions_exact"])
            assert float(mean) == model["mean_questions"]
            model_means.append(mean)
        mean = sum(model_means) / len(model_means)
        assert mean == Fraction(subject["mean_questions_exact"])
        assert float(mean) == subject["mean_questions"]
        assert subject["trial_count"] == sum(m["trial_count"] for m in subject["per_model"])
        llm_subject_means.append(mean)
    llm_macro = sum(llm_subject_means) / len(llm_subject_means)
    question_total = sum(t["ask_count"] for t in llm["trials"])
    assert question_total == llm["total_factual_questions"] == 6477
    llm_pooled = Fraction(question_total, len(llm["trials"]))
    assert llm_macro == Fraction(llm["mean_questions_across_subjects_exact"])
    assert llm_pooled == Fraction(llm["mean_questions_across_games_exact"])
    assert all(0 <= t["ask_count"] <= t["counted_actions"] <= 40 for t in llm["trials"])
    for relative_path in ("README.md", "oracle/summary.md", "self-answered/summary.md"):
        section = (
            (BASE / relative_path)
            .read_text()
            .split("## Question-count comparison\n", 1)[1]
            .split("\n## ", 1)[0]
        )
        for subject in llm["subjects"]:
            row = next(
                line
                for line in section.splitlines()
                if line.startswith(f"| {subject['canonical_name']} |")
            )
            assert row.endswith(f"| {subject['mean_questions']:.2f} |")
        assert (
            f"| **Average across subjects** | **32.50** | **23.56** | **{float(llm_macro):.2f}** |"
            in section
        )
        assert (
            f"| **Average across all completed games** | **32.44** | **23.56** | **{float(llm_pooled):.2f}** |"
            in section
        )
    with zipfile.ZipFile(BASE / "oracle/raw-data.zip") as archive:
        assert len(archive.infolist()) == 4929
        assert archive.testzip() is None
        inventory = json.loads((BASE / "oracle/raw-data-inventory.json").read_text())
        for item in inventory["files"]:
            assert archive.getinfo(item["path"]).file_size == item["bytes"]
        assert not any(
            Path(n).name in {"openrouter.yml", "openrouter.yaml"} for n in archive.namelist()
        )
    screenshots = sorted((BASE / "self-answered/screenshots").glob("*"))
    assert len(screenshots) == 2
    for path in screenshots:
        data = path.read_bytes()
        assert path.suffix == ".webp" and data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    for path in BASE.rglob("*.md"):
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            parts = urlsplit(target)
            if not parts.scheme and parts.path:
                assert (path.parent / unquote(parts.path)).is_file(), (path, target)
    print(
        json.dumps(
            {
                "verified": True,
                "arms": totals,
                "archive_entries": 4929,
                "webp_screenshots": 2,
                "llm_models": 12,
                "llm_scored_games": 359,
                "llm_mean_questions_across_subjects": float(llm_macro),
                "llm_mean_questions_across_games": float(llm_pooled),
                "provider_calls": 0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
