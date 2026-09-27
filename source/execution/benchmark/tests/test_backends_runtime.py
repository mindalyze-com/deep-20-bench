import json
from pathlib import Path

import pytest
from deep20_backends.config import FixedMockSettings
from deep20_backends.editions import EditionRegistry
from deep20_backends.models import Role
from deep20_benchmark.artifacts import ArtifactStore
from deep20_benchmark.backend_config import RuntimeConfig, resolve_runtime
from deep20_benchmark.backend_resolution import game_configuration, oracle_configuration
from deep20_benchmark.catalog import load_benchmark_catalog, load_model_catalog
from deep20_benchmark.models import (
    BenchmarkExecutionId,
    BenchmarkId,
    BenchmarkModelId,
    BenchmarkRequest,
    SubjectId,
)
from deep20_benchmark.runner import BenchmarkRunner
from deep20_benchmark.runtime import LiveEpisodeExecutor
from deep20_game.config import BenchmarkMode
from deep20_oracle.cache_contract import oracle_contract_hash
from deep20_oracle.catalog import load_subject_catalog
from deep20_oracle.util import load_yaml_unique
from pydantic import ValidationError

ROOT = Path(__file__).parents[4]


@pytest.fixture(autouse=True)
def offline_git_identity(monkeypatch):
    monkeypatch.setattr(ArtifactStore, "_git", lambda *_args: "a" * 40)


def inputs():
    models = load_model_catalog(ROOT / "config/edition-1.2/mock-models.yaml")
    benchmarks = load_benchmark_catalog(ROOT / "config/benchmarks.yaml")
    registry = EditionRegistry.model_validate(load_yaml_unique(ROOT / "config/editions.yaml"))
    config = RuntimeConfig.model_validate(load_yaml_unique(ROOT / "config/edition-1.2/all-mock.yaml"))
    definition = benchmarks.entry(BenchmarkId("B-0003"))
    model = models.model(BenchmarkModelId("M-9900"))
    runtime = resolve_runtime(registry.edition("1.2"), config, guesser=model.configuration,
                              oracle=definition.oracle_configuration,
                              validator=definition.validator_configuration)
    return models, benchmarks, runtime


def run_mock(tmp_path, runtime=None):
    models, benchmarks, default = inputs()
    runtime = runtime or default
    runner = BenchmarkRunner(
        store=ArtifactStore(tmp_path), model_catalog=models, benchmark_catalog=benchmarks,
        subject_catalog=load_subject_catalog(ROOT / "config/subjects.yaml"),
        executor=LiveEpisodeExecutor(),
    )
    request = BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0003"), model_id=BenchmarkModelId("M-9900"),
        execution_id=BenchmarkExecutionId("BX-offline-draft"),
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        target_ids=(SubjectId("T-0001"),), runtime=runtime,
    )
    return runner, request, runner.run(request)


def test_all_mock_runs_use_real_scheduler_and_are_unscored(tmp_path):
    runner, request, result = run_mock(tmp_path)
    assert result.summary.counts.scheduled == 3
    assert result.summary.counts.infrastructure_failed == 0
    assert result.summary.counts.scoring_eligible == 0
    assert result.summary.success_rate is None
    assert result.run.runtime.roles.synthetic
    for trial in result.subjects[0].trials:
        episode = trial.result
        assert episode.outcome.success
        assert episode.outcome.synthetic
        assert not episode.outcome.publication_eligible
        assert episode.costs_usd.total == 0
        assert episode.summary.oracle_quality.reviewed_questions == 0
        assert episode.turns[0].adjudication.oracle_quality.decision_path == "review_bypassed"
        for call in episode.audit.calls:
            trace = call.provider if hasattr(call, "provider") else call.oracle.provider
            assert trace.backend.inference_requests == 0
            assert trace.usage.search_count == 0
            assert trace.resolved_provider is None
    # A completed execution returns its saved result without consuming scripts again.
    assert runner.run(request) == result


def test_mock_reviewer_disagreement_invokes_mock_judge_without_fake_provider_calls(tmp_path):
    _, _, runtime = inputs()
    reviewer = FixedMockSettings(response={
        "answer": "NO", "basis": "other", "supporting_statement": "Synthetic disagreement.",
        "evidence_indices": [],
    })
    runtime = runtime.model_copy(update={"roles": runtime.roles.model_copy(update={"reviewer": reviewer})})
    _, _, result = run_mock(tmp_path, runtime)
    for trial in result.subjects[0].trials:
        outcome = trial.result.turns[0].adjudication
        assert outcome.answer == "UNKNOWN"
        assert outcome.oracle_quality.judge_invoked
        assert outcome.oracle_quality.decision_path == "judge_disagreement"
        assert trial.result.llm.oracle.provider_usage.judge.providers == ()


def test_privileged_role_changes_do_not_change_guesser_cache_namespace():
    models, benchmarks, runtime = inputs()
    changed = runtime.model_copy(update={"roles": runtime.roles.model_copy(update={
        "judge": FixedMockSettings(response={
            "answer": "YES", "basis": "other", "supporting_statement": "Different fixture.",
            "evidence_indices": [],
        }),
    })})
    base_guesser = models.model(BenchmarkModelId("M-9900")).configuration
    base_oracle = benchmarks.entry(BenchmarkId("B-0003")).oracle_configuration
    assert game_configuration(base_guesser, runtime, Role.GUESSER) == game_configuration(
        base_guesser, changed, Role.GUESSER,
    )
    assert oracle_contract_hash(oracle_configuration(base_oracle, runtime)) != oracle_contract_hash(
        oracle_configuration(base_oracle, changed),
    )


