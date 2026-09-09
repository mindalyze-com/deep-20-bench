from __future__ import annotations

import pytest
from pydantic import ValidationError
from test_judge_knowledge_policy import _judged_episode, _qualified_run
from test_result_audit_model import _provider_audit

from deep20_publication.compiler import _public_episode
from deep20_publication.models import (
    EpisodeActionTurn,
    EpisodeResultArtifact,
    OracleConfigurationSnapshot,
)


def concise_episode() -> EpisodeResultArtifact:
    payload = _judged_episode().model_dump(mode="json")
    payload["llm_details"]["oracle"]["configuration"]["adjudication_policy"] = "concise_knowledge_v1"
    for role in ("reviewer", "judge"):
        payload["turns"][0]["adjudication"]["oracle_quality"][role].update(
            basis="other", supporting_statement="PRIVATE_SUPPORT: remembered fact or unresolved gap.",
        )
    return EpisodeResultArtifact.model_validate(payload)


def test_private_support_round_trips_and_is_excluded_from_public_output() -> None:
    result = concise_episode()
    assert EpisodeResultArtifact.model_validate_json(result.model_dump_json()) == result
    run, _ = _qualified_run()
    episode = run.episodes[0].model_copy(update={"result": result})
    public = _public_episode(episode).model_dump_json()
    assert "PRIVATE_SUPPORT" not in public
    assert "supporting_statement" not in public
    assert "oracle_quality" not in public


@pytest.mark.parametrize("change", (
    {"basis": "mixed"}, {"basis": "model_knowledge"}, {"basis": "unresolved"},
    {"supporting_statement": None}, {"supporting_statement": "x" * 601},
))
def test_invalid_concise_decision_is_rejected(change: dict[str, str | None]) -> None:
    payload = concise_episode().model_dump(mode="json")
    payload["turns"][0]["adjudication"]["oracle_quality"]["judge"].update(change)
    with pytest.raises(ValidationError):
        EpisodeResultArtifact.model_validate(payload)


def test_concise_support_cannot_be_imported_under_earlier_policy() -> None:
    payload = concise_episode().model_dump(mode="json")
    payload["llm_details"]["oracle"]["configuration"]["adjudication_policy"] = "judge_stable_knowledge_v1"
    with pytest.raises(ValidationError):
        EpisodeResultArtifact.model_validate(payload)


@pytest.mark.parametrize("basis", ("evidence", "other"))
def test_concise_unknown_keeps_valid_evidence_context_private(basis: str) -> None:
    payload = concise_episode().model_dump(mode="json")
    decision = payload["turns"][0]["adjudication"]["oracle_quality"]["reviewer"]
    decision.update(answer="UNKNOWN", basis=basis, evidence_indices=[1])
    result = EpisodeResultArtifact.model_validate(payload)
    turn = result.turns[0]
    assert isinstance(turn, EpisodeActionTurn)
    assert turn.adjudication.oracle_quality is not None
    assert turn.adjudication.oracle_quality.reviewer is not None
    assert turn.adjudication.oracle_quality.reviewer.evidence_indices == (1,)
    assert EpisodeResultArtifact.model_validate_json(result.model_dump_json()) == result
    run, _ = _qualified_run()
    public = _public_episode(run.episodes[0].model_copy(update={"result": result})).model_dump_json()
    assert "PRIVATE_SUPPORT" not in public
    assert "evidence_indices" not in public

    decision["evidence_indices"] = [2]
    with pytest.raises(ValidationError, match="outside supplied evidence"):
        EpisodeResultArtifact.model_validate(payload)
    decision["evidence_indices"] = [1]
    decision.pop("supporting_statement")
    with pytest.raises(ValidationError, match="UNKNOWN must not identify supporting evidence"):
        EpisodeResultArtifact.model_validate(payload)


@pytest.mark.parametrize(("target", "query_count", "search_count", "valid"), (
    (3, 3, 4, True), (3, 5, 5, True), (3, 3, 6, False), (3, 6, 3, False),
    (5, 7, 7, True), (5, 7, 8, False), (28, 30, 30, True),
))
def test_concise_research_uses_recorded_target_and_bonus_budget(
    target: int, query_count: int, search_count: int, valid: bool,
) -> None:
    result = concise_episode()
    payload = result.model_dump(mode="json")
    if target != 3:
        payload["llm_details"]["oracle"]["configuration"]["research_query_target"] = target
    provider = _provider_audit()
    provider.update(usage={"search_count": search_count}, web_search_requests=search_count)
    prompt = {"version": "live-web-oracle-v16-search-headroom", "hash": "a" * 64}
    payload["audit"] = {
        "schema_version": 1,
        "unavailable_call_count": (
            result.summary.guesser_call_count + result.summary.ask_count
            + result.summary.guess_count - 1
        ),
        "calls": [{
            "component": "oracle", "call_id": f"OC-{'0' * 32}",
            "turn_number": 1, "status": "success",
            "oracle": {"role": "oracle", "prompt": prompt, "provider": provider},
            "research": {
                "question_class": "closed_fact", "resolution": "answered_primary",
                "attempts": [{
                    "attempt_number": 1, "strategy": "primary", "outcome": "answered",
                    "attempted_queries": [f"reported query {i}" for i in range(query_count)],
                    "query_provenance": "model_reported", "evidence_count": 1,
                    "basis": "evidence", "supporting_statement": "PRIVATE_SUPPORT: source facts.",
                    "prompt": prompt, "provider": provider,
                }],
            },
        }],
    }
    if not valid:
        with pytest.raises(ValidationError, match="exceeds its search budget"):
            EpisodeResultArtifact.model_validate(payload)
        return
    parsed = EpisodeResultArtifact.model_validate(payload)
    assert parsed.llm_details.oracle.configuration.research_search_limit == target + 2
    assert EpisodeResultArtifact.model_validate_json(parsed.model_dump_json()) == parsed


@pytest.mark.parametrize("target", (0, 29, True, "5"))
def test_research_query_target_is_strict_and_bounded(target: int | str | bool) -> None:
    payload = concise_episode().llm_details.oracle.configuration.model_dump(mode="json")
    payload["research_query_target"] = target
    with pytest.raises(ValidationError, match="research_query_target"):
        OracleConfigurationSnapshot.model_validate(payload)


def test_default_query_target_preserves_serialization_and_earlier_policies() -> None:
    config = concise_episode().llm_details.oracle.configuration
    assert config.research_query_target == 3
    assert "research_query_target" not in config.model_dump(mode="json")
    payload = config.model_dump(mode="json")
    payload.update(adjudication_policy="judge_stable_knowledge_v1", research_query_target=5)
    with pytest.raises(ValidationError, match="requires concise_knowledge_v1"):
        OracleConfigurationSnapshot.model_validate(payload)
