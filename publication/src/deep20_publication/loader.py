from __future__ import annotations

import json

from pydantic import BaseModel, JsonValue, ValidationError

from .integrity import (
    PublicationInputError,
    sha256_text,
    verify_signed_object,
)
from .models import (
    BenchmarkManifestArtifact,
    BenchmarkStateEnvelope,
    BenchmarkSummaryEnvelope,
    CompletedTrialArtifactEnvelope,
    LoadedEpisode,
    LoadedRun,
    ModelCatalog,
    PublicationConfig,
    SubjectCatalog,
)


def _validate_model[ModelT: BaseModel](
    model: type[ModelT],
    value: object,
    label: str,
) -> ModelT:
    try:
        return model.model_validate(value)
    except ValidationError as error:
        raise PublicationInputError(f"{label} schema validation failed: {error}") from error


def parse_publication_config(
    value: dict[str, JsonValue],
    label: str,
) -> PublicationConfig:
    return _validate_model(PublicationConfig, value, label)


def parse_model_catalog(value: dict[str, JsonValue], label: str) -> ModelCatalog:
    return _validate_model(ModelCatalog, value, label)


def parse_subject_catalog(
    value: dict[str, JsonValue],
    label: str,
) -> tuple[SubjectCatalog, str]:
    catalog = _validate_model(SubjectCatalog, value, label)
    payload = catalog.model_dump(mode="json")
    serialized = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return catalog, sha256_text(serialized)


def parse_run(
    *,
    summary: dict[str, JsonValue],
    manifest: dict[str, JsonValue],
    state: dict[str, JsonValue],
    summary_label: str,
    manifest_label: str,
    state_label: str,
    relative_summary_path: str,
) -> LoadedRun:
    verify_signed_object(summary, summary_label)
    verify_signed_object(manifest, manifest_label)
    verify_signed_object(state, state_label)

    envelope = _validate_model(
        BenchmarkSummaryEnvelope,
        summary,
        summary_label,
    )
    parsed_manifest = _validate_model(BenchmarkManifestArtifact, manifest, manifest_label)
    parsed_state = _validate_model(BenchmarkStateEnvelope, state, state_label)
    return LoadedRun(
        summary=envelope.payload,
        manifest=parsed_manifest,
        state=parsed_state.payload,
        summary_path=relative_summary_path,
    )


def parse_completed_episode(
    *,
    value: dict[str, JsonValue],
    label: str,
    relative_path: str,
    actual_file_integrity_hash: str,
    expected_integrity_hash: str | None,
) -> LoadedEpisode:
    verify_signed_object(value, label)
    envelope = _validate_model(CompletedTrialArtifactEnvelope, value, label)
    if (
        expected_integrity_hash is not None
        and actual_file_integrity_hash != expected_integrity_hash
    ):
        raise PublicationInputError(f"{label} differs from its summary integrity reference")
    return LoadedEpisode(
        identity=envelope.payload.identity,
        result=envelope.payload.result,
        relative_path=relative_path,
        integrity_hash=envelope.integrity_hash,
    )
