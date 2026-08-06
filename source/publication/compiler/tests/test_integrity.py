from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import JsonValue, ValidationError

from deep20_publication.integrity import (
    PublicationInputError,
    canonical_json,
    parse_yaml_object,
    sha256_text,
    verify_signed_object,
)
from deep20_publication.loader import parse_diagnostic_error_outputs
from deep20_publication.models import (
    BenchmarkManifestArtifact,
    BenchmarkSummaryArtifact,
    ContractReliabilitySnapshot,
    EpisodeContractViolationTurn,
    EpisodeResultArtifact,
    ErrorOutputPreview,
    EvidenceDecisionBasisSnapshot,
    EvidenceReviewDecisionSnapshot,
    GamePolicySnapshot,
    PublicRun,
    PublishedDataset,
    TrialArtifactReferences,
)


def test_yaml_loader_rejects_duplicate_keys() -> None:
    with pytest.raises(PublicationInputError, match="duplicate key"):
        parse_yaml_object("value: 1\nvalue: 2\n", "duplicate.yml")


def test_integrity_verification_rejects_modified_payload() -> None:
    payload: dict[str, JsonValue] = {"schema_version": 1, "value": "original"}
    signed: dict[str, JsonValue] = {
        "payload": payload,
        "integrity_hash": sha256_text(canonical_json({"payload": payload})),
    }
    signed["payload"] = {"schema_version": 1, "value": "modified"}

    with pytest.raises(PublicationInputError, match="integrity hash mismatch"):
        verify_signed_object(signed, "test")


def test_publication_contract_accepts_only_current_artifact_versions() -> None:
    assert BenchmarkManifestArtifact.model_fields["schema_version"].default == 3
    assert BenchmarkSummaryArtifact.model_fields["schema_version"].default == 3
    assert EpisodeResultArtifact.model_fields["schema_version"].default == 9
    assert PublishedDataset.model_fields["schema_version"].default == 8
    assert "working_tree_dirty_before_run" not in BenchmarkManifestArtifact.model_fields
    assert "clean_worktree" not in PublicRun.model_fields

    with pytest.raises(ValidationError, match="Input should be 3"):
        BenchmarkManifestArtifact.model_validate({"schema_version": 2})
    with pytest.raises(ValidationError, match="Input should be 9"):
        EpisodeResultArtifact.model_validate({"schema_version": 8})


def test_publication_contract_rejects_retired_policy_snapshots() -> None:
    common = {
        "benchmark_mode": "official",
        "max_questions": 50,
        "max_consecutive_contract_violations": 2,
        "reveal_entity_type": True,
        "final_guess_after_limit": True,
        "include_oracle_evidence": True,
        "include_guesser_conversation": True,
    }

    with pytest.raises(ValidationError, match="Input should be 9"):
        GamePolicySnapshot.model_validate({"version": 8, **common})
    assert (
        GamePolicySnapshot.model_validate(
            {
                "version": 9,
                **common,
            }
        ).version
        == 9
    )


def test_publication_contract_accepts_bounded_reviewer_model_knowledge() -> None:
    decision = EvidenceReviewDecisionSnapshot.model_validate(
        {
            "answer": "NO",
            "basis": "model_knowledge",
            "evidence_indices": [],
        }
    )

    assert decision.basis is EvidenceDecisionBasisSnapshot.MODEL_KNOWLEDGE
    with pytest.raises(ValidationError, match="must not identify supporting evidence"):
        EvidenceReviewDecisionSnapshot.model_validate(
            {
                "answer": "NO",
                "basis": "model_knowledge",
                "evidence_indices": [1],
            }
        )


def test_contract_violation_turn_requires_feedback_only_for_counted_penalty() -> None:
    violation = EpisodeContractViolationTurn(
        turn_number=1,
        violation_code="invalid_guesser_output",
        violation_kind="invalid_json",
        feedback_event="FORMAT_ERROR",
        counted=True,
        counted_questions=1,
        guesser_call_id=f"GC-{'0' * 32}",
    )

    assert violation.feedback_event == "FORMAT_ERROR"

    with pytest.raises(ValidationError, match="only counted contract violations"):
        violation.model_copy(
            update={"counted": False},
        ).__class__.model_validate(
            {
                **violation.model_dump(mode="json"),
                "counted": False,
            }
        )


def test_contract_reliability_keeps_success_independent_from_breach() -> None:
    reliability = ContractReliabilitySnapshot(
        evaluated_outputs=31,
        valid_outputs=30,
        violations=1,
        counted_penalties=1,
        affected_trials=1,
        compliance_rate=Decimal(30) / Decimal(31),
        status="breached",
    )

    assert reliability.status == "breached"
    assert reliability.valid_outputs == 30


def test_error_output_preview_enforces_the_250_character_crop() -> None:
    preview = ErrorOutputPreview(
        component="guesser",
        attempt_number=2,
        finish_reason="length",
        text="x" * 250,
        original_characters=10_000,
        trailing_whitespace_characters=9_700,
        truncated=True,
    )

    assert len(preview.text) == 250
    with pytest.raises(ValidationError, match="String should have at most 250 characters"):
        ErrorOutputPreview(
            component="guesser",
            attempt_number=2,
            finish_reason="length",
            text="x" * 251,
            original_characters=10_000,
            trailing_whitespace_characters=9_700,
            truncated=True,
        )


def test_trial_artifacts_accept_private_error_output_reference() -> None:
    artifacts = TrialArtifactReferences.model_validate(
        {
            "trial_result": {
                "relative_path": "runs/M-0001/BX-example/trial/result.yml",
                "integrity_hash": "0" * 64,
            },
            "error_outputs": None,
        }
    )

    assert artifacts.error_outputs is None


def test_private_error_output_capture_validates_integrity_and_strips_no_text() -> None:
    unsigned: dict[str, JsonValue] = {
        "schema_version": 1,
        "component": "guesser",
        "call_id": f"GC-{'1' * 32}",
        "failure_code": "invalid_guesser_output",
        "recovered": False,
        "recovery": {},
        "outputs": [
            {
                "attempt_number": 1,
                "response_id": "private-provider-id",
                "finish_reason": "stop",
                "output": '{"result":{"action":"ASK","question":""}}',
            }
        ],
        "recorded_at": "2026-07-30T12:00:00+00:00",
    }
    signed: dict[str, JsonValue] = {
        **unsigned,
        "integrity_hash": sha256_text(canonical_json(unsigned)),
    }
    text = canonical_json(signed) + "\n"

    records = parse_diagnostic_error_outputs(
        text=text,
        label="error-outputs.jsonl",
        expected_record_count=1,
        expected_integrity_hash=sha256_text(text),
    )

    assert records[0].outputs[0].output.endswith('question":""}}')
    with pytest.raises(PublicationInputError, match="signed artifact reference"):
        parse_diagnostic_error_outputs(
            text=text,
            label="error-outputs.jsonl",
            expected_record_count=1,
            expected_integrity_hash="0" * 64,
        )
