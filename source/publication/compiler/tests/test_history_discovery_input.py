from __future__ import annotations

import pytest
from pydantic import JsonValue
from test_compiler import _qualification_context

from deep20_publication.integrity import PublicationInputError, canonical_json, sha256_text
from deep20_publication.loader import parse_manifest


def _signed_manifest(discovery_policy: str | None) -> dict[str, JsonValue]:
    run, _ = _qualification_context()
    payload = run.manifest.model_dump(mode="json")
    inventory: dict[str, JsonValue] = {
        "policy": "historical_ask_v1",
        "normalization": "casefold-ascii-spaces-v1",
        "context_hash": "a" * 64,
        "cutoff": "2026-09-08T00:00:00Z",
        "sources": [],
        "snapshot_hash": "b" * 64,
    }
    if discovery_policy is not None:
        inventory["discovery_policy"] = discovery_policy
    payload["oracle_cache"] = inventory
    payload.pop("integrity_hash")
    payload["integrity_hash"] = sha256_text(canonical_json(payload))
    return payload


@pytest.mark.parametrize("policy", [None, "per_subject_history_v1"])
def test_signed_history_manifest_keeps_discovery_policy(policy: str | None) -> None:
    manifest = parse_manifest(_signed_manifest(policy), "history-manifest")
    assert manifest.oracle_cache is not None
    assert manifest.oracle_cache.discovery_policy == policy
    if policy is None:
        assert "discovery_policy" not in manifest.oracle_cache.model_dump(mode="json")


def test_history_discovery_policy_still_requires_a_known_signed_value() -> None:
    with pytest.raises(PublicationInputError, match="schema validation failed"):
        parse_manifest(_signed_manifest("unrecognized_history_v1"), "unknown-policy")

    tampered = _signed_manifest("per_subject_history_v1")
    inventory = tampered["oracle_cache"]
    assert isinstance(inventory, dict)
    inventory.pop("discovery_policy")
    with pytest.raises(PublicationInputError, match="integrity hash mismatch"):
        parse_manifest(tampered, "tampered-policy")
