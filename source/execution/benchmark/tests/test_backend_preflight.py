from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from deep20_backends.config import InteractiveSettings, OllamaSettings
from deep20_backends.editions import EditionRegistry
from deep20_backends.models import (
    BackendCapabilities,
    BackendKind,
    BackendObservation,
    BackendUsage,
    ModelResponse,
    Role,
)
from deep20_benchmark.backend_config import RuntimeConfig, resolve_runtime
from deep20_benchmark.backend_preflight import run_backend_preflight
from deep20_benchmark.backend_resolution import resolved_definition, resolved_model
from deep20_benchmark.catalog import load_benchmark_catalog, load_model_catalog
from deep20_benchmark.models import BenchmarkId, BenchmarkModelId, SubjectId
from deep20_game.config import BenchmarkMode
from deep20_oracle.util import canonical_json, load_yaml_unique

ROOT = Path(__file__).parents[4]


def inputs():
    model = load_model_catalog(ROOT / "config/models.yaml").model(BenchmarkModelId("M-0003"))
    definition = load_benchmark_catalog(ROOT / "config/benchmarks.yaml").benchmark(
        BenchmarkId("B-0003"), benchmark_mode=BenchmarkMode.EXPERIMENTAL, subject_ids=(SubjectId("T-0001"),))
    edition = EditionRegistry.model_validate(load_yaml_unique(ROOT / "config/editions.yaml")).edition("1.2")
    overrides = RuntimeConfig(roles={role.value: OllamaSettings(model="local", research="parallel" if role is Role.ORACLE else None)
                                    for role in (Role.ORACLE, Role.REVIEWER, Role.JUDGE)})
    runtime = resolve_runtime(edition, overrides, guesser=model.configuration,
                              oracle=definition.oracle_configuration, validator=definition.validator_configuration)
    return runtime, resolved_definition(definition, runtime), resolved_model(model, runtime)


def test_preflight_reuses_each_selected_role_contract_without_real_calls():
    runtime, definition, model = inputs()
    seen = []
    class Backend:
        capabilities = BackendCapabilities(tool_calls=True)
        def __init__(self, role, configuration):
            self.role = role
            self.configuration = configuration
        def complete(self, request):
            seen.append(request)
            role = self.role
            if role is Role.GUESSER:
                answer = {"result": {"action": "ASK", "question": "Is it well known?", "name": None, "description": None}}
            elif role is Role.VALIDATOR:
                answer = {"answer": "YES", "explanation": "The same identity."}
            elif role is Role.ORACLE:
                answer = {"answer": "YES", "basis": "other", "supporting_statement": "Known date.",
                          "evidence": [], "research_outcome": "answered", "attempted_queries": ["date one", "date two", "date three"]}
            else:
                answer = {"answer": "YES", "basis": "evidence", "supporting_statement": "The excerpt states the date.", "evidence_indices": [1]}
            now = datetime.now(UTC).isoformat()
            return ModelResponse(content=canonical_json(answer), requested_at=now, completed_at=now,
                finish_reason="stop", latency_ms=0, observation=BackendObservation(kind=BackendKind.OLLAMA,
                    model=self.configuration.model, resolved_model=self.configuration.model, resolved_provider="ollama",
                    inference_requests=1, usage=BackendUsage(search_requests=3 if role is Role.ORACLE else 0,
                                                            cost_usd=Decimal(0))))
        def close(self):
            pass
    class Factory:
        def create(self, role, configuration):
            # Exercise all role wire formats using a local observation, never HTTP.
            configuration = configuration.model_copy(update={"gateway": "ollama"})
            return Backend(role, configuration)
    # Game route validation uses the resolved configurations supplied to the canary.
    model = model.model_copy(update={"configuration": model.configuration.model_copy(update={"gateway": "ollama"})})
    definition = definition.model_copy(update={"validator_configuration": definition.validator_configuration.model_copy(update={"gateway": "ollama"})})
    report = run_backend_preflight(runtime, definition, model, Factory(), canary=True)
    assert all(result.status == "canary_passed" for result in report.roles)
    assert {request.role for request in seen} == set(Role)
    assert all(not request.tools for request in seen)
    guesser = next(request for request in seen if request.role is Role.GUESSER)
    assert "Ada Lovelace" not in canonical_json(guesser.model_dump(mode="json"))
    for request in seen:
        if request.role is not Role.ORACLE:
            assert request.max_search_requests is None


def test_guesser_operator_cannot_reuse_a_privileged_conversation():
    runtime, _, _ = inputs()
    with pytest.raises(ValueError, match="different operator contexts"):
        runtime.roles.model_validate({**runtime.roles.model_dump(),
            "guesser": InteractiveSettings(operator="same", isolated_context=True),
            "reviewer": InteractiveSettings(operator="same")})
