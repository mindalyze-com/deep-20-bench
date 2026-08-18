# Oracle usage

The `deep20-oracle` package answers one yes/no question about one configured subject. It makes
one live-web research attempt and, for a retrieval-related failure, one independent diversified
attempt. It blind-reviews every resulting `YES` or `NO` without web access and uses a separate
blind Judge only when those decisions disagree. It writes the complete typed research and
adjudication audit before returning. Reviewer and Judge use evidence first and have a labelled,
narrow model-knowledge fallback for stable closed facts. The Reviewer applies it conservatively
because agreement bypasses the Judge.

Run the examples below from the repository root.

## Prerequisites

- Python 3.14.6
- `uv`
- An OpenRouter API key with an appropriate spending limit

Install the workspace:

```bash
uv sync
```

For local use, put the credential in the ignored `private/openrouter.yml` file:

```yaml
api:
  api_key: your-openrouter-key
```

The existing `private/openrouter.yaml` spelling is also supported. If both files exist,
`openrouter.yml` takes precedence. `OPENROUTER_API_KEY` overrides either file for CI and
one-off execution.

The key must not be stored in ordinary configuration, logs, audit records, or committed files.
The entire `/private/` directory is Git-ignored; credential files should use owner-only
permissions.

## Configuration

The default configuration is `config/oracle.yaml`:

```yaml
gateway: openrouter
model: openai/gpt-5.6-luna
provider: openai
reasoning_effort: medium
allow_fallbacks: false
parallel_search: true
max_search_results: 5
max_output_tokens: 4096
timeout_seconds: 120
recovery:
  max_elapsed_seconds: 300
  max_request_attempts: 8
  no_result_retries: 1
  invalid_output_retries: 1
reviewer:
  gateway: openrouter
  model: google/gemini-3.5-flash-lite
  provider: google-ai-studio
  reasoning_effort: medium
  allow_fallbacks: false
  max_output_tokens: 4096
  timeout_seconds: 120
  recovery: {max_elapsed_seconds: 300, max_request_attempts: 8, no_result_retries: 1, invalid_output_retries: 1}
judge:
  gateway: openrouter
  model: anthropic/claude-opus-5
  provider: openrouter-auto
  provider_routing: automatic
  reasoning_effort: medium
  allow_fallbacks: true
  token_limit_parameter: max_tokens
  max_output_tokens: 4096
  timeout_seconds: 120
  recovery: {max_elapsed_seconds: 300, max_request_attempts: 8, no_result_retries: 1, invalid_output_retries: 1}
```

Configuration fields:

| Field | Meaning |
| --- | --- |
| `gateway` | Currently fixed to `openrouter`. |
| `model` | Exact OpenRouter provider/model slug; dynamic selectors are rejected. |
| `provider` | Requested OpenRouter provider route, or `openrouter-auto` for automatic routing. |
| `provider_routing` | `exact` by default, or `automatic` to let OpenRouter select the backend. |
| `reasoning_effort` | Reasoning effort passed to the selected model. |
| `allow_fallbacks` | Whether OpenRouter may route to a fallback endpoint. |
| `token_limit_parameter` | Request field used for the output ceiling. The default is `max_completion_tokens`; use `max_tokens` when the selected endpoints require it. |
| `parallel_search` | Whether OpenRouter web search explicitly uses the lower-cost Parallel engine. |
| `max_search_results` | Maximum results available to web search, from 1 to 10. |
| `max_output_tokens` | Provider output ceiling, from 128 to 65,536. |
| `timeout_seconds` | Request timeout, from 1 to 600 seconds. |
| `recovery` | Typed, bounded retry policy for transient provider failures and invalid output. |
| `reviewer` | No-web route that blindly checks every Oracle `YES` or `NO`. |
| `judge` | No-web route whose answer is final when Oracle and Reviewer disagree. |

The default roles deliberately use three model families: OpenAI for research, Google for
review, and Anthropic for disputed-case judgment. The Oracle and Reviewer use exact backend
routes. The Judge keeps the exact `anthropic/claude-opus-5` model but lets OpenRouter select an
available backend. Its route sends `max_tokens` so automatic routing can use endpoints that
support the Judge's structured-output contract. The resolved Judge provider is retained in
typed results for later reporting.

