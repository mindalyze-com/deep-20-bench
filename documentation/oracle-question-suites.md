# Direct Oracle question suites

`deep20 benchmark test-oracle` accepts a question directly or a saved suite. It calls the
production Oracle, Reviewer, and Judge service with no Guesser, Guess Validator, game,
startup canary, or historical ASK answer cache. Oracle UNKNOWN remains final; every
other answer receives blind review, and exact-token disagreement invokes the Judge.

## One question or repeated diagnostic

From the repository root:

```bash
uv run deep20 benchmark test-oracle \
  --target-id T-0009 \
  --question 'Is it a part of, or a substance produced by, a living organism?' \
  --repeat 3 --run-id spider-web-substance-001 --live --verbose
```

`--repeat` defaults to one and applies per selected question. It is independent of benchmark
iteration defaults. Paid execution requires `--live`. Without it, the command only previews the selection and
loads no credentials. `--dry-run` explicitly selects that same offline behavior. Every live
repetition makes fresh calls. The preview reports the number of questions, not the number of
role calls: each question can require research, review, Judge, and bounded format recovery.

Configuration defaults to the current B-0003 Oracle entry in `config/benchmarks.yaml`, including
the five-answer policy and role routes. `--benchmark-id` selects another current entry;
`--oracle-config FILE` selects a complete Oracle configuration instead. `--subjects-path` can
select a catalog for target IDs. The existing `deep20 oracle ask` remains available for its
single-call standalone workflow and its own default configuration.

## Collect cases in YAML or JSON

Store local suites under `private/reviews/`. For example:

```yaml
schema_version: 1
name: Spider web scope checks
cases:
  - id: organism-part-or-substance
    target_id: T-0009
    question: Is it a part of, or a substance produced by, a living organism?
    expected_answers: [NO]
    notes: The target is the web structure, not the silk material.
  - id: animal-built
    target_id: T-0009
    question: Is it a structure built or assembled by an animal?
    expected_answers: [YES]
```

Each case needs a unique `id`, a `question`, and exactly one of `target_id` or a complete
`subject` snapshot with the ordinary Oracle Subject fields. Inline subjects allow cases
outside the current catalog. They identify the subject; do not put expected answers or test
instructions in their descriptions.

`expected_answers` and `notes` are optional and remain report-only. An empty expectation is
unscored. Multiple allowed tokens express an explicitly chosen acceptance set, not probability.
Expected tokens are manual test assertions, not generated gold labels. Case IDs, repetition
numbers, suite names, expectations, notes, and prior outcomes never enter model messages.

Run one collected case repeatedly:

```bash
uv run deep20 benchmark test-oracle \
  --suite private/reviews/oracle-suites/spider-web-problematic.yml \
  --cases organism-part-or-substance --repeat 3 \
  --run-id spider-web-focused-001 --live --verbose
```

Repeat `--cases` to select several IDs; omit it to run every case. `--save-suite PATH` saves
the selected cases with resolved subject snapshots and refuses to overwrite an existing file.
Combine it with `--dry-run` to freeze a suite without calls. Saved snapshots prevent subsequent
catalog changes from silently changing a regression's subject identity.

## Export historical questions as a regression

The replay command can export any selection without credentials or model calls:

```bash
uv run deep20 benchmark replay-oracle \
  runs/M-0022/BX-20260907-B-0003-experimental-M0022-002 \
  --targets T-0009 --run-id spider-web-regression \
  --export-suite private/reviews/oracle-suites/spider-web-regression.yml
```

This preserves all 43 recorded Spider web ASK occurrences, including repeated wording, with
the original subject snapshots. GUESS actions and invalid actions are excluded. Historical
answers are not copied into expectations. Existing replay filters can select only problematic
turns. Remove `--targets` to export all recorded subjects.

Run an explicitly requested live regression through
`test-oracle --suite ... --run-id ... --live --verbose`. These saved collections are not
registered with pytest, CI, or normal offline regression tests. Long macOS runs
should use the detached screen/caffeinate pattern documented in [Oracle replay](oracle-question-replay.md).

## Results and continuation

Results stay in `private/reviews/oracle-suites/<run-id>/result.yml`, an integrity-checked atomic
checkpoint. `--verbose` additionally writes `review.md` and private raw role audits. The review
shows each role's answer and supporting statement, final answer, evidence, expected-answer
match, prompt versions/hashes, cost, latency, cache tokens, and which cases vary across repeats.
Stable answers are not necessarily correct; matching an expectation is not an independent
accuracy measurement. Known successful-call cost may exclude failed calls or missing telemetry.

Every call is marked in flight before it starts. `--live --resume` requires identical inputs,
repetition count, selected cases, subject snapshots, prompts, and configuration. Completed
calls are skipped. An interrupted call is marked `suite_interrupted` and is not silently
re-billed. Use a new ID to deliberately repeat it. Changing expectations or notes also requires
a new run ID so the report's evaluation criteria remain fixed.

`--max-consecutive-failures` defaults to one. A required role failure stops the suite; it never
uses the provisional Oracle answer as a fallback. Exit codes are 0 for a successful preview
or completed suite with no failures/mismatches, 1 for incomplete runs, failures or expectation
mismatches, and 2 for invalid setup. Unscored outcomes and token variation alone do not fail a run.

The suite runner changes no provider prompts, prefixes, sessions, tool budgets, or response
schemas. Existing automatic prompt-prefix caching remains enabled. It adds no padding or
response caching, and records actual cache tokens and costs without assuming savings. All
repeated calls retain the production blind factual projections.

## Offline by default

Normal `uv run pytest` excludes paid `integration` tests and blocks real network connections
in ordinary tests. Even explicitly selecting `-m integration` does not enable paid calls
without `--run-paid-tests` and the existing live-test environment opt-ins. Only run those
commands on explicit user demand. Credentials alone never authorize paid calls.
