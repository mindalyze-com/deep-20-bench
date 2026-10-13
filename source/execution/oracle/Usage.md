# Oracle usage

The `deep20-oracle` package answers one yes/no question about one configured subject:

1. The **Oracle** researches the question on the live web. If retrieval fails, it makes one
   independent second attempt with a different strategy.
2. The **Reviewer** checks every resulting `YES` or `NO` without web access and without seeing
   the Oracle's answer.
3. The **Judge** decides only when the two disagree. It is also blind and has no web access.

The package writes the full typed research and answer-check audit before returning. The
Reviewer and Judge rely on evidence first and may use their own knowledge only for narrow,
settled facts, labelled as such. The Reviewer uses this fallback more cautiously, because
agreeing with the Oracle skips the Judge.

The detailed three-token schemas, knowledge fallback, and examples below describe the default
standalone standard profile. The qualified profile follows the five-answer rules summarized
under Current policies. Run the examples from the repository root.

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

The spelling `private/openrouter.yaml` also works. If both files exist, `openrouter.yml` wins.
`OPENROUTER_API_KEY` overrides both files, for example in CI or for a single run.

Never put the key in normal configuration, logs, audit records, or committed files. The whole
`/private/` directory is ignored by Git; give credential files owner-only permissions.

## Configuration

The default configuration is `config/oracle.yaml`:

