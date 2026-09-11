# Deep20Bench publication

Evidence may additionally carry `kind: source_summary`. The strict reader and public projection
retain this label and the full evidence text. The site displays it as a model-reported source
summary, outside quotation blocks. An omitted kind means quotation and preserves old serialized
data. This optional field is supported by both current and maintained v9 projections/schemas;
no release/cohort pin changes or live calls accompany this representation change.

The private artifact reader also supports `concise_knowledge_v1`, its two decision bases
(`evidence`/`other`), bounded supporting statements, and single-attempt `bounded_unknown`.
It validates role policy and the configured query target plus two bonus search calls (five
when the target is omitted). Concise Reviewer/Judge UNKNOWN decisions may retain valid evidence
indices and either decision basis with private support; earlier policies retain their stricter
UNKNOWN format. Support fields are accepted only for the concise policy
and are excluded from the public projection. The release decision below admits the accepted
policy revisions; the v9/v10 transcript projections remain unchanged.


Benchmark executions support [historical Oracle answer reuse](../../documentation/oracle-history-cache.md) under the explicit
`historical_ask_v1`, `same_episode_ask_v1`, and `same_execution_ask_v1` policies. The benchmark
owns lazy subject loading from verified original trial files and adds eligible completed games
from the current execution. The engine owns a private map for repeats within one game.
Reused ASK turns retain original evidence and marked source provenance, with no
new adjudicator calls or cost. Cache metadata never enters Guesser history. Standalone
commands keep fresh-call behavior. The publisher reports this provenance after execution.


The site publishes benchmark editions **1.1** (current, default) and **1** (previous) through
one application. Edition 1.1 has four directional question answers plus UNKNOWN; edition 1
has YES/NO/UNKNOWN. Guess validation remains three-token in both editions.
See [benchmark editions](../../documentation/benchmark-editions-proposal.md) and
[qualified answers](../../documentation/five-answer-experiment.md).

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

The edition registry and site configuration live in `config/publication.yml` (version 2).
`default_edition_id` names the current cohort. Machine IDs are strings `1.0` and `1.1`;
display labels are `1` and `1.1`. Edition identity is separate from artifact or dataset schemas.
Subject catalog `status: inactive` affects new benchmark scheduling only. Publication keeps
all registered identities and uses the cohort's explicit target IDs, so historical results
for inactive subjects remain eligible. Its subject identity hash excludes status, matching
the benchmark producer.
The Python core accepts and returns strict frozen Pydantic models. Filesystem discovery,
generated-data persistence, the Node build, and the atomic `docs/` replacement live only in
the CLI composition root. The frontend reads generated JSON; it does not parse YAML or
reimplement scoring.

The builder writes public JSON into a temporary staging directory. Generated data is not stored
under the handwritten site source. The development server reads the latest committed data from
`docs/`.

## Edition contracts

| Edition | Cohort | Benchmark | Subjects | Rounds per subject | Limit | Failure score |
| --- | --- | --- | --- | --- | --- | --- |
| 1.1 | `qualified-core-v1` | B-0003 | 10 explicit IDs | 3 | 40 | 41 |
| 1 | `core-v2` | B-0001 | 7 explicit IDs | 5 | 50 | 51 |

Discovery validates every discovered artifact before edition selection, including diagnostics.
Edition 1.1 additionally requires paired `qualified_v1` profiles, the declared base seed,
subject identity hashes, the declared game rules (category visibility, final-guess opportunity,
and consecutive violation limit), normalized Oracle and Validator configuration hashes, the Oracle
factual-contract hash, and the pinned
Guesser/Oracle/Reviewer/Judge/recovery/Validator prompt versions from one complete accepted
release contract. Retained call audits must
cover every invoked role and agree with the episode records. Changed prompts or subjects
require an explicit publication-definition decision; profile name alone cannot admit a run.
Execution `experimental` provenance is preserved. Execution official-mode rules are unchanged.
The publication label means the run qualified for its declared edition.
Configuration pins hash canonical JSON after parsing the publication's typed snapshots, which
expand omitted defaults; they are not hashes of raw YAML or unnormalized execution JSON.
The factual-contract pin matches the hash recorded by the execution manifest.

