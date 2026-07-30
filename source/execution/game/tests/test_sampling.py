from __future__ import annotations

from deep20_game.config import SeedCapability
from deep20_game.sampling import (
    derive_guesser_prompt_nonce,
    derive_guesser_seed,
    guesser_sampling_decision,
)


def test_seed_derivation_is_repeatable_and_varies_by_trial_and_turn() -> None:
    first = derive_guesser_seed(base_seed=42, trial_number=1, turn_number=1)

    assert first == derive_guesser_seed(base_seed=42, trial_number=1, turn_number=1)
    assert first != derive_guesser_seed(base_seed=42, trial_number=2, turn_number=1)
    assert first != derive_guesser_seed(base_seed=42, trial_number=1, turn_number=2)
    assert 0 <= first <= (2**31) - 1


def test_seed_schedule_has_no_subject_or_execution_input() -> None:
    decision = guesser_sampling_decision(
        capability=SeedCapability.SUPPORTED,
        base_seed=99,
        trial_number=3,
        turn_number=7,
    )

    assert decision.mode == "prompt_nonce_plus_provider_seed"
    assert decision.seed == derive_guesser_seed(
        base_seed=99,
        trial_number=3,
        turn_number=7,
    )
    assert decision.prompt_nonce == derive_guesser_prompt_nonce(
        base_seed=99,
        trial_number=3,
    )
    assert set(decision.model_dump()) == {
        "mode",
        "base_seed",
        "trial_number",
        "turn_number",
        "prompt_nonce",
        "seed",
    }


def test_prompt_nonce_varies_by_trial_but_not_conversation_turn() -> None:
    first = derive_guesser_prompt_nonce(base_seed=42, trial_number=1)

    assert first == derive_guesser_prompt_nonce(base_seed=42, trial_number=1)
    assert first != derive_guesser_prompt_nonce(base_seed=42, trial_number=2)
    assert first != derive_guesser_prompt_nonce(base_seed=43, trial_number=1)
    assert len(first) == 8

    turn_one = guesser_sampling_decision(
        capability=SeedCapability.SUPPORTED,
        base_seed=42,
        trial_number=1,
        turn_number=1,
    )
    turn_two = guesser_sampling_decision(
        capability=SeedCapability.SUPPORTED,
        base_seed=42,
        trial_number=1,
        turn_number=2,
    )
    assert turn_one.prompt_nonce == turn_two.prompt_nonce
    assert turn_one.seed != turn_two.seed


def test_unsupported_seed_capability_uses_prompt_nonce_without_provider_seed() -> None:
    decision = guesser_sampling_decision(
        capability=SeedCapability.UNSUPPORTED,
        base_seed=99,
        trial_number=3,
        turn_number=7,
    )

    assert decision.mode == "prompt_nonce_only"
    assert decision.prompt_nonce == derive_guesser_prompt_nonce(
        base_seed=99,
        trial_number=3,
    )
    assert decision.seed is None
