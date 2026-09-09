# Oracle question replay

For direct questions, repeated diagnostic cases, and editable regression suites, use
[Direct Oracle question suites](oracle-question-suites.md).

`deep20 benchmark replay-oracle --live` sends the exact recorded ASK questions from a completed
benchmark through the current Oracle, Reviewer, and Judge. It creates no Guesser or Guess
Validator provider and runs no game or startup canary. The Oracle service owns research,
review, disagreement routing, retries, and local response validation exactly as in production.

Without `--live`, the command only previews its selection. Credentials, exported suites,
and normal regression commands never enable paid calls implicitly.

The last completed five-answer GPT-6 Astra run at implementation time is
`BX-20260907-B-0003-experimental-M0022-002`: 378 ASK occurrences in 30 trials across ten
subjects. The earlier execution ending in `001` has no complete benchmark result. The source
argument is explicit so adding another benchmark does not silently change a replay.

From the repository root, preview the full selection without credentials or paid calls:

```bash
uv run deep20 benchmark replay-oracle \
  runs/M-0022/BX-20260907-B-0003-experimental-M0022-002 \
  --run-id astra-oracle-replay-001 --dry-run
```

For a small live check, use a separate ID and a limit:

```bash
uv run deep20 benchmark replay-oracle \
  runs/M-0022/BX-20260907-B-0003-experimental-M0022-002 \
  --run-id astra-oracle-sample-001 --limit 5 --live --verbose
```

To replay all 378 questions, omit `--limit`. Run long macOS replays in a detached screen:

```bash
mkdir -p private/reviews/oracle-replay-launches
screen -dmS astra-oracle-replay /bin/zsh -c \
  'nohup /usr/bin/caffeinate -i uv run deep20 benchmark replay-oracle runs/M-0022/BX-20260907-B-0003-experimental-M0022-002 --run-id astra-oracle-replay-001 --live --verbose </dev/null >>private/reviews/oracle-replay-launches/astra-oracle-replay-001.log 2>&1 & wait'
```

Check `screen -ls`, the caffeinate and replay processes, and the log's first question result.
The initial `result.yml` contains the frozen plan. No live process means the replay is no
longer running. This command intentionally has no Guesser canary or Guesser call.

## Selection and configuration

The source can be a benchmark directory or its complete schema-v3 `result.yml`. Its original
integrity hash and typed model are checked before provider construction. The harness reads
the saved subject snapshots, including subjects that are now inactive or changed in the
catalog. It retains each ASK occurrence in source subject/trial/turn order. Repeated questions
are replayed separately. GUESS actions, contract violations, and trials without a retained
episode transcript are excluded; the preview reports the latter count. It does not reconstruct
missing actions from raw error output or Guesser text.

Optional filters can be combined:

```bash
uv run deep20 benchmark replay-oracle \
  runs/M-0022/BX-20260907-B-0003-experimental-M0022-002 \
  --run-id astra-selected-001 \
  --targets T-0001 --trials 2 --turns 3 --turns 5 --live --verbose
```

`--targets`, `--trials`, and `--turns` are repeatable. Turn numbers refer to the original
game transcript, not the index among ASK actions. `--limit N` applies after filtering.
Empty selections and filters with no matching ASK positions fail before paid calls.
The replay uses the source's actual occurrences, with no new iteration schedule.

By default, configuration comes from the **current** entry for the source benchmark ID in
`config/benchmarks.yaml`. B-0003 therefore selects the current five-answer policy and all three
current role routes. It does not silently reuse the source run's old Oracle settings or the
standalone three-answer `config/oracle.yaml`. `--benchmarks-path` selects another current
catalog. Alternatively, `--oracle-config FILE` selects one complete Oracle YAML configuration,
including Reviewer and Judge. A five-answer source requires a five-answer Oracle profile.
The preview prints the effective profile, policy, and complete factual-contract hash.

## Review artifacts and continuation

All output stays in the ignored directory
`private/reviews/oracle-replay/<run-id>/`. `result.yml` is a signed, atomically replaced
checkpoint containing the source identity/hash, exact selected questions, historical answers,
historical evidence and role decisions, old/new Oracle configurations, current contract hash,
and new results. New results include final and provisional answers, Reviewer/Judge decisions
and supporting statements, evidence, per-role routes and prompt versions/hashes, cache tokens,
latency, and reported costs. Full prompts and raw provider exchanges are excluded from this
checkpoint.

`--verbose` also writes `review.md`, with an answer comparison table and question-by-question
evidence and decision details, plus the standard credential-free Oracle audit under
`audit/<run-id>/`. The shared `RunArtifactPolicy` gates these auxiliary files. Files used for
review are local and never publication inputs. The Markdown is regenerated as progress is
saved; copy it before adding manual notes, or annotate a separate file.

Every call is marked in flight before it starts and checkpointed when it finishes. Reusing
an existing ID requires `--resume` with the same source, filters, configuration, and prompt
contract. For example:

```bash
uv run deep20 benchmark replay-oracle \
  runs/M-0022/BX-20260907-B-0003-experimental-M0022-002 \
  --run-id astra-oracle-replay-001 --live --verbose --resume
```

Completed calls, including failures, are skipped. An interrupted in-flight call is marked
`replay_interrupted` and is not silently repeated, since it may already have incurred cost.
Use a new ID and filters to retry a failed question or evaluate another prompt revision.
`--max-consecutive-failures` defaults to 5; reaching it stops new calls and leaves a resumable
checkpoint. Persistence failures stop immediately. A lock prevents concurrent writers.
Exit status is 0 for a successful preview or fully successful replay, 1 for recorded failures
or a circuit-breaker stop, and 2 for setup, validation, or unexpected execution errors.

Historical answers are comparison data, not ground truth. A changed answer is not necessarily
better, and an unchanged answer is not necessarily correct. Review scope, supporting facts,
evidence, and uncertainty for both. These are fixed historical questions; the harness cannot
estimate how a Guesser would adapt to the new answers or produce a new game score. Retrieval,
source changes, and model variation may affect the result as well as prompt changes.

## Isolation and caching

Each Oracle request contains only the replay run ID, recorded trusted subject, and current
question. Old answers, evidence, decisions, other questions, and source run metadata never
enter provider requests. The existing service supplies only its permitted blind projection
to Reviewer and Judge and controls any question metadata. The replay creates no Guesser
session, request, provider, or message history.

Application ASK reuse is disabled by construction: this harness calls the Oracle service
directly, without either benchmark cache. Every selected occurrence generates a fresh answer.
Automatic provider prefix caching retains the current service's separate role/version/subject
namespaces and controls. No padding, shared role session, or response cache is added. The
current prompt/schema/configuration contract is frozen in the checkpoint and checked on resume.
Per-role actual cache reads/writes, token usage, latency, and billed cost remain the evidence
for reuse; this harness makes no savings claim. Failed/interrupted calls can have additional
cost absent from the successful-call subtotal; verbose audits retain available failure traces.
