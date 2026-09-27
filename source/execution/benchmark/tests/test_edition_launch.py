from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml
from deep20_benchmark.artifacts import ArtifactStore
from deep20_benchmark.catalog import load_benchmark_catalog, load_model_catalog
from deep20_benchmark.edition_profiles import validate_execution
from deep20_benchmark.launch import prepare_request, request_definition, validate_resume
from deep20_benchmark.models import BenchmarkExecutionId, BenchmarkModelId
from deep20_benchmark.runner import BenchmarkRunner
from deep20_game.config import BenchmarkMode
from deep20_oracle.catalog import load_subject_catalog
from test_runner import FakeExecutor

ROOT = Path(__file__).parents[4]


@pytest.fixture
def repository(tmp_path):
    shutil.copytree(ROOT / 'config', tmp_path / 'config')
    return tmp_path


def inputs(root):
    return {'models': load_model_catalog(root / 'config/models.yaml'),
            'benchmarks': load_benchmark_catalog(root / 'config/benchmarks.yaml'),
            'subjects': load_subject_catalog(root / 'config/subjects.yaml')}


def request(root, **overrides):
    return prepare_request(root, **inputs(root), model_id=BenchmarkModelId('M-0001'),
                           execution_id=BenchmarkExecutionId('BX-edition-test'), **overrides)


def test_default_release_is_official_five_answers_three_trials(repository):
    result = request(repository)
    assert str(result.benchmark_id) == 'B-0003'
    assert result.benchmark_mode is BenchmarkMode.OFFICIAL
    assert result.iterations_override == 3
    assert len(result.target_ids) == 10
    assert result.base_seed == 0
    assert result.edition.edition_id == '1.1'
    assert result.edition.classification == 'standard'
    assert set(result.edition.answer_tokens) == {'YES', 'RATHER_YES', 'RATHER_NO', 'NO', 'UNKNOWN'}
    assert not any(result.edition.overrides.model_dump().values())


@pytest.mark.parametrize('overrides', [
    {'benchmark_id': 'B-0001'}, {'benchmark_id': 'B-0002'},
    {'mode': BenchmarkMode.EXPERIMENTAL}, {'edition_id': '9.9'},
    {'iterations': 5, 'mode': BenchmarkMode.OFFICIAL},
])
def test_incompatible_selections_are_rejected(repository, overrides):
    with pytest.raises(ValueError):
        request(repository, **overrides)
    assert not (repository / 'runs').exists()


@pytest.mark.parametrize('overrides,difference', [
    ({'iterations': 5}, 'iterations'),
    ({'target_ids': ('T-0001',)}, 'target_ids'),
    ({'base_seed': 17}, 'base_seed'),
    ({'benchmark_id': 'B-0001', 'variant_name': 'three-answer-control'}, 'game_policy'),
])
def test_explicit_overrides_are_recorded_variants(repository, overrides, difference):
    result = request(repository, **overrides)
    assert result.benchmark_mode is BenchmarkMode.EXPERIMENTAL
    assert result.edition.classification == 'variant'
    assert difference in result.edition.differences
    assert result.edition.comparison_hash != request(repository).edition.comparison_hash


def test_models_share_the_same_comparison_contract(repository):
    a = request(repository)
    b = prepare_request(repository, **inputs(repository), model_id=BenchmarkModelId('M-0015'),
                        execution_id=BenchmarkExecutionId('BX-another-edition-test'))
    assert a.edition == b.edition


def test_subject_drift_requires_a_named_variant(repository):
    path = repository / 'config/subjects.yaml'
    payload = yaml.safe_load(path.read_text())
    payload['subjects']['T-0001']['description'] += ' Changed identity.'
    path.write_text(yaml.safe_dump(payload))
    with pytest.raises(ValueError, match='subject_identities'):
        request(repository)
    assert request(repository, variant_name='changed-subject').edition.classification == 'variant'


def test_changed_prompt_version_is_rejected_before_execution(repository, monkeypatch):
    import deep20_benchmark.edition_profiles as profiles
    monkeypatch.setattr(profiles, 'guesser_prompt_version', lambda _profile: 'changed-prompt')
    with pytest.raises(ValueError, match='prompts'):
        request(repository)


def test_changed_role_config_must_match_release_pins(repository):
    path = repository / 'config/edition-profiles/1.1.yaml'
    payload = yaml.safe_load(path.read_text())
    payload['oracle_configuration']['reasoning_effort'] = 'high'
    path.write_text(yaml.safe_dump(payload))
    with pytest.raises(ValueError, match='release pins'):
        request(repository)


