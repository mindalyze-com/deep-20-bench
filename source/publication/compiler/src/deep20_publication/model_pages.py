"""Stable per-model summaries derived from the already compiled edition documents.

A model page keeps one URL per model and edition while the selected run behind it changes.
Every value is a projection of public run, subject, episode, and leaderboard documents;
observations only report counts and ranks for the tested subjects and cite their rounds.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from decimal import Decimal

from pydantic import Field

from .models import (
    EditionId,
    FrozenModel,
    LeaderboardRow,
    ModelSlugPin,
    PublicationDataBundle,
    PublicationModelDocument,
    PublicationModelIndexDocument,
    PublicModel,
    PublicModelEditionLink,
    PublicModelIndexEntry,
    PublicModelObservation,
    PublicModelRound,
    PublicModelRoundReference,
    PublicModelSubjectResult,
    PublicSupersededRun,
)

_SUBJECT_OBSERVATION_LIMIT = 2


class EditionModelPages(FrozenModel):
    """Model pages of one edition; `slug_aliases` maps retired slugs to current slugs."""

    edition_id: EditionId
    index: PublicationModelIndexDocument
    models: tuple[PublicationModelDocument, ...]
    slug_aliases: dict[str, str] = Field(default_factory=dict)


def model_slug(display_name: str) -> str:
    """Return the URL slug for a display name, e.g. `GPT-6 Astra (high)` -> `gpt-6-astra-high`."""
    ascii_name = (
        unicodedata.normalize("NFKD", display_name).encode("ascii", "ignore").decode("ascii")
    )
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    if not slug:
        raise ValueError(f"model display name has no URL characters: {display_name!r}")
    return slug


def _edition_slugs(
    models: tuple[PublicModel, ...],
    pins: dict[str, ModelSlugPin],
    edition_id: str,
) -> tuple[dict[str, str], dict[str, str]]:
    slugs = {
        model.model_id: (
            pin.slug
            if (pin := pins.get(model.model_id)) is not None and pin.slug is not None
            else model_slug(model.display_name)
        )
        for model in models
    }
    owners: dict[str, list[str]] = defaultdict(list)
    for model_id, slug in slugs.items():
        owners[slug].append(model_id)
    duplicates = sorted(slug for slug, model_ids in owners.items() if len(model_ids) > 1)
    if duplicates:
        raise ValueError(
            f"edition {edition_id} model slugs are not unique: {', '.join(duplicates)}; "
            "pin distinct slugs in config/publication.yml"
        )
    aliases: dict[str, str] = {}
    for model_id, slug in slugs.items():
        pin = pins.get(model_id)
        for previous in () if pin is None else pin.previous_slugs:
            if previous in owners or previous in aliases:
                raise ValueError(
                    f"edition {edition_id} previous model slug {previous} is still in use"
                )
            aliases[previous] = slug
    return slugs, aliases


def _competition_rank(value: Decimal, values: tuple[Decimal, ...]) -> int:
    return 1 + sum(other < value for other in values)


def _subject_results(
    bundle: PublicationDataBundle,
    execution_id: str,
    subject_averages: dict[str, tuple[Decimal, ...]],
) -> tuple[PublicModelSubjectResult, ...]:
    run_document = next(item for item in bundle.runs if item.run.execution_id == execution_id)
    subject_documents = {
        item.target_id: item for item in bundle.subjects if item.execution_id == execution_id
    }
    episodes = {
        (item.target_id, item.trial_id): item.episode
        for item in bundle.episodes
        if item.execution_id == execution_id
    }
    results: list[PublicModelSubjectResult] = []
    for subject in run_document.subjects:
        rounds: list[PublicModelRound] = []
        for trial in subject_documents[subject.target_id].trials:
            episode = episodes.get((subject.target_id, trial.trial_id))
            rounds.append(
                PublicModelRound(
                    target_id=subject.target_id,
                    trial_id=trial.trial_id,
                    trial_number=trial.trial_number,
                    status=trial.status,
                    terminal_reason=None if episode is None else episode.terminal_reason,
                    counted_questions=trial.counted_questions,
                    penalized_questions=trial.penalized_questions,
                    rejected_guess_count=0 if episode is None else episode.rejected_guess_count,
                    format_errors=0 if trial.contract is None else trial.contract.violations,
                )
            )
        averages = subject_averages.get(subject.target_id, ())
        results.append(
            PublicModelSubjectResult(
                target_id=subject.target_id,
                display_name=subject.display_name,
                entity_type=subject.entity_type,
                average_questions=subject.average_questions,
                successful=subject.successful,
                model_failed=subject.model_failed,
                infrastructure_failed=subject.infrastructure_failed,
                rank=(
                    _competition_rank(subject.average_questions, averages)
                    if subject.average_questions is not None
                    else None
                ),
                ranked_models=len(averages),
                rounds=tuple(sorted(rounds, key=lambda item: item.trial_number)),
            )
        )
    return tuple(results)


def _reference(item: PublicModelRound) -> PublicModelRoundReference:
    return PublicModelRoundReference(target_id=item.target_id, trial_id=item.trial_id)


def _scored_rounds(subject: PublicModelSubjectResult) -> tuple[PublicModelRound, ...]:
    return tuple(item for item in subject.rounds if item.status != "infrastructure_failure")


def _observations(
    subjects: tuple[PublicModelSubjectResult, ...],
) -> tuple[PublicModelObservation, ...]:
    """Select count- and rank-based statements in a fixed order; ties keep subject order."""
    order = {subject.target_id: index for index, subject in enumerate(subjects)}
    ranked = sorted(
        (subject for subject in subjects if subject.rank is not None and _scored_rounds(subject)),
        key=lambda subject: (subject.rank, subject.average_questions, order[subject.target_id]),
    )
    observations: list[PublicModelObservation] = []
    strongest = ranked[:_SUBJECT_OBSERVATION_LIMIT]
    for subject in strongest:
        observations.append(PublicModelObservation(
            kind="strongest_subject", target_id=subject.target_id,
            value=subject.average_questions, count=subject.rank,
            rounds=tuple(_reference(item) for item in _scored_rounds(subject)),
        ))
    hardest = [subject for subject in reversed(ranked) if subject not in strongest]
    for subject in hardest[:_SUBJECT_OBSERVATION_LIMIT]:
        observations.append(PublicModelObservation(
            kind="hardest_subject", target_id=subject.target_id,
            value=subject.average_questions, count=subject.rank,
            rounds=tuple(_reference(item) for item in _scored_rounds(subject)),
        ))

    rounds = tuple(item for subject in subjects for item in _scored_rounds(subject))
    solved = tuple(item for item in rounds if item.status == "success")
    if solved:
        fewest = min(solved, key=lambda item: item.counted_questions)
        most = max(solved, key=lambda item: item.counted_questions)
        observations.append(PublicModelObservation(
            kind="fewest_questions", target_id=fewest.target_id,
            count=fewest.counted_questions, rounds=(_reference(fewest),),
        ))
        if most.counted_questions != fewest.counted_questions:
            observations.append(PublicModelObservation(
                kind="most_questions", target_id=most.target_id,
                count=most.counted_questions, rounds=(_reference(most),),
            ))

    spreads = []
    for subject in subjects:
        values = tuple(
            item.penalized_questions
            for item in _scored_rounds(subject)
            if item.penalized_questions is not None
        )
        if len(values) >= 2:
            spreads.append((max(values) - min(values), subject))
    if spreads:
        spread, subject = max(spreads, key=lambda entry: (entry[0], -order[entry[1].target_id]))
        if spread > 0:
            observations.append(PublicModelObservation(
                kind="uneven_subject", target_id=subject.target_id, value=spread,
                rounds=tuple(_reference(item) for item in _scored_rounds(subject)),
            ))

    wrong_guesses = sum(item.rejected_guess_count for item in rounds)
    if wrong_guesses:
        worst = max(rounds, key=lambda item: item.rejected_guess_count)
        observations.append(PublicModelObservation(
            kind="wrong_guesses", target_id=worst.target_id, count=wrong_guesses,
            value=Decimal(worst.rejected_guess_count), rounds=(_reference(worst),),
        ))

    for item in rounds:
        if item.status == "model_failure":
            observations.append(PublicModelObservation(
                kind="model_failure", target_id=item.target_id,
                value=item.penalized_questions, count=item.counted_questions,
                rounds=(_reference(item),),
            ))

    with_format_errors = tuple(item for item in rounds if item.format_errors)
    if with_format_errors:
        observations.append(PublicModelObservation(
            kind="format_errors",
            count=sum(item.format_errors for item in with_format_errors),
            rounds=tuple(_reference(item) for item in with_format_errors),
        ))
    return tuple(observations)


def _published_rows(bundle: PublicationDataBundle) -> tuple[LeaderboardRow, ...]:
    """Leaderboard rows whose selected run is published in this bundle."""
    official = {reference.execution_id for reference in bundle.manifest.official_runs}
    return tuple(row for row in bundle.leaderboard.leaderboard if row.execution_id in official)


def build_model_pages(
    bundles: tuple[PublicationDataBundle, ...],
    pins: tuple[ModelSlugPin, ...],
    superseded: dict[str, dict[str, tuple[PublicSupersededRun, ...]]],
) -> tuple[EditionModelPages, ...]:
    """Build every edition's model index and model documents.

    `superseded` maps edition ID to model ID to the replaced qualifying runs.
    """
    pins_by_model = {pin.model_id: pin for pin in pins}
    published_models = {row.model.model_id for bundle in bundles for row in _published_rows(bundle)}
    unknown = sorted(set(pins_by_model) - published_models)
    if unknown:
        raise ValueError(f"model slug pins name unpublished models: {', '.join(unknown)}")

    slugs_by_edition: dict[str, dict[str, str]] = {}
    aliases_by_edition: dict[str, dict[str, str]] = {}
    for bundle in bundles:
        rows = _published_rows(bundle)
        slugs, aliases = _edition_slugs(
            tuple(row.model for row in rows), pins_by_model, bundle.manifest.edition_id,
        )
        slugs_by_edition[bundle.manifest.edition_id] = slugs
        aliases_by_edition[bundle.manifest.edition_id] = aliases

    pages: list[EditionModelPages] = []
    for bundle in bundles:
        edition_id = bundle.manifest.edition_id
        cohort = bundle.manifest.active_cohort
        slugs = slugs_by_edition[edition_id]
        rows = _published_rows(bundle)
        ranked_models = sum(row.rank is not None for row in rows)
        official = {reference.execution_id for reference in bundle.manifest.official_runs}
        subject_averages: dict[str, list[Decimal]] = defaultdict(list)
        for run_document in bundle.runs:
            if run_document.run.execution_id not in official:
                continue
            for subject in run_document.subjects:
                if subject.average_questions is not None:
                    subject_averages[subject.target_id].append(subject.average_questions)
        averages = {target: tuple(values) for target, values in subject_averages.items()}

        documents: list[PublicationModelDocument] = []
        entries: list[PublicModelIndexEntry] = []
        for row in rows:
            execution_id = row.execution_id
            if execution_id is None:
                continue
            model_id = row.model.model_id
            subjects = _subject_results(bundle, execution_id, averages)
            other_editions = tuple(
                PublicModelEditionLink(
                    edition_id=other.manifest.edition_id,
                    edition_label=other.manifest.active_cohort.edition_label,
                    slug=slugs_by_edition[other.manifest.edition_id][model_id],
                    execution_id=other_execution_id,
                    rank=other_row.rank,
                    ranked_models=sum(
                        item.rank is not None for item in other.leaderboard.leaderboard
                    ),
                    question_score=other_row.question_score,
                )
                for other in bundles
                if other.manifest.edition_id != edition_id
                for other_row in _published_rows(other)
                if other_row.model.model_id == model_id
                and (other_execution_id := other_row.execution_id) is not None
            )
            documents.append(PublicationModelDocument(
                edition_id=edition_id,
                slug=slugs[model_id],
                ranked_models=max(ranked_models, 1),
                iterations=cohort.iterations,
                max_questions=cohort.max_questions,
                result=row,
                subjects=subjects,
                observations=_observations(subjects),
                other_editions=other_editions,
                superseded_runs=superseded.get(edition_id, {}).get(model_id, ()),
            ))
            entries.append(PublicModelIndexEntry(
                slug=slugs[model_id],
                model=row.model,
                execution_id=execution_id,
                rank=row.rank,
                question_score=row.question_score,
                success_rate=row.success_rate,
                successful=row.successful,
                terminal_trials=row.terminal_trials,
            ))
        index = PublicationModelIndexDocument(
            edition_id=edition_id,
            models=tuple(sorted(
                entries,
                key=lambda entry: (entry.model.display_name.casefold(), entry.model.model_id),
            )),
        )
        pages.append(EditionModelPages(
            edition_id=edition_id,
            index=index,
            models=tuple(documents),
            slug_aliases=aliases_by_edition[edition_id],
        ))
    return tuple(pages)
