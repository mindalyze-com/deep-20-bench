from __future__ import annotations

import json
from decimal import Decimal

import pytest
import yaml
from deep20_benchmark import oracle_suite_cli as cli
from deep20_benchmark.cli import benchmark_app
from deep20_benchmark.models import SubjectId
from deep20_benchmark.oracle_replay import ReplayFailure, ReplayStatus
from deep20_benchmark.oracle_suite import (
    QuestionCase,
    QuestionSuite,
    SuiteReport,
    build_suite_plan,
    run_oracle_suite,
    summarize_suite,
)
from deep20_benchmark.oracle_suite_io import (
    SuiteStore,
    load_question_suite,
    render_suite_review,
    write_question_suite,
)
from deep20_oracle.artifacts import RunArtifactPolicy
from deep20_oracle.catalog import SubjectCatalog, SubjectCatalogEntry
from deep20_oracle.models import OracleAnswer
from test_oracle_replay import Observer, service_for
from test_oracle_replay import source as source_fixture
from typer.testing import CliRunner


@pytest.fixture
def source(tmp_path):
    return source_fixture.__wrapped__(tmp_path)


def make_plan(source, *, repeat=3, expected=(OracleAnswer.NO,)):
    suite = QuestionSuite(name="PRIVATE_SUITE_NAME", cases=(QuestionCase(
        id="PRIVATE_CASE_ID", subject=source.subjects[0].subject,
        question="Is it old?", expected_answers=expected, notes="PRIVATE_EXPECTATION_NOTES",
    ),))
    return build_suite_plan(suite, source.run.definition.oracle_configuration,
                            run_id="suite-test", repetitions=repeat)


def fresh_report(plan):
    return SuiteReport(plan=plan, plan_hash=plan.content_hash(), started_at="2026-09-07", updated_at="2026-09-07")


def test_fresh_repetitions_blind_roles_expectations_and_variation(source, tmp_path):
    plan = make_plan(source)
    service, providers = service_for(plan, tmp_path, ["YES", "YES", "UNKNOWN"], ["NO", "YES"], ["NO"])
    store = SuiteStore(tmp_path / "suite", RunArtifactPolicy(verbose=True))
    result = run_oracle_suite(fresh_report(plan), service, store, Observer())
    assert result.status is ReplayStatus.COMPLETED
    assert [o.adjudication.final_answer for o in result.outcomes] == [OracleAnswer.NO, OracleAnswer.YES, OracleAnswer.UNKNOWN]
    assert [len(p.requests) for p in providers] == [3, 2, 1]
    for provider in providers:
        for request in provider.requests:
            text = json.dumps(request.model_dump(mode="json"))
            assert all(secret not in text for secret in ["PRIVATE_SUITE_NAME", "PRIVATE_CASE_ID", "PRIVATE_EXPECTATION_NOTES", "expected_answers", "repetition"])
    summary = summarize_suite(result)
    assert (summary.assessed, summary.matched, summary.mismatched, summary.unstable_cases) == (3, 1, 2, 1)
    assert summary.known_cost_usd == Decimal("0.06")
    assert store.load() == result
    text = (store.directory / "review.md").read_text()
    assert "mismatch" in text and "PRIVATE_EXPECTATION_NOTES" in text
    assert "RAW_TRACE_SENTINEL" not in (store.directory / "result.yml").read_text()


def test_expectations_do_not_change_provider_projection(source, tmp_path):
    requests = []
    for number, expected in enumerate(((OracleAnswer.YES,), (OracleAnswer.NO,))):
        plan = make_plan(source, repeat=1, expected=expected)
        service, providers = service_for(plan, tmp_path / str(number), ["UNKNOWN"], [], [])
        result = run_oracle_suite(fresh_report(plan), service,
            SuiteStore(tmp_path / f"r{number}", RunArtifactPolicy()), Observer())
        request = providers[0].requests[0]
        requests.append(request.model_copy(update={"messages": request.messages[:-1]}))
        assert summarize_suite(result).mismatched == 1
    assert requests[0] == requests[1]


def test_resume_does_not_repeat_interrupted_or_completed_calls(source, tmp_path):
    plan = make_plan(source)
    service, providers = service_for(plan, tmp_path, ["UNKNOWN"] * 3, [], [])
    store = SuiteStore(tmp_path / "suite", RunArtifactPolicy())
    class Interrupted:
        def ask(self, request):
            if len(providers[0].requests) == 1:
                raise KeyboardInterrupt
            return service.ask(request)
    with pytest.raises(KeyboardInterrupt):
        run_oracle_suite(fresh_report(plan), Interrupted(), store, Observer())
    checkpoint = store.load()
    assert checkpoint.in_flight == 2
    result = run_oracle_suite(checkpoint, service, store, Observer())
    assert [o.status for o in result.outcomes] == ["success", "failure", "success"]
    assert result.outcomes[1].code == "suite_interrupted"
    assert len(providers[0].requests) == 2
    assert run_oracle_suite(result, service, store, Observer()) == result
    assert len(providers[0].requests) == 2


