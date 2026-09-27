import json
from pathlib import Path

import pytest
from pydantic import JsonValue, ValidationError

from deep20_publication.cli import read_publication_config
from deep20_publication.draft import DraftReport, load_draft, render_draft
from deep20_publication.edition_registry import EditionRegistry
from deep20_publication.integrity import (
    PublicationInputError,
    canonical_json,
    parse_yaml_object,
    sha256_text,
)

ROOT = Path(__file__).parents[4]


def signed(value: dict[str, JsonValue]) -> dict[str, JsonValue]:
    return {**value, "integrity_hash": sha256_text(canonical_json(value))}


def fixture(root: Path) -> tuple[Path, dict[str, JsonValue]]:
    (root / "config").mkdir(parents=True)
    (root / "config/editions.yaml").write_text((ROOT / "config/editions.yaml").read_text())
    runtime: dict[str, JsonValue] = {"edition": {"edition_id": "1.2"}, "roles": {"guesser": {"implementation": "mock"}}}
    manifest = signed({"schema_version": 4, "request": {"execution_id": "BX-draft", "model_id": "M-9900", "runtime": runtime}})
    report = signed({"schema_version": 1, "edition_id": "1.2", "status": "draft", "execution_id": "BX-draft",
        "model_id": "M-9900", "runtime_fingerprint": sha256_text(canonical_json(runtime)),
        "manifest_integrity_hash": manifest["integrity_hash"], "synthetic": True, "publication_eligible": False,
        "scheduled_trials": 3, "scoring_eligible_trials": 0, "infrastructure_failed_trials": 0,
        "accounting_scope": "retained_episode_audits", "roles": [
            {"role": role, "backend": "mock", "model": "<script>private</script>", "logical_calls": 0,
             "inference_requests": 0, "control_bypasses": 0, "search_requests": 0, "extract_requests": 0,
             "input_tokens": 0, "output_tokens": 0, "reported_cost_usd": "0", "unmetered_calls": 0, "model_digests": []}
            for role in ("guesser", "oracle", "reviewer", "judge", "validator")]})
    path = root / "private/editions/1.2/runs/M-9900/BX-draft"
    path.mkdir(parents=True)
    (path / "manifest.json").write_text(json.dumps(manifest))
    (path / "draft-report.json").write_text(json.dumps(report))
    return path, report


def test_draft_preview_validates_signed_identity_and_escapes_html(tmp_path: Path) -> None:
    fixture(tmp_path)
    report = load_draft(tmp_path, edition_id="1.2", model_id="M-9900", run_id="BX-draft")
    html = render_draft(report)
    assert "1.2 DRAFT" in html
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "Unmetered calls" in html
    assert not (tmp_path / "docs").exists()


def test_tampered_projection_is_rejected(tmp_path: Path) -> None:
    path, report = fixture(tmp_path)
    report["scheduled_trials"] = 5
    (path / "draft-report.json").write_text(json.dumps(report))
    with pytest.raises(PublicationInputError, match="integrity"):
        load_draft(tmp_path, edition_id="1.2", model_id="M-9900", run_id="BX-draft")


def test_synthetic_scores_and_private_extra_fields_are_rejected(tmp_path: Path) -> None:
    _, report = fixture(tmp_path)
    with pytest.raises(ValidationError, match="eligible scores"):
        DraftReport.model_validate({**report, "scoring_eligible_trials": 3})
    with pytest.raises(ValidationError, match="Extra inputs"):
        DraftReport.model_validate({**report, "raw_response": "private text"})


def test_released_editions_are_the_only_public_registry_entries() -> None:
    registry = EditionRegistry.model_validate(parse_yaml_object((ROOT / "config/editions.yaml").read_text(), "registry"))
    config = read_publication_config(ROOT / "config/publication.yml")
    registry.validate_publication(config)
    assert config.default_edition_id == "1.1"
    assert {cohort.edition_id for cohort in config.cohorts} == {"1.0", "1.1"}
    assert next(e for e in registry.editions if e.edition_id == "1.2").status == "draft"


def test_public_edition_cannot_be_previewed_as_draft(tmp_path: Path) -> None:
    fixture(tmp_path)
    with pytest.raises(PublicationInputError, match="explicit draft"):
        load_draft(tmp_path, edition_id="1.1", model_id="M-9900", run_id="BX-draft")
