from __future__ import annotations

from typing import Literal

import pytest
from pydantic import HttpUrl, ValidationError
from test_compiler import _qualification_context

from deep20_publication.compiler import _reason_codes
from deep20_publication.models import (
    CohortConfig,
    EpisodeAction,
    EpisodeActionTurn,
    EpisodeEvidence,
    EpisodeResultArtifact,
    EpisodeTurnAdjudication,
    EvidenceDecisionBasisSnapshot,
    EvidenceReviewDecisionSnapshot,
    FactualAnswer,
    LoadedRun,
    OracleAdjudicationSnapshot,
    OracleConfigurationSnapshot,
)

POLICY = "judge_stable_knowledge_v1"


def _qualified_run() -> tuple[LoadedRun, CohortConfig]:
    source, cohort = _qualification_context()
    payload = source.model_dump(mode="json")
    definition = payload["manifest"]["definition"]
    definition["game_policy"]["prompt_profile"] = "qualified_v1"
    definition["game_policy"]["benchmark_mode"] = "experimental"
    for item in (definition, payload["manifest"]["request"], payload["summary"]):
        item["benchmark_id"] = "B-0003"
    payload["manifest"]["request"]["benchmark_mode"] = "experimental"
    configuration = payload["episodes"][0]["result"]["llm_details"]["oracle"]["configuration"]
    configuration["prompt_profile"] = "qualified_v1"
    definition["oracle_configuration"] = configuration
    return LoadedRun.model_validate(payload), cohort


def _judged_episode(
    *, policy: str = POLICY, role: Literal["reviewer", "judge"] = "judge",
    answer: FactualAnswer = "NO", indices: tuple[int, ...] = (),
) -> EpisodeResultArtifact:
    run, _ = _qualified_run()
    result = run.episodes[0].result
    config = result.llm_details.oracle.configuration.model_copy(update={"adjudication_policy": policy})
    known = EvidenceReviewDecisionSnapshot(
        answer=answer, basis=EvidenceDecisionBasisSnapshot.MODEL_KNOWLEDGE,
        evidence_indices=indices,
    )
    unknown = EvidenceReviewDecisionSnapshot(
        answer="UNKNOWN", basis=EvidenceDecisionBasisSnapshot.EVIDENCE,
    )
    quality = OracleAdjudicationSnapshot(
        oracle_answer="RATHER_YES", reviewer=known if role == "reviewer" else unknown,
        judge=known, disagreement=True, judge_invoked=True,
        final_answer=answer, decision_path="judge_disagreement",
    )
    turn = EpisodeActionTurn(
        turn_number=1, counted=True, counted_questions=1,
        guesser_call_id=f"GC-{'0' * 32}",
        action=EpisodeAction(action="ASK", question="Did it originate in Rome?",
                             name=None, description=None),
        adjudication=EpisodeTurnAdjudication(
            component="oracle", call_id=f"OC-{'0' * 32}", answer=answer,
            evidence=(EpisodeEvidence(source_url=HttpUrl("https://example.test/source"),
                                      excerpt="An incomplete account.", validation="model_reported"),),
            oracle_quality=quality,
        ),
    )
    revised = result.model_copy(update={
        "audit": None, "turns": (turn,),
        "llm_details": result.llm_details.model_copy(update={
            "oracle": result.llm_details.oracle.model_copy(update={"configuration": config}),
        }),
    })
    return EpisodeResultArtifact.model_validate_json(revised.model_dump_json())


@pytest.mark.parametrize("answer", ("YES", "NO", "RATHER_YES", "RATHER_NO"))
def test_new_judge_decision_round_trips_with_explicit_policy(answer: FactualAnswer) -> None:
    result = _judged_episode(answer=answer)
    assert result.llm_details.oracle.configuration.adjudication_policy == POLICY
    assert EpisodeResultArtifact.model_validate_json(result.model_dump_json()) == result


@pytest.mark.parametrize(("policy", "role", "answer"), (
    ("profile_default", "judge", "NO"),
    (POLICY, "reviewer", "NO"),
    ("profile_default", "judge", "RATHER_NO"),
    ("profile_default", "judge", "RATHER_YES"),
    (POLICY, "judge", "UNKNOWN"),
))
def test_publication_rejects_knowledge_outside_declared_contract(
    policy: str, role: Literal["reviewer", "judge"], answer: FactualAnswer,
) -> None:
    with pytest.raises(ValidationError):
        _judged_episode(policy=policy, role=role, answer=answer)


def test_model_knowledge_cannot_claim_evidence_indices() -> None:
    with pytest.raises(ValidationError, match="evidence"):
        _judged_episode(indices=(1,))


def test_historical_configuration_retains_default_and_rejects_wrong_profile() -> None:
    run, _ = _qualified_run()
    config = run.episodes[0].result.llm_details.oracle.configuration
    assert config.adjudication_policy == "profile_default"
    assert "adjudication_policy" not in config.model_dump(mode="json")
    payload = config.model_dump(mode="json")
    payload.update(prompt_profile="standard", adjudication_policy=POLICY)
    with pytest.raises(ValidationError, match="requires qualified_v1"):
        OracleConfigurationSnapshot.model_validate(payload)


def test_existing_search_mode_snapshot_round_trips_without_changing_defaults() -> None:
    run, _ = _qualified_run()
    config = run.episodes[0].result.llm_details.oracle.configuration
    assert "parallel_search_mode" not in config.model_dump(mode="json")
    payload = config.model_dump(mode="json")
    payload["parallel_search_mode"] = "fast"
    revised = OracleConfigurationSnapshot.model_validate(payload)
    assert revised.model_dump(mode="json")["parallel_search_mode"] == "fast"
    payload["parallel_search"] = False
    with pytest.raises(ValidationError, match="requires parallel_search"):
        OracleConfigurationSnapshot.model_validate(payload)


def test_new_policy_cannot_be_mixed_into_historical_manifest_or_release() -> None:
    run, cohort = _qualified_run()
    payload = run.model_dump(mode="json")
    payload["episodes"][0]["result"]["llm_details"]["oracle"]["configuration"][
        "adjudication_policy"
    ] = POLICY
    with pytest.raises(ValidationError, match="policy differs from manifest"):
        LoadedRun.model_validate(payload)
    payload["manifest"]["definition"]["oracle_configuration"]["adjudication_policy"] = POLICY
    revised = LoadedRun.model_validate(payload)
    assert "experimental_prompt_profile" in _reason_codes(revised, cohort)
