import shutil
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest
from deep20_benchmark import cli
from deep20_benchmark.artifacts import ArtifactStore
from deep20_benchmark.canary import LlmCanaryResult, StartupCanaryResult
from deep20_benchmark.launch import prepare_request, request_definition
from deep20_benchmark.models import (
    BenchmarkExecutionId,
    BenchmarkLlmRole,
    BenchmarkModelId,
    ExecutionStatus,
)
from test_edition_launch import inputs
from typer.testing import CliRunner

ROOT = Path(__file__).parents[4]


@pytest.fixture
def environment(tmp_path, monkeypatch):
    shutil.copytree(ROOT / 'config', tmp_path / 'config')
    monkeypatch.setattr(cli, 'repository_root', lambda: tmp_path)
    monkeypatch.setattr(cli, 'prevent_idle_system_sleep', nullcontext)
    return tmp_path


def invoke(*options, command='run'):
    return CliRunner().invoke(cli.benchmark_app, [command, '--model', 'M-0001',
                             '--run-id', 'BX-cli-test', *options])


def forbid(*_args, **_kwargs):
    pytest.fail('preflight must not load credentials, run canaries, or execute a benchmark')


@pytest.mark.parametrize('options', [
    ('B-0001',), ('B-0002',), ('--edition', '9.9'),
    ('--iterations', '5', '--benchmark-mode', 'official'),
    ('--expected-comparison', '0' * 64),
])
def test_invalid_plan_stops_before_credentials_and_paid_calls(environment, monkeypatch, options):
    for name in ('load_openrouter_api_key', 'run_startup_canaries', 'LiveEpisodeExecutor'):
        monkeypatch.setattr(cli, name, forbid)
    result = invoke(*options)
    assert result.exit_code == 1, result.output
    assert not (environment / 'runs').exists()


def test_offline_dry_run_defaults_to_official_release(environment, monkeypatch):
    for name in ('load_openrouter_api_key', 'run_startup_canaries', 'LiveEpisodeExecutor'):
        monkeypatch.setattr(cli, name, forbid)
    result = invoke('--dry-run')
    assert result.exit_code == 0, result.output
    assert 'edition=1.1' in result.output and 'mode=official' in result.output
    assert 'answers=YES,NO,UNKNOWN,RATHER_YES,RATHER_NO' in result.output
    assert 'trials_per_subject=3 subjects=10 games=30 question_limit=40' in result.output
    assert not (environment / 'runs').exists()


def test_explicit_trial_override_is_visible_variant(environment, monkeypatch):
    monkeypatch.setattr(cli, 'load_openrouter_api_key', forbid)
    result = invoke('--iterations', '5', '--dry-run')
    assert result.exit_code == 0, result.output
    assert 'classification=variant' in result.output and 'mode=experimental' in result.output
    assert 'trials_per_subject=5' in result.output and 'overrides=iterations' in result.output


def test_benchmark_mode_rejects_unknown_value(environment):
    assert invoke('--benchmark-mode', 'draft').exit_code == 2


@pytest.mark.parametrize('command', ['run', 'repair'])
@pytest.mark.parametrize('canary', [True, False])
def test_official_canaries_and_concise_logging(environment, monkeypatch, command, canary):
    requests, probes = [], []
    class Runner:
        def __init__(self, **kwargs):
            pass
        def run(self, request, **kwargs):
            requests.append(request)
            return SimpleNamespace(outcome=SimpleNamespace(has_infrastructure_failures=False))
    monkeypatch.setattr(cli, 'BenchmarkRunner', Runner)
    monkeypatch.setattr(cli, 'load_openrouter_api_key', lambda _root: 'offline')
    monkeypatch.setattr(cli, 'run_startup_canaries', lambda *args, **kwargs:
                        (probes.append((args, kwargs)) or SimpleNamespace(valid=True, roles=())))
    result = invoke(*([] if canary else ['--no-canary']), command=command)
    assert result.exit_code == 0, result.output
    assert bool(probes) == canary
    assert requests[0].benchmark_mode.value == 'official'
    assert requests[0].edition.classification == 'standard'
    assert 'benchmark.plan' in result.output
    assert 'guesser_conversation' not in result.output


def test_completed_execution_skips_paid_canaries(environment, monkeypatch):
    monkeypatch.setattr(ArtifactStore, '_git', staticmethod(lambda _args: 'offline'))
    values = inputs(environment)
    request = prepare_request(environment, **values, model_id=BenchmarkModelId('M-0001'),
                              execution_id=BenchmarkExecutionId('BX-cli-test'))
    store = ArtifactStore(environment)
    manifest = store.execution_manifest(request=request,
        definition=request_definition(request, values['benchmarks'], values['subjects']),
        model=values['models'].model(request.model_id), subject_catalog_hash=values['subjects'].content_hash())
    monkeypatch.setattr(ArtifactStore, 'load_manifest', lambda *_args: manifest)
    monkeypatch.setattr(ArtifactStore, 'load_state', lambda *_args: SimpleNamespace(status=ExecutionStatus.COMPLETED))
    monkeypatch.setattr(cli, 'load_openrouter_api_key', lambda _root: 'offline')
    monkeypatch.setattr(cli, 'run_startup_canaries', forbid)
    monkeypatch.setattr(cli, 'BenchmarkRunner', lambda **kwargs: SimpleNamespace(
        run=lambda *args, **kwargs: SimpleNamespace(outcome=SimpleNamespace(has_infrastructure_failures=False))))
    assert invoke().exit_code == 0
    monkeypatch.setattr(cli, 'load_openrouter_api_key', forbid)
    changed = invoke('--iterations', '5')
    assert changed.exit_code == 1 and 'edition_resume_mismatch' in changed.output


def test_failed_canary_stops_before_execution(environment, monkeypatch):
    monkeypatch.setattr(cli, 'load_openrouter_api_key', lambda _root: 'offline')
    monkeypatch.setattr(cli, 'LiveEpisodeExecutor', forbid)
    monkeypatch.setattr(cli, 'run_startup_canaries', lambda *args, **kwargs: StartupCanaryResult(
        valid=False, roles=(LlmCanaryResult(role=BenchmarkLlmRole.JUDGE, model='anthropic/test',
        provider='anthropic', valid=False, error_code='provider_unavailable'),)))
    result = invoke()
    assert result.exit_code == 1 and 'LLM startup canary failed' in result.output
    assert not (environment / 'runs').exists()


def test_repair_retains_exclusion_and_reports_remaining_failures(environment, monkeypatch):
    captured = []
    class Runner:
        def __init__(self, **kwargs):
            captured.append(kwargs['executor'])
        def run(self, request, **kwargs):
            captured.append(kwargs['repair'])
            return SimpleNamespace(outcome=SimpleNamespace(has_infrastructure_failures=True),
                                   summary=SimpleNamespace(counts=SimpleNamespace(infrastructure_failed=2)))
    monkeypatch.setattr(cli, 'BenchmarkRunner', Runner)
    monkeypatch.setattr(cli, 'load_openrouter_api_key', lambda _root: 'offline')
    result = invoke('--judge-ignore-provider', 'Amazon-Bedrock', '--no-canary', command='repair')
    assert result.exit_code == 1 and 'benchmark_infrastructure_failures_remain' in result.output
    assert captured[0].judge_ignored_providers == ('amazon-bedrock',)
    assert captured[1].judge_ignored_providers == ('amazon-bedrock',)
