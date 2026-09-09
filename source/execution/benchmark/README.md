# Benchmark control plane

For a Guesser-free replay of recorded questions against the current Oracle pipeline, use
`deep20 benchmark replay-oracle`. See [Oracle question replay](../../../documentation/oracle-question-replay.md)
for the Astra five-answer source, preview, filters, private comparison reports, and continuation.

New B-0003 executions use `concise_knowledge_v1`: one research attempt requesting
`research_query_target` queries (default 3), with an API ceiling calculated as the target plus
two bonus calls. Valid completed answers within that ceiling retain normal independent
evidence/knowledge decisions and private `evidence`/`other` basis plus a supporting statement. This policy permits source-free directional answers
and retained UNKNOWN context; the earlier evidence/recovery rules below describe historical
policies. See [the current policy](../../../documentation/five-answer-experiment.md#concise-evidenceknowledge-policy).


Benchmark executions support [historical Oracle answer reuse](../../../documentation/oracle-history-cache.md) under the explicit
`historical_ask_v1`, `same_episode_ask_v1`, and `same_execution_ask_v1` policies. The benchmark
lazily loads verified historical trials and adds eligible live ASK answers after each completed,
scoring-eligible game. Later repetitions reuse these answers; resume restores them from verified
trial artifacts. The engine also stores answers immediately for normalized repeats within one
game. Repeats still count as questions. Reused ASK turns retain original evidence and marked
source provenance, with no new adjudicator calls or cost. Each Guesser conversation starts fresh;
cache metadata never enters it. Standalone commands keep fresh-call behavior. Guesser and
Validator responses are never cached. Older manifests retain their recorded cache scope.

New direct runs discover other processes' completed games when each subject starts. Trial YAML
is written atomically after each game, so the source run need not be finished. Each subject's
inventory is saved before reuse and restored on resume; subsequent questions and repetitions
for that subject do not rescan external history. Pass `--oracle-history-before` to freeze all
subjects at one cutoff. Existing executions retain the discovery policy in their manifest.


B-0003 adds an experimental five-answer qualified_v1 profile with three default repetitions and the same models. Its Guesser and Oracle profiles must match. Qualified tokens stay out of standard runs and the v9 publication. See [Five-answer experiment](../../../documentation/five-answer-experiment.md).

Earlier B-0003 definitions explicitly selected `adjudication_policy: judge_stable_knowledge_v1` in
Oracle configuration. The versioned Judge fallback changes the immutable definition hash;
use fresh execution IDs and compare policies separately. Missing policy retains the historical
profile behavior. The configured policy reaches structured startup canaries, provider schemas,
local validation, and saved episode configuration. Scheduling remains three iterations, and
Oracle UNKNOWN and Oracle-Reviewer agreement still bypass the Judge.

The concise policy now gives a completed Oracle reply with explicit zero recorded searches
the existing bounded invalid-output retry. Missing telemetry and route/cache/budget faults
do not authorize retry. The retry still requires a recorded search, preserves blind inputs,
and retains all costs. This service revision changes the factual contract for fresh runs.

`deep20-benchmark` is the top-level orchestration package. Each execution applies a benchmark
definition to exactly one registered Guesser configuration, persists every trial continuously,
publishes live typed state, aggregates that model's observations, renders derived summaries,
and returns one complete immutable `BenchmarkResult`.

Dependency direction is one-way:

```text
deep20-benchmark → deep20-game → deep20-oracle
```

Lower packages receive typed persistence and observation protocols. They never choose benchmark
paths, configure logging, or own routine benchmark `INFO` lines.

## Catalogs and scheduling

`B-0002` is an experimental concise-prompt variant of `B-0001`, with five default repeats.
Its revised Guesser and factual-adjudication profiles keep the same models, scoring, and
three-answer protocol. It cannot run in official mode or enter the standard leaderboard.
Startup canaries run by default for this experiment as well as official runs. See
[Concise prompt experiment](../../../documentation/concise-prompt-experiment.md).

`config/models.yaml` registers exact Guesser configurations by immutable `M-…` ID.
Each configuration also declares `structured_output_mode`. The normal
`strict_json_schema` mode requires provider-side JSON Schema enforcement. A route explicitly
set to `json_object` still requires OpenRouter JSON formatting, uses the same fixed action
instructions, and is validated locally against the complete action contract without repair.
`config/benchmarks.yaml` registers benchmark policy templates by `B-…` ID and fixes:

- Default iterations, normally three.
- Game policy apart from the required per-run benchmark mode.
- Oracle, blind Reviewer, blind Judge, and Guess Validator configurations. Reviewer and Judge
  routes are nested under the Oracle configuration.

All three benchmark templates now allow 40 counted questions and one final guess-only
opportunity. Their changed definition hashes require new execution IDs. Existing runs retain
their recorded 50-question policy; a resume or repair must use its original definition.
Publication edition 1.0 remains at 50 for the historical leaderboard. Edition 1.1 declares a
separate 40-question release cohort with its own prompt and configuration pins. Neither cohort
admits a different limit; current execution defaults do not change either release definition.

`--model` is required and binds one immutable Guesser configuration to the run. With no target
selection, a new execution selects every active subject in catalog order; explicit target lists
preserve caller order and reject inactive subjects. Trials run numerically and execution is
sequential. Failed trials are
retained as infrastructure failures and are never silently replaced.

`config/subjects.yaml` retains all subjects. Its optional per-entry `status` is `active` by
default; set `status: inactive` to remove a subject from new benchmark schedules without
deleting its identity. Stephen King (`T-0003`) and Mario (`T-0007`) are inactive, leaving ten
active subjects. Reactivate either by setting `status: active`.

Existing execution IDs retain their signed subject selection on resume or repair, even when a
subject is now inactive. Omitted targets use that recorded selection. Status does not enter
the subject identity hash or any component request, so status changes alone do not invalidate
existing runs. Changes to subject identity, game policy, or other immutable context still fail
the existing consistency checks. Historical publication cohorts retain their configured IDs.

`--benchmark-mode` is also required and accepts exactly `official` or `experimental`. There is
no implicit mode: omitting the option stops before credentials or providers are accessed and
prints both valid choices.

Public route metadata can be checked independently without paid model calls. This checks the
complete registered Guesser catalog, but it does not decide whether an official run may start:

```bash
uv run deep20 benchmark preflight
```

For a running official execution, render its completed position scores against both the
published overall leader and the published model leading over the same completed prefix:

```bash
uv run python scripts/benchmark-progress-report.py \
  M-0022 BX-20260904-official-M0022-001
```

Markdown is the default. Pass `--format` or `--format console` for padded ASCII console tables:

```bash
uv run python scripts/benchmark-progress-report.py \
  M-0022 BX-20260904-official-M0022-001 --format console
```

Pass `--context` to prepend the latest resolved question and answer from both the current and
previous rounds, including Oracle evidence excerpts and source URLs. An optional count selects
more recent questions from each round, for example `--context 3`. This is report-only data and
is never added to Guesser history or any later model request.

The report reads validated terminal trial artifacts and generated publication data. It lists
the subject, penalized question score, cumulative total cost, and output-contract break count
for both models at each completed position. A combined final column presents both break counts
in the same model order as the cost column. Subject and overall rows total the included breaks.
Averages and costs use two decimal places. Candidate costs include superseded repair attempts.
Subject-average rows state how many configured iterations are represented. The status section
reports the exact live position and distinguishes active failures from repaired historical
failures. A separate timing section reports active runtime and estimates remaining
time from the candidate's own elapsed speed. It maps the live position and turn to the overall
leader's actual per-trial timing, uses that point as the completed fraction of the leader's
run, and projects the candidate's total and remaining runtime from that fraction. A separate
linear estimate uses completed positions only. Both estimates show remaining duration and a
finish timestamp in the system timezone; `--timezone` accepts an explicit IANA timezone. The
script rejects a run whose benchmark, subject order, iteration count, seed, or scoring policy
does not match the active published cohort.

Official runs make one small, real call for each configured role before any trial starts. The
Guesser, Oracle, and Guess Validator calls ask the exact model under its configured routing
policy to reply with `Hi`. The Reviewer and Judge calls use their real prompts and structured
response schema with one fixed synthetic subject, question, and numbered evidence excerpt.
Each must return the expected typed evidence decision. This catches route-specific
structured-output and request-parameter failures before a trial needs either role.
An execution whose durable state is already `completed` skips these paid startup calls. The
runner still validates the immutable execution context and returns the existing typed result.

Exact routes must resolve to their configured backend. Automatic routes must report the backend
that OpenRouter selected. The Reviewer and Judge checks are blind and have no web access. They
do not receive an Oracle answer, Reviewer answer, episode history, or a real benchmark subject.
All checks use isolated sessions and separate prompt-cache namespaces. Unexpected output is
discarded, and canary data never enters benchmark state or Guesser history. Use `--no-canary`
to skip these paid calls. The standalone command still probes one Guesser's structured
contract:

```bash
uv run deep20 benchmark canary --model M-0001
```

```bash
uv run deep20 benchmark run B-0001 \
  --model M-0001 \
  --benchmark-mode experimental \
  --targets T-0001 \
  --targets T-0004 \
  --run-id BX-019-example \
  --iterations 3 \
  --seed 42 \
  --log-level INFO
```

Target selection and iteration flags are optional; `--model`, `--run-id`, and
`--benchmark-mode` are required. Every run enforces an infrastructure circuit breaker: after
`--max-consecutive-infrastructure-failures` consecutive infrastructure failures (default 5) the
run aborts with a typed `infrastructure_circuit_breaker_open` error instead of burning the
remaining schedule; the execution can be resumed or repaired later. This minimal form runs the
selected model against all active subjects with the default three iterations:

```bash
uv run deep20 benchmark run B-0001 \
  --model M-0001 \
  --benchmark-mode experimental \
  --run-id BX-019-example
```

For a completed execution with infrastructure failures, `repair` re-runs only those failed
trials. For an execution aborted by the circuit breaker, it re-runs eligible failed trials and
then continues the unstarted schedule. Trial identities, episode run IDs, and variation tokens
stay unchanged, while every repaired game starts with a fresh episode and Guesser session.
Scoring-eligible trials are never re-run, and each trial allows at most
`--max-repair-attempts` total start attempts (default 3, counted from durable `trial_started`
events). Replaced failure diagnostics and partial metrics remain in the typed trial result as
superseded attempts. Final total cost includes those attempts. Every resume or repair records
the executing Git commit in the signed benchmark event stream and final typed result. Official
repairs run startup canaries by default; pass `--no-canary` to skip those paid probes:

```bash
uv run deep20 benchmark repair B-0001 \
  --model M-0001 \
  --benchmark-mode official \
  --run-id BX-019-example
```

Experimental repairs may explicitly pass `--allow-oracle-contract-change` after an Oracle
implementation or prompt fix. The original signed manifest, schedule, scored games and failed
attempt costs remain intact. A signed resume event records the previous/current Oracle hashes,
the current definition hash and the replacement history snapshot. Historical sources are
cleared across this boundary, while the original cutoff and same-episode policy stay fixed.
Later repairs use the recorded active contract; another change requires explicit opt-in again.
This does not permit model, subject, game-policy, or configuration changes. The final result
lists its contract revisions and retains an execution-level publication-ineligible flag.
The independent publisher can accept explicitly authorized release revisions only after
complete scoring coverage and its full contract checks; see `source/publication/README.md`.
Mixed-contract executions never seed historical ASK inventories. Official repairs cannot use
this exception. Prefer a fresh
execution when a uniform factual contract is required for comparison.

The batch wrapper requires the benchmark ID and execution mode explicitly. Preview a
five-answer batch on all active subjects with:

```bash
scripts/run-all-models.sh B-0003 experimental 001 \
  --exclude-model M-0013 \
  --exclude-model M-0017 \
  --dry-run
```

The example exclusions reflect the unresolved Qwen identity mismatch and unavailable Ox Alpha
route checked on 7 September 2026; they are caller choices, not automatic catalog exclusions.
Recheck the routes before selecting the actual batch. To select only particular models, repeat
`--model`, for example `--model M-0001 --model M-0006`. Omitting selections starts from all
registered models; `--exclude-model` then removes named registrations. Unknown IDs, duplicate
selections, an empty selection, or incompatible benchmark/mode settings fail before launch.

The positional arguments are benchmark ID, mode, optional three-digit sequence (default `001`),
and optional iterations. Iterations come from the benchmark catalog when omitted: **3 for
B-0003**. B-0001 also defaults to 3; B-0002 retains its separate default of 5. The former
`scripts/run-all-models.sh experimental ...` syntax is rejected. Use `B-0001 official` explicitly
for a standard official batch; B-0003 requires `experimental`.

`--dry-run` validates local configuration and prints the commands without writing batch
artifacts, checking live routes, running canaries, or starting games. Remove it to execute the
batch. Full macOS batches must still run in detached `screen` sessions with
`nohup /usr/bin/caffeinate -i ... </dev/null >>run.log 2>&1 &`. Verify screen, caffeinate,
benchmark processes, startup canaries, manifests, and the first turn after launching.

The wrapper defaults to per-subject history discovery for every model, matching direct runs.
It can reuse newly completed games from concurrent runs without an extra option. History is
discovered once per subject, so available answers can depend on process timing. Preview it with:

```bash
scripts/run-all-models.sh B-0003 experimental 002 \
  --model M-0001 --model M-0006 --dry-run
```

Use `--oracle-history-before` for a shared, timezone-aware fixed cutoff, or `--no-oracle-cache`
to disable all ASK reuse policies. `--refresh-oracle-history` remains an explicit spelling of
the default. These options are mutually exclusive.
A real launch saves its model selection, iterations, seed 0,
and cache settings in `benchmark-logs/<batch-id>/batch.json`. Restarting the same batch reuses
the recorded cutoff or refresh mode, including older fixed-cutoff batches; changing saved
settings requires a fresh sequence. Keep source history artifacts immutable for a comparison
with a fixed cutoff. Dry-run previews do not save a batch plan.

Models run concurrently, with `DEEP20BENCH_STAGGER_SECONDS` (default 45 seconds) between starts.
The benchmark CLI owns active-subject selection; the wrapper supplies no subject hints or target
overrides. Startup canaries remain enabled. Execution IDs include the benchmark ID to avoid
cross-profile collisions: `BX-YYYYMMDD-B-NNNN-MODE-MNNNN-SSS`. Batch logs live under
`benchmark-logs/BX-YYYYMMDD-B-NNNN-MODE-ALL-SSS/`, with stdout and stderr merged into one
append-only `M-NNNN.log` per model. A process lock prevents concurrent launches of the same batch.
The wrapper waits for every child and returns a failure status if any child fails. An interrupted
launcher terminates its remaining child process groups. `RUN_DATE=YYYYMMDD` selects the original
batch date when restarting on another day; existing benchmark consistency and resume rules apply.

Detached benchmark commands must be one-shot jobs. Do not submit them to a launchd service with
`KeepAlive` enabled: launchd will restart a successfully completed execution. A direct `nohup`
command must include `&` to run in the background. The benchmark also skips paid startup
canaries for an already completed execution as a defensive safeguard.

On macOS, every `benchmark run` and `benchmark repair` process automatically starts
`/usr/bin/caffeinate` for its own lifetime. This applies to direct commands and commands started
by the wrapper. It prevents idle system sleep while still allowing the display to sleep. Other
operating systems do nothing. Set `DEEP20BENCH_CAFFEINATE=0` for a single invocation to disable
the behavior. A missing or failed `caffeinate` process produces a warning and does not fail the
benchmark. The assertion does not override lid-close sleep, manual sleep, shutdown, or battery
depletion.

Resume validates the immutable execution manifest and executes only trials that were never
started. A trial directory without a typed terminal result is recorded as interrupted rather
than replayed.

## Guesser sampling

`--seed` is a benchmark-level base seed. For every trial, Deep20Bench derives an opaque prompt
variation token; for every Guesser call on supported routes it also derives a portable 31-bit
provider seed. These derivations use only the base seed, trial number, and, for provider seeds,
Guesser turn number. They never use the subject, target ID, execution ID, Oracle state, or
adjudicator evidence. Separate model runs using the same base seed and trial numbers therefore
receive the same paired variation schedule without sharing execution state.

The token appears only in the initial `BEGIN` user event. Its value remains visible in normal
conversation history, while all later adjudicator replies remain exactly `YES`, `NO`, or
`UNKNOWN`. The only non-adjudicator exception is the fixed, subject-independent `FORMAT_ERROR`
after a malformed Guesser output; parser details and raw output remain hidden. The system
prompt contains only the fixed rule explaining the token, preserving its stable cacheable
prefix.

Each registered Guesser declares `seed_capability: supported` or `unsupported`. Supported
OpenRouter requests include the derived `seed` and require the selected endpoint to honor every
request parameter. Unsupported models omit the provider seed but still receive the
subject-independent prompt variation token, so the complete benchmark can include model
families without a seed API. A different base seed does not force a different answer; identical
actions remain valid evidence of model stability.

The current `openai/gpt-5.6-luna` OpenRouter route is registered as `unsupported`: requiring the
`seed` parameter leaves no compatible OpenAI endpoint. The benchmark therefore uses
OpenRouter's normal pinned-provider routing for `M-0001` and records that its sampling is
prompt-token-only.

`M-0017` uses `stealth/ox-alpha` pinned to the Stealth endpoint. The route does not advertise
`seed` or strict structured outputs, so it uses the subject-independent prompt variation token
and `structured_output_mode: json_object`. Invalid or incomplete JSON remains a scored model
contract violation under the same recovery policy as every other Guesser.

The default base seed is `0`. Reusing a base seed reproduces the variation schedule on a
best-effort basis; use a different `--seed` for a new controlled replicate set.

## Typed result

`BenchmarkRunner.run(BenchmarkRequest) -> BenchmarkResult` is the primary interface.
`BenchmarkRequest.benchmark_mode` has no default and requires `BenchmarkMode.OFFICIAL` or
`BenchmarkMode.EXPERIMENTAL`. Every request, ID, catalog entry, event, state snapshot, manifest,
artifact reference, failure, summary, and nested result is a strict frozen Pydantic object.

```text
BenchmarkResult
├── run.model: BenchmarkModelSnapshot
└── subjects: tuple[SubjectBenchmarkResult, ...]
    └── trials
        ├── CompletedTrialResult → EpisodeResult
        └── InfrastructureFailedTrialResult → BenchmarkFailure + partial metrics
```

The result retains every observation. Aggregation reports counts, eligible success rate,
inclusive quartiles, mean, sample standard deviation, question distributions, per-component
and total cost, tokens, latency, cache telemetry, recovery attempts/reasons/usage, grouped
terminal failures, duration, and output-contract reliability. Reliability includes evaluated
and valid outputs, violations, counted-turn penalties, affected trials, compliance rate, and a
clean/breached/not-evaluable status. It is independent of gameplay success: a recovered
successful trial remains breached. Aggregation performs no outlier deletion and produces no
composite leaderboard score. Factual-adjudication aggregates additionally report
Oracle–Reviewer agreement and disagreement, disagreement rate by deterministic question type,
Judge answer distribution, final `UNKNOWN` frequency, Oracle answers changed by the Judge, and
separate Reviewer, Judge, and total quality-control cost.

Published aggregate statistics use stable human-scale precision: success rates use four
decimal places, USD values use eight, and count/token/time statistics use two, with redundant
trailing zeroes removed. Calculations and complete trial/provider records retain their original
`Decimal` precision; rounding occurs only when constructing aggregate and compact-summary
objects.

Every completed episode also contains a versioned `audit.calls` log. It records one sanitized
entry for each retained Guesser, Oracle, and Validator call, in execution order. Entries keep
the turn number, component call ID, prompt version/hash, timestamps, route, HTTP/finish/cache
status, retry and recovery totals, exact provider usage, latency, cost, raw-output length,
discarded-output count, web-search request count, citation-annotation count, and an allowlisted
OpenRouter execution-stage summary. Oracle entries keep separate primary, Reviewer, and Judge
role summaries, plus the optional diversified-recovery role. The research summary also retains
the deterministic question class, attempt strategy, classified outcome and resolution,
evidence count, and bounded model-reported query strings. A `web_search_requests` value counts
search queries, not returned documents, and the reported query strings are not independently
verified provider telemetry. Evidence and citation counts therefore remain separate
observations. `unavailable_call_count`
states how many attempted component calls had no safe trace to project. Schema-v9 results made
before this additive field have no `audit` section and remain valid inputs.

The exact serialized top-level object is written once to
`runs/<model-id>/<execution-id>/result.yml` with a SHA-256 integrity hash. Nested result files
are generated from the corresponding typed objects. Raw prompts and full provider exchanges are
intentionally absent from the returned object. Trials with discarded textual error completions
carry a typed reference to their private diagnostic artifact. Trial and benchmark `result.yml`
objects additionally carry a typed preview of the latest textual error attempt: the exact first
250 characters, the original character count, trailing-whitespace count, attempt number, finish
reason, and whether truncation occurred. The preview is derived in memory while handling the
error; it is not read back from the diagnostic artifact.

## Persistence and live observation

In benchmark mode, component records are validated, integrity-hashed, acknowledged through the
typed sink interfaces, and discarded in memory after their sanitized result audit and metrics
have been incorporated. The lower components never open files, and the benchmark does not
create per-trial raw component audit logs. The retained result audit excludes prompts, message
history, request/response bodies, raw output, evidence text, citation URLs, response IDs,
sessions, cache keys, headers, credentials, and router endpoint details. When an error attempt
returns textual output, the benchmark
composition root writes the full completion plus bounded attempt metadata to a signed
`error-outputs.jsonl` with owner-only permissions. This applies to terminal failures and
recovered error attempts. The diagnostic excludes prompts, message history, subject state, full
provider responses, annotations, and hidden reasoning, and no runtime path reads it back into a
model request. The bounded preview is written only to result objects: it is excluded from
Guesser-visible history, provider requests, caches, progress events, live state, summaries,
reports, and console logs. Benchmark progress JSONL, including typed contract-violation events,
is appended and `fsync`ed immediately;
`state.yml` is replaced atomically after every progress event.

If valid Oracle research remains inconclusive after recovery, the trial receives `UNKNOWN`
and continues under the normal scoring rules. Question keywords never turn missing evidence
into an infrastructure failure. Actual provider, schema, required-search, routing, and
persistence failures retain their infrastructure classification. New research audits use
`question_class: other`; historical labels and outcomes are not rewritten.

The revised factual contract `oracle-factual-answer-v2-inconclusive-unknown` is included in
benchmark definition hashes even when ASK caching is disabled. Fresh execution IDs are
required, and historical-cache inventories from the previous contract are incompatible.

```text
runs/
└── M-0001/BX-019-example/
    ├── manifest.json
    ├── state.yml
    ├── benchmark-events.jsonl
    ├── result.yml
    ├── summary.yml
    ├── summary.md
    └── subjects/T-0001/
        ├── result.yml
        ├── summary.md
        └── trials/trial-001/
            ├── result.yml
            └── error-outputs.jsonl  # only when an error attempt returned text; mode 0600
```

`result.yml` is the sole exhaustive result. `summary.yml` is a compact derived index of subject
summaries and individual trial references, while `summary.md` is its human-readable rendering.
Both can be regenerated from the result and leaf artifacts; neither is a second authoritative
benchmark result. Each subject report lists the counted-question value for every terminal
trial, followed by its average, minimum, median, and maximum over scoring-eligible trials.
Reports show average Guesser, combined factual-adjudication, Guess Validator, and total cost per
terminal trial. The Oracle cost includes the Oracle, Reviewer, and any invoked Judge; the
quality-control line separately reports Reviewer and Judge activity and cost. The run header
also shows total benchmark cost, calculated by summing the unrounded recorded cost of every
terminal trial, including partial costs from infrastructure-failed trials. Benchmark mode does
not retain component prompts, full provider responses, episode events, or raw call-level audits.
It does retain the bounded `audit.calls` projection inside every `EpisodeResult`, so the trial,
subject, and top-level exhaustive results preserve the same forensic facts. Error-output
artifacts are the narrow raw-text exception: they retain only textual completions discarded by
error handling and the metadata required to distinguish their attempts. Artifact references
carry paths, record counts, and integrity hashes.

The publication compiler uses only retained terminal attempts for model and benchmark cost
comparisons. Superseded infrastructure attempts remain in this gross execution total and the
repair ledger, but do not increase published comparative costs.

## Console policy

The benchmark command alone configures handlers and component levels. At `INFO`, it emits one
run context line containing the immutable benchmark and model context, one subject line, one
condensed line per resolved turn, one terminal trial line, and one final result line.
Lower-component diagnostics remain below the benchmark's routine output level. Prompts, raw
responses, evidence excerpts, subject descriptions, credentials, headers, and environment
values are never logged.

Direct questions and collected regression cases can run through the same Oracle service with
`deep20 benchmark test-oracle`. See [Direct Oracle question suites](../../../documentation/oracle-question-suites.md).
