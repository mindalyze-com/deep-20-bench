# Deep20Bench documentation

Up to three models answer each Guesser question:

- The **Oracle** researches the question on the live web.
- The **Reviewer** answers again from the Oracle's evidence, without web access and without
  seeing the Oracle's answer. It runs only when the Oracle's answer is not UNKNOWN.
- The **Judge** decides only when the two disagree. It also sees the evidence but not the web
  or either earlier answer.

A reused answer (see below) skips all three, because it was already checked.

Standard and concise profiles answer with YES, NO, or UNKNOWN. The qualified profile adds
RATHER_YES and RATHER_NO for questions; guess validation still uses three answers.

What the roles may rely on depends on the policy:

- In standard and concise profiles, the Reviewer and Judge may use their own knowledge for
  narrow, settled facts, and must label it.
- New B-0003 definitions select `adjudication_policy: concise_knowledge_v1`. The Oracle,
  Reviewer, and Judge may all decide from evidence or other knowledge, labelled as `evidence`
  or `other`, with a short supporting statement. See
  [Five-answer experiment](five-answer-experiment.md#concise-evidenceknowledge-policy).
- Earlier qualified definitions used evidence-only review, optionally with limited Judge
  knowledge under `judge_stable_knowledge_v1`.
- Published edition 1.1 accepts several pinned release contracts; each run records which one
  it used.

Benchmark runs can reuse fully checked ASK answers from earlier games or the same game, with
their source recorded. Standalone commands always make new calls. Either way, the Guesser gets
only the final answer token, never evidence, cache details, or another component's private
state.

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
- [Project README](../README.md) - project overview and quick start.

## Experiment analyses

- [Akinator question-count comparison](analysis/akinator/README.md) - Akinator with Oracle
  and Codex answers, compared with saved LLM benchmark results.
- [Codex versus regular Oracle](analysis/codex-as-oracle/comparison.md) - subject results
  and model-ranking changes across eight direct-Codex experiments, with matched coverage.
- [Codex as Oracle](analysis/codex-as-oracle/README.md) - experiment helpers and individual
  model reports using fresh Codex answers.

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

When writing documentation, describe the live Oracle as the source of research evidence and
the Oracle/Reviewer/Judge pipeline as the source of the final answer tokens. The Fact
Builder/Fact Dossier is retired; references to it are obsolete. The ASK answer cache reuses
compatible finished answers under an explicit policy. It is different from provider prompt
caching, which only reuses computation for an identical prompt prefix.
