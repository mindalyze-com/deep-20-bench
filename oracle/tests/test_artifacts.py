from deep20_oracle.artifacts import RunArtifactPolicy


def test_default_artifact_policy_gates_current_and_future_auxiliary_files() -> None:
    policy = RunArtifactPolicy()

    assert policy.permits("result.yml")
    assert not policy.permits("manifest.json")
    assert not policy.permits("oracle-calls.jsonl")
    assert not policy.permits("future-component-debug.jsonl")


def test_verbose_artifact_policy_permits_every_component_file() -> None:
    policy = RunArtifactPolicy(verbose=True)

    assert policy.permits("result.yml")
    assert policy.permits("manifest.json")
    assert policy.permits("future-component-debug.jsonl")
