"""Offline edition resolution. No credentials, providers, or artifact writes."""

from pathlib import Path
from typing import TYPE_CHECKING

from deep20_backends.editions import Edition, EditionRegistry
from deep20_game.config import BenchmarkMode, GamePolicy
from deep20_game.prompt import VALIDATOR_PROMPT_VERSION, guesser_prompt_version
from deep20_oracle.cache_contract import oracle_contract_hash
from deep20_oracle.catalog import SubjectCatalog, SubjectStatus
from deep20_oracle.config import AdjudicationPolicy, PromptProfile
from deep20_oracle.models import OracleAnswer, OracleResearchStrategy, OracleRole, Subject
from deep20_oracle.prompt import evidence_review_prompt_version, research_prompt_version
from deep20_oracle.protocol import STANDARD_ANSWERS
from deep20_oracle.util import canonical_json, load_yaml_unique, sha256_text

from .edition_models import (
    EditionExecution,
    EditionOverrides,
    EditionProfile,
    QualifiedRelease,
    ReleasePrompts,
    SubjectIdentity,
)

if TYPE_CHECKING:
    from deep20_oracle.config import OracleConfig

    from .models import BenchmarkDefinitionSnapshot


def registered_edition(root: Path, edition_id: str | None) -> Edition:
    registry = EditionRegistry.model_validate(load_yaml_unique(root / "config/editions.yaml"))
    return registry.edition(edition_id)


def load_profile(path: Path) -> EditionProfile:
    profile = EditionProfile.model_validate(load_yaml_unique(path))
    if profile.launchable:
        release = profile.cohort.eligibility
        oracle, validator = profile.oracle_configuration, profile.validator_configuration
        assert isinstance(release, QualifiedRelease) and oracle is not None and validator is not None
        # Match the independent publication reader's normalized route representation.
        payload = oracle.model_dump(mode="json")
        payload["provider_routing"] = oracle.provider_routing.value
        for role in ("reviewer", "judge"):
            payload[role]["provider_routing"] = getattr(oracle, role).provider_routing.value
        if (sha256_text(canonical_json(payload)) != release.oracle_configuration_hash
            or sha256_text(canonical_json(validator.model_dump(mode="json")))
            != release.validator_configuration_hash):
            raise ValueError("edition_contract_mismatch: configuration differs from release pins")
    return profile


def edition_profile(root: Path, edition: Edition) -> EditionProfile:
    if edition.profile_path is None:
        raise ValueError("edition has no released profile")
    profile = load_profile(root / "config" / edition.profile_path)
    cohort = profile.cohort
    if (cohort.edition_id, cohort.edition_label, cohort.edition_status, cohort.benchmark_id) != (
        edition.edition_id, edition.label, edition.status.value, edition.benchmark_id,
    ):
        raise ValueError("edition profile differs from its registry entry")
    return profile


def profile_policy(profile: EditionProfile, mode: BenchmarkMode) -> GamePolicy:
    release = profile.cohort.eligibility
    if not isinstance(release, QualifiedRelease):
        raise TypeError("archived edition is read-only; use a named experimental variant")
    return GamePolicy(
        benchmark_mode=mode, prompt_profile=profile.prompt_profile,
        max_questions=profile.cohort.max_questions,
        **release.game_rules.model_dump(),
    )


def profile_hash(profile: EditionProfile) -> str:
    # Publication model selection and labels are not experimental conditions.
    payload = profile.model_dump(mode="json", exclude={"cohort": {
        "model_ids": True, "display_name": True, "edition_label": True, "edition_status": True,
        "eligibility": {"accepted_revisions"},
    }})
    return sha256_text(canonical_json(payload))


def current_prompts(policy: GamePolicy, oracle: OracleConfig) -> ReleasePrompts:
    primary = research_prompt_version(OracleResearchStrategy.PRIMARY, oracle.prompt_profile,
                                      policy=oracle.adjudication_policy)
    recovery = (primary if oracle.adjudication_policy is AdjudicationPolicy.CONCISE_KNOWLEDGE_V1
                else research_prompt_version(OracleResearchStrategy.DIVERSIFIED_RECOVERY,
                                             oracle.prompt_profile, policy=oracle.adjudication_policy))
    return ReleasePrompts(
        guesser=guesser_prompt_version(policy.prompt_profile), oracle=primary, recovery=recovery,
        reviewer=evidence_review_prompt_version(OracleRole.REVIEWER, oracle.prompt_profile,
                                                policy=oracle.adjudication_policy),
        judge=evidence_review_prompt_version(OracleRole.JUDGE, oracle.prompt_profile,
                                             policy=oracle.adjudication_policy),
        validator=VALIDATOR_PROMPT_VERSION,
    )


