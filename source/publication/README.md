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
source/publication/
├── compiler/
│   ├── pyproject.toml               independent Python package
│   ├── src/deep20_publication/      discovery, integrity, classification, and scoring
│   └── tests/                       compiler, integrity, determinism, and boundary tests
└── site/                            independent Vue 3 + Vue Router + Vite frontend
```

The active cohort and site configuration lives in `config/publication.yml`.
The Python core accepts and returns strict frozen Pydantic models. Filesystem discovery,
generated-data persistence, the Node build, and the atomic `docs/` replacement live only in
the CLI composition root. The frontend reads generated JSON; it does not parse YAML or
reimplement scoring.

The builder writes public JSON into a temporary staging directory. Generated data is not stored
under the handwritten site source. The development server reads the latest committed data from
`docs/`.

## Build

From the repository root:

```bash
uv sync --project source/publication/compiler --group dev
npm ci --prefix source/publication/site
uv run --project source/publication/compiler deep20-publication build
```

The build:

1. discovers `runs/M-????/BX-*/summary.yml`;
2. validates each signed summary, adjacent manifest, state, and referenced completed-trial
   artifact, including both the reference file hash and signed episode envelope;
3. compiles the active cohort and a strict public episode projection from
   `config/publication.yml`;
4. records separate UTC publication and application build times in typed public metadata;
5. writes the complete `deep20bench-v9.json`, its generated JSON Schema, and
   `leaderboard.csv`, plus typed, split JSON documents for the SPA;
6. builds the Vue application, statically renders the homepage, eight editorial pages, every
   selected official run summary, and every subject summary, and writes entry shells for episode
   routes;
7. uses the configured base path for clean direct URLs on GitHub Pages and normal static HTTP
   hosts;
8. runs strict Vue/TypeScript checks and the static build;
9. atomically replaces the generated-only site output in `docs/`.

Before publishing a new run with contract violations, refresh the public-safe Guesser output
snapshot:

```bash
uv run --project source/publication/compiler deep20-publication capture-guesser-outputs
```

This command reads the owner-only diagnostics locally. It writes only turn identity, violation
kind, attempt number, finish reason, and exact visible Guesser text to
`source/publication/data/guesser-violation-outputs-v1.json`. It excludes call IDs, response IDs,
recovery data, and all Oracle, Reviewer, Judge, and Validator records. Normal builds read this
tracked snapshot and never read the owner-only diagnostics.

To verify that committed output is current without replacing it:

```bash
uv run --project source/publication/compiler deep20-publication build --check
```

A normal build refreshes the homepage timestamp. Verification reuses the timestamp already in
the committed manifest, so `--check` compares the remaining output byte for byte.

## Test

```bash
uv run --project source/publication/compiler ruff check source/publication/compiler
uv run --project source/publication/compiler mypy source/publication/compiler/src source/publication/compiler/tests
uv run --project source/publication/compiler pytest -q source/publication/compiler/tests
npm run --prefix source/publication/site check
```

No credential or network access is needed once the locked Python and Node dependencies are
installed.

The browser uses typed public documents embedded in each statically rendered page for its first
hydration. It fetches one small run, subject, or episode document only when later navigation
needs it. Subject pages embed their run and subject documents so their aggregate result and
ordinary episode links exist in the initial HTML. The complete version 9 JSON remains a download
and is not imported into the
application bundle. Browser promise caching applies only to immutable public reporting files.
It cannot affect model requests, benchmark execution, or Guesser-visible state.

The build uses Vue server rendering with a memory-history router, then hydrates the same tree
with a web-history router in the browser. The homepage, eight editorial and result pages, and
every selected official run summary contain their real content and ordinary links in the
initial HTML. Charts and interactive controls start after hydration. There is no separate
fallback content tree or content-hiding script. Chart containers keep their declared height;
SVG initialization waits until the container is within 300 pixels of the viewport. Offscreen
data-only updates are retained until the chart returns; already-rendered SVGs still follow
viewport resizes. Data refreshes do not resize an unchanged chart, and cached routes reconnect
their observers when activated.

The generated pages have route-specific titles, descriptions, social metadata, canonical URLs,
and accurate publication modification times in `sitemap.xml`. Every page includes `og:site_name`
from the configured site title. The homepage includes separate Dataset and WebSite JSON-LD
nodes, using the configured site identity and canonical URL, `https://deep20bench.com/`.
Hosting the homepage at this domain root supports Google's site-name requirements.
The compiler's typed route manifest is also published as `data/routes.json`.
Vite bundles its page metadata into the client, so initial HTML, hydration, and client navigation
use the same titles, descriptions, social metadata, canonical URLs, and indexability rules
without an extra metadata request. Short navigation labels never write document metadata.
The sitemap contains the homepage, editorial URLs, every selected official run,
and every subject summary. These pages do not emit a robots meta tag, so search engines use their
default `index, follow` behavior. Episode evidence pages remain outside the sitemap and emit
`noindex, follow`; aliases and downloads remain outside the sitemap. The generated 404 page also
emits `noindex, follow`.