def test_required_role_failure_stops_without_oracle_fallback(source, tmp_path):
    plan = make_plan(source)
    service, providers = service_for(plan, tmp_path, ["YES"], ["FAIL"], [])
    store = SuiteStore(tmp_path / "suite", RunArtifactPolicy())
    result = run_oracle_suite(fresh_report(plan), service, store, Observer())
    assert result.status is ReplayStatus.STOPPED
    assert len(result.outcomes) == 1 and isinstance(result.outcomes[0], ReplayFailure)
    assert [len(p.requests) for p in providers] == [1, 1, 0]
    assert {p.name for p in store.directory.iterdir()} == {"result.yml"}


def test_suite_file_selection_snapshot_validation_integrity_and_html(source, tmp_path):
    subject = source.subjects[0].subject
    entry = SubjectCatalogEntry(**subject.model_dump())
    catalog = SubjectCatalog(subjects={subject.target_id: entry})
    suite = QuestionSuite(name="suite", cases=(
        QuestionCase(id="first", target_id=SubjectId(subject.target_id), question="<script>unsafe</script>"),
        QuestionCase(id="second", subject=subject, question="Second?"),
    ))
    path = tmp_path / "suite.yml"
    write_question_suite(path, suite)
    assert load_question_suite(path) == suite
    with pytest.raises(FileExistsError):
        write_question_suite(path, suite)
    plan = build_suite_plan(suite, source.run.definition.oracle_configuration, run_id="direct",
                           repetitions=2, case_ids=("first",), catalog=catalog)
    assert plan.total == 2 and plan.case_at(1).subject == subject and plan.case_at(1).target_id is None
    assert [plan.repetition_at(i) for i in (1, 2)] == [1, 2]
    with pytest.raises(ValueError):
        build_suite_plan(suite, source.run.definition.oracle_configuration, run_id="direct", case_ids=("missing",))
    service, _ = service_for(plan, tmp_path, ["UNKNOWN"] * 2, [], [])
    store = SuiteStore(tmp_path / "review", RunArtifactPolicy())
    result = run_oracle_suite(fresh_report(plan), service, store, Observer())
    assert "<script>" not in render_suite_review(result)
    assert "&lt;script&gt;" in render_suite_review(result)
    payload = yaml.safe_load((store.directory / "result.yml").read_text())
    payload['payload']['plan']['suite']['name'] = 'tampered'
    (store.directory / 'result.yml').write_text(yaml.safe_dump(payload))
    with pytest.raises(ValueError):
        store.load()


@pytest.mark.parametrize("change", [
    {"target_id": "T-0009", "subject": {}}, {"question": " "}, {"expected_answers": ["MAYBE"]},
    {"unexpected": "private"}, {"id": "../invalid"},
])
def test_invalid_inputs_rejected(change):
    data = {"id": "case", "target_id": "T-0009", "question": "Question?", **change}
    with pytest.raises(ValueError):
        QuestionCase.model_validate_json(json.dumps(data))


def test_cli_preview_and_export_never_load_credentials_or_construct_providers(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("preview performed a paid setup action")
    monkeypatch.setattr(cli, "load_openrouter_api_key", forbidden)
    monkeypatch.setattr(cli, "OpenRouterOracleProviderSet", forbidden)
    runner = CliRunner()
    result = runner.invoke(benchmark_app, ["test-oracle", "--run-id", "preview", "--target-id", "T-0009", "--question", "Is it old?", "--repeat", "3", "--dry-run"])
    assert result.exit_code == 0, result.output
    preview = runner.invoke(benchmark_app, ["test-oracle", "--run-id", "default-preview", "--target-id", "T-0009", "--question", "Is it old?"])
    assert preview.exit_code == 0, preview.output
    invalid = runner.invoke(benchmark_app, ["test-oracle", "--run-id", "invalid", "--question", "Missing subject", "--dry-run"])
    assert invalid.exit_code == 2
    mixed = runner.invoke(benchmark_app, ["test-oracle", "--run-id", "mixed", "--suite", str(tmp_path / "missing"), "--question", "Question?", "--dry-run"])
    assert mixed.exit_code == 2


def test_default_tests_cannot_connect_to_openrouter():
    import socket
    with pytest.raises(pytest.fail.Exception, match="Network access is disabled"):
        socket.create_connection(("openrouter.ai", 443))
