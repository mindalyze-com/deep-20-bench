# Deep20Bench documentation

Deep20Bench uses a live-web Oracle for research, a blind no-web Reviewer for independent
checking, and a blind no-web Judge for disputed answers. Standard and concise profiles use
YES, NO, and UNKNOWN. The qualified profile adds RATHER_YES and RATHER_NO for factual questions;
identity validation keeps three tokens. Every directional Oracle answer requires blind review,
and every exact-token disagreement requires the Judge.

Standard and concise Reviewer/Judge policies permit a narrow, labelled stable-knowledge
fallback. Qualified review is evidence-only; its Judge can use bounded knowledge only under
the explicit `judge_stable_knowledge_v1` policy. New B-0003 definitions select that policy,
while published edition 1.1 retains its separately pinned release configuration.

New benchmark executions can reuse fully adjudicated historical or same-game ASK answers with
source attribution. Standalone commands make fresh calls. In every case the Guesser receives
only the final token, never evidence, cache metadata, or another component's private state.

## Current documentation

- [Architecture](architecture.md) - current system boundaries, contracts, audit model, and
  benchmark/game integration.
- [Guesser output-contract recovery](guesser-output-contract.md) - scored format correction,
  isolation proof obligations, reliability metrics, reporting, and schema versions.
- [Homepage creation and publication](homepage-creation.md) - implemented independent
  publication package, scoring, static-site generation, and GitHub Pages architecture.
- [Publication package](../source/publication/README.md) - current edition contracts, commands,
  qualification rules, public schemas, and frontend behavior.
- [Benchmark edition design record](benchmark-editions-proposal.md) - the dated original design,
  with links to the implemented edition 1.0 and 1.1 contracts.
- [Five-answer experiment](five-answer-experiment.md) - qualified-answer meanings, rationale,
  Judge policies, prompt versions, and trial requirements.
- [Concise prompt experiment](concise-prompt-experiment.md) - the implemented three-answer
  experimental profile and diagnostic requirements.
- [Question-score confidence intervals](confidence-intervals.md) - repeated-trial estimand,
  stratified calculation, interpretation, and reporting boundary.
- [Benchmark control plane](../source/execution/benchmark/README.md) - catalogs, typed API, scheduling,
  persistence, observation, result hierarchy, and console policy.
- [Game engine overview](../source/execution/game/README.md) - package scope and links to its documentation.
- [Game engine concept](../source/execution/game/Concept.md) - one-episode state machine, component independence,
  session history, caching, audit, and failure model.
- [Game usage](../source/execution/game/Usage.md) - one-episode CLI/API behavior, history, adjudication,
  caching, artifacts, and failure semantics.
- [Oracle usage](../source/execution/oracle/Usage.md) - Oracle/Reviewer/Judge flow, configuration, CLI and
  Python examples, metrics, generated files, failure behavior, and testing.
- [LLM caching](llm-caching.md) - project-wide evaluation rule and the current per-role caching
  decisions, with dated route measurements.
- [Historical Oracle answers](oracle-history-cache.md) - benchmark-only historical and
  same-game reuse, matching, provenance, accounting, and isolation.
- [Custom domain](custom-domain-migration.md) - verified hosting state and deployment checks.
- [Project README](../README.md) - concise project overview and quick start.

## Proposals

- [Community-funded runs](community-funded-runs.md) - proposed funding rules and a dated
  provider assessment; no model-specific funding system is implemented.
- [Post-hoc conversation evaluation](post-hoc-conversation-evaluation.md) - proposed blind
  and privileged LLM review of completed Guesser trajectories; outside the benchmark score.

## Current implementation status

Implemented:

- Versioned subject catalog.
- Configurable OpenRouter model and provider route.
- Independent live-web research on cache misses, with one diversified recovery attempt for
  eligible retrieval failures.
- Blind no-web review of every directional Oracle answer, with no prior answer disclosed.
- Blind no-web Judge resolution of every exact-token Oracle-Reviewer disagreement.
- Strict profile-specific answer parsing and role-specific decision-basis validation.
- Benchmark-only historical and same-game ASK reuse with original evidence and provenance.
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
- Independent edition-scoped publication, v10 datasets, and a maintained edition 1 v9 export.

Documentation should describe the live Oracle as the source of research evidence and the
Oracle/Reviewer/Judge pipeline as the source of final factual answer tokens. References to
building or querying the retired Fact Builder/Fact Dossier are obsolete. The supported ASK
cache reuses compatible completed answers under an explicit policy; it is distinct from
provider prompt caching, which only reuses prefix computation.
