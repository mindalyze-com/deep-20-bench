"""Offline checks for model selection, launch boundaries and decision identity."""

from __future__ import annotations

import json
import socket
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path

import bridge
import comparison
import experiment
import httpx
import live_entry
import pytest
import test_bridge
from deep20_benchmark.catalog import load_model_catalog
from deep20_benchmark.models import BenchmarkExecutionId, BenchmarkModelId
from deep20_game.models import GameProviderRequest
from deep20_game.openrouter_provider import OpenRouterGameProvider
from deep20_oracle.models import StrictModel
from pydantic import ValidationError
from spend_guard import BudgetState

REAL_REPOSITORY = bridge.REPOSITORY
MODEL_IDS = load_model_catalog(REAL_REPOSITORY / "config/models.yaml").registered_model_ids()


@pytest.fixture(autouse=True)
def isolated_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "config").symlink_to(REAL_REPOSITORY / "config", target_is_directory=True)
    for name in ("ROOT", "EXECUTION", "MODEL", "BASELINE"):
        monkeypatch.setattr(bridge, name, getattr(bridge, name))
    monkeypatch.setattr(bridge, "REPOSITORY", tmp_path)

    def reject(address: object, *args: object, **kwargs: object) -> None:
        raise AssertionError("network forbidden in offline tests")

    monkeypatch.setattr(socket.socket, "connect", reject)
    monkeypatch.setattr(socket, "create_connection", reject)


def preview(model: BenchmarkModelId | None = None) -> experiment.PreparedExperiment:
    return experiment.prepare(
        experiment.Options(
            command=experiment.Command.PREVIEW,
            model=model or BenchmarkModelId("M-0001"),
            execution=BenchmarkExecutionId("BX-generic-offline"),
            budget_usd=Decimal(5),
        )
    )


@pytest.mark.parametrize("model", MODEL_IDS, ids=str)
def test_every_catalog_model_uses_the_same_offline_preview(model: BenchmarkModelId) -> None:
    prepared = preview(model)
    assert prepared.request.model_id == model
    assert prepared.model == load_model_catalog(REAL_REPOSITORY / "config/models.yaml").model(model)
    assert prepared.request.iterations_override == 3
    assert len(prepared.request.target_ids) == 10
    experiment.validate_prepared(prepared)
    assert not (bridge.ROOT / "budget.json").exists()
    assert not (bridge.ROOT / "runs").exists()
    restored = experiment.load_prepared(
        experiment.Options(
            command=experiment.Command.PROGRESS,
            execution=prepared.request.execution_id,
        )
    )
    assert restored == prepared


def test_live_opt_in_is_checked_before_loading_or_network() -> None:
    with pytest.raises(ValidationError, match="requires --live"):
        experiment.main(["run", "--execution", "BX-missing"])


def test_preview_and_model_identity_cannot_be_overwritten() -> None:
    prepared = preview()
    saved = (bridge.ROOT / "experiment.json").read_bytes()
    with pytest.raises(FileExistsError):
        preview()
    assert (bridge.ROOT / "experiment.json").read_bytes() == saved
    with pytest.raises(ValueError, match="model does not match"):
        experiment.load_prepared(
            experiment.Options(
                command=experiment.Command.PENDING,
                execution=prepared.request.execution_id,
                model=BenchmarkModelId("M-0021"),
            )
        )


def test_launch_rejects_preview_drift_before_network() -> None:
    prepared = preview()
    request = prepared.request.model_copy(update={"iterations_override": 1})
    bridge.write_model(bridge.ROOT / "request.json", request)
    with pytest.raises(ValueError, match="configuration changed"):
        experiment.launch(prepared)
    assert not (bridge.ROOT / "budget-launch.claim").exists()


def test_launch_injects_one_budget_into_canary_and_games(monkeypatch: pytest.MonkeyPatch) -> None:
    prepared = preview()
    config = prepared.model.configuration
    metadata = httpx.Response(
        200,
        request=httpx.Request("GET", "https://example.invalid"),
        json={
            "data": {
                "id": config.model,
                "endpoints": [
                    {
                        "tag": config.provider,
                        "status": 0,
                        "context_length": 1_000_000,
                        "pricing": {"prompt": "0.000001", "completion": "0.000004"},
                    }
                ],
            },
        },
    )
    monkeypatch.setattr(httpx, "get", lambda *a, **k: metadata)
    captured: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request.content)
        return httpx.Response(200, json={"usage": {"cost": "0.01"}})

    def run(factory: bridge.ProviderFactory | None = None) -> None:
        assert factory is not None
        for title in ("canary", "game"):
            provider = factory("offline-placeholder", config, title=title)
            assert isinstance(provider, OpenRouterGameProvider)
            with httpx.Client(
                transport=httpx.MockTransport(handler),
                event_hooks=provider.http_client._client.event_hooks,
            ) as client:
                client.post(
                    "https://example.invalid/chat/completions",
                    json={
                        "model": config.model,
                        "max_tokens": config.max_output_tokens,
                        "provider": {"only": [config.provider], "allow_fallbacks": False},
                        "messages": [{"role": "user", "content": "PUBLIC-FIXTURE"}],
                    },
                )
            provider.close()

    monkeypatch.setattr(live_entry, "main", run)
    experiment.launch(prepared)
    budget = BudgetState.model_validate_json((bridge.ROOT / "budget.json").read_text())
    assert budget.reported_usd == Decimal("0.02")
    assert budget.attempts == 2
    assert budget.reserved_usd == 0
    assert captured[0] == captured[1]
    assert b"budget" not in captured[0]
    with pytest.raises(FileExistsError):
        experiment.launch(prepared)
    assert len(captured) == 2


