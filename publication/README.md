# Deep20Bench publication

`deep20-publication` is the independent, deterministic post-processor for the Deep20Bench
homepage. It validates signed benchmark artifacts, decides official eligibility, selects the
latest qualified run for each model, calculates the declared question score, emits a versioned
public JSON/CSV projection, and builds the static GitHub Pages site.

It does not import the benchmark runner, game, Oracle, Reviewer, Judge, Validator, provider,
prompts, sessions, or credentials. It never makes a model request. Publication happens only
after the source runs have completed.

## Package layout

```text
publication/
├── publication.yml              typed active-cohort and site configuration
├── pyproject.toml               independent Python package
├── src/deep20_publication/      discovery, integrity, classification, scoring, serialization
├── tests/                       compiler, integrity, determinism, and boundary tests
└── site/                        independent Vue 3 + Vue Router + Vite frontend
```

The Python core accepts and returns strict frozen Pydantic models. Filesystem discovery,
generated-data persistence, the Node build, and the atomic `docs/` replacement live only in
the CLI composition root. The frontend reads generated JSON; it does not parse YAML or
reimplement scoring.

## Build

From the repository root:

```bash
uv sync --project publication --group dev
npm ci --prefix publication/site
uv run --project publication deep20-publication build
```

The build:

1. discovers `runs/M-????/BX-*/summary.yml`;
2. validates each signed summary, adjacent manifest, state, and referenced completed-trial
   artifact, including both the reference file hash and signed episode envelope;
3. compiles the active cohort and a strict public episode projection from
   `publication/publication.yml`;
4. writes the complete `deep20bench-v5.json` and `leaderboard.csv` downloads, plus typed,
   split JSON documents for the SPA;
5. builds the Vue application and writes static entry shells for every execution, subject, and
   episode route;
6. uses the configured base path for clean direct URLs on GitHub Pages and normal static HTTP
   hosts;
7. runs strict Vue/TypeScript checks and the static build;
8. atomically replaces the generated-only site output in `docs/`.

To verify that committed output is current without replacing it:

```bash
uv run --project publication deep20-publication build --check
```

## Test

```bash
uv run --project publication ruff check publication
uv run --project publication mypy publication/src publication/tests
uv run --project publication pytest -q publication/tests
npm run --prefix publication/site check
```

No credential or network access is needed once the locked Python and Node dependencies are
installed.

The SPA loads `manifest.json` and `leaderboard.json` first. It fetches one small run, subject,
or episode document only when that route needs it. The complete version 5 JSON remains a
download and is not imported into the application bundle. Browser promise caching applies only
to these immutable public reporting files. It is application caching, not provider prompt
caching, and it cannot affect model requests, benchmark execution, or Guesser-visible state.

The app uses clean history routes. Generated route shells make direct reloads work on static
HTTP hosts. Direct `file://` navigation is not supported because clean history paths require an
HTTP origin. Opening `docs/index.html` directly shows the local preview command instead of a
blank page.

Start the Vue development server from the repository root:

```bash
npm run --prefix publication/site dev -- --host 127.0.0.1 --port 4173
```

Then open <http://127.0.0.1:4173/deep-20-bench/>.

## Official eligibility

A run reaches the official leaderboard when its signed files pass integrity validation, it is
terminal, it contains the active subject set, and every subject has all configured completed
trials (currently five, numbered 1 through 5). A completed model failure remains a valid scored
trial. An infrastructure-failed or missing trial does not count as completed, so the run waits
for its retry instead of qualifying with four trials.

Qualification does not compare the run's benchmark version, seed, question limit, subject
catalog hash, `publication_eligible` flags, or immutable model configuration with the current
catalog. The published model metadata comes from the selected signed run. When several runs
qualify for one configured model ID, publication selects the run with the greatest typed
completion timestamp. It never selects by score, and a latest-timestamp tie fails the build.
Cache status and cache metrics are reporting-only and never affect qualification.

Only selected current-protocol runs and their models enter the leaderboard, public run details,
and generated routes. Historical protocol artifacts live outside `runs/` under `archive/` and
are never parsed by the publication compiler. Non-qualifying current runs remain under `runs/`
but are omitted from the public projection. The version 5 JSON shape emits an empty `lab_runs`
collection. Tampered or malformed discovered input still fails the build.

The score uses exact decimal arithmetic:

```text
failure penalty = question limit + 1
trial value = counted questions on success, otherwise the failure penalty
subject average = sum of that subject's trial values / number of its trials
model score = sum of all subject averages / number of subjects
```

The question score remains in the unit used by the game. Lower is better. Ranking uses the
unrounded value, and exact ties remain joint ties. Every completed trial contributes to its
subject average, including model failures at the declared penalty. Averaging the subject
averages gives every subject equal weight. Because the active cohort has five trials for each
of seven subjects, this is also the average of all 35 penalized trial values. Infrastructure
failures remain unscored. Episode details preserve both the observed question count and the
penalized trial value.

The publication dataset schema is an output contract, not a run-artifact contract. Completed
protocol 9 runs created before question scoring remain valid inputs. The publisher derives the
question score from their signed `counted_questions`, outcome, and question-limit fields. It
does not require a B20 field, a run migration, or another benchmark execution.

## Cross-model cost, time, and efficiency

