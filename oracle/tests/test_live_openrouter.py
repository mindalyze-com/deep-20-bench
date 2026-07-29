from __future__ import annotations

import os
from pathlib import Path

import pytest
from deep20_oracle import (
    Oracle,
    OracleRequest,
    RunAuditWriter,
    load_openrouter_api_key,
    load_oracle_config,
    load_subject_catalog,
)
from deep20_oracle.openrouter_provider import OpenRouterOracleProviderSet


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("DEEP20_RUN_LIVE_TEST") != "1",
    reason="set DEEP20_RUN_LIVE_TEST=1 to make the paid live request",
)
def test_live_openrouter_one_call(tmp_path: Path) -> None:
    root = Path(__file__).parents[2]
    config = load_oracle_config(root / "config" / "oracle.yaml")
    catalog = load_subject_catalog(root / "config" / "subjects.yaml")
    providers = OpenRouterOracleProviderSet(load_openrouter_api_key(root), config)
    audit = RunAuditWriter(
        tmp_path / "runs",
        config=config,
        subject_catalog_hash=catalog.content_hash(),
        repository=root,
    )
    with providers:
        call = Oracle(
            providers.oracle,
            providers.reviewer,
            providers.judge,
            audit,
            config,
        ).ask(
            OracleRequest(
                run_id="live-integration",
                subject=catalog.subject("T-0001"),
                question="Was this person born before 1900?",
            )
        )
    assert call.audit.provider.usage.search_count >= 1
