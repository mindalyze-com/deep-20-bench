from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from test_compiler import _qualification_context
from test_result_audit_model import _provider_audit

from deep20_publication.cli import _read_yaml
from deep20_publication.compiler import (
    _oracle_prompt_versions_match,
    _public_versioned_run_model,
    _reason_codes,
    compile_publication,
)
from deep20_publication.integrity import canonical_json, sha256_text
from deep20_publication.legacy import legacy_dataset
from deep20_publication.loader import parse_publication_config, parse_subject_catalog
from deep20_publication.models import (
    AcceptedReleaseRevision,
    CohortConfig,
    EpisodeResultArtifact,
    LoadedRun,
    OracleAdjudicationSnapshot,
    OracleResultCallAuditSnapshot,
    PublicationConfig,
    PublicationEditionsDocument,
    QualifiedEligibility,
    ReleaseGameRules,
    ReleasePromptVersions,
    ReleaseSubjectIdentity,
)
from deep20_publication.split import edition_index, split_publication

REPOSITORY = Path(__file__).resolve().parents[4]


def _qualified_run() -> tuple[LoadedRun, CohortConfig]:
    source, cohort = _qualification_context()
    payload = json.loads(source.model_dump_json().replace("BX-test", "BX-qualified"))
    definition = payload["manifest"]["definition"]
    definition["game_policy"]["prompt_profile"] = "qualified_v1"
    definition["game_policy"]["benchmark_mode"] = "experimental"
    definition["game_policy"]["max_questions"] = 40
    for item in (definition, payload["manifest"]["request"], payload["summary"]):
        item["benchmark_id"] = "B-0003"
    payload["manifest"]["request"]["benchmark_mode"] = "experimental"
    episode = payload["episodes"][0]["result"]
    episode["llm_details"]["oracle"]["configuration"]["prompt_profile"] = "qualified_v1"
    definition["oracle_configuration"] = episode["llm_details"]["oracle"]["configuration"]
    versions = ReleasePromptVersions(
        guesser="guesser-release", oracle="oracle-release", recovery="recovery-release",
        reviewer="reviewer-release", judge="judge-release", validator="validator-release",
    )
    for field, version in (("under_test", versions.guesser), ("oracle", versions.oracle),
                           ("validator", versions.validator)):
        episode["models"][field]["prompt_version"] = version
    episode["audit"] = {
        "schema_version": 1,
        "calls": [{
            "component": role, "call_id": f"{prefix}-{'0' * 32}",
            "turn_number": 1, "status": "success",
            "prompt": {"version": version, "hash": "a" * 64},
            "provider": _provider_audit(),
        } for role, prefix, version in (
            ("guesser", "GC", versions.guesser), ("validator", "VC", versions.validator),
        )],
    }
    loaded = LoadedRun.model_validate(payload)
    detail = loaded.episodes[0].result
    release = QualifiedEligibility(
        prompts=versions,
        game_rules=ReleaseGameRules(max_consecutive_contract_violations=5,
                                    reveal_entity_type=True, final_guess_after_limit=True),
        oracle_configuration_hash=sha256_text(canonical_json(
            detail.llm_details.oracle.configuration.model_dump(mode="json"))),
        validator_configuration_hash=sha256_text(canonical_json(
            detail.llm_details.validator.configuration.model_dump(mode="json"))),
        subject_identities=(ReleaseSubjectIdentity(
            target_id="T-0001", identity_hash=sha256_text(canonical_json(
                detail.run.subject.model_dump(mode="json"))),
        ),),
    )
    return loaded, cohort.model_copy(update={
        "cohort_id": "qualified-test", "edition_id": "1.1", "edition_label": "1.1",
        "benchmark_id": "B-0003", "max_questions": 40, "eligibility": release,
    })


def _config() -> PublicationConfig:
    return parse_publication_config(_read_yaml(REPOSITORY / "config/publication.yml"), "test")