def identities(subjects: tuple[Subject, ...]) -> tuple[SubjectIdentity, ...]:
    return tuple(SubjectIdentity(target_id=s.target_id,
                                identity_hash=sha256_text(canonical_json(s.model_dump(mode="json"))))
                 for s in subjects)


def comparison_hash(definition: BenchmarkDefinitionSnapshot, base_seed: int,
                    subject_ids: tuple[SubjectIdentity, ...], prompts: ReleasePrompts,
                    profile: EditionProfile | EditionExecution) -> str:
    # Mode and display labels do not change the factual experiment. Model under test,
    # execution IDs and timestamps deliberately do not participate.
    return sha256_text(canonical_json({
        "game_policy": definition.game_policy.model_dump(mode="json", exclude={"benchmark_mode"}),
        "oracle_configuration": definition.oracle_configuration.model_dump(mode="json"),
        "validator_configuration": definition.validator_configuration.model_dump(mode="json"),
        "oracle_contract_hash": oracle_contract_hash(definition.oracle_configuration),
        "prompts": prompts.model_dump(mode="json"),
        "subjects": [s.model_dump(mode="json") for s in subject_ids],
        "iterations": definition.iterations, "base_seed": base_seed,
        "score": profile.score.model_dump(mode="json"),
    }))


def resolve_execution(profile: EditionProfile, definition: BenchmarkDefinitionSnapshot,
                      subjects: SubjectCatalog, overrides: EditionOverrides,
                      base_seed: int, *, allow_inactive: bool = False) -> EditionExecution:
    if not profile.launchable:
        raise ValueError("archived edition is read-only; select a current or draft edition")
    release = profile.cohort.eligibility
    assert isinstance(release, QualifiedRelease)
    selected = tuple(subjects.subject(str(i)) for i in definition.subject_ids)
    for subject in selected:
        if not allow_inactive and subjects.entry(subject.target_id).status is SubjectStatus.INACTIVE:
            raise ValueError("edition target is inactive; revise the profile explicitly")
    actual_ids = identities(selected)
    prompts = current_prompts(definition.game_policy, definition.oracle_configuration)
    differences: list[str] = []
    checks = {
        "benchmark_id": str(definition.benchmark_id) == profile.cohort.benchmark_id,
        "game_policy": definition.game_policy.model_dump(exclude={"benchmark_mode"})
        == profile_policy(profile, definition.game_policy.benchmark_mode).model_dump(exclude={"benchmark_mode"}),
        "oracle_configuration": definition.oracle_configuration == profile.oracle_configuration,
        "validator_configuration": definition.validator_configuration == profile.validator_configuration,
        "prompts": prompts == release.prompts,
        "oracle_contract": oracle_contract_hash(definition.oracle_configuration) == release.oracle_contract_hash,
        "subject_identities": all(s in release.subject_identities for s in actual_ids),
    }
    semantic = tuple(k for k, equal in checks.items() if not equal)
    if semantic and overrides.variant_name is None:
        raise ValueError("edition_contract_mismatch: " + ", ".join(semantic)
                         + "; use a separate named --variant for a deliberate experiment")
    differences.extend(semantic)
    if definition.iterations != profile.cohort.iterations:
        if overrides.iterations is None:
            raise ValueError("edition_contract_mismatch: iterations changed without an override")
        differences.append("iterations")
    if tuple(str(i) for i in definition.subject_ids) != profile.cohort.target_ids:
        if overrides.target_ids is None:
            raise ValueError("edition_contract_mismatch: subject schedule changed without an override")
        differences.append("target_ids")
    if base_seed != profile.cohort.base_seed:
        if overrides.base_seed is None:
            raise ValueError("edition_contract_mismatch: seed changed without an override")
        differences.append("base_seed")
    variant = bool(differences or overrides.variant_name)
    if variant and definition.game_policy.benchmark_mode is BenchmarkMode.OFFICIAL:
        raise ValueError("edition variants require experimental mode")
    answers = (tuple(OracleAnswer) if definition.game_policy.prompt_profile
               is PromptProfile.QUALIFIED_V1 else STANDARD_ANSWERS)
    return EditionExecution(
        edition_id=profile.cohort.edition_id, revision=profile.revision,
        profile_hash=profile_hash(profile), comparison_hash=comparison_hash(
            definition, base_seed, actual_ids, prompts, profile),
        classification="variant" if variant else "standard", overrides=overrides,
        differences=tuple(differences), answer_tokens=answers, prompts=prompts,
        subject_identities=actual_ids, score=profile.score,
    )


def validate_execution(record: EditionExecution, definition: BenchmarkDefinitionSnapshot,
                       subjects: tuple[Subject, ...], base_seed: int) -> None:
    prompts = current_prompts(definition.game_policy, definition.oracle_configuration)
    if record.comparison_hash != comparison_hash(definition, base_seed, identities(subjects), prompts, record):
        raise ValueError("edition_contract_mismatch: resolved execution changed after preflight")
