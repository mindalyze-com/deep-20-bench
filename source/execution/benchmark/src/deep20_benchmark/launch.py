"""Shared pre-spend planning for single runs and batches."""

from pathlib import Path

from deep20_game.config import BenchmarkMode
from deep20_oracle.catalog import SubjectCatalog

from .backend_resolution import resolved_definition, resolved_model
from .catalog import BenchmarkCatalog, ModelCatalog
from .edition_models import EditionOverrides
from .edition_profiles import edition_profile, registered_edition, resolve_execution
from .edition_runtime import select_runtime
from .models import (
    BenchmarkDefinitionSnapshot,
    BenchmarkExecutionId,
    BenchmarkId,
    BenchmarkManifest,
    BenchmarkModelId,
    BenchmarkRequest,
    SubjectId,
)


def prepare_request(
    root: Path, *, models: ModelCatalog, benchmarks: BenchmarkCatalog, subjects: SubjectCatalog,
    model_id: BenchmarkModelId, execution_id: BenchmarkExecutionId,
    edition_id: str | None = None, benchmark_id: str | None = None,
    mode: BenchmarkMode | None = None, iterations: int | None = None,
    target_ids: tuple[str, ...] | None = None, base_seed: int | None = None,
    variant_name: str | None = None, runtime_config_path: Path | None = None,
    existing: BenchmarkManifest | None = None,
) -> BenchmarkRequest:
    if existing is not None and existing.request.edition is not None:
        saved = existing.request.edition
        edition_id = edition_id or saved.edition_id
        benchmark_id = benchmark_id or str(existing.request.benchmark_id)
        old = saved.overrides
        iterations = iterations if iterations is not None else old.iterations
        target_ids = target_ids if target_ids is not None else old.target_ids
        base_seed = base_seed if base_seed is not None else old.base_seed
        variant_name = variant_name if variant_name is not None else old.variant_name
    edition = registered_edition(root, edition_id)
    selected_id = BenchmarkId(benchmark_id or edition.benchmark_id)
    if str(selected_id) != edition.benchmark_id and variant_name is None:
        raise ValueError("edition_contract_mismatch: benchmark does not match selected edition")
    entry = benchmarks.entry(selected_id)
    model = models.model(model_id)
    if edition.runtime_overrides:
        runtime = select_runtime(root, edition_id=edition.edition_id, config_path=runtime_config_path,
                                 model=model, benchmark=entry)
        return BenchmarkRequest(
            benchmark_id=selected_id, execution_id=execution_id, model_id=model_id,
            benchmark_mode=mode or BenchmarkMode.EXPERIMENTAL,
            target_ids=tuple(SubjectId(t) for t in target_ids) if target_ids is not None else (),
            iterations_override=iterations, base_seed=base_seed if base_seed is not None else 0,
            runtime=runtime,
        )
    if runtime_config_path is not None:
        raise ValueError("runtime overrides require an explicit draft edition")
    profile = edition_profile(root, edition)
    targets = target_ids if target_ids is not None else profile.cohort.target_ids
    count = iterations if iterations is not None else profile.cohort.iterations
    seed = base_seed if base_seed is not None else profile.cohort.base_seed
    variant = bool(variant_name or targets != profile.cohort.target_ids
                   or count != profile.cohort.iterations or seed != profile.cohort.base_seed)
    selected_mode = mode or (BenchmarkMode.EXPERIMENTAL if variant else BenchmarkMode.OFFICIAL)
    if not variant and selected_mode is not BenchmarkMode.OFFICIAL:
        raise ValueError("released edition runs use official mode; name a --variant for experiments")
    definition = benchmarks.benchmark(selected_id, benchmark_mode=selected_mode,
                                     subject_ids=tuple(SubjectId(t) for t in targets),
                                     iterations_override=count)
    overrides = EditionOverrides(iterations=iterations, target_ids=target_ids,
                                 base_seed=base_seed, variant_name=variant_name)
    record = resolve_execution(profile, definition, subjects, overrides, seed,
                               allow_inactive=existing is not None)
    return BenchmarkRequest(
        benchmark_id=selected_id, execution_id=execution_id, model_id=model_id,
        benchmark_mode=selected_mode, target_ids=definition.subject_ids,
        iterations_override=count, base_seed=seed, edition=record,
    )


def request_definition(request: BenchmarkRequest, benchmarks: BenchmarkCatalog,
                       subjects: SubjectCatalog) -> BenchmarkDefinitionSnapshot:
    targets = request.target_ids or tuple(SubjectId(s.target_id) for s in subjects.active_subjects())
    definition = benchmarks.benchmark(request.benchmark_id, benchmark_mode=request.benchmark_mode,
                                     subject_ids=targets, iterations_override=request.iterations_override)
    return resolved_definition(definition, request.runtime) if request.runtime else definition


def validate_resume(existing: BenchmarkManifest, request: BenchmarkRequest,
                    benchmarks: BenchmarkCatalog, models: ModelCatalog, subjects: SubjectCatalog) -> None:
    definition = request_definition(request, benchmarks, subjects)
    model = models.model(request.model_id)
    if request.runtime:
        model = resolved_model(model, request.runtime)
    if (existing.request != request or existing.definition != definition or existing.model != model
        or existing.subject_catalog_hash != subjects.content_hash()):
        raise ValueError("edition_resume_mismatch: immutable execution differs; use a fresh run ID")


def plan_summary(request: BenchmarkRequest, definition: BenchmarkDefinitionSnapshot) -> str:
    edition = request.edition
    if edition is None:
        return f"edition={request.runtime.edition.edition_id if request.runtime else 'unknown'} mode={request.benchmark_mode} draft=true"
    explicit = ','.join(edition.overrides.model_dump(exclude_none=True)) or 'none'
    return (f"edition={edition.edition_id} revision={edition.revision} mode={request.benchmark_mode} "
            f"classification={edition.classification} benchmark={request.benchmark_id} "
            f"answers={','.join(edition.answer_tokens)} trials_per_subject={definition.iterations} "
            f"subjects={len(definition.subject_ids)} games={len(definition.subject_ids) * definition.iterations} "
            f"question_limit={definition.game_policy.max_questions} seed={request.base_seed} "
            f"overrides={explicit} variant={edition.overrides.variant_name or 'none'} "
            f"differences={','.join(edition.differences) or 'none'} comparison={edition.comparison_hash}")