The Oracle configuration snapshot accepts the additive `adjudication_policy` setting. Missing
or `profile_default` preserves historical serialization and evidence-only qualified review.
`judge_stable_knowledge_v1` is valid only for qualified_v1 and permits labelled knowledge only
for the Judge, with no supporting evidence indices. The Reviewer remains evidence-only.
All four directional tokens are permitted for this Judge basis; UNKNOWN cannot use it.
Episode policy must match the manifest. On 8 September 2026 the user explicitly accepted the
new completed B-0003 results for edition 1.1. The primary contract now pins
`concise_knowledge_v1`, Oracle v17, Reviewer v12, Judge v15, the current subject descriptions,
and Validator v2. Three named revisions are also accepted: `judge-knowledge-evidence-context`
retains the completed GPT-6 Astra run's Oracle v12 and bounded Judge knowledge policy;
`concise-source-context-transition` retains the completed Gemini 3.8 Flash run's recorded
Oracle v16/v17 and Reviewer v11/v12 transition. `concise-property-scope-repair` retains
Claude Opus's original Oracle v16, Reviewer v10/v11, and Judge v13/v14 results alongside
its completed repair using Oracle v17, Reviewer v12, and Judge v15. These revisions list
the exact observed role-version combinations. On the same date, the user authorized repairs
of only Opus's one and Grok's three infrastructure-failed iterations, preserving all 56
previously scored results, including scored model losses.

`eligibility.accepted_revisions` contains strict, complete contracts with their own configuration,
factual-contract, and subject-identity hashes. A run must match one whole contract; pins cannot
be mixed across revisions. Each retained Oracle call must match one complete allowed prompt
combination. A missing or unlisted factual-contract hash still fails qualification, including
when prompt versions match. Full 30-trial coverage, integrity, role audits, game rules, seed,
and newest-qualified-run selection remain required. No execution ID is selected by hand.
Repaired runs enter the ranking only after all 30 trials are scoring eligible.

The accepted revisions are published in edition metadata and described on the Method page.
Adjudication and subject-description differences can affect the comparison; published runs
retain their actual settings and experimental provenance. This explicit publication decision
retains multiple Oracle prompt versions in the public run model's `prompt_versions` list;
the singular `prompt_version` is null for such runs and unchanged for single-version runs. It
does not make a mixed-contract run eligible as an execution-time answer-cache source. Future
unlisted revisions require another publication-definition decision.

These checks run only after execution. They add no model calls and do not change Guesser-visible
state, prompts, provider caching, answer reuse, or sessions.

Latest-run selection, scores, confidence intervals, costs, and efficiency normalization run
independently per edition. Never merge leaderboards or present an inter-edition score change
as model improvement. An edition with no qualified run publishes valid empty data and an
explicit empty state; diagnostics are not substitutes for completed release runs.

`data/editions.json` owns the default, document paths, and immutable run-to-edition mapping.
Each `data/editions/<id>/` directory contains `manifest.json`, `leaderboard.json`,
`repeat-averages.json`, `leaderboard.csv`, and `deep20bench-v10.json` with its schema.
Run, subject, and episode documents retain their existing global paths and now carry
`edition_id`. Split schema versions are manifest 2, leaderboard 4, repeat averages 2,
run 4, subject 2, episode 3; application-build remains 1.

`data/deep20bench-v9.json` and its maintained schema remain current for all selected standard
edition 1 data. v9 cannot represent qualified tokens or multiple editions. `legacy.py` is the
strict adapter; it rejects qualified datasets. Unversioned CSV/manifest/leaderboard/repeat
paths retain edition 1 for existing consumers; the GUI uses only edition-scoped documents.