```yaml
gateway: openrouter
model: openai/gpt-5.6-luna
provider: openai
reasoning_effort: medium
allow_fallbacks: false
parallel_search: true
parallel_search_mode: fast
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
| `parallel_search_mode` | Parallel mode: `basic`, `fast`, `turbo`, or `advanced`. Repository configs select `fast`; omitted fields retain legacy `basic`. Other modes require `parallel_search: true`. |
| `max_search_results` | Maximum results available to web search, from 1 to 10. |
| `max_output_tokens` | Provider output ceiling, from 128 to 65,536. |
| `timeout_seconds` | Request timeout, from 1 to 600 seconds. |
| `recovery` | Typed, bounded retry policy for transient provider failures and invalid output. |
| `reviewer` | No-web route that blindly checks every Oracle `YES` or `NO`. |
| `judge` | No-web route whose answer is final when Oracle and Reviewer disagree. |

The default roles use three model families on purpose: OpenAI for research, Google for
review, and Anthropic for disputes. The Oracle and Reviewer use fixed backend providers. The
Judge always uses the `anthropic/claude-opus-5` model but lets OpenRouter pick an available
backend. Its route sends `max_tokens` so that automatic routing can use endpoints that support
the Judge's structured output. The provider actually used is recorded in the typed results.

A run manifest stores the complete configuration. Later calls that reuse the same run ID with a
different configuration are rejected before any provider request, so they cost nothing.

The adapter does not send OpenRouter's `provider.require_parameters` filter on purpose.
OpenRouter's web-search tool runs at the router level, and that filter would reject capable
OpenAI endpoints before the search tool could run. The exact model and provider are still
enforced through `model`, `provider.only`, fallbacks disabled by default, a check of the model
actually used, and required web-search telemetry.

## Current policies

- **Answer research.** New B-0003 runs use `concise_knowledge_v1`: one research attempt that
  asks for `research_query_target` search queries (default 3), with an API limit of that target
  plus two extra calls. A valid answer within that limit keeps its independent evidence or
  knowledge decision, a private `evidence`/`other` basis, and a supporting statement. This
  policy allows directional answers without sources and keeps context for UNKNOWN answers. The
  older evidence and recovery rules below describe earlier policies. See
  [the current policy](../../../documentation/five-answer-experiment.md#concise-evidenceknowledge-policy).
- **UNKNOWN under `concise_knowledge_v1`.** Reviewer and Judge UNKNOWN may cite valid evidence
  indices that show the uncertainty, with either `evidence` or `other` basis and the required
  supporting statement. No answer is converted into another. Reviewer UNKNOWN goes to the blind
  Judge; Judge UNKNOWN is a final, playable answer. Invalid references and truly invalid
  responses still fail after limited retries. Older policies keep their UNKNOWN rules.
- **Evidence format.** The concise policy accepts exact quotations and clearly labelled
  summaries of retrieved source facts. Each evidence item may have up to 2,000 characters; there
  is no separate word limit, and longer context is not a protocol error. Use
  `kind: quotation` for exact text or `kind: source_summary` for a faithful summary in the
  model's own words. If `kind` is omitted, the item is treated as a quotation, as before. The
  Reviewer and Judge see the summary label with the full numbered evidence and still do not see
  earlier decisions. See `documentation/five-answer-experiment.md` for the evidence and version
  rules.
- **Five answers.** The `qualified_v1` profile allows YES, RATHER_YES, RATHER_NO, NO, and
  UNKNOWN. Every answer other than UNKNOWN is blind-reviewed, and any exact difference goes to
  the Judge. Current B-0003 runs use `concise_knowledge_v1`, as described above. Earlier
  qualified policies kept the Reviewer evidence-only and optionally selected
  `judge_stable_knowledge_v1` for limited, labelled Judge knowledge. With `profile_default`,
  qualified review remains evidence-only. Oracle UNKNOWN still skips both roles. See
  [Five-answer experiment](../../../documentation/five-answer-experiment.md).
- **Concise prompts.** `OracleConfig.prompt_profile: concise_v1` selects the experimental concise
  research and review prompts as one matched set. The default `standard` prompts are unchanged.
  See [Concise prompt experiment](../../../documentation/concise-prompt-experiment.md).
- **Answer reuse.** Benchmark runs can
  [reuse earlier Oracle answers](../../../documentation/oracle-history-cache.md) under the
  explicit `historical_ask_v1`, `same_episode_ask_v1`, and `same_execution_ask_v1` policies.
  The benchmark loads verified earlier rounds when first needed and adds eligible new answers
  from finished games in the current run for later rounds. Within one game, a repeated
  (normalized) question also reuses its answer. Repeated questions still count. Reused turns
  keep their original evidence and a source label, with no new answer-checking calls or cost.
  Each Guesser conversation starts fresh, and cache details never enter it. Standalone commands
  always make new calls. Reused answers skip this Oracle service entirely; when the service runs,
  every role generates a new answer.
- **Question replay.** To test revised Oracle, Reviewer, or Judge prompts on recorded benchmark
  questions without a Guesser, use
  [Oracle question replay](../../../documentation/oracle-question-replay.md). It calls this same
  service with new generations and stores comparisons under `private/reviews/`.
- **Edition 1.2 backend.** The inactive
  [edition 1.2 draft](../../../documentation/edition-1.2-draft.md) connects Research, Reviewer,
  and Judge through typed role interfaces. The default implementations keep the existing
  OpenRouter logic; the benchmark also provides local, interactive, and mock versions. Reviewer
  `approve_primary` is an explicit synthetic test outcome, not a provider decision. Standalone
  Oracle commands keep their defaults. The draft's managed Parallel tools use separate
  credentials and the benchmark's spending allowance.

## Research outcomes and recovery

Each research attempt returns an answer, evidence, an outcome category, and one to eight search
queries as reported by the model. The queries are kept for auditing. They are labelled
`model_reported` because they are not checked against provider telemetry, which records only
the number of web searches.

The outcome is one of `answered`, `no_results`, `irrelevant_results`,
`insufficient_coverage`, `conflicting_sources`, `ambiguous_question`, or
`open_world_not_provable`. The four outcomes from `no_results` to `conflicting_sources` trigger
exactly one recovery attempt. That attempt receives only the same trusted subject and question.
It uses a fixed prompt with alternative strategies for each kind of question, its own session,
and its own prompt-cache namespace. It never sees the first attempt's queries, answer,
evidence, outcome, trace, or response.

The main prompt allows a reliable fact that directly contradicts the question. For example, an
authoritative date of death supports `NO` for "Is this person currently alive?" A plain
profession or role means a documented profession or recognized role, not a one-off appearance
or activity.

`ambiguous_question` and `open_world_not_provable` are final `UNKNOWN` outcomes with no recovery
attempt. If valid research is still inconclusive after recovery, the answer is also `UNKNOWN`,
however the question is worded. Keyword lists no longer decide whether missing evidence counts
as an infrastructure failure. Technical failures (provider, schema, required search, routing,
saving) still fail the call. The Reviewer and Judge receive only the trusted subject, the
original question, and the numbered evidence of a directional answer; Oracle `UNKNOWN` skips
both.

New research audits use `question_class: other`. Older labels and failures stay readable;
historical results are not rewritten. The revised answer contract is
`oracle-factual-answer-v2-inconclusive-unknown`. Standalone manifests and benchmark and cache
contracts refuse to mix it with the older behavior, so use new execution IDs.

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

Target IDs use the form `T-NNNN`. The description should identify the exact entity without
turning into a biography. Duplicate YAML keys, mismatched IDs, malformed URLs, duplicate aliases,
and unknown fields are rejected.

An entry may set `status: active` or `status: inactive`; the default is active. Inactive entries
keep their IDs, aliases, and descriptions. New benchmark runs skip them, but standalone Oracle
and game commands can still use them for audits. Set the status back to `active` to include the
subject in new benchmarks. Components receive plain `Subject` values, so the status never
reaches model requests or prompt caches. The catalog hash ignores status but changes with any
other catalog edit.

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
`--max-output-tokens`, and `--timeout-seconds`. The run manifest stores the values actually
used, including overrides. Reusing a run ID with different overrides is rejected. These flags
affect only the research Oracle; the Reviewer and Judge always use their own sections of the
selected YAML file.

Parallel search is on by default. It uses the same OpenRouter web-search tool, but with the
Parallel engine instead of the provider's own search. Engines can rank sources and pick
excerpts differently, so compare them under separate run IDs:

```bash
uv run deep20 oracle ask T-0001 \
  "Was this person born before 1900?" \
  --run-id parallel-search