def test_profile_defaults_cannot_be_shadowed_in_catalog(repository):
    path = repository / 'config/benchmarks.yaml'
    payload = yaml.safe_load(path.read_text())
    payload['benchmarks']['B-0003']['default_iterations'] = 5
    path.write_text(yaml.safe_dump(payload))
    with pytest.raises(ValueError, match='cannot override profile'):
        request(repository)


def test_execution_validates_contract_again_after_preflight(repository):
    values = inputs(repository)
    result = request(repository)
    definition = request_definition(result, values['benchmarks'], values['subjects'])
    selected = tuple(values['subjects'].subject(str(t)) for t in result.target_ids)
    validate_execution(result.edition, definition, selected, result.base_seed)
    with pytest.raises(ValueError, match='changed after preflight'):
        validate_execution(result.edition, definition.model_copy(update={'iterations': 5}), selected, 0)


def test_runner_persists_standard_and_variant_contracts_and_blocks_resume(repository, monkeypatch):
    monkeypatch.setattr(ArtifactStore, '_git', staticmethod(lambda _args: 'offline-commit'))
    values = inputs(repository)
    first = request(repository, target_ids=('T-0001',), iterations=1)
    executor = FakeExecutor()
    runner = BenchmarkRunner(store=ArtifactStore(repository), model_catalog=values['models'],
                             benchmark_catalog=values['benchmarks'], subject_catalog=values['subjects'],
                             executor=executor)
    result = runner.run(first)
    assert result.run.edition == first.edition
    assert result.outcome.publication_eligible is False
    manifest = runner.store.load_manifest(first.model_id, first.execution_id)
    assert manifest.request.edition == first.edition
    restored = prepare_request(repository, **values, model_id=first.model_id,
                               execution_id=first.execution_id, existing=manifest)
    assert restored == first
    validate_resume(manifest, restored, values['benchmarks'], values['models'], values['subjects'])
    changed = request(repository, iterations=5)
    with pytest.raises(ValueError, match='immutable execution'):
        validate_resume(manifest, changed, values['benchmarks'], values['models'], values['subjects'])
    assert len(executor.calls) == 1
    assert executor.calls[0].edition == first.edition
    assert result.run.edition.model_dump_json() not in str(result.subjects[0].trials[0].result.guesser_conversation)


def test_comparison_rejects_different_trials_and_unprofiled_history(repository, monkeypatch):
    from deep20_benchmark.comparison import require_comparable
    monkeypatch.setattr(ArtifactStore, '_git', staticmethod(lambda _args: 'offline'))
    values = inputs(repository)
    store = ArtifactStore(repository)
    def manifest(req):
        return store.execution_manifest(request=req,
            definition=request_definition(req, values['benchmarks'], values['subjects']),
            model=values['models'].model(req.model_id), subject_catalog_hash=values['subjects'].content_hash())
    a = manifest(request(repository))
    b = manifest(prepare_request(repository, **values, model_id=BenchmarkModelId('M-0015'),
                                execution_id=BenchmarkExecutionId('BX-other-model')))
    require_comparable(a, b)
    with pytest.raises(ValueError, match='comparison_contract_mismatch'):
        require_comparable(a, manifest(request(repository, iterations=5)))
    with pytest.raises(ValueError, match='historical run'):
        require_comparable(a, a.model_copy(update={'request': a.request.model_copy(update={'edition': None})}))


@pytest.mark.parametrize('overrides', [
    {}, {'benchmark_id': 'B-0001', 'variant_name': 'three-answer-control'},
])
def test_resume_restores_benchmark_and_retains_now_inactive_subjects(repository, monkeypatch, overrides):
    monkeypatch.setattr(ArtifactStore, '_git', staticmethod(lambda _args: 'offline'))
    values = inputs(repository)
    original = request(repository, **overrides)
    manifest = ArtifactStore(repository).execution_manifest(request=original,
        definition=request_definition(original, values['benchmarks'], values['subjects']),
        model=values['models'].model(original.model_id),
        subject_catalog_hash=values['subjects'].content_hash())
    path = repository / 'config/subjects.yaml'
    payload = yaml.safe_load(path.read_text())
    payload['subjects']['T-0001']['status'] = 'inactive'
    path.write_text(yaml.safe_dump(payload))
    with pytest.raises(ValueError, match='inactive'):
        request(repository, **overrides)
    restored = request(repository, existing=manifest)
    assert restored == original
    values = inputs(repository)
    validate_resume(manifest, restored, values['benchmarks'], values['models'], values['subjects'])


def test_publication_model_selection_does_not_change_execution_contract(repository):
    original = request(repository)
    path = repository / 'config/edition-profiles/1.1.yaml'
    payload = yaml.safe_load(path.read_text())
    payload['cohort']['model_ids'].append('M-0027')
    path.write_text(yaml.safe_dump(payload))
    assert request(repository) == original
