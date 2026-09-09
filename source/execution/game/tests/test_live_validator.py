"""Opt-in semantic checks for generic-kind and particular-entity acceptance."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

import pytest
from deep20_benchmark.catalog import load_benchmark_catalog, load_model_catalog
from deep20_benchmark.models import BenchmarkId, BenchmarkModelId
from deep20_game.audit import GameRunAuditWriter
from deep20_game.models import ActionType, GuesserAction
from deep20_game.openrouter_provider import OpenRouterGameProvider
from deep20_game.prompt import VALIDATOR_PROMPT_VERSION, validator_messages
from deep20_game.validator import GuessValidator
from deep20_oracle.catalog import load_subject_catalog
from deep20_oracle.credentials import load_openrouter_api_key
from deep20_oracle.models import OracleAnswer, StrictModel


class IdentityCase(StrictModel):
    case_id: str
    target_id: str
    name: str
    description: str
    expected: OracleAnswer
    target_description: str | None = None


CASES = (
    IdentityCase(
        case_id="doorknob", target_id="T-0012", name="Doorknob",
        description="A round handle turned to open a door", expected=OracleAnswer.YES,
    ),
    IdentityCase(
        case_id="lever", target_id="T-0012", name="Lever door handle",
        description="A hand-operated lever fitting used to open a building door.",
        expected=OracleAnswer.YES,
    ),
    IdentityCase(
        case_id="whole-door", target_id="T-0012", name="Door",
        description="The hinged panel used to close a doorway.", expected=OracleAnswer.NO,
    ),
    IdentityCase(
        case_id="latch", target_id="T-0012", name="Door latch",
        description="The catch or bolt holding a door closed, excluding the operating handle.",
        expected=OracleAnswer.NO,
    ),
    IdentityCase(
        case_id="broader-class", target_id="T-0012", name="Hardware",
        description="The general class of metal fittings used in buildings.",
        expected=OracleAnswer.NO,
    ),
    IdentityCase(
        case_id="floor-bike-pump", target_id="T-0008", name="Floor bicycle pump",
        description="A floor-standing air pump used to inflate bicycle tires.",
        expected=OracleAnswer.YES,
    ),
    IdentityCase(
        case_id="same-specific-entity", target_id="T-0011", name="Luna",
        description="Earth's natural satellite.", expected=OracleAnswer.YES,
    ),
    IdentityCase(
        case_id="different-specific-entity", target_id="T-0011", name="Titan",
        description="Saturn's largest natural satellite.", expected=OracleAnswer.NO,
    ),
    IdentityCase(
        case_id="generic-for-specific", target_id="T-0011", name="Natural satellite",
        description="The general category of naturally occurring bodies orbiting planets.",
        expected=OracleAnswer.NO,
    ),
    IdentityCase(
        case_id="restricted-design", target_id="T-0012", name="Doorknob",
        description="A round handle turned to open a door", expected=OracleAnswer.NO,
        target_description=(
            "A lever-shaped door handle, explicitly excluding round doorknobs. "
            "The target is the lever fitting used by hand to open a building door."
        ),
    ),
)


@pytest.mark.integration
@pytest.mark.parametrize("case", CASES, ids=lambda case: case.case_id)
def test_live_validator_identity_acceptance(tmp_path: Path, case: IdentityCase) -> None:
    if os.environ.get("DEEP20_RUN_LIVE_VALIDATOR") != "1":
        pytest.skip("set DEEP20_RUN_LIVE_VALIDATOR=1 for paid identity checks")

    root = Path(__file__).resolve().parents[4]
    benchmark = load_benchmark_catalog(root / "config/benchmarks.yaml").entry(
        BenchmarkId("B-0003")
    )
    model = load_model_catalog(root / "config/models.yaml").model(BenchmarkModelId("M-0006"))
    catalog = load_subject_catalog(root / "config/subjects.yaml")
    subject = catalog.subject(case.target_id)
    if case.target_description is not None:
        subject = subject.model_copy(update={"description": case.target_description})
    configuration = benchmark.validator_configuration
    sink = GameRunAuditWriter(
        tmp_path / "auxiliary",
        game_policy=benchmark.game_policy,
        oracle_config=benchmark.oracle_configuration,
        guesser_config=model.configuration,
        validator_config=configuration,
        subject_catalog_hash=catalog.content_hash(),
        repository=root,
    )
    guess = GuesserAction(
        action=ActionType.GUESS,
        question=None,
        name=case.name,
        description=case.description,
    )
    with OpenRouterGameProvider(
        load_openrouter_api_key(root), configuration, title="Deep20Bench Validator Calibration"
    ) as provider:
        call = GuessValidator(provider, sink, configuration).validate(
            run_id=f"validator-kind-{case.case_id}",
            episode_id=f"EP-{uuid.uuid7().hex}",
            subject=subject,
            guess=guess,
        )

    # Retain semantic decisions and billing, never raw exchanges or message bodies.
    (tmp_path / "result.json").write_text(
        json.dumps(
            {
                "case": case.model_dump(mode="json"),
                "subject": subject.model_dump(mode="json"),
                "result": call.result.model_dump(mode="json"),
                "prompt_version": call.audit.prompt_version,
                "prompt_hash": call.audit.prompt_hash,
                "metrics": call.metrics.model_dump(mode="json"),
                "resolved_model": call.audit.provider.resolved_model,
                "resolved_provider": call.audit.provider.resolved_provider,
                "finish_reason": call.audit.provider.finish_reason,
                "response_cache_status": call.audit.provider.response_cache_status,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    assert call.audit.messages == validator_messages(subject, guess)
    assert call.audit.prompt_version == VALIDATOR_PROMPT_VERSION
    assert call.audit.provider.usage.search_count == 0
    assert call.result.answer is case.expected, call.result.explanation