uv run deep20 oracle ask T-0001 \
  "Was this person born before 1900?" \
  --run-id native-search \
  --no-parallel-search
```

The repository Oracle configuration and benchmark templates use `parallel_search_mode: fast`
for new runs. Set it to `basic` to compare with Basic. If the field is missing, Basic is used and
nothing extra is serialized, so older manifests stay valid. `--no-parallel-search` also clears
the Parallel mode when switching to the provider's own search.

A non-default mode is stored in the fixed configuration, sent to the search tool, and given its
own prompt-cache namespace for the primary and recovery attempts. It does not change prompts,
review rules, Guesser history, or the no-web Reviewer and Judge requests.

The installed OpenRouter SDK does not know the newer `mode` field. After the SDK serializes a
request, the adapter adds back only a configured non-default mode and checks that the expected
Parallel tool is present. A test with the real SDK and a mock HTTP transport covers this path.
Basic and no-web requests are sent unchanged.

On 6 September 2026, OpenRouter listed Basic/Advanced at $0.005 and Fast/Turbo at $0.001 per
search request, including up to ten results. Model token costs remain additional. Check the
[OpenRouter web-search documentation](https://openrouter.ai/docs/guides/features/server-tools/web-search)
for current pricing before relying on projected savings.

The command prints the complete `OracleCall` as JSON to standard output and writes one short
log line to standard error:

```text
2026-07-26 22:15:01.100 INFO oracle.run run=development-001 target=T-0001 model=openai/... provider=openai
```

A multi-line question is JSON-escaped onto one line. The console never shows the prompt, raw
response, evidence excerpts, annotations, subject description, or API key.

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

Applications that embed the package set up their own handler for the `deep20.oracle` logger.
The package does not change global logging settings.

### Guesser-safe projection

Only this value may be added to a Guesser conversation:

```python
answer = call.guesser_answer()
```

It returns only the `OracleAnswer` enum, so it cannot leak evidence, excerpts, raw output, or
provider metadata.

### Cost and latency

`OracleCall.metrics` holds the total provider-reported cost, latency, token counts, and number
of web searches. Its `oracle` field combines the primary and recovery research if both ran;
`reviewer` and the optional `judge` hold the other roles' metrics.

`OracleCall.adjudication` holds each role's blind decision and basis, the decision path, the
final answer, and a fixed question-shape category (`temporal_comparison`,
`quantitative_comparison`, `negation`, or `other`). Benchmark summaries report agreement,
disagreement by question type, answers changed by the Judge, and Reviewer and Judge cost. None
of this reaches the Guesser. JSON output writes decimal costs as strings to keep their precision:

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

If OpenRouter reports no cost at all (rather than zero), `cost_usd` is `null`.

### Prompt caching

Within this service, the Oracle, Reviewer, and Judge never reuse earlier answers and use no
application or OpenRouter response cache. Every role that runs generates a new answer; only the
Oracle searches the web. The Reviewer and Judge may use their own knowledge under the limited
policy below. That is neither conversation memory nor an answer cache.

Provider prompt caching is a separate optimization: it can reuse computation for an identical
input prefix. Each subject, run, and research strategy uses a stable OpenRouter session ID. The
prompt cache key comes from the prompt version and the trusted subject snapshot, so the primary
and recovery attempts use separate sessions and cache namespaces. No explicit cache breakpoint
or padding is set. The provider caches automatically, and `OracleCall.metrics` records
`cached_input_tokens` and `cache_write_tokens` for every call.

The Reviewer and Judge each have their own session and cache namespace, based on the role,
prompt version, and trusted subject snapshot. They never share a namespace with the Oracle,
Guesser, Guess Validator, or each other. Prompt caching only reuses computation for an identical
prefix; it never reuses an answer. Their Google AI Studio and Anthropic routes cache and price
differently, so cache telemetry is evaluated per role.

See [LLM caching](../../../documentation/llm-caching.md) for the project rule, the current
assessment, and the experiment needed before this decision changes.

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

An unsuccessful attempt has `UNKNOWN`, no evidence, an outcome other than `answered`, and the
queries it tried. The Oracle keeps this attempt data in its audit and reduces the chosen attempt
to the simpler final `OracleResult` below.

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

For both roles, an evidence-based `YES` or `NO` uses `basis="evidence"` and needs at least one
supporting evidence index (counting from 1). `UNKNOWN` uses `basis="evidence"` with no indices.
Reviewer `UNKNOWN` sends the question to the Judge, because it disagrees with the Oracle's `YES`
or `NO` (the only answers that get reviewed). Judge `UNKNOWN` is final. Neither prompt contains
an earlier answer.

Both roles start from the supplied evidence. If it neither settles the question nor
contradicts itself, either role may answer with `basis="model_knowledge"` and no indices, but
only for a settled, widely known fact with a single answer, such as sole authorship,
birthplace, creator, or inventor. If the evidence names someone else as the sole author or
creator, that counts as `basis="evidence"`.

The Reviewer uses this fallback more cautiously, because agreeing with the Oracle skips the
Judge. Neither role may use it for current or disputed facts, opinions, open-ended relations,
affiliations, citizenships, awards, visits, `ever`, `only`, or complete or exact counts. When
unsure, the role returns `UNKNOWN`.

For example, web sources are unlikely to state the exact negative sentence “Albert Schweitzer
did not write *Being and Time*.” A catalog naming Martin Heidegger as the work's sole author is
the preferred direct evidence. If the Oracle did not supply it, the Reviewer or Judge may still
return `NO` from high-confidence model knowledge and label that basis honestly. This exception
does not apply to open-world negatives or exhaustive claims. One excerpt saying that a person
won a Nobel Prize in Physics does not establish whether the person won two Nobel Prizes;
without an exact count or complete authoritative evidence, the role must return `UNKNOWN`.

The Reviewer can use the fallback for every Oracle `YES` or `NO`. The Judge can use it only when
an Oracle–Reviewer disagreement reaches it. An Oracle `UNKNOWN` still skips both checking roles
and is final.

Evidence is not fetched again or verified independently. Provider citation annotations stay in
the audit record for later review. Deep20Bench does not prefer or filter particular sources or
domains. OpenRouter's search engine picks and ranks sources as usual, and the Oracle uses the
results without reordering them.

The evidence URL field is `source_url`. When validating provider output, the common spelling
`url` is accepted and immediately renamed to `source_url`. Giving both spellings, or any other
unknown evidence field, is invalid. Application code, typed results, and saved records only use
`source_url`.

## Run audit files

Standalone Oracle calls write no run files by default. Pass `--verbose` to create or extend:

```text
runs/<run-id>/
├── manifest.json
└── oracle-calls.jsonl
```

The manifest contains the Git revision, whether the working tree had uncommitted changes, the
Oracle configuration and its hash, the subject-catalog hash, the evidence policy, the creation
time, and a reproducibility statement.

Each JSONL line is a `success` or `failure` record. It contains the original request, the
primary and optional recovery attempts, the resolution, the model-reported queries, the
research result or error, the final decision, the Reviewer and optional Judge traces, model
routing, web-search telemetry, tokens, cost, and latency per role, timestamps, and an
integrity hash.

In verbose mode, the writer checks the existing manifest and call log before appending. A
changed configuration or catalog, a broken hash, malformed JSON, a duplicate call ID, or a
write error stops the operation. Without `--verbose`, the signed call is returned and nothing
is saved.

Run files are deliberately not Git-ignored. After a run:

```bash
uv run pytest
uv run ruff check .
git diff --check
git add runs/development-001
```

Review the audit content before committing it. The application does not stage or commit files.

## Failure behavior

Failures are typed, and audited when a run context exists. Important codes:

| Code | Meaning |
| --- | --- |
| `provider_request_failed` | The OpenRouter request failed. |
| `provider_incomplete_response` | The provider did not finish with a completed answer. |
| `provider_content_filtered` | An Oracle-family provider response ended with `content_filter`; the actual filter rule may be undisclosed. |
| `provider_output_limit_exceeded` | The provider stopped because the configured output ceiling was reached. |
| `provider_empty_response` | The response had no structured textual content. |
| `web_search_not_used` | Provider telemetry reported no web search. |
| `resolved_model_mismatch` | The resolved model differed from the configured model. |
| `invalid_structured_output` | JSON or domain validation failed. |
| `audit_configuration_mismatch` | A run ID was reused with another Oracle configuration. |
| `audit_catalog_mismatch` | A run ID was reused with another subject catalog. |
| `audit_integrity_mismatch` | Existing run data failed its integrity check. |
| `audit_write_failed` | The audit record could not be persisted. |

Retry rules:

- **Transport errors.** The adapters retry typed temporary transport failures and
  408/429/500/502/503/504/524/529 responses within the configured backoff budget, and honor
  `Retry-After`.
- **Empty or incomplete results** get the configured limited no-result retry. For Oracle
  research this also covers `content_filter` and `length`, but only when the route and the
  searches actually used are known and allowance remains. Both provider search limits are
  reduced by the searches already used; the messages stay the same. Missing telemetry or an
  unclear transport outcome cannot reset the search budget.
- **Shared budget.** No-result and format retries share one allowance, and every attempt counts
  in billing and retry metrics. When the allowance runs out, the check fails; there is no
  unchecked answer and no made-up `UNKNOWN`.
- **Format retries.** Oracle and Reviewer calls add a random eight-character hexadecimal
  `question_id` after the question, with a fixed instruction to ignore it. A format retry
  changes only this ID. No invalid output, validation feedback, attempt number, or earlier
  decision is sent. Transport retries keep the same ID, and Judge format retries resend the
  exact request. The changed ID does not set a provider seed or guarantee a different answer.
  The policy is versioned as `question-id-v1` in the
  `oracle-factual-answer-v4-bounded-format-retry` contract hash, so use new run and execution
  IDs. Logical prompt hashes ignore the random ID; privileged provider traces keep the actual
  request. The ID never enters Guesser history or another role's request.

These are transport and format retries. The Oracle's single research-recovery attempt is
different: it is a second search strategy and gets nothing from the first attempt.

A real Oracle, Reviewer, or Judge `UNKNOWN` is a valid decision, including inconclusive research
after recovery. Transport errors, exhausted schema retries, and search, routing, or audit
failures are exceptions. If a required Reviewer or Judge call fails, the whole check fails; the
provisional Oracle answer is never used instead.

## Testing

Run the offline suite and lint checks:

```bash
uv run pytest
uv run ruff check .
uv build --all-packages
```

The paid live integration test is opt-in:

```bash
DEEP20_RUN_LIVE_TEST=1 uv run pytest -m integration --run-paid-tests \
  source/execution/oracle/tests/test_live_openrouter.py
```

It finds credentials the same way as the CLI, makes a real (paid) provider request, and writes
only to a temporary test run directory.

For repeated direct questions and saved test cases without a Guesser, see
[Direct Oracle question suites](../../../documentation/oracle-question-suites.md).
