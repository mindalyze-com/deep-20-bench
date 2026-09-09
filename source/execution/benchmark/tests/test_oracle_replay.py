from __future__ import annotations

import json
from contextlib import nullcontext
from decimal import Decimal

import pytest
import yaml
from deep20_benchmark import oracle_replay_cli as cli
from deep20_benchmark.artifacts import ArtifactIntegrityError, load_benchmark_result_file
from deep20_benchmark.cli import benchmark_app
from deep20_benchmark.models import (
    BenchmarkExecutionId,
    BenchmarkId,
    BenchmarkModelId,
    BenchmarkRequest,
    SubjectId,
    TrialId,
)
from deep20_benchmark.oracle_replay import (
    ReplayFailure,
    ReplayReport,
    ReplaySelection,
    ReplayStatus,
    build_replay_plan,
    run_replay,
    summarize_replay,
)
from deep20_benchmark.oracle_replay_io import ReplayStore, render_replay_review
from deep20_game.config import BenchmarkMode
from deep20_game.models import (
    ActionTurnResult,
    ContractViolationTurnResult,
    GuesserAction,
    TurnAdjudication,
)
from deep20_oracle.artifacts import RunArtifactPolicy
from deep20_oracle.audit import RunAuditWriter
from deep20_oracle.config import AdjudicationPolicy, OracleConfig, PromptProfile
from deep20_oracle.errors import OracleProviderError
from deep20_oracle.models import (
    Evidence,
    OracleAdjudication,
    OracleAnswer,
    OracleDecisionPath,
    ProviderTrace,
    ProviderUsage,
)
from deep20_oracle.provider import ProviderExchange, ProviderRequest
from deep20_oracle.service import Oracle
from deep20_oracle.util import canonical_json, sha256_text
from test_runner import FakeExecutor, _runner
from typer.testing import CliRunner


@pytest.fixture
def source(tmp_path):
    runner, _ = _runner(tmp_path, FakeExecutor())
    result = runner.run(BenchmarkRequest(
        benchmark_id=BenchmarkId("B-0001"), execution_id=BenchmarkExecutionId("BX-replay-source"),
        model_id=BenchmarkModelId("M-0001"), benchmark_mode=BenchmarkMode.EXPERIMENTAL,
    ))
    oracle_config = result.run.definition.oracle_configuration.model_copy(update={
        "prompt_profile": PromptProfile.QUALIFIED_V1,
        "adjudication_policy": AdjudicationPolicy.CONCISE_KNOWLEDGE_V1,
    })
    definition = result.run.definition.model_copy(update={
        "game_policy": result.run.definition.game_policy.model_copy(update={
            "prompt_profile": PromptProfile.QUALIFIED_V1,
        }), "oracle_configuration": oracle_config,
    })
    baseline = TurnAdjudication(
        component="oracle", call_id="OC-" + "1" * 32, answer=OracleAnswer.UNKNOWN,
        evidence=(Evidence(source_url="https://example.test/old", excerpt="OLD_EVIDENCE_SENTINEL",
                           validation="model_reported"),),
        oracle_quality=OracleAdjudication(
            oracle_answer=OracleAnswer.UNKNOWN, disagreement=False, judge_invoked=False,
            final_answer=OracleAnswer.UNKNOWN, decision_path=OracleDecisionPath.ORACLE_UNKNOWN,
        ),
    )
    subjects = []
    for subject in result.subjects:
        trials = []
        for trial in subject.trials:
            ask = ActionTurnResult(
                turn_number=1, action=GuesserAction(action="ASK", question="Is it old?",
                                                   name=None, description=None),
                adjudication=baseline, counted=True, counted_questions=1,
                guesser_call_id="GC-" + "1" * 32,
            )
            guess = ActionTurnResult(
                turn_number=2,
                action=GuesserAction(action="GUESS", question=None,
                                     name="Guess sentinel", description="A guess"),
                adjudication=TurnAdjudication(
                    component="guess_validator", call_id="VC-" + "1" * 32, answer=OracleAnswer.NO,
                ), counted=True, counted_questions=2, guesser_call_id="GC-" + "2" * 32,
            )
            turns = (
                ask, guess,
                ask.model_copy(update={"turn_number": 3, "counted_questions": 3}),
                ContractViolationTurnResult(
                    turn_number=4, violation_kind="invalid_json", feedback_event="FORMAT_ERROR",
                    counted=True, counted_questions=4, guesser_call_id="GC-" + "4" * 32,
                ),
            )
            episode = trial.result.model_copy(update={
                "turns": turns,
                "llm_details": trial.result.llm_details.model_copy(update={
                    "oracle": trial.result.llm_details.oracle.model_copy(update={
                        "configuration": oracle_config,
                    }),
                }),
            })
            trials.append(trial.model_copy(update={"result": episode}))
        subjects.append(subject.model_copy(update={"trials": tuple(trials)}))
    return result.model_copy(update={
        "run": result.run.model_copy(update={"definition": definition}), "subjects": tuple(subjects),
    })