def test_current_release_defaults_and_distinct_edition_identity() -> None:
    config = _config()
    assert config.default_edition_id == "1.1"
    assert config.active_cohort.iterations == 3
    assert len(config.active_cohort.target_ids) == 10
    assert config.active_cohort.max_questions == 40
    assert isinstance(config.active_cohort.eligibility, QualifiedEligibility)
    assert config.active_cohort.eligibility.prompts.guesser.endswith("category-guide")
    assert config.active_cohort.eligibility.oracle_contract_hash is not None
    payload = config.model_dump(mode="json")
    payload["default_edition_id"] = "9.9"
    with pytest.raises(ValidationError):
        PublicationConfig.model_validate(payload)


@pytest.mark.parametrize("recorded_contract", ("current", "previous", "missing"))
def test_release_checks_factual_contract_even_when_prompts_match(recorded_contract: str) -> None:
    run, cohort = _qualified_run()
    current = _config().active_cohort.eligibility
    assert isinstance(current, QualifiedEligibility)
    assert isinstance(cohort.eligibility, QualifiedEligibility)
    expected_hash = current.oracle_contract_hash
    assert expected_hash is not None
    release = cohort.eligibility.model_copy(update={"oracle_contract_hash": expected_hash})
    cohort = cohort.model_copy(update={"eligibility": release})
    payload = run.model_dump(mode="json")
    payload["manifest"]["oracle_contract_hash"] = {
        "current": expected_hash, "previous": "b" * 64, "missing": None,
    }[recorded_contract]
    reasons = _reason_codes(LoadedRun.model_validate(payload), cohort)
    assert reasons == (() if recorded_contract == "current" else ("oracle_contract_mismatch",))


def test_qualified_release_accepts_matching_experimental_provenance_only_in_its_edition() -> None:
    old, previous = _qualification_context()
    new, current = _qualified_run()
    assert _reason_codes(old, previous) == ()
    assert _reason_codes(new, current) == ()
    assert "experimental_prompt_profile" in _reason_codes(new, previous)
    assert "experimental_prompt_profile" in _reason_codes(old, current)
    assert new.manifest.request.benchmark_mode == "experimental"
    assert "trial_coverage_mismatch" in _reason_codes(new, current.model_copy(update={"iterations": 3}))


def test_accepted_revision_requires_its_whole_contract_and_complete_coverage() -> None:
    run, cohort = _qualified_run()
    assert isinstance(cohort.eligibility, QualifiedEligibility)
    payload = run.model_dump(mode="json")
    payload["manifest"]["oracle_contract_hash"] = "b" * 64
    run = LoadedRun.model_validate(payload)
    accepted = AcceptedReleaseRevision.model_validate({
        **cohort.eligibility.model_dump(mode="json", exclude={"kind", "accepted_revisions"}),
        "revision_id": "accepted-previous", "oracle_contract_hash": "b" * 64,
    })
    current = cohort.eligibility.model_copy(update={
        "oracle_configuration_hash": "c" * 64,
        "oracle_contract_hash": "a" * 64,
        "accepted_revisions": (accepted,),
    })
    cohort = CohortConfig.model_validate(cohort.model_copy(update={"eligibility": current}).model_dump())
    assert _reason_codes(run, cohort) == ()
    assert "trial_coverage_mismatch" in _reason_codes(
        run, cohort.model_copy(update={"iterations": 3}),
    )
    # Matching the primary factual contract and the alternate configuration separately
    # must not qualify a run: no complete contract accepts this combination.
    payload["manifest"]["oracle_contract_hash"] = "a" * 64
    assert _reason_codes(LoadedRun.model_validate(payload), cohort)
    payload["manifest"]["oracle_contract_hash"] = "d" * 64
    assert "oracle_contract_mismatch" in _reason_codes(LoadedRun.model_validate(payload), cohort)
    payload["manifest"]["oracle_contract_hash"] = "b" * 64
    payload["episodes"][0]["result"]["audit"] = None
    assert "release_prompt_audit_missing" in _reason_codes(LoadedRun.model_validate(payload), cohort)


