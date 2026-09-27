from __future__ import annotations

import json
from pathlib import Path

import bridge
import pytest
from deep20_benchmark.artifacts import ArtifactStore
from deep20_benchmark.catalog import load_model_catalog
from deep20_benchmark.models import (
    BenchmarkExecutionId,
    BenchmarkRequest,
    BenchmarkResult,
    SubjectId,
)
from deep20_benchmark.runner import BenchmarkRunner
from deep20_game.config import BenchmarkMode, ModelConfig
from deep20_game.models import GameProviderExchange, GameProviderRequest
from deep20_game.openrouter_provider import OpenRouterGameProvider
from deep20_oracle import load_subject_catalog
from deep20_oracle.openrouter_provider import OpenRouterProvider
from deep20_oracle.provider import ProviderRequest
from deep20_oracle.util import sha256_text


class TestBroker(bridge.Broker):
    __test__ = False

    def wait(self, request: ProviderRequest | GameProviderRequest) -> bridge.Decision:
        self.sequence += 1
        base = {"sequence": self.sequence, "request_hash": sha256_text(request.model_dump_json())}
        if isinstance(request, GameProviderRequest):
            return bridge.ValidatorDecision.model_validate(
                {**base, "result": {"answer": "YES", "explanation": "Offline identity fixture."}}
            )
        return bridge.OracleDecision.model_validate(
            {
                **base,
                "oracle": {
                    "answer": "YES",
                    "basis": "other",
                    "evidence": [],
                    "supporting_statement": "Remembered fact, used only in an offline fixture.",
                    "research_outcome": "answered",
                    "attempted_queries": ["offline fixture"],
                },
                "reviewer": {
                    "answer": "NO",
                    "basis": "other",
                    "evidence_indices": [],
                    "supporting_statement": "Offline disagreement fixture.",
                },
                "judge": {
                    "answer": "RATHER_YES",
                    "basis": "other",
                    "evidence_indices": [],
                    "supporting_statement": "Offline judgment fixture.",
                },
                "search_count": 1,
            }
        )


@pytest.mark.parametrize("injected_factory", [False, True])
def test_full_runner_roundtrip_and_guesser_isolation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, injected_factory: bool
) -> None:
    captured: list[GameProviderRequest] = []

    class OfflineGuesser:
        def __init__(self, api_key: str, config: ModelConfig, *, title: str):
            self.config = config

        def close(self) -> None:
            pass

        def complete(self, request: GameProviderRequest) -> GameProviderExchange:
            captured.append(request)
            if len(captured) == 2:
                raw = "malformed fixture"
            elif len(captured) == 4:
                raw = json.dumps(
                    {
                        "result": {
                            "action": "GUESS",
                            "question": None,
                            "name": "Albert Einstein",
                            "description": "The physicist.",
                        }
                    }
                )
            else:
                raw = json.dumps(
                    {
                        "result": {
                            "action": "ASK",
                            "question": "Is this a person?",
                            "name": None,
                            "description": None,
                        }
                    }
                )
            return GameProviderExchange(
                raw_output=raw,
                trace=bridge.local_trace(self.config, request, raw, "2026-09-10T00:00:00Z", 0),
            )

    monkeypatch.setattr(bridge, "OpenRouterGameProvider", OfflineGuesser)
    store = ArtifactStore(tmp_path)
    monkeypatch.setattr(
        store, "_git", lambda arguments: "0" * 40 if arguments[0] == "rev-parse" else ""
    )
    runner = BenchmarkRunner(
        store=store,
        model_catalog=load_model_catalog(bridge.REPOSITORY / "config/models.yaml"),
        benchmark_catalog=bridge.experimental_catalog(),
        subject_catalog=load_subject_catalog(bridge.REPOSITORY / "config/subjects.yaml"),
        executor=bridge.DirectExecutor(
            "offline-placeholder", TestBroker(tmp_path / "work"),
            OfflineGuesser if injected_factory else None,
        ),
    )
    request = BenchmarkRequest(
        benchmark_id=bridge.BENCHMARK,
        model_id=bridge.MODEL,
        execution_id=BenchmarkExecutionId("BX-20260910-offline-direct-001"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        iterations_override=1,
        target_ids=(SubjectId("T-0001"),),
    )
    result = runner.run(request)
    roundtrip = BenchmarkResult.model_validate_json(result.model_dump_json())
    trial = roundtrip.subjects[0].trials[0]
    assert trial.status == "completed", trial.model_dump_json()
    assert trial.result.success
    assert trial.result.counted_questions == 3
    assert trial.result.summary.contract.violations == 1
    assert len(captured) == 4
    assert "Albert Einstein" not in json.dumps([r.messages for r in captured])
    assert "offline judgment" not in json.dumps([r.messages for r in captured]).lower()
    assert "malformed fixture" not in json.dumps(captured[2].messages)
    assert "FORMAT_ERROR" in json.dumps(captured[2].messages)
    assert "RATHER_YES" in captured[1].messages[-1]["content"]
    assert store.load_benchmark_result(bridge.MODEL, request.execution_id) == result


def test_manual_routes_reject_openrouter_and_official_mode() -> None:
    catalog = bridge.experimental_catalog()
    entry = catalog.entry(bridge.BENCHMARK)
    with pytest.raises(ValueError, match="openrouter gateway"):
        OpenRouterGameProvider("unused", entry.validator_configuration, title="offline")
    with pytest.raises(ValueError, match="openrouter gateway"):
        OpenRouterProvider("unused", entry.oracle_configuration)
    with pytest.raises(ValueError, match="experimental benchmark mode"):
        catalog.benchmark(
            bridge.BENCHMARK,
            benchmark_mode=BenchmarkMode.OFFICIAL,
            subject_ids=(SubjectId("T-0001"),),
        )