def plan_for(source, **selection):
    return build_replay_plan(
        source, source.run.definition.oracle_configuration, run_id="replay-test",
        selection=ReplaySelection(**selection),
    )


def report_for(plan):
    return ReplayReport(
        plan=plan, plan_hash=plan.content_hash(), started_at="2026-09-07", updated_at="2026-09-07",
    )


class Observer:
    def __init__(self):
        self.outcomes = []

    def completed(self, outcome, total):
        self.outcomes.append(outcome)


class FakeProvider:
    def __init__(self, config, *, research, answers):
        self.config = config
        self.research = research
        self.answers = list(answers)
        self.requests = []

    def complete(self, request: ProviderRequest) -> ProviderExchange:
        self.requests.append(request)
        answer = self.answers.pop(0)
        if answer == "FAIL":
            raise OracleProviderError("PRIVATE_PROVIDER_ERROR", code="provider_request_failed")
        payload = {
            "answer": answer,
            "basis": "other" if answer == "UNKNOWN" else "evidence",
            "supporting_statement": "NEW_SUPPORT_SENTINEL",
        }
        if self.research:
            payload.update({
                "evidence": [{"source_url": "https://example.test/new", "excerpt": "NEW_EVIDENCE",
                              "validation": "model_reported"}],
                "research_outcome": "ambiguous_question" if answer == "UNKNOWN" else "answered",
                "attempted_queries": ["subject property"],
            })
        else:
            payload["evidence_indices"] = [] if answer == "UNKNOWN" else [1]
        raw = json.dumps(payload)
        return ProviderExchange(raw_output=raw, trace=ProviderTrace(
            requested_at="2026-09-07T00:00:00+00:00", completed_at="2026-09-07T00:00:01+00:00",
            latency_ms=1000, requested_model=self.config.model, resolved_model=self.config.model,
            requested_provider=self.config.provider, resolved_provider=self.config.provider,
            request={"messages": list(request.messages)}, response={"private": "RAW_TRACE_SENTINEL"},
            raw_output=raw, usage=ProviderUsage(
                input_tokens=100, output_tokens=30, search_count=int(self.research),
                cached_input_tokens=10, cost_usd=Decimal("0.01"),
            ),
        ))


def service_for(plan, tmp_path, research, review, judge):
    config = plan.oracle_configuration
    providers = (
        FakeProvider(config, research=True, answers=research),
        FakeProvider(config.reviewer, research=False, answers=review),
        FakeProvider(config.judge, research=False, answers=judge),
    )
    writer = RunAuditWriter(
        tmp_path / "unused-audit", config=config, subject_catalog_hash="a" * 64, repository=tmp_path,
    )
    return Oracle(*providers, writer, config), providers


def test_selection_preserves_repeats_order_subjects_and_excludes_non_ask(source):
    plan = plan_for(source)
    assert len(plan.cases) == 8
    assert [case.turn_number for case in plan.cases] == [1, 3] * 4
    assert all(case.question == "Is it old?" for case in plan.cases)
    subset = plan_for(source, targets=(SubjectId("T-0002"),), trials=(TrialId("trial-002"),),
                      turns=(3,), limit=1)
    assert len(subset.cases) == 1
    assert subset.cases[0].subject == source.subjects[1].subject
    assert subset.source_ask_count == 8


@pytest.mark.parametrize("selection", [
    {"targets": (SubjectId("T-9999"),)}, {"trials": (TrialId("trial-999"),)},
    {"turns": (2,)}, {"turns": (0,)}, {"turns": (1, 1)},
])
def test_bad_selection_is_rejected(source, selection):
    with pytest.raises(ValueError):
        plan_for(source, **selection)


def test_five_answer_source_rejects_three_answer_config(source):
    with pytest.raises(ValueError, match="five-answer"):
        build_replay_plan(source, OracleConfig(model="openai/test", provider="openai"),
                          run_id="test", selection=ReplaySelection())


