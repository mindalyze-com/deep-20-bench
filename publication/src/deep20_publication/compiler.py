from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Literal

from .models import (
    CohortConfig,
    CompletedTrialSummary,
    ContractReliabilitySnapshot,
    DatasetProvenance,
    EpisodeActionTurn,
    EpisodeComponentMetrics,
    EpisodeModelVersion,
    EpisodeResultArtifact,
    EvidenceReviewConfigurationSnapshot,
    InfrastructureFailedTrialSummary,
    LeaderboardRow,
    LoadedEpisode,
    LoadedRun,
    PublicActionTurn,
    PublicationConfig,
    PublicComponentTelemetry,
    PublicContractViolationTurn,
    PublicEpisodeDetail,
    PublicEpisodeModelVersion,
    PublicEpisodeTelemetry,
    PublicEvidence,
    PublicGuesserDisclosure,
    PublicModel,
    PublicOracleSupportRole,
    PublicOracleSupportUsage,
    PublicRun,
    PublicRunCostTotals,
    PublicRunTotals,
    PublicSubject,
    PublicTrial,
    PublishedDataset,
    SubjectCatalog,
    SubjectSummary,
    Winner,
)


def _public_model(run: LoadedRun) -> PublicModel:
    model = run.manifest.model
    return PublicModel(
        model_id=model.model_id,
        display_name=model.display_name,
        route=model.configuration.model,
        provider=model.configuration.provider,
        reasoning_effort=model.configuration.reasoning_effort,
        seed_capability=model.configuration.seed_capability,
        configuration_hash=model.configuration_hash,
    )


def _contract(
    contract: ContractReliabilitySnapshot,
) -> ContractReliabilitySnapshot:
    return contract.model_copy()


def _b20_score(
    penalized_questions: Decimal | None,
    *,
    failure_penalty: Decimal,
    target_questions: int,
) -> Decimal | None:
    if penalized_questions is None:
        return None
    target = Decimal(target_questions)
    denominator = failure_penalty - target
    if denominator <= 0:
        raise ValueError("B20 target must be below the failure penalty")
    if penalized_questions < 0 or penalized_questions > failure_penalty:
        raise ValueError("penalized questions fall outside the B20 scale")
    return target * (failure_penalty - penalized_questions) / denominator