The static Results area has four views:

```text
/results/             score, outcome, reliability, cost, and time overview
/results/cost/        full-run component costs and per-episode costs
/results/time/        provider-reported Guesser response time
/results/efficiency/  cost-adjusted ranking and cost-quality frontier
```

Cost pages use provider-reported costs recorded in the selected signed run. They are historical
measurements, not estimates based on current prices. Full benchmark cost includes the Guesser,
Primary Oracle, Reviewer, Judge, and Validator. Per-episode values divide by terminal episodes.
Support cost is full cost minus Guesser cost.

The Results time page shows only Guesser response time. This is the sum of provider-reported
latency for every recorded Guesser call. Guesser time per episode divides that sum by terminal
episodes. Guesser latency per call divides it by recorded Guesser calls. The page excludes
Oracle, Reviewer, Judge, Validator, scheduling, concurrency, and other benchmark overhead.

Question score remains the primary benchmark result. Cost efficiency is a separate official
ranking:

```text
cost-adjusted question score =
    question score × (recorded Guesser cost / terminal episodes)
```

The unit is USD·questions per episode, and lower is better. Ranking uses exact decimals. The
site displays rounded values. The formula uses only Guesser cost so that Oracle, Reviewer,
Judge, and Validator pricing does not change the rank of the model under test. A proportional
reduction in recorded Guesser cost has the same effect as the same proportional reduction in
question score.

The calculation has three steps:

1. Calculate the Question Score by averaging penalized trial values within each subject, then
   averaging those subject averages.
2. Divide the run's total recorded Guesser cost by its terminal episode count.
3. Multiply the two exact values.

For example, `12.3 questions × $0.0500 per episode` gives a cost-adjusted score of
`0.615 USD·questions per episode`.

A run is efficiency-ranked only when it has a question score, at least one terminal episode, at
least one completed Guesser call, and a positive recorded Guesser cost. Existing signed
artifacts do not distinguish a genuinely free call from a provider response that omitted its
price. The publisher therefore treats zero aggregate Guesser cost as unavailable instead of
ranking it as free.

The efficiency chart also marks the Pareto frontier. A model is on the frontier when no other
ranked model has both an equal-or-lower question score and an equal-or-lower Guesser cost per
episode, with at least one strict improvement. Pareto status is descriptive and does not alter
either official rank.

All comparison values are derived after model calls from completed artifacts. They are
reporting-only. They never enter a Guesser request, history, retry, session, cache namespace, or
later trial. The feature does not change provider-side prompt caching or add application
response caching.

## Public drill-down

Every completed public trial can be followed through three static levels:

```text
/runs/<execution>/
└── subjects/<target>/
    └── episodes/<trial>/
```

The last page identifies the hidden subject prominently, then renders the typed sequence of
Guesser questions or guesses beside the final adjudicated `YES`, `NO`, or `UNKNOWN` answer.
Oracle evidence URLs and excerpts are expandable and labeled `model_reported`, because
publication preserves the research Oracle's evidence claims but does not independently certify
them.

Typed contract-violation turns are rendered in their exact transcript position. A breached
episode, subject, or run says “Model broke the output contract” even when gameplay ultimately
succeeded. The public JSON, CSV leaderboard, and site expose compliance, violations, affected
trials, counted-turn penalties, and each turn's typed violation reason as an independent
reliability aspect. Episode pages explain whether the turn was charged and whether the fixed
`FORMAT_ERROR` event was sent. The question total already includes those penalties, so
publication does not add another score penalty.

The contract is short, explicit, and fixed for the whole episode. Compliance tests whether the
model retains and applies that instruction as the conversation grows. A violation can show that
the model lost track of the required action format or failed to complete an action. This is
separate from gameplay success: a model can solve the game while breaking the protocol, or fail
the game while following the protocol correctly.

Malformed provider completions remain in signed, owner-only `error-outputs.jsonl` diagnostic
artifacts. Publication never reads those files into the public dataset or a report page and
does not publish cropped previews. This preserves the diagnostic isolation contract. Public
pages show the typed reason recorded in the completed episode artifact instead.

The technical section exposes requested/resolved models and providers, prompt-contract versions,
token/cache/latency/cost telemetry, and immutable episode provenance. The compiler intentionally
does not project system instructions, raw Guesser conversation records, variation tokens, call
IDs, raw provider responses, sessions, cache keys, diagnostics, credentials, or headers.
The package accepts only the current manifest/summary schema 3, episode schema 9, and game
protocol 9. It has no legacy adapter, schema downgrade, or per-run exclusion path. Every
discovered run must satisfy the current strict read contract. Internal read-model names remain
version-neutral; signed wire `schema_version` fields are the artifact-version authority.

The public episode projection publishes the final quality-controlled answer and Oracle research
evidence without exposing blind Reviewer or Judge decisions.

The static site also includes `/story/`, a handwritten origin-and-lineage page. It says Patrick
Heusser and Markus Tuor developed the idea together, and Patrick later designed and built the
benchmark. It then situates Deep20Bench alongside directly linked prior work. The Apple
Entity-Deduction Arena paper is acknowledged prominently as the closest published predecessor
found during research. This editorial page is site source only: it does not enter the generated
benchmark dataset or any source run artifact.
