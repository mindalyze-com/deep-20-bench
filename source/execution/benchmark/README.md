# Benchmark control plane

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

`config/models.yaml` registers exact Guesser configurations by immutable `M-…` ID.
`config/benchmarks.yaml` registers benchmark policy templates by `B-…` ID and fixes:

- Default iterations, normally three.
- Game policy apart from the required per-run benchmark mode.
- Oracle, blind Reviewer, blind Judge, and Guess Validator configurations. Reviewer and Judge
  routes are nested under the Oracle configuration.

`--model` is required and binds one immutable Guesser configuration to the run. With no target
selection, every registered subject is selected in catalog order; explicit target lists
preserve caller order. Trials run numerically and execution is sequential. Failed trials are
retained as infrastructure failures and are never silently replaced.

`--benchmark-mode` is also required and accepts exactly `official` or `experimental`. There is
no implicit mode: omitting the option stops before credentials or providers are accessed and
prints both valid choices.

Public route metadata can be checked independently without paid model calls. This checks the
complete registered Guesser catalog, but it does not decide whether an official run may start:

```bash
uv run deep20 benchmark preflight
```

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
selected model against the complete subject catalog with the default three iterations:

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

To run the complete subject catalog for every registered model concurrently, use the repository
wrapper:

```bash
scripts/run-all-models.sh official 002 3
```

The positional arguments are mode, three-digit batch sequence, and iterations (default `3`).
The script starts every registered model concurrently, staggering launches by
`DEEP20BENCH_STAGGER_SECONDS` (default 45 seconds) to decorrelate provider rate-limit bursts,
and does not pass `--targets`, so every
execution expands to all registered subjects. IDs follow `BX-YYYYMMDD-MODE-MNNNN-SSS`.
Standard output and error are merged within a separate
`benchmark-logs/BX-YYYYMMDD-MODE-ALL-SSS/M-NNNN.log` file for each model, so concurrent output
does not interleave. Reusing the same sequence resumes those execution IDs.

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
typed sink interfaces, and discarded in memory after their metrics and result have been
incorporated. The lower components never open files, and the benchmark does not create
per-trial component audit logs. When an error attempt returns textual output, the benchmark
composition root writes the full completion plus bounded attempt metadata to a signed
`error-outputs.jsonl` with owner-only permissions. This applies to terminal failures and
recovered error attempts. The diagnostic excludes prompts, message history, subject state, full
provider responses, annotations, and hidden reasoning, and no runtime path reads it back into a
model request. The bounded preview is written only to result objects: it is excluded from
Guesser-visible history, provider requests, caches, progress events, live state, summaries,
reports, and console logs. Benchmark progress JSONL, including typed contract-violation events,
is appended and `fsync`ed immediately;
`state.yml` is replaced atomically after every progress event.

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
not retain component prompts, full provider responses, episode events, or call-level audits.
Error-output artifacts are the narrow exception: they retain only textual completions discarded
by error handling and the metadata required to distinguish their attempts. Artifact references
carry paths, record counts, and integrity hashes.

## Console policy

The benchmark command alone configures handlers and component levels. At `INFO`, it emits one
run context line containing the immutable benchmark and model context, one subject line, one
condensed line per resolved turn, one terminal trial line, and one final result line.
Lower-component diagnostics remain below the benchmark's routine output level. Prompts, raw
responses, evidence excerpts, subject descriptions, credentials, headers, and environment
values are never logged.
