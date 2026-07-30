from __future__ import annotations

import inspect
from typing import Any, get_args, get_type_hints

import pytest
from deep20_benchmark.canary import run_startup_canaries
from deep20_benchmark.models import (
    BenchmarkExecutionId,
    BenchmarkId,
    BenchmarkModelId,
    BenchmarkRequest,
)
from deep20_benchmark.preflight import validate_execution_routes
from deep20_benchmark.runner import BenchmarkRunner
from deep20_game.config import BenchmarkMode
from deep20_game.errors import GameError
from deep20_game.sinks import ExecutionObserver, GameAuditSink
from deep20_oracle.diagnostics import diagnose_exception, provider_failure_code
from deep20_oracle.errors import OracleError
from deep20_oracle.sinks import OracleAuditSink
from pydantic import ValidationError


def _contains_any(annotation: object) -> bool:
    return annotation is Any or any(_contains_any(argument) for argument in get_args(annotation))


def test_public_control_plane_and_sink_signatures_expose_no_any() -> None:
    callables = (
        BenchmarkRunner.run,
        GameAuditSink.persist_guesser_success,
        GameAuditSink.persist_guesser_failure,
        GameAuditSink.persist_validator_success,
        GameAuditSink.persist_validator_failure,
        GameAuditSink.persist_episode_event,
        GameAuditSink.persist_episode_result,
        OracleAuditSink.persist_oracle_success,
        OracleAuditSink.persist_oracle_failure,
        ExecutionObserver.observe,
        GameError.__init__,
        OracleError.__init__,
        diagnose_exception,
        provider_failure_code,
        run_startup_canaries,
        validate_execution_routes,
    )

    for callable_object in callables:
        signature = inspect.signature(callable_object)
        hints = get_type_hints(callable_object)
        assert signature.return_annotation is not inspect.Signature.empty
        assert all(not _contains_any(annotation) for annotation in hints.values())


def test_request_json_round_trip_is_strict_and_typed() -> None:
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"),
        execution_id=BenchmarkExecutionId("BX-round-trip-001"),
        model_id=BenchmarkModelId("M-0001"),
        benchmark_mode=BenchmarkMode.OFFICIAL,
        base_seed=42,
    )

    assert BenchmarkRequest.model_validate_json(request.model_dump_json()) == request
    assert request.base_seed == 42
    assert request.benchmark_mode is BenchmarkMode.OFFICIAL
    with pytest.raises(ValidationError):
        BenchmarkRequest.model_validate(
            {
                **request.model_dump(mode="json"),
                "unexpected": "rejected",
            }
        )
    with pytest.raises(
        ValidationError,
        match="benchmark_mode is required; choose 'official' or 'experimental'",
    ):
        BenchmarkRequest.model_validate(
            {
                "benchmark_id": "B-0001",
                "execution_id": "BX-round-trip-001",
                "model_id": "M-0001",
            }
        )
    with pytest.raises(ValidationError):
        BenchmarkRequest.model_validate(
            {
                "benchmark_id": "B-0001",
                "execution_id": "BX-round-trip-001",
                "model_ids": ["M-0001", "M-0002"],
            }
        )