Canonical pages use `/editions/<id>/`, with results, methodology, and data underneath.
Unversioned GUI links resolve to 1.1. Existing `/runs/...` links resolve their recorded edition.
The selector preserves the current result measure. On a detail page it matches the same model
ID, then subject ID; an episode switch stops at the destination subject. Missing counterparts
show a short explanation. About uses the same content in both editions; its edition-scoped
paths preserve the selection and share the canonical `/about/` URL. The selector keeps the
displayed edition selected and shows a loading state until navigation finishes. A native details dropdown shows only the selected version and Current/Previous status when
closed. Inside, ordinary links switch editions, followed by the selected edition's compact
settings, answer vocabulary, and What changed link. These settings replace the separate
page-wide metadata rows. Hovering an edition with a mouse or focusing its link with the keyboard
previews that edition's settings and comparison link without changing the selected edition.
The preview remains while moving into its settings, and resets when leaving or closing the panel.
Settings use the existing edition manifest loader; late preview responses cannot replace a newer choice.
The same disclosure works on phones, tablets, desktop, and without
JavaScript; every link and the trigger retain a 44-pixel touch target. The panel fits the
viewport and scrolls internally on short screens. After hydration, Escape restores trigger
focus, outside interactions close the panel, and navigation closes it. Pending navigation
keeps the displayed edition selected and prevents a second edition change.
The selector shares the top header row before Source at every screen width. Phones show
the version, status indicator, and chevron; the full status remains in the accessible name
and dropdown. Narrow phones use an icon-only Menu control. The dropdown aligns within the
viewport, and all controls keep their touch targets. Choices display `v.1.0` and `v.1.1`;
a lime indicator identifies the current edition. The selector panel stays dark, with a
subtle selected row and lime checkmark for either edition. A Current badge identifies the
latest edition; the compact settings and answer tokens below use the same dark palette.
Previous editions retain a small amber indicator. A compact, muted notice below the header identifies the
previous edition, including on direct detail links. Plain text links open the edition
comparison or switch to the current edition using the selector's same destination rules.
The notice is announced politely, works without JavaScript, and remains while a switch loads.
The result header uses content-driven height and
compact title/tab spacing. Data-load errors are separate from empty results.

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
3. independently compiles every declared edition and its strict public episode projection from
   `config/publication.yml`;
4. records separate UTC publication and application build times in typed public metadata;
5. writes `editions.json`, per-edition v10 JSON/schema/CSV and split documents, plus the
   maintained v9 edition 1 compatibility projection and schema;
6. builds the Vue application, statically renders both edition homepages and editorial pages, every
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
npm run --prefix source/publication/site test:unit
npm run --prefix source/publication/site test:ui:editions -- --workers=2
```

No credential or network access is needed once the locked Python and Node dependencies are
installed. The edition browser suite needs Playwright's Chromium and WebKit browsers. It
checks the dropdown on desktop and phones, touch targets, keyboard navigation, reloads, browser
history, slow loading, edition-specific downloads, and navigation without JavaScript.
The cross-browser script also includes the phone WebKit edition checks.

The browser uses typed public documents embedded in each statically rendered page for its first
hydration. It fetches one small run, subject, or episode document only when later navigation
needs it. Subject pages embed their run and subject documents so their aggregate result and
ordinary episode links exist in the initial HTML. The complete version 10 datasets and version 9
compatibility JSON remain downloads and are not imported into the
application bundle. Browser promise caching applies only to immutable public reporting files.
It cannot affect model requests, benchmark execution, or Guesser-visible state.

The build uses Vue server rendering with a memory-history router, then hydrates the same tree
with a web-history router in the browser. The homepage, eight editorial and result pages, and
every selected official run summary contain their real content and ordinary links in the
initial HTML. Charts and interactive controls start after hydration. There is no separate
fallback content tree or content-hiding script. Every prerendered page links its rendered
components' CSS in the initial HTML, using Vite's
SSR asset manifest. Route styles therefore apply before the first paint, even with delayed or
disabled JavaScript. Hydration reuses the styled content without a page-wide loading overlay.
The asset manifest is build-only and is removed from the generated site.

Chart containers keep their declared height; the shared ECharts module downloads and SVG
initialization starts only when a container is within 300 pixels of the viewport.
Failed downloads show a reload notice while static results
and links remain available. Offscreen
data-only updates are retained until the chart returns; already-rendered SVGs still follow
viewport resizes. Data refreshes do not resize an unchanged chart, and cached routes reconnect
their observers when activated. The document preloads the two locally bundled normal Latin
fonts used above the fold; Vite resolves their content-hashed URLs for the configured base path.
Delayed route scroll restoration stops when the visitor has already moved the page, so early
scrolling can reveal and load charts without being reset by a later restoration attempt.

The generated pages have route-specific titles, descriptions, social metadata, canonical URLs,
and accurate publication modification times in `sitemap.xml`. Every page includes `og:site_name`
from the configured site title. The homepage includes separate Dataset and WebSite JSON-LD
nodes, using the configured site identity and canonical URL, `https://deep20bench.com/`.
The Dataset node identifies its CC BY 4.0 license using the same canonical license URL as the
Data page and footer. The Data page distinguishes reusable result data from source-available
software. Subject titles use the full model name and setting followed by the subject, without
repeating the generic results label. Their H1 includes both model and subject identity.
Hosting the homepage at this domain root supports Google's site-name requirements.
The compiler's typed route manifest is also published as `data/routes.json`.
Vite bundles its page metadata into the client, so initial HTML, hydration, and client navigation
use the same titles, descriptions, social metadata, canonical URLs, and indexability rules
without an extra metadata request. Short navigation labels never write document metadata.
Homepage Dataset and WebSite JSON-LD use one shared generator for static HTML and browser
navigation. Switching editions updates dataset identity, settings, and download URLs; leaving
the homepage removes that markup. Late data loads cannot restore a previous page's markup.
The sitemap contains the homepage, editorial URLs, every selected official run,
and every subject summary. These pages do not emit a robots meta tag, so search engines use their
default `index, follow` behavior. Episode evidence pages remain outside the sitemap and emit
`noindex, follow`; aliases and downloads remain outside the sitemap. The generated 404 page also
emits `noindex, follow`.