class RouteFixture(StrictModel):
    valid: bool = False


def test_failed_startup_is_not_repeated(monkeypatch: pytest.MonkeyPatch) -> None:
    preview()
    calls: list[int] = []

    def invalid_route(*args: object, **kwargs: object) -> RouteFixture:
        calls.append(1)
        return RouteFixture()

    monkeypatch.setattr(live_entry, "OpenRouterRouteMetadata", lambda: object())
    monkeypatch.setattr(live_entry, "validate_catalog_routes", invalid_route)
    with pytest.raises(RuntimeError, match="preflight failed"):
        live_entry.main()
    before = (bridge.ROOT / "route-preflight.json").read_bytes()
    with pytest.raises(ValueError, match="fresh experiment"):
        live_entry.main()
    assert (bridge.ROOT / "route-preflight.json").read_bytes() == before
    assert len(calls) == 1


@pytest.mark.parametrize("identity", ["missing", "stale", "matching"])
def test_submit_matches_operator_request_identity(identity: str) -> None:
    prepared = preview()
    work_root = bridge.ROOT / "work"
    work_root.mkdir()
    work = bridge.ValidatorWork(
        sequence=2,
        context=bridge.WorkContext(target_id="T-0001", trial_number=1),
        request_hash="current-hash",
        request=GameProviderRequest(
            messages=({"role": "user", "content": "fixture"},),
            output_schema={},
            schema_name="fixture",
            session_id="fixture",
            prompt_cache_key="fixture",
        ),
    )
    bridge.write_model(work_root / "pending.json", work)
    raw = {"result": {"answer": "YES", "explanation": "Offline identity fixture."}}
    path = bridge.ROOT / "decision.json"
    path.write_text(
        json.dumps(raw)
        if identity == "missing"
        else json.dumps(
            {
                **raw,
                "kind": "validator",
                "sequence": 2 if identity == "matching" else 1,
                "request_hash": "current-hash" if identity == "matching" else "old-hash",
            }
        )
    )

    def submit() -> None:
        experiment.main(
            ["submit", "--execution", str(prepared.request.execution_id), "--input", str(path)]
        )

    if identity == "matching":
        submit()
        assert (work_root / "response-0002.json").exists()
    else:
        with pytest.raises(ValueError, match="identity does not match"):
            submit()
        assert not (work_root / "response-0002.json").exists()


def test_progress_uses_prepared_schedule_and_unknown_billing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    experiment.main(
        [
            "preview",
            "--model",
            "M-0001",
            "--execution",
            "BX-progress-offline",
            "--budget-usd",
            "5",
            "--iterations",
            "1",
        ]
    )
    capsys.readouterr()
    experiment.main(["progress", "--execution", "BX-progress-offline"])
    report = json.loads(capsys.readouterr().out)
    assert report["scheduled_games"] == 10
    assert report["canary_cost_usd"] is None


def test_comparison_uses_saved_schedule_and_subjects(monkeypatch: pytest.MonkeyPatch) -> None:
    test_bridge.test_full_runner_roundtrip_and_guesser_isolation(
        bridge.REPOSITORY,
        monkeypatch,
        injected_factory=True,
    )
    monkeypatch.setattr(bridge, "ROOT", bridge.REPOSITORY)
    monkeypatch.setattr(bridge, "EXECUTION", "BX-20260910-offline-direct-001")
    monkeypatch.setattr(comparison, "BASELINE", BenchmarkExecutionId(bridge.EXECUTION))
    # A comparison of the same saved run must not require today's subject catalog.
    (bridge.REPOSITORY / "config").unlink()
    comparison.main()
    report = comparison.Comparison.model_validate_json(
        (bridge.ROOT / "comparison.json").read_text()
    )
    assert report.scheduled_games == 1
    assert report.completed_games == 1
    assert report.subject_snapshots_match is True
    assert report.base_seed_matches is True
    assert len(report.subjects[0].iterations) == 1


def test_failed_persistence_prevents_http_attempt() -> None:
    from spend_guard import Budget, PriceBound, Rate

    def fail(state: BudgetState) -> None:
        raise OSError("offline persistence failure")

    budget = Budget(
        BudgetState(limit_usd=Decimal(5)),
        PriceBound(
            model="fixture/model",
            provider="fixture",
            context_tokens=100000,
            max_output_tokens=100,
            rate=Rate(
                input_per_token=Decimal("0.000001"),
                output_per_token=Decimal("0.000002"),
                per_request=Decimal(0),
            ),
        ),
        fail,
    )
    handler: Callable[[httpx.Request], httpx.Response] = lambda request: pytest.fail(
        "transport ran"
    )
    with (
        httpx.Client(
            transport=httpx.MockTransport(handler), event_hooks={"request": [budget.reserve]}
        ) as client,
        pytest.raises(OSError, match="persistence"),
    ):
        client.post(
            "https://example.invalid",
            json={
                "model": "fixture/model",
                "max_tokens": 100,
                "provider": {"only": ["fixture"], "allow_fallbacks": False},
                "messages": [{"role": "user", "content": "fixture"}],
            },
        )
    assert budget.state.attempts == 0
