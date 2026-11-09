from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from deep20_publication.comparison import build_comparison
from deep20_publication.models import (
    PublicationComparisonDocument,
    PublicationDocument,
    PublicSubjectSummary,
    PublicTrialSummary,
    PublishedDataset,
)
from deep20_publication.split import split_publication

REPOSITORY = Path(__file__).resolve().parents[4]


@pytest.mark.parametrize("edition", ("1.0", "1.1"))
def test_comparison_preserves_every_source_value_and_excludes_transcripts(edition: str) -> None:
    dataset = PublishedDataset.model_validate_json(
        (REPOSITORY / "docs/data/editions" / edition / "deep20bench-v10.json").read_text()
    )
    bundle = split_publication(dataset)
    comparison = build_comparison(bundle)
    assert comparison.edition_id == edition
    assert comparison.iterations == dataset.active_cohort.iterations
    assert comparison.max_questions == dataset.active_cohort.max_questions
    assert comparison.target_ids == dataset.active_cohort.target_ids
    assert len(comparison.models) == len(dataset.official_runs)
    for model in comparison.models:
        run = next(run for run in bundle.runs if run.run.execution_id == model.result.execution_id)
        assert model.result == next(row for row in (dataset.run_results or dataset.leaderboard)
                                    if row.execution_id == run.run.execution_id)
        assert model.totals == run.run.totals
        for subject, summary in zip(model.subjects, run.subjects, strict=True):
            for field in PublicSubjectSummary.model_fields:
                assert getattr(subject, field) == getattr(summary, field)
            source = next(item for item in bundle.subjects
                          if item.execution_id == run.run.execution_id
                          and item.target_id == subject.target_id)
            for result, original in zip(subject.rounds, sorted(
                source.trials, key=lambda item: item.trial_number,
            ), strict=True):
                for field in PublicTrialSummary.model_fields:
                    assert getattr(result, field) == getattr(original, field)
    serialized = comparison.model_dump_json()
    assert TypeAdapter(PublicationDocument).validate_json(serialized) == comparison
    for field in ('"turns"', '"evidence"', '"guesser_disclosure"', '"provider_trace"',
                  '"call_id"', '"system_message"', '"begin_message"'):
        assert field not in serialized


def test_comparison_rejects_incomplete_and_duplicate_results() -> None:
    dataset = PublishedDataset.model_validate_json(
        (REPOSITORY / "docs/data/editions/1.0/deep20bench-v10.json").read_text()
    )
    comparison = build_comparison(split_publication(dataset))
    model = comparison.models[0]
    with pytest.raises(ValidationError, match="unique"):
        PublicationComparisonDocument.model_validate(comparison.model_copy(
            update={"models": (model, model)},
        ).model_dump())
    subject = model.subjects[0].model_copy(update={"rounds": model.subjects[0].rounds[:-1]})
    incomplete = model.model_copy(update={"subjects": (subject, *model.subjects[1:])})
    with pytest.raises(ValidationError, match="rounds"):
        PublicationComparisonDocument.model_validate(comparison.model_copy(
            update={"models": (incomplete,)},
        ).model_dump())


def test_dated_runs_of_same_model_keep_separate_scores_and_transcripts() -> None:
    """Two dates remain two observations, with one current leaderboard result."""
    from datetime import timedelta
    from deep20_publication.models import LeaderboardRow

    dataset = PublishedDataset.model_validate_json(
        (REPOSITORY / 'docs/data/editions/1.1/deep20bench-v10.json').read_text()
    )
    current = dataset.official_runs[0]
    row = next(item for item in dataset.leaderboard if item.execution_id == current.execution_id)
    earlier = current.model_copy(update={
        'execution_id': 'BX-dated-comparison-earlier',
        'completed_at': current.completed_at - timedelta(days=30),
    })
    old_row = LeaderboardRow.model_validate({
        **row.model_dump(), 'execution_id': earlier.execution_id,
        'completed_at': earlier.completed_at, 'is_latest': False,
        'rank': None, 'efficiency_rank': None, 'ideal_distance_rank': None,
        'product_efficiency_rank': None, 'ideal_distance_score': None,
        'normalized_question_score': None, 'normalized_guesser_cost': None,
    })
    selected = dataset.model_copy(update={
        'official_runs': (current, earlier), 'leaderboard': (row,),
        'run_results': (row, old_row),
    })
    bundle = split_publication(selected)
    comparison = build_comparison(bundle)
    assert comparison.schema_version == 2
    assert [item.result.execution_id for item in comparison.models] == [current.execution_id, earlier.execution_id]
    assert len({item.result.model.model_id for item in comparison.models}) == 1
    assert comparison.models[0].result.question_score == row.question_score
    assert comparison.models[1].result.question_score == old_row.question_score
    assert comparison.models[1].result.rank is None
    assert comparison.models[1].result.ideal_distance_score is None
    assert {item.execution_id for item in bundle.episodes} == {current.execution_id, earlier.execution_id}


def test_earlier_run_cannot_borrow_current_rank() -> None:
    from deep20_publication.models import LeaderboardRow

    dataset = PublishedDataset.model_validate_json(
        (REPOSITORY / 'docs/data/editions/1.1/deep20bench-v10.json').read_text()
    )
    with pytest.raises(ValidationError, match='earlier runs'):
        LeaderboardRow.model_validate({**dataset.leaderboard[0].model_dump(), 'is_latest': False})
