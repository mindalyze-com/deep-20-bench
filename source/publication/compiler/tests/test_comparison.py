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
        assert model.result == next(row for row in dataset.leaderboard
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