def test_accepted_revision_requires_all_subjects_and_unique_names() -> None:
    _, cohort = _qualified_run()
    assert isinstance(cohort.eligibility, QualifiedEligibility)
    revision = {
        **cohort.eligibility.model_dump(mode="json", exclude={"kind", "accepted_revisions"}),
        "revision_id": "accepted-previous", "oracle_contract_hash": "b" * 64,
    }
    payload = cohort.model_dump(mode="json")
    payload["eligibility"]["accepted_revisions"] = [revision, revision]
    with pytest.raises(ValidationError, match="revision IDs must be unique"):
        CohortConfig.model_validate(payload)
    payload["eligibility"]["accepted_revisions"] = [revision]
    revision["subject_identities"] = [{"target_id": "T-0002", "identity_hash": "a" * 64}]
    with pytest.raises(ValidationError, match="cover exactly the cohort targets"):
        CohortConfig.model_validate(payload)


def test_prompt_transitions_match_complete_observed_role_combinations() -> None:
    _, cohort = _qualified_run()
    assert isinstance(cohort.eligibility, QualifiedEligibility)
    old = cohort.eligibility.prompts
    new = old.model_copy(update={"oracle": "oracle-next", "reviewer": "reviewer-next"})
    call_payload = {
        "component": "oracle", "call_id": f"OC-{'0' * 32}",
        "turn_number": 1, "status": "success",
        "oracle": {
            "role": "oracle", "prompt": {"version": old.oracle, "hash": "a" * 64},
            "provider": _provider_audit(),
        },
        "reviewer": {
            "role": "reviewer", "prompt": {"version": new.reviewer, "hash": "b" * 64},
            "provider": _provider_audit(),
        },
    }
    mixed = OracleResultCallAuditSnapshot.model_validate(call_payload)
    assert not any(_oracle_prompt_versions_match(mixed, version) for version in (old, new))
    transition = old.model_copy(update={"reviewer": new.reviewer})
    assert _oracle_prompt_versions_match(mixed, transition)


def test_additional_recorded_prompt_versions_do_not_admit_unlisted_versions() -> None:
    run, cohort = _qualified_run()
    assert isinstance(cohort.eligibility, QualifiedEligibility)
    alternate = cohort.eligibility.prompts.model_copy(update={"guesser": "guesser-next"})
    revised = cohort.eligibility.model_copy(update={"additional_prompt_versions": (alternate,)})
    cohort = cohort.model_copy(update={"eligibility": revised})
    payload = run.model_dump(mode="json")
    episode = payload["episodes"][0]["result"]
    episode["models"]["under_test"]["prompt_version"] = alternate.guesser
    episode["audit"]["calls"][0]["prompt"]["version"] = alternate.guesser
    assert _reason_codes(LoadedRun.model_validate(payload), cohort) == ()
    episode["audit"]["calls"][0]["prompt"]["version"] = "unlisted-guesser"
    assert "prompt_revision_mismatch" in _reason_codes(LoadedRun.model_validate(payload), cohort)


def test_run_model_retains_multiple_oracle_versions_without_relaxing_model_identity() -> None:
    run, _ = _qualified_run()
    first = run.episodes[0].result.models.oracle
    second = first.model_copy(update={"prompt_version": "oracle-next"})
    model = _public_versioned_run_model(
        role="oracle", versions=(first, second), provider_routing="exact",
        provider_usages=(), calls=2, cost_usd=Decimal(0),
    )
    assert model.prompt_version is None
    assert model.prompt_versions == (first.prompt_version, "oracle-next")
    with pytest.raises(ValueError, match="inconsistent oracle model configuration"):
        _public_versioned_run_model(
            role="oracle", versions=(first, second.model_copy(update={"requested_model": "other"})),
            provider_routing="exact", provider_usages=(), calls=2, cost_usd=Decimal(0),
        )


