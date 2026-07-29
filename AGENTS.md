# Deep20Bench project conventions

## Publication deployment

- `deep20-publication build` generates the static GitHub Pages site in `docs/`.
- Do not create, save, or deploy a Codex Sites project for this repository.
- Do not add `.openai/hosting.json` or other Sites deployment configuration.
- Treat requests to run or publish the publication as local `docs/` generation unless the user
  explicitly names another destination.

## Highest-priority benchmark invariant: Guesser isolation

- The Guesser is the model under test. Preserving the integrity of its information boundary is
  the project's highest priority and overrides convenience, observability, performance,
  caching, and reporting concerns.
- The Guesser may receive only its fixed system instructions, the intentionally disclosed broad
  category, an initial opaque variation token derived solely from the benchmark base seed and
  trial number, its own prior structured actions, the adjudicated `YES`, `NO`, or `UNKNOWN`
  tokens that the game explicitly returns, and the fixed protocol-defined `FORMAT_ERROR` event
  immediately after its own invalid structured output.
- `FORMAT_ERROR` is the only permitted contract-repair channel. It must be canonical,
  versioned, subject-independent, and identical for every violation. It may state only that the
  immediately preceding response failed the public structured-action contract, was not
  semantically adjudicated, consumed one counted turn, and must be retried using the displayed
  public wire formats. It must never include the malformed output, a parser detail, a dynamic
  validation error, correctness feedback, subject data, adjudicator data, evidence, or private
  state.
- The variation token is model-visible sampling control, not subject metadata. It must change on
  every repeated trial number, remain paired across subjects and models, appear only in the
  initial `BEGIN` event, use a versioned subject-independent derivation, and never incorporate
  a subject, target, execution, model, provider, Oracle, Reviewer, Judge, Validator, evidence,
  or private-state identifier.
- The Guesser must never access an Oracle, Reviewer, Judge, Guess Validator/verifier, engine,
  audit, or other component's conversation, prompt, hidden reasoning, raw response, evidence,
  citations, explanation, subject snapshot, canonical identity, aliases, description, reference
  URL, provider trace, tools, search results, logs, files, or other private state.
- Enforce the boundary against indirect channels as well as direct prompt construction,
  including shared session state, prompt-cache namespaces, response/application caches,
  metadata, error details, retries, report generation, and future reuse of run artifacts.
- Oracle calls receive only the trusted subject snapshot and the current Guesser question.
  Reviewer and Judge calls each receive only the trusted subject snapshot, current question,
  and numbered Oracle evidence excerpts. Neither receives the Oracle answer, Reviewer answer,
  explanation, provider trace, search process, or episode history; neither has web access.
  Guess Validator calls receive only the trusted subject snapshot and the current structured
  guess. The only adjudicator information permitted to flow back to the Guesser is the final
  protocol-defined answer token.
- An Oracle `UNKNOWN` bypasses review and is final. Every Oracle `YES` or `NO` requires an
  independent Reviewer decision. Agreement is final; every disagreement, including Reviewer
  `UNKNOWN`, requires the blind Judge, whose `YES`, `NO`, or `UNKNOWN` is final. A required
  Reviewer or Judge failure is an infrastructure failure and must never fall back to an
  unchecked Oracle answer.
- An invalid Guesser output is not an Oracle, Reviewer, Judge, or Guess Validator call. A
  Guesser provider call that ends without a completed structured action (`length` finish, empty
  output, or another non-`stop` finish) is classified as invalid Guesser output and attributed
  to the model under test, not to infrastructure. Before the question limit, an invalid output
  creates a typed contract-violation turn, consumes one counted turn, appends the fixed
  `FORMAT_ERROR`, and continues; once the policy's consecutive contract-violation limit is
  exhausted it terminates as a scoring-eligible model failure. On the final guess-only
  opportunity it creates the typed violation and terminates without another retry or additional
  count. Raw malformed output is never appended to Guesser-visible history.
- Durable audits and final reports may combine privileged component data only after the relevant
  model calls. They must never be injected into a later Guesser request or reused as Guesser
  conversational state.
- Every change touching prompts, message history, provider requests, sessions, caches, tools,
  auditing, reports, retries, or component wiring must explicitly review this isolation
  invariant and add or update tests that prove the Guesser-visible projection remains limited
  to the permitted data.

## Reuse before duplication

- Before adding an implementation, look for an existing source of truth. Reuse or extend it
  when reasonable; derive repeated schemas, constants, formats, and behavior from one canonical
  definition instead of copying them.

## Writing style

- Use short, simple, neutral language. Avoid marketing language, hype, and exaggeration.

## Console logging

- Emit one concise `INFO` result log per successful major operation, not start/completion pairs
  or verbose implementation traces.
- Prefix every console log with a local timestamp formatted as
  `YYYY-MM-DD HH:MM:SS.mmm`.