def _reason_codes(
    run: LoadedRun,
    cohort: CohortConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if run.state.status != "completed":
        reasons.append("incomplete")
    subjects = {
        subject.target_id: subject
        for subject in run.summary.subjects
    }
    if set(subjects) != set(cohort.target_ids):
        reasons.append("subject_cohort_mismatch")
    expected_numbers = set(range(1, cohort.iterations + 1))
    for target_id in cohort.target_ids:
        subject = subjects.get(target_id)
        if subject is None:
            continue
        completed_numbers = {
            trial.identity.trial_number
            for trial in subject.trials
            if isinstance(trial, CompletedTrialSummary)
        }
        if (
            len(subject.trials) != cohort.iterations
            or completed_numbers != expected_numbers
        ):
            reasons.append("trial_coverage_mismatch")
    return tuple(dict.fromkeys(reasons))


def _trial(
    trial: CompletedTrialSummary | InfrastructureFailedTrialSummary,
    *,
    failure_penalty: Decimal,
    b20_target_questions: int,
    episode: LoadedEpisode | None = None,
) -> PublicTrial:
    if isinstance(trial, CompletedTrialSummary):
        status: Literal["success", "model_failure"] = (
            "success" if trial.success else "model_failure"
        )
        scored_questions = (
            Decimal(trial.counted_questions) if trial.success else failure_penalty
        )
        return PublicTrial(
            trial_id=trial.identity.trial_id,
            trial_number=trial.identity.trial_number,
            status=status,
            counted_questions=trial.counted_questions,
            scored_questions=scored_questions,
            b20_score=_b20_score(
                scored_questions,
                failure_penalty=failure_penalty,
                target_questions=b20_target_questions,
            ),
            cost_usd=trial.cost_usd,
            duration_ms=trial.duration_ms,
            contract=_contract(trial.contract),
            failure_code=trial.failure.code if trial.failure else None,
            episode=_public_episode(episode) if episode is not None else None,
        )
    return PublicTrial(
        trial_id=trial.identity.trial_id,
        trial_number=trial.identity.trial_number,
        status="infrastructure_failure",
        counted_questions=trial.partial_metrics.counted_questions,
        scored_questions=None,
        b20_score=None,
        cost_usd=trial.partial_metrics.cost_usd,
        duration_ms=trial.partial_metrics.duration_ms,
        contract=None,
        failure_code=trial.failure.code,
    )


def _public_component_telemetry(
    metrics: EpisodeComponentMetrics,
) -> PublicComponentTelemetry:
    return PublicComponentTelemetry(
        calls=metrics.calls,
        cost_usd=metrics.cost_usd,
        latency_ms=metrics.latency_ms,
        total_tokens=metrics.total_tokens,
        input_tokens=metrics.input_tokens,
        cached_input_tokens=metrics.cached_input_tokens,
        cache_write_tokens=metrics.cache_write_tokens,
        output_tokens=metrics.output_tokens,
        reasoning_tokens=metrics.reasoning_tokens,
        estimated_cache_savings_usd=metrics.estimated_cache_savings_usd,
    )


def _public_model_version(version: EpisodeModelVersion) -> PublicEpisodeModelVersion:
    return PublicEpisodeModelVersion(
        role=version.role,
        configuration_id=version.configuration_id,
        requested_model=version.requested_model,
        requested_provider=version.requested_provider,
        resolved_models=version.resolved_models,
        resolved_providers=version.resolved_providers,
        reasoning_effort=version.reasoning_effort,
        prompt_version=version.prompt_version,
    )


def _public_oracle_support_role(
    configuration: EvidenceReviewConfigurationSnapshot,
    *,
    calls: int,
    cost_usd: Decimal,
) -> PublicOracleSupportRole:
    return PublicOracleSupportRole(
        requested_model=configuration.model,
        requested_provider=configuration.provider,
        reasoning_effort=configuration.reasoning_effort,
        calls=calls,
        cost_usd=cost_usd,
    )


def _public_guesser_disclosure(
    result: EpisodeResultArtifact,
) -> tuple[PublicGuesserDisclosure | None, dict[int, str]]:
    conversation = result.guesser_conversation
    if not conversation:
        return None, {}

    system_messages = tuple(
        message.content
        for message in conversation
        if message.role == "system" and message.turn_number is None
    )
    begin_messages = tuple(
        message.content
        for message in conversation
        if message.role == "user" and message.turn_number is None
    )
    if len(system_messages) != 1 or len(begin_messages) != 1:
        raise ValueError("retained Guesser conversation has an invalid introduction")

    recorded_outputs: dict[int, str] = {}
    for message in conversation:
        if message.role != "assistant":
            continue
        if message.turn_number is None:
            raise ValueError("retained Guesser output has no turn number")
        if message.turn_number in recorded_outputs:
            raise ValueError("retained Guesser conversation has duplicate turn output")
        recorded_outputs[message.turn_number] = message.content

    return (
        PublicGuesserDisclosure(
            system_message=system_messages[0],
            begin_message=begin_messages[0],
        ),
        recorded_outputs,
    )


def _public_episode(episode: LoadedEpisode) -> PublicEpisodeDetail:
    result = episode.result
    oracle_configuration = result.llm_details.oracle.configuration
    oracle_quality = result.summary.oracle_quality
    guesser_disclosure, recorded_outputs = _public_guesser_disclosure(result)
    turns = tuple(
        (
            PublicActionTurn(
                turn_number=turn.turn_number,
                action=turn.action.action,
                question=turn.action.question,
                guess_name=turn.action.name,
                guess_description=turn.action.description,
                adjudicator=turn.adjudication.component,
                answer=turn.adjudication.answer,
                validator_explanation=turn.adjudication.explanation,
                counted=turn.counted,
                counted_questions=turn.counted_questions,
                evidence=tuple(
                    PublicEvidence(
                        source_url=evidence.source_url,
                        excerpt=evidence.excerpt,
                        validation=evidence.validation,
                    )
                    for evidence in turn.adjudication.evidence
                ),
                recorded_output=recorded_outputs.get(turn.turn_number),
            )
            if isinstance(turn, EpisodeActionTurn)
            else PublicContractViolationTurn(
                turn_number=turn.turn_number,
                violation_code=turn.violation_code,
                violation_kind=turn.violation_kind,
                feedback_event=turn.feedback_event,
                counted=turn.counted,
                counted_questions=turn.counted_questions,
            )
        )
        for turn in result.turns
    )
    return PublicEpisodeDetail(
        episode_run_id=episode.identity.episode_run_id,
        episode_id=result.run.episode_id,
        subject_name=result.run.subject.canonical_name,
        subject_description=result.run.subject.description,
        subject_reference_url=result.run.subject.reference_url,
        started_at=result.run.started_at,
        completed_at=result.run.completed_at,
        duration_ms=result.run.duration_ms,
        success=result.outcome.success,
        terminal_reason=result.outcome.terminal_reason,
        scoring_eligible=result.outcome.scoring_eligible,
        publication_eligible=result.outcome.publication_eligible,
        total_turns=result.summary.total_turns,
        counted_questions=result.summary.counted_questions,
        ask_count=result.summary.ask_count,
        guess_count=result.summary.guess_count,
        rejected_guess_count=result.summary.rejected_guess_count,
        oracle_unknown_count=result.summary.oracle_unknown_count,
        cache_status=result.summary.cache_status,
        total_cost_usd=result.summary.costs_usd.total,
        total_tokens=result.summary.tokens.total,
        contract=_contract(result.summary.contract),
        models=tuple(
            _public_model_version(version)
            for version in (
                result.models.under_test,
                result.models.oracle,
                result.models.validator,
            )
        ),
        oracle_support=PublicOracleSupportUsage(
            oracle=_public_oracle_support_role(
                oracle_configuration,
                calls=result.llm_details.oracle.metrics.calls,
                cost_usd=(
                    result.summary.costs_usd.oracle
                    - oracle_quality.quality_control_cost_usd
                ),
            ),
            reviewer=_public_oracle_support_role(
                oracle_configuration.reviewer,
                calls=oracle_quality.reviewed_questions,
                cost_usd=oracle_quality.reviewer_cost_usd,
            ),
            judge=_public_oracle_support_role(
                oracle_configuration.judge,
                calls=oracle_quality.judge_invocations,
                cost_usd=oracle_quality.judge_cost_usd,
            ),
        ),
        guesser_disclosure=guesser_disclosure,
        telemetry=PublicEpisodeTelemetry(
            guesser=_public_component_telemetry(result.llm_details.guesser.metrics),
            oracle=_public_component_telemetry(result.llm_details.oracle.metrics),
            validator=_public_component_telemetry(result.llm_details.validator.metrics),
        ),
        turns=turns,
    )


def _subject(
    subject: SubjectSummary,
    *,
    failure_penalty: Decimal,
    b20_target_questions: int,
    episodes: dict[tuple[str, str], LoadedEpisode],
) -> PublicSubject:
    trials = tuple(
        _trial(
            trial,
            failure_penalty=failure_penalty,
            b20_target_questions=b20_target_questions,
            episode=episodes.get(
                (trial.identity.target_id, trial.identity.trial_id)
            ),
        )
        for trial in subject.trials
    )
    scored = tuple(
        trial.scored_questions for trial in trials if trial.scored_questions is not None
    )
    subject_score = (
        sum(scored, start=Decimal(0)) / Decimal(len(scored))
        if len(scored) == len(trials) and scored
        else None
    )
    counts = subject.summary.counts
    return PublicSubject(
        target_id=subject.target_id,
        display_name=subject.display_name,
        entity_type=subject.entity_type,
        success_rate=subject.summary.success_rate,
        subject_score=subject_score,
        b20_score=_b20_score(
            subject_score,
            failure_penalty=failure_penalty,
            target_questions=b20_target_questions,
        ),
        successful=counts.successful,
        model_failed=counts.model_failed,
        infrastructure_failed=counts.infrastructure_failed,
        contract=_contract(subject.summary.contract),
        trials=trials,
    )


def _total_cost(run: LoadedRun) -> Decimal:
    return run.summary.summary.total_cost_usd


def _public_run_totals(run: LoadedRun) -> PublicRunTotals:
    guesser_cost = Decimal(0)
    primary_oracle_cost = Decimal(0)
    reviewer_cost = Decimal(0)
    judge_cost = Decimal(0)
    validator_cost = Decimal(0)
    total_tokens = 0
    guesser_think_time_ms = 0

    for episode in run.episodes:
        result = episode.result
        quality = result.summary.oracle_quality
        guesser_cost += result.summary.costs_usd.guesser
        reviewer_cost += quality.reviewer_cost_usd
        judge_cost += quality.judge_cost_usd
        primary_oracle_cost += max(
            result.summary.costs_usd.oracle - quality.quality_control_cost_usd,
            Decimal(0),
        )
        validator_cost += result.summary.costs_usd.validator
        total_tokens += result.summary.tokens.total
        guesser_think_time_ms += result.llm_details.guesser.metrics.latency_ms

    for subject in run.summary.subjects:
        for trial in subject.trials:
            if not isinstance(trial, InfrastructureFailedTrialSummary):
                continue
            partial = trial.partial_metrics
            guesser_cost += partial.guesser_cost_usd
            reviewer_cost += partial.reviewer_cost_usd
            judge_cost += partial.judge_cost_usd
            primary_oracle_cost += max(
                partial.oracle_cost_usd
                - partial.reviewer_cost_usd
                - partial.judge_cost_usd,
                Decimal(0),
            )
            validator_cost += partial.validator_cost_usd
            total_tokens += partial.tokens

    repair = run.summary.summary.repair.partial_metrics
    guesser_cost += repair.guesser_cost_usd
    reviewer_cost += repair.reviewer_cost_usd
    judge_cost += repair.judge_cost_usd
    primary_oracle_cost += max(
        repair.oracle_cost_usd
        - repair.reviewer_cost_usd
        - repair.judge_cost_usd,
        Decimal(0),
    )
    validator_cost += repair.validator_cost_usd
    total_tokens += repair.tokens

    component_total_cost = (
        guesser_cost
        + primary_oracle_cost
        + reviewer_cost
        + judge_cost
        + validator_cost
    )
    total_cost = _total_cost(run)
    if abs(total_cost - component_total_cost) > Decimal("0.00000001"):
        raise ValueError("public run component costs differ from the benchmark total")

    return PublicRunTotals(
        costs_usd=PublicRunCostTotals(
            guesser=guesser_cost,
            primary_oracle=primary_oracle_cost,
            reviewer=reviewer_cost,
            judge=judge_cost,
            validator=validator_cost,
            total=total_cost,
        ),
        total_tokens=total_tokens,
        runtime_ms=round(
            (run.state.updated_at - run.manifest.created_at).total_seconds() * 1_000
        ),
        guesser_think_time_ms=guesser_think_time_ms,
    )


def _public_run(
    run: LoadedRun,
    *,
    reasons: tuple[str, ...],
    failure_penalty_offset: int,
    b20_target_questions: int,
) -> PublicRun:
    penalty = Decimal(run.manifest.definition.game_policy.max_questions + failure_penalty_offset)
    completed_trial_count = sum(
        isinstance(trial, CompletedTrialSummary)
        for subject in run.summary.subjects
        for trial in subject.trials
    )
    if len(run.episodes) != completed_trial_count:
        raise ValueError("publication requires one validated detail artifact per completed trial")
    episodes = {
        (episode.identity.target_id, episode.identity.trial_id): episode
        for episode in run.episodes
    }
    subjects = tuple(
        _subject(
            subject,
            failure_penalty=penalty,
            b20_target_questions=b20_target_questions,
            episodes=episodes,
        )
        for subject in run.summary.subjects
    )
    subject_scores = tuple(
        subject.subject_score for subject in subjects if subject.subject_score is not None
    )
    descriptive_score = (
        sum(subject_scores, start=Decimal(0)) / Decimal(len(subject_scores))
        if len(subject_scores) == len(subjects)
        and subject_scores
        else None
    )
    descriptive_b20_score = _b20_score(
        descriptive_score,
        failure_penalty=penalty,
        target_questions=b20_target_questions,
    )
    counts = run.summary.summary.counts
    return PublicRun(
        execution_id=run.summary.execution_id,
        model_id=run.summary.model.model_id,
        model_name=run.summary.model.display_name,
        benchmark_id=run.summary.benchmark_id,
        benchmark_name=run.summary.display_name,
        classification="official" if not reasons else "lab",
        reason_codes=reasons,
        completed_at=run.state.updated_at,
        created_at=run.manifest.created_at,
        git_commit=run.manifest.git_commit,
        benchmark_mode=run.manifest.definition.game_policy.benchmark_mode,
        target_ids=run.manifest.request.target_ids,
        iterations=run.manifest.definition.iterations,
        base_seed=run.manifest.request.base_seed,
        max_questions=run.manifest.definition.game_policy.max_questions,
        success_rate=run.summary.summary.success_rate,
        descriptive_score=descriptive_score,
        descriptive_b20_score=descriptive_b20_score,
        penalized_score=descriptive_score if not reasons else None,
        b20_score=descriptive_b20_score if not reasons else None,
        total_cost_usd=_total_cost(run),
        successful=counts.successful,
        model_failed=counts.model_failed,
        infrastructure_failed=counts.infrastructure_failed,
        terminal_trials=counts.terminal,
        contract=_contract(run.summary.summary.contract),
        totals=_public_run_totals(run),
        subjects=subjects,
    )


def _rank(rows: tuple[LeaderboardRow, ...]) -> tuple[LeaderboardRow, ...]:
    evaluated = sorted(
        (row for row in rows if row.penalized_score is not None),
        key=lambda row: (
            row.penalized_score,
            row.model.display_name.casefold(),
            row.model.model_id,
        ),
    )
    ranked_by_id: dict[str, LeaderboardRow] = {}
    prior_score: Decimal | None = None
    prior_rank = 0
    for index, row in enumerate(evaluated, start=1):
        rank = prior_rank if prior_score == row.penalized_score else index
        ranked_by_id[row.model.model_id] = row.model_copy(update={"rank": rank})
        prior_rank = rank
        prior_score = row.penalized_score
    awaiting = sorted(
        (row for row in rows if row.penalized_score is None),
        key=lambda row: (row.model.display_name.casefold(), row.model.model_id),
    )
    return tuple(ranked_by_id[row.model.model_id] for row in evaluated) + tuple(awaiting)


def _select_latest_qualified_runs(
    runs: tuple[PublicRun, ...],
    model_ids: tuple[str, ...],
) -> tuple[PublicRun, ...]:
    qualified_by_model: dict[str, list[PublicRun]] = defaultdict(list)
    for run in runs:
        if run.classification == "official":
            qualified_by_model[run.model_id].append(run)

    selected: list[PublicRun] = []
    for model_id in model_ids:
        matches = sorted(
            qualified_by_model.get(model_id, ()),
            key=lambda run: (run.completed_at, run.execution_id),
            reverse=True,
        )
        if len(matches) >= 2 and matches[0].completed_at == matches[1].completed_at:
            raise ValueError(f"official run timestamp tie for {model_id}")
        if matches:
            selected.append(matches[0])
    return tuple(selected)


def compile_publication(
    *,
    runs: tuple[LoadedRun, ...],
    config: PublicationConfig,
    subject_catalog: SubjectCatalog,
    subject_catalog_hash: str,
) -> PublishedDataset:
    cohort = config.active_cohort
    missing_targets = tuple(
        target_id for target_id in cohort.target_ids if target_id not in subject_catalog.subjects
    )
    if missing_targets:
        raise ValueError(f"active cohort has unknown targets: {missing_targets}")

    loaded_by_identity = {
        (run.summary.model.model_id, run.summary.execution_id): run
        for run in runs
    }
    projected_runs: list[PublicRun] = []
    for loaded_run in runs:
        reasons = _reason_codes(
            loaded_run,
            cohort,
        )
        projected_runs.append(
            _public_run(
                loaded_run,
                reasons=reasons,
                failure_penalty_offset=config.score.failure_penalty_offset,
                b20_target_questions=config.score.b20.target_questions,
            )
        )

    selected = _select_latest_qualified_runs(
        tuple(projected_runs),
        cohort.model_ids,
    )
    selected_by_model = {run.model_id: run for run in selected}
    public_models_by_id = {
        model_id: _public_model(
            loaded_by_identity[(model_id, selected_run.execution_id)]
        )
        for model_id, selected_run in selected_by_model.items()
    }
    public_models = tuple(
        public_models_by_id[model_id]
        for model_id in cohort.model_ids
        if model_id in selected_by_model
    )
    rows: list[LeaderboardRow] = []
    for model_id in cohort.model_ids:
        selected_run = selected_by_model.get(model_id)
        if selected_run is None:
            continue
        rows.append(
            LeaderboardRow(
                rank=None,
                model=public_models_by_id[model_id],
                status="evaluated",
                execution_id=selected_run.execution_id,
                completed_at=selected_run.completed_at,
                penalized_score=selected_run.penalized_score,
                b20_score=selected_run.b20_score,
                success_rate=selected_run.success_rate,
                total_cost_usd=selected_run.total_cost_usd,
                successful=selected_run.successful,
                terminal_trials=selected_run.terminal_trials,
                contract=_contract(selected_run.contract),
            )
        )
    leaderboard = _rank(tuple(rows))
    evaluated = tuple(row for row in leaderboard if row.penalized_score is not None)
    winner = None
    if evaluated:
        evaluated_scores = tuple(
            row.penalized_score
            for row in evaluated
            if row.penalized_score is not None
        )
        winning_score = min(evaluated_scores)
        winners = tuple(row for row in evaluated if row.penalized_score == winning_score)
        winner = Winner(
            model_ids=tuple(row.model.model_id for row in winners),
            display_names=tuple(row.model.display_name for row in winners),
            penalized_score=winning_score,
            b20_score=next(
                row.b20_score
                for row in winners
                if row.b20_score is not None
            ),
            joint=len(winners) > 1,
        )

    selected_dates = tuple(run.completed_at for run in selected)
    return PublishedDataset(
        site=config.site,
        score_policy=config.score,
        active_cohort=cohort,
        provenance=DatasetProvenance(
            source_run_count=len(projected_runs),
            official_run_count=len(selected),
            lab_run_count=0,
            latest_completed_at=max(selected_dates) if selected_dates else None,
            subject_catalog_hash=subject_catalog_hash,
        ),
        winner=winner,
        leaderboard=leaderboard,
        models=public_models,
        official_runs=tuple(
            sorted(selected, key=lambda run: (run.completed_at, run.execution_id), reverse=True)
        ),
        lab_runs=(),
    )