A run manifest freezes the complete configuration and rejects later calls that try to reuse
the same run ID with a different configuration. This validation happens before the provider
request, so an incompatible run ID does not incur model, search, or cache-write cost.

The adapter deliberately does not send OpenRouter's `provider.require_parameters` filter.
OpenRouter's web-search server tool runs at the router layer; enabling that endpoint filter
causes otherwise-capable OpenAI endpoints to be rejected before the server tool can run.
Exact model and provider routing are still enforced through `model`, `provider.only`, disabled
fallbacks by default, resolved-model validation, and required web-search telemetry.

## Research outcomes and recovery

Each research attempt returns an answer, evidence, a classified outcome, and one to eight exact
query strings reported by the model. The query strings are bounded audit data. They are not
verified against provider telemetry and are labelled `model_reported`; provider telemetry
separately records only the number of web-search requests.

The outcome is one of `answered`, `no_results`, `irrelevant_results`,
`insufficient_coverage`, `conflicting_sources`, `ambiguous_question`, or
`open_world_not_provable`. The first four non-answer outcomes trigger exactly one recovery
attempt. The recovery receives only the same trusted subject and current question. It uses a
fixed prompt with alternative strategies by question family, a distinct session, and a
distinct prompt-cache namespace. It never receives the first query, answer, evidence, outcome,
trace, or provider response.

The primary prompt permits a reliable direct counterfact. For example, an authoritative death
date directly supports `NO` for "Is this person currently alive?" A bare profession or role is
interpreted as a documented professional or recognized biographical role, not any incidental
appearance or activity.

`ambiguous_question` and `open_world_not_provable` are genuine final `UNKNOWN` outcomes and do
not invoke recovery. Two retrieval failures on a deterministic closed or temporal fact produce
the infrastructure error `oracle_research_exhausted`; they do not silently become a factual
`UNKNOWN`. Repeated retrieval failure for an open-world or other non-closed family remains a
classified final `UNKNOWN`. Reviewer and Judge still receive only a decisive result's trusted
subject, original question, and numbered evidence.

## Subject catalog

Subjects live in `config/subjects.yaml`:

```yaml
version: 1
subjects:
  T-0001:
    target_id: T-0001
    canonical_name: Albert Einstein
    aliases:
      - Einstein
    entity_type: person
    description: >-
      Albert Einstein, the theoretical physicist identified by Wikidata Q937.
    reference_url: https://en.wikipedia.org/wiki/Albert_Einstein
```

Target IDs use `T-NNNN`. The description should identify the exact entity without becoming a
general-purpose biography. Duplicate YAML keys, mismatched IDs, malformed URLs, duplicate
aliases, and unexpected fields are rejected.

## Command-line usage

Ask a configured subject:

```bash
uv run deep20 oracle ask T-0001 \
  "Was this person born before 1900?" \
  --run-id development-001
```

Override the configuration or catalog:

```bash
uv run deep20 oracle ask T-0001 \
  "Did this person receive a Nobel Prize?" \
  --run-id development-001 \
  --config-path config/oracle.yaml \
  --catalog-path config/subjects.yaml
```

Override model behavior for one call without editing the YAML file:

```bash
uv run deep20 oracle ask T-0001 \
  "Was this person born in Europe?" \
  --run-id model-comparison-001 \
  --model openai/gpt-5.6-luna \
  --reasoning-effort medium \
  --provider openai \
  --no-allow-fallbacks \
  --parallel-search \
  --max-search-results 3 \
  --max-output-tokens 1000 \
  --timeout-seconds 90
```

Available per-call overrides are `--model`, `--reasoning-effort`, `--provider`,
`--allow-fallbacks`/`--no-allow-fallbacks`,
`--parallel-search`/`--no-parallel-search`, `--max-search-results`,
`--max-output-tokens`, and `--timeout-seconds`. The effective values - not just the base
configuration - are frozen in the run manifest. Reusing a run ID with different overrides is
rejected. These flags override the research Oracle only; Reviewer and Judge routes remain the
independently configured nested sections of the selected YAML file.