@pytest.mark.parametrize(("change", "reason"), (
    ("prompt", "prompt_revision_mismatch"),
    ("seed", "base_seed_mismatch"),
    ("rules", "game_rules_mismatch"),
    ("subject", "subject_identity_mismatch"),
    ("support", "support_configuration_mismatch"),
    ("audit", "release_prompt_audit_missing"),
    ("audit_identity", "release_prompt_audit_missing"),
    ("guesser", "guesser_configuration_mismatch"),
))
def test_release_rejects_revision_drift(change: str, reason: str) -> None:
    run, cohort = _qualified_run()
    payload = run.model_dump(mode="json")
    result = payload["episodes"][0]["result"]
    if change == "prompt":
        result["models"]["under_test"]["prompt_version"] = "earlier-diagnostic"
    elif change == "seed":
        payload["manifest"]["request"]["base_seed"] = 1
    elif change == "rules":
        payload["manifest"]["definition"]["game_policy"]["final_guess_after_limit"] = False
    elif change == "subject":
        result["run"]["subject"]["canonical_name"] = "A different identity"
    elif change == "support":
        result["llm_details"]["oracle"]["configuration"]["model"] = "different/model"
    elif change == "guesser":
        result["llm_details"]["guesser"]["configuration"]["model"] = "different/model"
    elif change == "audit_identity":
        result["audit"]["calls"][1]["call_id"] = f"VC-{'1' * 32}"
    else:
        result["audit"] = None
    assert reason in _reason_codes(LoadedRun.model_validate(payload), cohort)


def test_same_model_keeps_independent_results_and_document_ownership() -> None:
    old, previous = _qualification_context()
    new, current = _qualified_run()
    previous = previous.model_copy(update={"edition_status": "previous"})
    config = _config().model_copy(update={"cohorts": (current, previous)})
    subjects, _ = parse_subject_catalog(_read_yaml(REPOSITORY / "config/subjects.yaml"), "test")
    datasets = tuple(compile_publication(
        runs=(old, new), config=config, subject_catalog=subjects, cohort=cohort,
        subject_catalog_hash="a" * 64, built_at=datetime(2026, 9, 6, tzinfo=UTC),
    ) for cohort in config.cohorts)
    assert [dataset.official_runs[0].execution_id for dataset in datasets] == [
        "BX-qualified", "BX-test",
    ]
    for dataset in datasets:
        bundle = split_publication(dataset)
        identities = [document.edition_id for document in bundle.runs]
        identities.extend(document.edition_id for document in bundle.subjects)
        identities.extend(document.edition_id for document in bundle.episodes)
        assert set(identities) == {dataset.active_cohort.edition_id}
    index = edition_index(config, datasets)
    payload = index.model_dump(mode="json")
    payload["editions"][1]["runs"] = payload["editions"][0]["runs"]
    with pytest.raises(ValidationError, match="edition"):
        PublicationEditionsDocument.model_validate(payload)
    assert legacy_dataset(datasets[1]).schema_version == 9
    with pytest.raises(TypeError):
        legacy_dataset(datasets[0])


@pytest.mark.parametrize("answer", ("RATHER_YES", "RATHER_NO"))
def test_qualified_tokens_are_never_valid_guess_answers(answer: str) -> None:
    run, _ = _qualified_run()
    payload = run.episodes[0].result.model_dump(mode="json")
    payload["turns"][0]["adjudication"]["answer"] = answer
    with pytest.raises(ValidationError, match="Guess Validator"):
        EpisodeResultArtifact.model_validate(payload)


def test_exact_token_disagreement_requires_judge() -> None:
    decision = {"answer": "RATHER_YES", "basis": "evidence", "evidence_indices": [1]}
    payload = {
        "oracle_answer": "YES", "reviewer": decision, "disagreement": True,
        "judge_invoked": True, "judge": decision, "final_answer": "RATHER_YES",
        "decision_path": "judge_disagreement",
    }
    assert OracleAdjudicationSnapshot.model_validate(payload).final_answer == "RATHER_YES"
    payload["judge"] = None
    with pytest.raises(ValidationError, match="Judge"):
        OracleAdjudicationSnapshot.model_validate(payload)
