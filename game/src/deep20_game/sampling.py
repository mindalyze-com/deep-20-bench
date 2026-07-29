from __future__ import annotations

import base64

from deep20_oracle.util import canonical_json, sha256_text

from .config import SeedCapability
from .models import GuesserSamplingDecision, GuesserSamplingMode

MAX_PORTABLE_SEED = (2**31) - 1
SAMPLING_SEED_DOMAIN = "deep20-guesser-seed-v1"
PROMPT_NONCE_DOMAIN = "deep20-guesser-prompt-nonce-v1"


def derive_guesser_seed(
    *,
    base_seed: int,
    trial_number: int,
    turn_number: int,
) -> int:
    """Derive a portable seed without using subject or execution identity."""
    material = canonical_json(
        {
            "base_seed": base_seed,
            "domain": SAMPLING_SEED_DOMAIN,
            "trial_number": trial_number,
            "turn_number": turn_number,
        }
    )
    return int(sha256_text(material)[:16], 16) % (MAX_PORTABLE_SEED + 1)


def derive_guesser_prompt_nonce(
    *,
    base_seed: int,
    trial_number: int,
) -> str:
    """Derive one short model-visible perturbation token per benchmark trial."""
    material = canonical_json(
        {
            "base_seed": base_seed,
            "domain": PROMPT_NONCE_DOMAIN,
            "trial_number": trial_number,
        }
    )
    digest = bytes.fromhex(sha256_text(material))
    return base64.b32encode(digest).decode("ascii")[:8]


def guesser_sampling_decision(
    *,
    capability: SeedCapability,
    base_seed: int,
    trial_number: int,
    turn_number: int,
) -> GuesserSamplingDecision:
    seed = (
        derive_guesser_seed(
            base_seed=base_seed,
            trial_number=trial_number,
            turn_number=turn_number,
        )
        if capability is SeedCapability.SUPPORTED
        else None
    )
    return GuesserSamplingDecision(
        mode=(
            GuesserSamplingMode.PROMPT_NONCE_PLUS_PROVIDER_SEED
            if seed is not None
            else GuesserSamplingMode.PROMPT_NONCE_ONLY
        ),
        base_seed=base_seed,
        trial_number=trial_number,
        turn_number=turn_number,
        prompt_nonce=derive_guesser_prompt_nonce(
            base_seed=base_seed,
            trial_number=trial_number,
        ),
        seed=seed,
    )
