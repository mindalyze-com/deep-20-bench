# Deep20Bench project conventions

## Required references

Read and follow the relevant detailed specification before changing these areas:

- Prompts, model-visible history, adjudication, provider requests, retries, sessions, tools,
  artifacts, reporting, or component boundaries: `documentation/architecture.md` and
  `documentation/guesser-output-contract.md`.
- Provider prompt caching or any response/application cache: `documentation/llm-caching.md`.
- Benchmark execution, persistence, observation, logging, or results:
  `source/execution/benchmark/README.md`.
- Game behavior, history, failures, or standalone artifacts: `source/execution/game/Concept.md`
  and `source/execution/game/Usage.md`.
- Oracle, Reviewer, Judge, credentials, or standalone audits:
  `source/execution/oracle/Usage.md`.
- Publication or generated site output: `source/publication/README.md` and
  `documentation/homepage-creation.md`.

## Publication deployment

- `deep20-publication build` regenerates the tracked GitHub Pages site in `docs/`. Any commit
  that changes publication source or generated output must include the complete regenerated
  `docs/` tree.
- Treat `docs/data/deep20bench-v9.json` as a long-lived external compatibility URL. If a newer
  publication schema becomes primary, keep publishing this path and update it with all current
  data that can be represented by the v9 contract; do not leave it frozen, rename it, or remove
  it merely because v10 or a later schema exists. Keep its companion v9 schema available and
  document any data that cannot be represented in v9.
- Unless the user explicitly requests it in the current request, do not commit, push, tag,
  release, open a pull request, or publish externally. Treat requests to run or publish the
  publication as local `docs/` generation. Never push feature or development branches; when
  explicitly requested, push only the final revision on `main`.
- Never create, save, or deploy a Codex Sites project, `.openai/hosting.json`, or other Sites
  configuration for this repository.

## Long benchmark launches

- On macOS, run full benchmarks in detached `screen` sessions with
  `nohup /usr/bin/caffeinate -i ... </dev/null >>run.log 2>&1 &`. Do not attach them to Codex
  execution sessions.
- Verify `screen`, `caffeinate`, the benchmark process, canaries, manifest, and first turn. No
  live process means interruption. For a clean run, remove only its exact artifacts and use a
  new ID.

## Highest-priority invariant: Guesser isolation

- The Guesser is the model under test. Its information boundary overrides convenience,
  observability, performance, caching, and reporting.
- Guesser-visible state is limited to fixed system instructions, the broad category, its own
  structured actions, final `YES`/`NO`/`UNKNOWN` tokens, and the fixed `FORMAT_ERROR` after its
  own invalid output. The initial versioned variation token derives only from base seed and
  trial number, varies by trial, stays paired across subjects and models, appears only in
  `BEGIN`, and contains no subject, execution, model, provider, component, or private-state ID.
- `FORMAT_ERROR` is the only contract-repair channel. It is canonical, versioned,
  subject-independent, and identical for every violation. It says only that the public contract
  failed without semantic adjudication, consumed one turn, and must be retried using its
  displayed wire formats. It never includes malformed output, validation or parser details,
  correctness feedback, subject or adjudicator data, evidence, or private state.
- The Guesser must not access any other component's conversation, prompt, reasoning, response,
  evidence, subject state or identity, tools, traces, logs, files, or private state, directly or
  through sessions, caches, metadata, errors, retries, artifacts, or reports.
- Preserve the blind call projections: Oracle gets trusted subject plus current question;
  Reviewer and Judge get those plus numbered Oracle evidence, but no prior answer, trace,
  episode history, or web access; Validator gets trusted subject plus current guess. Only the
  final protocol answer token returns to the Guesser.
- Oracle `UNKNOWN` is final. Oracle `YES` or `NO` requires independent Reviewer adjudication.
  Agreement is final; disagreement, including Reviewer `UNKNOWN`, requires the blind Judge.
  Required Reviewer or Judge failure is infrastructure failure, never an Oracle fallback.
