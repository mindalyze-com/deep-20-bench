# Deep20Bench documentation

Deep20Bench uses a live-web Oracle for research, a blind no-web Reviewer for independent
checking, and a blind no-web Judge for disputed answers. Both quality-control roles use
evidence first and have a labelled, narrow model-knowledge fallback for stable closed facts.
The Reviewer applies it conservatively because agreement bypasses the Judge. The former Fact
Builder and Fact Dossier design has been removed; it is not a supported architecture.

## Current documentation

- [Architecture](architecture.md) — current system boundaries, contracts, audit model, and
  benchmark/game integration.
- [Guesser output-contract recovery](guesser-output-contract.md) — scored format correction,
  isolation proof obligations, reliability metrics, reporting, and schema versions.
- [Homepage creation and publication](homepage-creation.md) — implemented independent
  publication package, scoring, static-site generation, and GitHub Pages architecture.
- [Benchmark control plane](../benchmark/README.md) — catalogs, typed API, scheduling,
  persistence, observation, result hierarchy, and console policy.
- [Game engine overview](../game/README.md) — package scope and links to its documentation.
- [Game engine concept](../game/Concept.md) — one-episode state machine, component independence,
  session history, caching, audit, and failure model.
- [Game usage](../game/Usage.md) — one-episode CLI/API behavior, history, adjudication,
  caching, artifacts, and failure semantics.
- [Oracle usage](../oracle/Usage.md) — Oracle/Reviewer/Judge flow, configuration, CLI and
  Python examples, metrics, generated files, failure behavior, and testing.
- [LLM caching](llm-caching.md) — project-wide evaluation rule and the current per-role caching
  decisions.
- [Post-hoc conversation evaluation](post-hoc-conversation-evaluation.md) — concept for blind
  and privileged LLM review of completed Guesser trajectories.
- [Project README](../README.md) — concise project overview and quick start.

## Current implementation status

Implemented:

- Versioned subject catalog.
- Configurable OpenRouter model and provider route.
- One independent live-web Oracle research request per factual question.
- Blind no-web review of every initial Oracle `YES` or `NO`, with no prior answer disclosed.
- Blind no-web Judge resolution of every Oracle–Reviewer disagreement; the Judge's
  `YES`, `NO`, or `UNKNOWN` is final.
- Mandatory decision-basis labels that distinguish evidence from the Reviewer or Judge's
  bounded stable-knowledge fallback.
- Strict `YES`, `NO`, or `UNKNOWN` result parsing for all three factual-adjudication roles.
- Scored Guesser `FORMAT_ERROR` recovery with typed contract-reliability reporting.
- Model-reported URL and excerpt evidence.
- Answer-only Guesser projection.
- Opt-in durable success and failure audit records behind the general `--verbose` flag.
- Concise console lifecycle logs.
- Guesser model integration.
- Game engine and turn limits.
- Strict LLM identity validation.
- Stateful visible Guesser history with OpenRouter sticky routing and prefix-cache telemetry.
- Optional game manifests and linked episode/call artifacts under the shared artifact policy.
- Typed model and benchmark catalogs.
- Single-model subject × iteration scheduling with typed failure continuation.
- Continuous hierarchical persistence, resumable live state, and integrity-protected results.
- Fully typed benchmark-run, model snapshot, subject, trial, aggregation, event, and artifact APIs.
- Aggregate YAML and Markdown reporting without outlier deletion.
- Typed agreement, disagreement, Judge-outcome, answer-change, question-type, and
  quality-control-cost reporting.

Documentation should describe the live Oracle as the source of research evidence and the
Oracle/Reviewer/Judge pipeline as the source of final factual answer tokens. References to
building, warming, validating, caching, or querying a persistent fact collection are obsolete.
Provider-side prompt caching may reduce repeated-prefix computation, but it is not a fact
collection or an answer cache.