def test_runtime_cannot_change_an_existing_execution(tmp_path):
    runner, request, _ = run_mock(tmp_path)
    changed = request.runtime.model_copy(update={
        "roles": request.runtime.roles.model_copy(update={"validator": FixedMockSettings(response={
            "answer": "NO", "explanation": "Different synthetic verdict.",
        })}),
    })
    with pytest.raises(ValueError, match="does not match|different immutable"):
        runner.run(request.model_copy(update={"runtime": changed}))


def test_edition_registry_retains_default_and_draft_is_explicit():
    registry = EditionRegistry.model_validate(load_yaml_unique(ROOT / "config/editions.yaml"))
    assert registry.edition().edition_id == "1.1"
    assert registry.edition("1.2").status == "draft"
    assert not registry.edition().runtime_overrides


def test_approval_mock_cannot_be_used_as_a_validator():
    _, _, runtime = inputs()
    values = json.loads(runtime.model_dump_json())
    values["roles"]["validator"] = {"implementation": "mock", "behavior": "approve_primary"}
    with pytest.raises(ValidationError, match="only for Reviewer"):
        type(runtime).model_validate(values)


def test_interactive_guesser_uses_real_format_error_path_and_only_public_history(tmp_path):
    from deep20_backends.config import InteractiveSettings
    from deep20_benchmark.backend_factory import BackendFactory
    from deep20_benchmark.interactive_backend import InteractiveBackend
    from deep20_benchmark.work_models import WorkIdentity, WorkStatus, WorkSubmission
    from deep20_benchmark.work_queue import MemoryWorkQueue
    models, benchmarks, runtime = inputs()
    entry = models.models["M-9900"]
    entry = entry.model_copy(update={"configuration": entry.configuration.model_copy(update={
        "gateway": "interactive", "model": "isolated-guesser", "provider": "interactive",
    })})
    models = models.model_copy(update={"models": {"M-9900": entry}})
    script = runtime.roles.guesser.responses
    binding = InteractiveSettings(model="isolated-guesser", operator="isolated-worker", isolated_context=True)
    runtime = runtime.model_copy(update={"roles": runtime.roles.model_copy(update={"guesser": binding})})
    queue = MemoryWorkQueue()
    projections = []

    def factory(context):
        identity = WorkIdentity(execution_id=context.identity.execution_id, model_id=context.identity.model_id,
            target_id=context.identity.target_id, trial_id=context.identity.trial_id,
            attempt_number=context.attempt_number, role=Role.GUESSER)
        def worker(role, settings):
            replies = iter(("MALFORMED_PRIVATE_MARKER", *(json.dumps(reply) for reply in script)))
            def operate(_seconds):
                pending = next(receipt for receipt in queue.receipts() if receipt.status is WorkStatus.PENDING)
                claim = queue.claim(pending.request_id, operator=settings.operator, role=role)
                work = queue.read(claim)
                projections.append(work.inference.messages)
                queue.submit(WorkSubmission(request_id=claim.request_id, request_hash=claim.request_hash,
                    claim_id=claim.claim_id, content=next(replies)))
            return InteractiveBackend(settings, identity, queue, wait=operate)
        return BackendFactory(api_key=None, runtime=runtime, interactive=worker,
                              on_episode_committed=lambda: queue.finish_attempt(identity))

    runner = BenchmarkRunner(store=ArtifactStore(tmp_path), model_catalog=models, benchmark_catalog=benchmarks,
        subject_catalog=load_subject_catalog(ROOT / "config/subjects.yaml"),
        executor=LiveEpisodeExecutor(factory_provider=factory))
    result = runner.run(BenchmarkRequest(benchmark_id=BenchmarkId("B-0003"), model_id=BenchmarkModelId("M-9900"),
        execution_id=BenchmarkExecutionId("BX-interactive-offline"), benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        target_ids=(SubjectId("T-0001"),), runtime=runtime))
    assert result.summary.counts.infrastructure_failed == 0
    assert result.summary.contract.violations == 3
    assert result.summary.contract.counted_penalties == 3
    assert all(receipt.status is WorkStatus.CONSUMED for receipt in queue.receipts())
    visible = json.dumps([[message.model_dump(mode="json") for message in messages] for messages in projections])
    assert "FORMAT_ERROR" in visible
    assert "RATHER_YES" in visible
    assert "MALFORMED_PRIVATE_MARKER" not in visible
    assert "Albert Einstein" not in visible
    assert "T-0001" not in visible
    assert "isolated-worker" not in visible
    assert runtime.roles.oracle.response["supporting_statement"] not in visible


def test_local_factual_reuse_requires_explicit_digest_pins():
    from deep20_backends.config import OllamaSettings
    from deep20_benchmark.backend_config import RoleBindings
    roles = {role.value: OllamaSettings(model="local", research="parallel" if role is Role.ORACLE else None) for role in Role}
    unpinned = RoleBindings.model_validate(roles)
    assert not unpinned.factual_cache_eligible
    pinned = RoleBindings.model_validate({name: binding.model_copy(update={"model_digest": "a" * 64}) for name, binding in roles.items()})
    assert pinned.factual_cache_eligible
