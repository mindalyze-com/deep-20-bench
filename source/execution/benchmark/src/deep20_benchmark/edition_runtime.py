"""Edition selection and private draft artifact locations owned by the benchmark root."""

from pathlib import Path

from deep20_backends.editions import EditionRegistry
from deep20_oracle.util import load_yaml_unique

from .backend_config import RuntimeConfig, RuntimeSnapshot, resolve_runtime
from .catalog import BenchmarkCatalogEntry
from .models import BenchmarkModelSnapshot


def select_runtime(
    root: Path,
    *,
    edition_id: str | None,
    config_path: Path | None,
    model: BenchmarkModelSnapshot,
    benchmark: BenchmarkCatalogEntry,
) -> RuntimeSnapshot | None:
    if edition_id is None:
        if config_path is not None:
            raise ValueError("--runtime-config requires explicit --edition 1.2")
        return None
    registry = EditionRegistry.model_validate(load_yaml_unique(root / "config" / "editions.yaml"))
    edition = registry.edition(edition_id)
    if edition.benchmark_id != str(benchmark.benchmark_id):
        raise ValueError("edition does not match the selected benchmark")
    if not edition.runtime_overrides:
        if config_path is not None:
            raise ValueError("the selected edition does not permit runtime overrides")
        return None
    return resolve_runtime(
        edition,
        RuntimeConfig.model_validate(load_yaml_unique(config_path)) if config_path else RuntimeConfig(),
        guesser=model.configuration, oracle=benchmark.oracle_configuration,
        validator=benchmark.validator_configuration,
    )


def draft_runs_root(root: Path, runtime: RuntimeSnapshot) -> Path:
    return root / "private" / "editions" / runtime.edition.edition_id / "runs"