This repository publishes through GitHub Pages at `https://deep20bench.com/`, with base path `/`.
The prerenderer derives `CNAME` and `robots.txt` from the canonical URL in every complete build.
The root robots file allows crawling and advertises `https://deep20bench.com/sitemap.xml`.
After deployment, submit that sitemap in Google Search Console.
See Google's guidance for [robots.txt location](https://developers.google.com/crawling/docs/robots-txt/create-robots-txt)
and [sitemap submission](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap).

The app uses clean history routes. Generated route directories make direct reloads work on
static HTTP hosts. Direct `file://` navigation is not supported because clean history paths and
route data require an HTTP origin.

Start the Vue development server from the repository root:

```bash
npm run --prefix source/publication/site dev -- --host 127.0.0.1 --port 4173
```

Then open <http://127.0.0.1:4173/>. The browser fixture suite explicitly retains the historical
project-path configuration; static-output tests exercise the production domain-root build.

The original `https://mindalyze-com.github.io/deep-20-bench/data/deep20bench-v9.json`
address remains an external compatibility endpoint. Keep the v9 JSON and schema current and
verify the old address reaches valid current JSON after the custom-domain deployment. The v9
site metadata now uses base path `/`; its schema accepts both root and project paths. Verify
old page redirects individually, including run, subject, and episode routes. See
`documentation/custom-domain-migration.md` for the deployment checks.

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
but are omitted from the public projection. The version 7 JSON shape emits an empty `lab_runs`
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

Each official question score also has a 95% repeated-trial confidence interval. The calculation
treats subjects as fixed strata and the completed seeded trials within each subject as
independent repetitions. It estimates each subject's sample variance, combines the equally
weighted variance terms, and uses a Welch–Satterthwaite t critical value. A wider interval means
less repeatable performance in the current experiment. The interval does not cover new subject
selection, later model or provider behavior, or direct pairwise model differences. See
[`documentation/confidence-intervals.md`](../../documentation/confidence-intervals.md).

Independence is a modeling assumption. Separate calls and variation tokens support it, but unique
seeds do not prove it. The interval is an approximate interval for the aggregate mean, not a
prediction range for individual trials.

Confidence intervals are reporting-only. The compiler derives them after completed model calls
from typed penalized trial values. They never enter Guesser-visible history, provider requests,
sessions, caches, retries, adjudication, or later trials.

## Cross-model stability, cost, time, and efficiency

The static Results area has five views:

```text
/results/             score, outcome, stability, cost, and time overview
/results/reliability/ repeated-trial stability ranking by 95% confidence-interval width
/results/cost/        full-run component costs and per-episode costs
/results/time/        tested-model response time and end-to-end benchmark runtime
/results/efficiency/  normalized ideal-distance ranking and cost-quality trade-off
```

Every model uses the same 95% confidence level. The Stability view therefore ranks by
confidence-interval width, not by confidence level. It subtracts the lower bound from the upper
bound and sorts from smallest to largest. A smaller width indicates a more repeatable aggregate
score on the fixed subjects. This rank is independent of score quality: a model may be consistently
bad or inconsistently good. A scatter chart shows CI width against question score; lower-left
means lower score and a smaller confidence interval width. The chart does not create a weighted score.

Cost pages use provider-reported costs recorded in the selected signed run. They are historical
measurements, not estimates based on current prices. Published comparisons use only the retained
terminal attempt for each trial. They exclude superseded infrastructure attempts so a repaired
Oracle, Reviewer, Judge, Validator, or provider failure cannot inflate the tested model's cost.
The signed benchmark artifact keeps those attempts in its gross execution total and repair
ledger. Recovery requests inside the retained terminal attempt remain included. Tested-model
cost is called Guesser cost in the methodology. Full benchmark cost includes the Guesser,
Primary Oracle, Reviewer, Judge, and Validator. Per-episode values divide by terminal episodes.
Support cost is full cost minus Guesser cost. When repair overhead was excluded, the cost table
and run ledger show its amount as separate, non-comparable information.

The first chart on the Results time page shows tested-model response time. This is the sum of
provider-reported latency for every recorded Guesser call. Model time per episode divides that
sum by terminal episodes. Model latency per call divides it by recorded Guesser calls. A second
chart shows end-to-end runtime, which also includes support-model calls, scheduling, concurrency,
and other benchmark work.

Question score remains the primary benchmark result. Cost efficiency is a separate official
ranking. It first normalizes the question score and recorded Guesser cost per episode across
the current eligible cohort:

```text
normalized value = (value − cohort minimum) / (cohort maximum − cohort minimum)

ideal distance = √(normalized question score² + normalized Guesser cost²)
```

