# Oracle evidence-only audit

This snapshot reviews every persisted Oracle `ASK` call in the active `runs/`
directory as of the two timestamps recorded in `audit-manifest.json`.

The review corpus contains only:

- opaque execution, model, target, trial, turn, and call locators;
- the Guesser's question;
- the Oracle's `YES`, `NO`, or `UNKNOWN` token; and
- the Oracle's own recorded evidence URLs and excerpts.

It excludes subject snapshots, canonical identities, Guesser conversations,
prompts, explanations, provider metadata, metrics, and all external web content.
No source URL was opened during the review.

## Decision rule

`confirmed_wrong` means the recorded evidence directly entails the opposite of
the Oracle answer. Missing or weak support is not enough to label an answer
wrong.

`ambiguous_not_counted` identifies a plausible error for which the wording
admits another reading. `evidence_gap_not_counted` identifies an answer whose
recorded evidence does not resolve the question, but also does not prove the
answer false.

## Result

- 648 Oracle calls reviewed
- 994 evidence items reviewed
- 4 calls confirmed wrong
- 2 additional repeated calls ambiguous and likely wrong under the ordinary
  historical reading
- 1 notable evidence gap, not counted as a wrong answer

The four confirmed errors comprise three distinct failure patterns: the same
`born before 1800` comparison was inverted in two calls, a `born before 1300`
comparison was inverted once, and a disjunctive `science fiction or fantasy`
question was answered `NO` despite evidence explicitly saying the person was
best known for fantasy (as well as horror).

See `findings.jsonl` for the evidence-only judgments and
`evidence-only-calls.jsonl` for the complete controlled corpus.