def test_real_oracle_pipeline_is_blind_and_generates_fresh_repeated_answers(source, tmp_path):
    plan = plan_for(source, limit=3)
    service, providers = service_for(
        plan, tmp_path, ["RATHER_YES", "YES", "UNKNOWN"], ["RATHER_YES", "RATHER_NO"], ["NO"],
    )
    store = ReplayStore(tmp_path / "review", RunArtifactPolicy(verbose=True))
    report = run_replay(report_for(plan), service, store, Observer())
    assert report.status is ReplayStatus.COMPLETED
    assert [item.adjudication.final_answer for item in report.outcomes] == [
        OracleAnswer.RATHER_YES, OracleAnswer.NO, OracleAnswer.UNKNOWN,
    ]
    assert [len(provider.requests) for provider in providers] == [3, 2, 1]
    for provider in providers:
        for request in provider.requests:
            content = json.dumps(request.model_dump(mode="json"))
            assert "OLD_EVIDENCE_SENTINEL" not in content
            assert "Guess sentinel" not in content
            assert "BX-replay-source" not in content
            assert "trial-" not in content
    for provider in providers[1:]:
        for request in provider.requests:
            assert "NEW_SUPPORT_SENTINEL" not in json.dumps(request.messages)
            assert "NEW_EVIDENCE" in json.dumps(request.messages)
    assert providers[0].requests[0].session_id != providers[1].requests[0].session_id
    assert providers[1].requests[0].session_id != providers[2].requests[0].session_id
    assert store.load() == report
    encoded = (store.directory / "result.yml").read_text()
    assert "RAW_TRACE_SENTINEL" not in encoded
    assert "prompt_version" in encoded
    assert "NEW_SUPPORT_SENTINEL" in (store.directory / "review.md").read_text()
    summary = summarize_replay(report)
    assert (summary.changed, summary.unchanged, summary.final_unknown) == (2, 1, 1)
    assert summary.known_cost_usd == Decimal("0.06")


def test_required_role_failure_is_not_an_oracle_fallback_and_circuit_breaker_stops(source, tmp_path):
    plan = plan_for(source, limit=3)
    service, providers = service_for(plan, tmp_path, ["YES", "YES"], ["FAIL", "FAIL"], [])
    store = ReplayStore(tmp_path / "review", RunArtifactPolicy())
    report = run_replay(report_for(plan), service, store, Observer(), max_consecutive_failures=2)
    assert report.status is ReplayStatus.STOPPED
    assert len(report.outcomes) == 2
    assert all(isinstance(item, ReplayFailure) for item in report.outcomes)
    assert [len(provider.requests) for provider in providers] == [2, 2, 0]
    assert {path.name for path in store.directory.iterdir()} == {"result.yml"}
    assert "PRIVATE_PROVIDER_ERROR" not in (store.directory / "result.yml").read_text()


def test_resume_accounts_for_interrupted_call_and_skips_completed_calls(source, tmp_path):
    plan = plan_for(source, limit=3)
    service, providers = service_for(plan, tmp_path, ["UNKNOWN"] * 3, [], [])
    store = ReplayStore(tmp_path / "review", RunArtifactPolicy())
    class InterruptingOracle:
        def ask(self, request):
            if len(providers[0].requests) == 1:
                raise KeyboardInterrupt
            return service.ask(request)
    with pytest.raises(KeyboardInterrupt):
        run_replay(report_for(plan), InterruptingOracle(), store, Observer())
    checkpoint = store.load()
    assert checkpoint.in_flight == 2
    resumed = run_replay(checkpoint, service, store, Observer())
    assert [item.status for item in resumed.outcomes] == ["success", "failure", "success"]
    assert resumed.outcomes[1].code == "replay_interrupted"
    assert len(providers[0].requests) == 2
    assert run_replay(resumed, service, store, Observer()) == resumed
    assert len(providers[0].requests) == 2


def test_checkpoint_integrity_lock_and_safe_rendering(source, tmp_path):
    plan = plan_for(source, limit=1)
    store = ReplayStore(tmp_path / "review", RunArtifactPolicy())
    report = report_for(plan)
    with store.locked(), pytest.raises(ValueError, match="already running"), store.locked():
        pass
    store.save(report)
    path = store.directory / "result.yml"
    assert path.stat().st_mode & 0o077 == 0
    path.write_text(path.read_text().replace("2026-09-07", "2026-09-08"))
    with pytest.raises(ValueError, match="integrity"):
        store.load()
    unsafe_case = plan.cases[0].model_copy(update={"question": "<script>alert(1)</script>"})
    unsafe_plan = plan.model_copy(update={"cases": (unsafe_case,)})
    failed = report_for(unsafe_plan).model_copy(update={"outcomes": (
        ReplayFailure(case_number=1, recorded_at="now", code="failure"),
    )})
    rendered = render_replay_review(failed)
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered


def test_source_loader_checks_original_signed_payload(source, tmp_path):
    payload = source.model_dump(mode="json")
    payload.pop("integrity_hash")
    payload["artifacts"]["result"]["integrity_hash"] = None
    payload["integrity_hash"] = sha256_text(canonical_json(payload))
    path = tmp_path / "source.yml"
    path.write_text(yaml.safe_dump(payload))
    assert load_benchmark_result_file(path).run.execution_id == source.run.execution_id
    path.write_text(path.read_text().replace("Is it old?", "Is it new?"))
    with pytest.raises(ArtifactIntegrityError):
        load_benchmark_result_file(path)


def test_cli_dry_run_and_resume_never_construct_guesser_or_load_credentials_when_done(
    source, tmp_path, monkeypatch,
):
    monkeypatch.setattr(cli, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(cli, "load_benchmark_result_file", lambda _path: source)
    monkeypatch.setattr(cli, "load_oracle_config", lambda _path: source.run.definition.oracle_configuration)
    monkeypatch.setattr(cli, "load_openrouter_api_key", lambda _root: pytest.fail("credentials loaded"))
    monkeypatch.setattr(cli, "OpenRouterOracleProviderSet", lambda *_args: pytest.fail("providers created"))
    args = ["replay-oracle", "source.yml", "--run-id", "replay-test", "--oracle-config", "current.yml"]
    assert CliRunner().invoke(benchmark_app, [*args, "--dry-run"]).exit_code == 0
    assert CliRunner().invoke(benchmark_app, args).exit_code == 0
    assert not (tmp_path / "private").exists()
    args = [*args, "--live"]
    plan = plan_for(source, limit=1)
    directory = tmp_path / "private/reviews/oracle-replay/replay-test"
    report = report_for(plan).model_copy(update={
        "status": ReplayStatus.COMPLETED,
        "outcomes": (ReplayFailure(case_number=1, recorded_at="now", code="test_failure"),),
    })
    ReplayStore(directory, RunArtifactPolicy()).save(report)
    assert CliRunner().invoke(benchmark_app, [*args, "--limit", "1", "--resume"]).exit_code == 1
    assert CliRunner().invoke(benchmark_app, [*args, "--limit", "2", "--resume"]).exit_code == 2
    assert CliRunner().invoke(benchmark_app, [*args, "--limit", "1"]).exit_code == 2


def test_cli_executes_current_pipeline_and_rejects_changed_contract_before_calls(
    source, tmp_path, monkeypatch, caplog,
):
    config = source.run.definition.oracle_configuration
    providers = (
        FakeProvider(config, research=True, answers=["YES"]),
        FakeProvider(config.reviewer, research=False, answers=["YES"]),
        FakeProvider(config.judge, research=False, answers=[]),
    )
    class ProviderSet:
        def __init__(self, _key, current_config):
            assert current_config == config
            self.oracle, self.reviewer, self.judge = providers

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

    monkeypatch.setattr(cli, "repository_root", lambda: tmp_path)
    monkeypatch.setattr(cli, "load_benchmark_result_file", lambda _path: source)
    monkeypatch.setattr(cli, "load_oracle_config", lambda _path: config)
    monkeypatch.setattr(cli, "load_openrouter_api_key", lambda _root: "unused")
    monkeypatch.setattr(cli, "OpenRouterOracleProviderSet", ProviderSet)
    monkeypatch.setattr(cli, "prevent_idle_system_sleep", nullcontext)
    args = ["replay-oracle", "source.yml", "--run-id", "replay-test",
            "--oracle-config", "current.yml", "--limit", "1", "--live"]
    result = CliRunner().invoke(benchmark_app, args)
    assert result.exit_code == 0, result.output
    report = ReplayStore(tmp_path / "private/reviews/oracle-replay/replay-test",
                         RunArtifactPolicy()).load()
    assert report.outcomes[0].adjudication.final_answer is OracleAnswer.YES
    assert [len(provider.requests) for provider in providers] == [1, 1, 0]
    assert "OLD_EVIDENCE_SENTINEL" not in caplog.text
    assert "NEW_SUPPORT_SENTINEL" not in caplog.text
    assert "Is it old?" not in caplog.text
    assert "RAW_TRACE_SENTINEL" not in caplog.text
    monkeypatch.setattr(cli, "load_openrouter_api_key", lambda _root: pytest.fail("credentials loaded"))
    monkeypatch.setattr(cli, "load_oracle_config", lambda _path: config.model_copy(update={
        "adjudication_policy": AdjudicationPolicy.JUDGE_STABLE_KNOWLEDGE_V1,
    }))
    assert CliRunner().invoke(benchmark_app, [*args, "--resume"]).exit_code == 2