Lower is better. Both normalized dimensions range from 0 to 1 and have equal weight. A score of
0 would match the cohort minimum on both dimensions. The theoretical maximum is √2. The
compiler emits the normalized components and distance as typed Decimals. It ranks with the
algebraically equivalent exact rational squared distance, so square-root rounding cannot change
the order. The site rounds values only for display.

The calculation has three steps:

1. Calculate the Question Score by averaging penalized trial values within each subject, then
   averaging those subject averages.
2. Divide the retained terminal attempts' recorded Guesser cost by the terminal episode count.
3. Min/max-normalize both cohort measures and calculate their Euclidean distance from `(0, 0)`.

For example, normalized question score `0.06` and normalized cost `0.08` give distance `0.10`.

A run is efficiency-ranked only when it has a question score, at least one terminal episode, at
least one completed Guesser call, and a positive recorded Guesser cost. Existing signed
artifacts do not distinguish a genuinely free call from a provider response that omitted its
price. The publisher therefore treats zero aggregate Guesser cost as unavailable instead of
ranking it as free.

The prior product score remains in schema 8 as `cost_adjusted_question_score`. Its historical
`efficiency_rank` field keeps the same product-rank meaning for compatibility, and
`product_efficiency_rank` is an explicit alias:

```text
legacy product score = question score × recorded Guesser cost per episode
```

The official distance rank is published separately as `ideal_distance_rank`. Because its bounds
come from the current cohort, adding or removing a model can change every normalized value and
distance rank. For example, if Llama 4 Maverick is removed from the current 12-model cohort,
Claude Opus 5 moves from distance rank 2 to 1, Grok 4.5 moves from 3 to 5, and GPT-5 Nano moves
from 5 to 6. No underlying benchmark result changes; only the cohort normalization changes.

The compiler also marks Pareto-efficient models. A model is Pareto-efficient when no other
eligible model has both an equal-or-lower question score and equal-or-lower recorded Guesser
cost, with at least one strict improvement. This dominance statement does not depend on
normalization.

The efficiency chart uses the emitted normalized components on fixed 0-to-1 square axes. Labelled
dashed quarter-circles show equal ideal distance, including a faint 1.25 guide. Diamond markers
and table badges identify Pareto-efficient models. Tooltips retain the original question score
and recorded cost. Axis tick labels translate each normalized position back to those raw units
for display only.

This schema change affects only the post-run public projection. Benchmark manifest, summary,
state, and episode artifact schemas are unchanged. Existing signed runs remain valid inputs and
do not need migration or reruns; the compiler derives every new field after loading them.

Each Results page uses short, keyboard- and tap-accessible information popovers to define the
page-specific metrics and explain when chart or table orders differ. The popovers sit in the
related chart header: in a third column on wide screens and below the explanatory copy when
space is limited. Stability and Efficiency use a contained metric-definition card for the
formula and interpretation. Longer calculation details remain available through a native
details disclosure inside the card.

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
artifacts. An explicit post-run capture reads those files once and writes a tracked,
public-safe Guesser-violation snapshot. It keeps only the turn identity, violation kind,
attempt number, finish reason, and exact visible Guesser text. It drops call IDs, response IDs,
recovery metadata, and every support-model record. The publication compiler reads the public
snapshot, not the owner-only diagnostics. Episode pages show the typed rejection reason, the
captured text when one exists, and the required formats from the exact `FORMAT_ERROR` event.
Calls with no textual completion are labeled as such.

The technical section exposes requested/resolved models and providers, routing policy, safe
per-provider call/cost/latency totals, fallback counts, prompt-contract versions, component
telemetry, and immutable episode provenance for every LLM role. Legacy episodes keep their
recorded resolved-provider names and state that per-call provider totals were not retained. The
compiler intentionally does not project system instructions, raw Guesser conversation records,
variation tokens, call IDs, response IDs, support-model outputs, sessions, cache keys, recovery
diagnostics, credentials, or headers.
The strict source reader validates the private episode `audit.calls` projection when present,
including the typed Oracle research-attempt classification and bounded model-reported queries,
but the public compiler does not copy it into the public dataset. Public technical telemetry
continues to come from the existing aggregate allowlist.
The package accepts only the current manifest/summary schema 3, episode schema 9, and game
protocol 9. It has no legacy adapter, schema downgrade, or per-run exclusion path. Every
discovered run must satisfy the current strict read contract. Internal read-model names remain
version-neutral; signed wire `schema_version` fields are the artifact-version authority.

The public episode projection publishes the final quality-controlled answer and Oracle research
evidence without exposing blind Reviewer or Judge decisions.

The static site also includes `/about/`, a handwritten origin-and-lineage page. It says Patrick
Heusser and Markus Tuor developed the idea together, and Patrick later designed and built the
benchmark. It then situates Deep20Bench alongside directly linked prior work. The Apple
Entity-Deduction Arena paper is acknowledged prominently as the closest published predecessor
found during research. This editorial page is site source only: it does not enter the generated
benchmark dataset or any source run artifact.