Parallel search is enabled by default. It keeps the same OpenRouter web-search server-tool
contract while using Parallel rather than the provider's automatic/native search engine.
Search ranking and excerpts can differ between engines, so compare them with distinct run IDs:

```bash
uv run deep20 oracle ask T-0001 \
  "Was this person born before 1900?" \
  --run-id parallel-search

uv run deep20 oracle ask T-0001 \
  "Was this person born before 1900?" \
  --run-id native-search \
  --no-parallel-search
```

At the time this option was introduced, OpenRouter listed Parallel server-tool searches at
$0.001 per request and passed native provider search pricing through separately. Model token
costs remain additional. Check the
[OpenRouter web-search documentation](https://openrouter.ai/docs/guides/features/server-tools/web-search)
for current pricing before relying on projected savings.

The command prints the complete `OracleCall` as JSON on standard output. One concise run-context
log is written to standard error:

```text
2026-07-26 22:15:01.100 INFO oracle.run run=development-001 target=T-0001 model=openai/... provider=openai
```

Multiline questions are JSON-escaped onto one console line. The console never includes the
rendered prompt, raw response, evidence excerpts, annotations, subject description, or API key.

## Python API

```python
from pathlib import Path

from deep20_oracle import (
    Oracle,
    OracleRequest,
    RunAuditWriter,
    load_openrouter_api_key,
    load_oracle_config,
    load_subject_catalog,
)
from deep20_oracle.openrouter_provider import OpenRouterOracleProviderSet

root = Path.cwd()
config = load_oracle_config(root / "config/oracle.yaml")
catalog = load_subject_catalog(root / "config/subjects.yaml")

audit = RunAuditWriter(
    root / "runs",
    config=config,
    subject_catalog_hash=catalog.content_hash(),
    repository=root,
)

with OpenRouterOracleProviderSet(load_openrouter_api_key(root), config) as providers:
    oracle = Oracle(
        providers.oracle,
        providers.reviewer,
        providers.judge,
        audit,
        config,
    )
    call = oracle.ask(
        OracleRequest(
            run_id="development-001",
            subject=catalog.subject("T-0001"),
            question="Was this person born before 1900?",
        )
    )

print(call.result.answer)  # Provisional research answer.
print(call.adjudication.final_answer)
print(call.result.evidence)
print(call.metrics.cost_usd)
print(call.metrics.latency_ms)
```

Embedding applications configure their own handler for the `deep20.oracle` logger. The package
does not modify global logging configuration.

### Guesser-safe projection

Only this value may be added to a Guesser conversation:

```python
answer = call.guesser_answer()
```

It returns the `OracleAnswer` enum and cannot expose evidence, excerpts, raw output, or provider
metadata.

### Cost and latency

`OracleCall.metrics` groups the total provider-reported cost, latency, token counts, and
web-search count. Its `oracle` field combines primary and recovery research when both ran;
`reviewer` and optional `judge` retain the other role metrics. `OracleCall.adjudication` retains
the blind role decisions, each decision's basis,
decision path, final answer, and a deterministic question-shape category (`temporal_comparison`,
`quantitative_comparison`, `negation`, or `other`). Benchmark summaries aggregate agreement,
disagreement by question type, Judge answer changes, and Reviewer/Judge cost without exposing
those details to the Guesser. JSON output serializes decimal costs as strings to preserve
precision:

```json
{
  "metrics": {
    "cost_usd": "0.0123",
    "latency_ms": 1842,
    "input_tokens": 814,
    "cached_input_tokens": 0,
    "cache_write_tokens": 0,
    "output_tokens": 126,
    "reasoning_tokens": 38,
    "search_count": 1
  }
}
```

If OpenRouter omits cost rather than reporting zero cost, `cost_usd` is `null`.

### Prompt caching

The Oracle, Reviewer, and Judge do not reuse earlier answers and do not use an application or
OpenRouter response cache. Each invoked role performs fresh generation; only the Oracle has web
search. Reviewer and Judge may use parametric knowledge under the bounded policy below. This is
not conversation memory or an answer cache.

Provider-side prompt caching is a separate optimization that can reuse computation for an
exact shared input prefix. Each subject/run and research strategy uses a stable OpenRouter
session ID. The prompt cache key is derived from the prompt version and trusted subject
snapshot. Primary and recovery therefore use distinct session and cache namespaces. No
explicit breakpoint or padding is configured. Automatic caching is available at
the provider, and `OracleCall.metrics` records `cached_input_tokens` and
`cache_write_tokens` for every call.

Reviewer and Judge use their own role-specific session and cache namespaces derived from their
role, prompt version, and trusted subject snapshot. They never share a namespace with the
Oracle, Guesser, Guess Validator, or each other. Provider prompt caching may reuse only exact
prefix computation; it never reuses an answer. Their current Google AI Studio and Anthropic
routes have independent provider caching behavior and pricing, so cache telemetry is assessed
per role rather than combined.

See [LLM caching](../../../documentation/llm-caching.md) for the project rule, current assessment,
and the
experiment required before this decision changes.

## Result contract

The provider-facing research-attempt shape includes the classified outcome and exact queries:

```json
{
  "answer": "YES",
  "evidence": [
    {
      "source_url": "https://example.org/source",
      "excerpt": "The passage used by the model.",
      "validation": "model_reported"
    }
  ],
  "research_outcome": "answered",
  "attempted_queries": ["Albert Einstein date of death biography"]
}
```

An unsuccessful attempt uses `UNKNOWN`, no evidence, a non-`answered` outcome, and the queries
it tried. The Oracle keeps this attempt data in its audit and projects the selected attempt into
the simpler final `OracleResult` below.

A decisive result has one to three model-reported evidence items:

```json
{
  "answer": "YES",
  "evidence": [
    {
      "source_url": "https://example.org/source",
      "excerpt": "The passage used by the model.",
      "validation": "model_reported"
    }
  ]
}
```

An unresolved result is:

```json
{
  "answer": "UNKNOWN",
  "evidence": []
}
```

Reviewer and Judge use the same typed decision shape:

```json
{
  "answer": "NO",
  "basis": "evidence",
  "evidence_indices": [1]
}
```

or, for the bounded fallback:

```json
{
  "answer": "NO",
  "basis": "model_knowledge",
  "evidence_indices": []
}
```

For both roles, an evidence-based `YES` or `NO` uses `basis="evidence"` and requires at least
one supporting one-based evidence index. `UNKNOWN` uses `basis="evidence"` with no indices.
Reviewer `UNKNOWN` invokes the Judge because it disagrees with the only reviewed Oracle
possibilities, `YES` and `NO`. Judge `UNKNOWN` is final. Neither prompt contains an earlier
answer.

Reviewer and Judge both start with supplied evidence. If it does not directly settle the
question and is not contradictory, either role may use `basis="model_knowledge"` with no
indices only for a stable, widely established, closed fact with a unique answer. Sole
authorship, birthplace, creator, and inventor relations are examples. Authoritative
counter-attribution uses `basis="evidence"` when the relation is uniquely attributable.

The Reviewer applies the fallback more conservatively because an agreement with the Oracle
bypasses the Judge. Neither role may use it for current or disputed facts, subjective claims,
open-world relations, affiliations, citizenships, awards, visits, `ever`, `only`, or complete
or exact counts. It returns `UNKNOWN` when uncertain.

For example, web sources are unlikely to state the exact negative sentence “Albert Schweitzer
did not write *Being and Time*.” A catalog naming Martin Heidegger as the work's sole author is
the preferred direct evidence. If the Oracle did not supply it, the Reviewer or Judge may still
return `NO` from high-confidence model knowledge and label that basis honestly. This exception
does not apply to open-world negatives or exhaustive claims. One excerpt saying that a person
won a Nobel Prize in Physics does not establish whether the person won two Nobel Prizes;
without an exact count or complete authoritative evidence, the role must return `UNKNOWN`.

The Reviewer fallback is available for every initial Oracle `YES` or `NO`. The Judge fallback
is available only when an Oracle–Reviewer disagreement invokes the Judge. An initial Oracle
`UNKNOWN` still bypasses both quality-control roles and remains final.

Evidence is not independently fetched or verified. Provider citation annotations remain in the
audit record for later inspection. Deep20Bench does not impose source-specific ordering or
domain filters. OpenRouter's configured web-search engine selects and ranks sources normally;
the Oracle evaluates the available results without reranking them by source.

The canonical evidence URL field is `source_url`. At the external provider-validation boundary,
the common provider spelling `url` is accepted and immediately normalized to `source_url`.
Supplying both spellings or any other unknown evidence field remains invalid. Application code,
typed results, and persisted records only contain `source_url`.

## Run audit files

Standalone Oracle-pipeline calls write no run files by default. Pass `--verbose` to create or
extend:

```text
runs/<run-id>/
├── manifest.json
└── oracle-calls.jsonl
```

The manifest contains the Git revision, dirty-tree state, Oracle configuration and hash,
subject-catalog hash, evidence policy, creation time, and reproducibility statement.

Each JSONL line is either a `success` or `failure` record. It includes the original request,
typed primary and optional recovery attempts, classified resolution, model-reported queries,
research result or error, final adjudication, nested Reviewer and optional Judge traces, model
routing, web-search telemetry, per-role tokens/cost/latency, timestamps, and integrity hash.

In verbose mode, the writer validates the existing manifest and call log before appending.
Configuration or catalog changes, corrupted hashes, malformed JSON, duplicate call IDs, and
write failures stop the operation. Without `--verbose`, the signed call is returned without
persisting these auxiliary files.

Run files are intentionally not ignored. After a run:

```bash
uv run pytest
uv run ruff check .
git diff --check
git add runs/development-001
```

Review the audit content before committing it. The application does not stage or commit files.

## Failure behavior

Failures are typed and audited when a run context is available. Important codes include:

| Code | Meaning |
| --- | --- |
| `provider_request_failed` | The OpenRouter request failed. |
| `provider_incomplete_response` | The provider did not finish with a completed answer. |
| `provider_output_limit_exceeded` | The provider stopped because the configured output ceiling was reached. |
| `provider_empty_response` | The response had no structured textual content. |
| `web_search_not_used` | Provider telemetry reported no web search. |
| `resolved_model_mismatch` | The resolved model differed from the configured model. |
| `invalid_structured_output` | JSON or domain validation failed. |
| `oracle_research_exhausted` | Two research attempts failed to retrieve usable support for a deterministic closed or temporal fact. |
| `audit_configuration_mismatch` | A run ID was reused with another Oracle configuration. |
| `audit_catalog_mismatch` | A run ID was reused with another subject catalog. |
| `audit_integrity_mismatch` | Existing run data failed its integrity check. |
| `audit_write_failed` | The audit record could not be persisted. |

The adapters retry typed transient transport failures and explicit
408/429/500/502/503/504/524/529 responses within the configured bounded backoff budget,
honoring `Retry-After`. Empty and incomplete results receive the configured bounded no-result
retry. Each role may retry invalid structured output under its own policy by replaying the exact
request without adding validation feedback. These are transport or format retries. The Oracle's
one research-recovery request is a separate semantic evidence-acquisition strategy and receives
no prior-attempt content. Genuine Oracle, Reviewer, and Judge `UNKNOWN` values are valid
decisions; transport, exhausted closed-fact research, exhausted schema recovery, search,
model-routing, and audit failures are exceptions. A required Reviewer or Judge failure fails
the complete adjudication and never falls back to the provisional Oracle answer.

## Testing

Run the offline suite and lint checks:

```bash
uv run pytest
uv run ruff check .
uv build --all-packages
```

The paid live integration test is opt-in:

```bash
DEEP20_RUN_LIVE_TEST=1 uv run pytest -m integration \
  source/execution/oracle/tests/test_live_openrouter.py
```

It uses the same credential precedence as the CLI, makes a real provider request, and writes
only to a temporary test run directory.
