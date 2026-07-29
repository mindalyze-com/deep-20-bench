# Deep20Bench publication

`deep20-publication` is the independent, deterministic post-processor for the Deep20Bench
homepage. It validates signed benchmark artifacts, decides official eligibility, selects the
latest qualified run for each model, calculates the declared raw and B20 display
scores, emits a versioned public JSON/CSV
projection, and
builds the static GitHub Pages site.

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
└── site/                        independent Astro + TypeScript + Observable Plot frontend
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
4. writes `publication/site/public/data/deep20bench-v3.json` and `leaderboard.csv`;
5. prerenders execution, subject, and episode routes together with the main site;
6. rewrites generated URLs to portable, depth-aware relative files so the same output works on
   GitHub Pages and when `docs/index.html` is opened directly;
7. runs strict Astro/TypeScript checks and the static build;
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
but are omitted from the public projection. The version 3 JSON shape emits an empty `lab_runs`
collection. Tampered or malformed discovered input still fails the build.

The score uses exact decimal arithmetic:

```text
failure penalty = question limit + 1
trial value = counted questions on success, otherwise the failure penalty
subject score = mean of that subject's trial values
model score = mean of all subject scores
```

The exact penalized-question value remains canonical: lower is better, ranking uses the
unrounded value, and exact ties remain joint ties. The publication compiler additionally emits
the versioned B20 display score:

```text
target R = 20
failure penalty F = question limit + 1
B20 = R × (F - penalized questions) / (F - R)
```

B20 is linear and higher is better. Twenty B20 points means exactly twenty penalized questions;
scores above twenty beat the target, scores below twenty use more questions, and the scoring
floor is zero. Infrastructure failures remain unscored. The website leads with B20 while run,
subject, and episode details preserve counted and penalized questions.

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
trials, and counted-turn penalties as an independent reliability aspect. The question total
already includes those penalties, so publication does not alter B20 again.

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