This repository publishes through GitHub Pages at `https://deep20bench.com/`, with base path `/`.
The shared HTML template loads the optional Umami tracker asynchronously from
`https://umami.me.mindalyze.com/script.js`. Tracking is limited to `deep20bench.com`, so local
previews do not record visits. The application never awaits or calls the tracker. Unavailable
analytics must leave rendering and navigation working without a visitor-facing notice.
The tracker handles failed event requests internally; browsers may still show network failures
in developer tools. Do not suppress unrelated application errors to hide analytics failures.

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

Execution `prompt_profile` metadata accepts `standard`, `concise_v1`, and `qualified_v1`.
Revised profiles cannot enter the standard edition 1 leaderboard, regardless of subject and
trial coverage. Paired qualified profiles can enter edition 1.1 only when they satisfy its
explicit release contract. Standard historical artifacts omit this metadata and retain their
existing treatment.

A run reaches the official leaderboard when its signed files pass integrity validation, it is
terminal, it contains the active subject set, and every subject has all configured completed
trials (three for edition 1.1, five for edition 1). A completed model failure remains a valid scored
trial. An infrastructure-failed or missing trial does not count as completed. The run remains
ineligible until an explicitly requested resume or repair completes it; publication never
starts that operation or qualifies reduced coverage.

Qualification requires the run's recorded question limit to match the active cohort;
otherwise it reports `question_limit_mismatch`. The historical cohort remains at 50 questions.
New games default to 40 and must enter a separate matching cohort before publication. Historical
scores and failure penalties are never recomputed with the new default.

Historical edition 1 qualification does not compare the run's benchmark version, seed, subject catalog hash,
`publication_eligible` flags, or immutable model configuration with the current catalog.
The published model metadata comes from the selected signed run. When several runs
qualify for one configured model ID, publication selects the run with the greatest typed
completion timestamp. It never selects by score, and a latest-timestamp tie fails the build.
Cache status and cache metrics are reporting-only and never affect qualification.

Only selected current-protocol runs and their models enter the leaderboard, public run details,
and generated routes. Historical protocol artifacts live outside `runs/` under `archive/` and
are never parsed by the publication compiler. Non-qualifying current runs remain under `runs/`
but are omitted from the public projection. The public JSON shape emits an empty `lab_runs`
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
averages gives every subject equal weight. Both cohorts use equal repetition counts, so this is also the average of all 30 penalized
trial values in edition 1.1, or all 35 in edition 1. Infrastructure
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
prediction range for individual trials. Historical ASK reuse can share adjudicated answers
across trials. For cached runs, interpret the interval conditional on the recorded policy
and source inventory; this estimator does not correct for covariance from shared answers.

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
distance rank. Removing a model that sets a score or cost bound changes the scale for other
models and can change their distance ranks. No underlying benchmark result changes; only
the cohort normalization changes.

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
Guesser questions or guesses beside the final adjudicated token. Standard ASK and all GUESS
turns use `YES`, `NO`, or `UNKNOWN`; qualified ASK also permits `RATHER_YES` and `RATHER_NO`.
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
protocol 9. Its source reader has no legacy adapter, schema downgrade, or per-run exclusion path.
The separate v9 export adapter preserves public-download compatibility. Every
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

Same-game sources use the optional `scope: same_episode` public variant. The transcript names
the original turn in that game and provides a jump button, alongside the original evidence.
Internal call IDs remain private. This variant is supported by both v10 and v9.

Answers reused across games within one execution use `scope: same_execution`. The transcript
labels the earlier game in the current benchmark run and shows its original trial and turn.
This uses the historical source allowlist and is supported by both v10 and v9; private paths,
contract hashes and provider call IDs remain excluded.