- Empty, `length`, or other non-`stop` Guesser output without a complete structured action is
  invalid model output, not infrastructure failure. Before the limit it creates one typed,
  counted violation and appends only `FORMAT_ERROR`; the consecutive-violation limit ends in a
  scoring-eligible model failure. The final guess-only opportunity terminates without retry or
  extra count. Raw malformed output never enters visible history.
- Combine privileged data only in post-call audits and final reports, never in later Guesser
  requests or state. Changes to prompts, history, provider requests, sessions, caches, tools,
  audits, reports, retries, or wiring must review this invariant and test the visible projection.

## General implementation

- Treat every model and provider response as untrusted and validate it locally.
- Reuse or extend an existing source of truth when reasonable. Derive repeated schemas,
  constants, formats, and behavior from one canonical definition.
- Use WebP for raster assets unless tooling or a format-specific requirement prevents it.
- Write in English unless the user requests another language. Use hyphens, not em dashes.

## Console logging

- Follow the detailed console contract in `documentation/architecture.md`.
- Composition roots configure logging. Component libraries do not configure handlers or emit
  routine `INFO`; their diagnostics use the component logger at `DEBUG`.
- Emit one timestamped `INFO` result per successful major operation and one stable-coded failure.
  Never print prompts, raw responses, evidence, subject details, credentials, headers,
  environment values, or call IDs. Permitted standalone verbose audits and benchmark error
  output remain isolated artifacts, not console output.

## Artifact ownership

- Libraries never choose artifact paths or open files. They persist only through injected typed
  sinks and remain usable with in-memory or null sinks.
- The benchmark root owns persistence. Follow the referenced `error-outputs.jsonl` and public
  snapshot contracts; neither may enter model requests, caches, retries, or later trials.
  Benchmark mode creates no per-trial `audit/` tree or general raw logs.
- Standalone commands retain auxiliary artifacts only through `RunArtifactPolicy` and
  `--verbose`. Artifact policy is reporting-only and never changes requests, prompts, visible
  history, sessions, caches, adjudication, scoring, or typed results.

## LLM caching

- Every LLM-backed feature must explicitly evaluate provider prompt caching, even when the
  decision is disabled. Follow `documentation/llm-caching.md` and re-evaluate when prompts,
  models, routes, pricing, provider policy, or expected reuse changes.
- Prompt-prefix caching may reuse computation for an exact prefix but never an earlier Oracle,
  Reviewer, Judge, or Validator answer or extra state. Never add application or provider
  response caching.
- Keep safe stable prefixes, measure actual cache tokens, discounts, latency, and cost, and
  record route-specific thresholds and pricing. Do not pad without favorable measured
  break-even or claim unmeasured savings.

## Credentials

- Local provider credentials live only in ignored YAML files under `private/`. OpenRouter uses
  `private/openrouter.yml` with `api.api_key`; `private/openrouter.yaml` remains supported.
- Environment variables have priority; OpenRouter uses `OPENROUTER_API_KEY`. Keep files
  owner-only and covered by `/private/`. Never print, audit, publicly hash, or expose credential
  values in exceptions; provider request audits remain credential-free.

## Typed Python interfaces

- Public APIs and cross-component boundaries use concrete, strict, frozen Pydantic models.
  Domain variants use enums and discriminated unions; benchmark, model, execution, subject,
  trial, episode, call, and event identifiers use explicit types.
- Do not expose `Any`, `dict[str, Any]`, untyped dictionaries, or ad-hoc tuples across those
  boundaries. Dictionaries are limited to JSON/YAML serialization and external provider
  protocols; arbitrary provider JSON uses an explicit recursive JSON value type.
- Validate deserialized data into its declared model before business logic. Keep serialization
  at outer boundaries, and pass strict static type checks for new or modified boundary code.