- Log an Oracle call's original user question on its result line, JSON-escaped so multiline
  input remains one physical console line.
- Emit immutable run, episode, target, policy, model, and provider context once in a run header,
  not on each component call.
- Include the final answer, web-search count, evidence count, prompt-cache reads/writes, LLM
  latency, and LLM cost on each result line.
- Log failures once with a stable error code and any available model, search, latency, and cost
  metadata.
- Omit call identifiers from console logs. Standalone verbose audits may retain them; benchmark
  mode discards call-level records after typed in-memory processing except for the isolated
  error-output artifact defined below.
- Never print rendered LLM prompts, system instructions, raw model responses, evidence
  excerpts, citation annotations, subject descriptions, credentials, headers, or environment
  values to the console. Standalone verbose mode may retain those details in its durable audit;
  benchmark mode retains error completions only in the isolated private artifact below.
- Component libraries do not configure logging and do not emit routine `INFO` result lines.
  Diagnostics, when needed, use their component logger at `DEBUG`. The benchmark and standalone
  CLI composition roots configure their own handlers and levels.

## Artifact ownership

- Libraries never choose artifact paths or open files. They persist only through injected,
  typed sink protocols and remain usable with in-memory or null sinks.
- The benchmark control plane continuously persists manifests, live state, progress events,
  typed trial/subject/model/benchmark results, and reports. In benchmark mode, component calls
  and episode events pass through a typed sink and are discarded after their result and metrics
  have been incorporated. If a provider or structured-output attempt produces textual output
  that is discarded because of an error, the benchmark composition root must retain the full
  completion and attempt metadata in a signed, owner-only per-trial `error-outputs.jsonl`.
  This diagnostic artifact must exclude prompts, messages, trusted subject state, full provider
  responses, evidence annotations, and hidden reasoning; it must never be read into any model
  request, cache input, retry message, report body, or later trial. Benchmark mode must not
  create per-trial `audit/` directories or general raw call logs.
- Standalone `deep20 game play` and `deep20 oracle ask` commands remain composition roots. They
  may choose paths and retain auxiliary artifacts behind their shared `RunArtifactPolicy` and
  `--verbose` flag.
- Artifact policy is reporting-only and must never alter provider requests, prompts,
  Guesser-visible history, sessions, cache namespaces, adjudication, scoring, or typed results.

## LLM caching

- Every LLM-backed feature must explicitly evaluate provider-side prompt caching during design
  and review, even when the outcome is to leave caching disabled.
- Distinguish prompt-prefix caching from application/response caching. Prompt caching may reuse
  provider computation for an exact input prefix; it must not reuse an earlier Oracle,
  Reviewer, Judge, or Validator answer or add conversational state.
- Keep stable instructions, schemas, tool definitions, and other behavior-preserving context
  before variable input when doing so improves cache eligibility without weakening trust
  boundaries.
- Measure actual input tokens, cache-read tokens, cache-write tokens, cache discounts, cost, and
  latency before claiming savings. Record the caching decision and the model/provider-specific
  thresholds and write/read pricing.
- Do not lengthen a prompt solely to cross a cache threshold unless a measured break-even
  analysis shows lower total benchmark cost without changing behavior.
- Re-evaluate the decision when the prompt, model, provider route, pricing, cache policy, or
  expected request-reuse pattern changes.

## Credentials

- All components load local provider credentials from ignored YAML files under `private/`.
  OpenRouter uses `private/openrouter.yml` with `api.api_key`; the existing
  `private/openrouter.yaml` spelling is also supported.
- Environment variables remain the highest-priority override for CI and temporary execution.
  OpenRouter uses `OPENROUTER_API_KEY`.
- Credential files must remain covered by the repository's `/private/` ignore rule and should
  use owner-only file permissions.
- Never print, audit, hash into public metadata, or include credential values in exceptions.
  Provider request audit records must remain credential-free.

## Typed Python interfaces

- Every public API and cross-component Python interface accepts and returns concrete typed
  Python objects.
- Use strict, frozen Pydantic models for domain objects, requests, results, events, audit
  records, manifests, execution state, summaries, failures, and artifact references.
- Do not expose `Any`, `dict[str, Any]`, untyped dictionaries, or ad-hoc tuples across component
  boundaries. Use enums and discriminated unions for variants and terminal states.
- Use explicit types for benchmark, model, execution, subject, trial, episode, call, and event
  identifiers.
- Dictionaries are allowed only at explicit JSON/YAML serialization boundaries and external
  provider protocol boundaries. Arbitrary provider JSON uses an explicit recursive JSON value
  type rather than `Any`.
- Validate deserialized data into its declared model before it enters application logic.
  Business logic operates on typed objects; serialization happens only at the outer boundary.
- New and modified boundary code must pass the repository's strict static type checks.
