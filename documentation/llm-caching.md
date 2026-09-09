# LLM caching

The `per_subject_history_v1` discovery policy expands benchmark `historical_ask_v1` inputs to
compatible completed games found when each subject starts. It changes discovery timing only:
answer validation, blind projections, factual prompts, role schemas, routes, sessions, prices,
and provider prefix-cache namespaces remain unchanged. Each subject inventory is persisted
before reuse and restored on resume. Explicit history cutoffs and older manifests stay frozen.
Keep automatic exact-prefix caching on misses, without padding or provider response caching.
Hits have zero new adjudicator calls, tokens, searches, cost, and provider latency. Reduced live
traffic may affect prefix reuse; no live savings have been measured for this change. The change
is verified with offline fixtures and independent local processes only.

The benchmark's `same_execution_ask_v1` policy adds fully adjudicated live ASK answers after
each completed scoring-eligible game, for compatible repeats across repetitions in that run.
Resume restores them from verified original trial artifacts. This changes only the versioned
benchmark response-reuse policy; factual prompts, sessions, schemas, route settings, provider
prefix-cache namespaces, and prices remain unchanged. Keep exact-prefix caching on misses,
with no padding or provider response caching. Hits record zero new calls, tokens, searches,
cost and provider latency, with original telemetry retained only as marked source data.
Fewer live requests may reduce prefix reuse opportunities, so measure actual usage; this
offline-verified change makes no measured production saving claim. Old manifests retain their
recorded cache scope. See [ASK cache contracts](oracle-history-cache.md).

The labelled-source-context revision retains the 2,000-character evidence allowance and adds
`kind: source_summary` alongside exact quotations. Its research, Reviewer and Judge versions
are `live-web-oracle-v17-labelled-source-context`, `oracle-reviewer-v12-labelled-source-context`,
and `oracle-judge-v15-labelled-source-context`. The changed research schema, fixed role prefixes,
and labelled numbered evidence change the factual contract and role cache namespaces. Existing
policy hashes and historical quotation serialization are preserved; earlier compatible-profile
answers cannot enter the new contract. Guesser and Validator prefixes remain unchanged.
Keep automatic exact-prefix caching, with no padding or provider response cache. No live
recovery-rate, cost, latency or cache-saving improvement has been measured. Record actual
role-level usage in any later authorized check. Publication carries the label after the run;
it adds no model calls or provider caching. Existing release pins remain unchanged.

Concise missing-search recovery adds `explicit-zero-bounded-format-retry-v1` to the
factual contract. A completed reply with explicit zero search usage may use the existing
single invalid-output retry after route/cache/budget validation. Missing telemetry does not
count as zero. The retry preserves factual inputs and refreshes only the existing question ID;
its search caps use the remaining total allowance. Discarded answers remain private. The
retried reply must itself satisfy the search guard. Prompt prefixes and schemas are unchanged;
retain automatic exact-prefix caching without padding or response reuse, with no claimed
savings. A fresh run and history contract are required; existing results remain immutable.

The concise UNKNOWN-context revision uses `oracle-reviewer-v11-unknown-context` and
`oracle-judge-v14-unknown-context`. Review prompts and schema descriptions explicitly permit
private evidence references explaining UNKNOWN, with the original decision retained. These
versioned prefixes and schemas change the factual contract and isolate earlier ASK answers.
Earlier policy contracts and research/Guesser/Validator prefixes remain unchanged. Keep
automatic exact-prefix caching without padding or response caching; no measured cost or
latency saving is claimed. Private support remains audit-only. Use a fresh execution ID for
any later authorized live run; the stopped run and its failed outcomes stay unchanged.

An explicitly requested experimental repair may instead preserve scored games and record the
new Oracle contract in a signed repair revision. Its replacement history inventory has no
sources, retains the original cutoff, and is pinned for subsequent resumes. Same-episode
reuse remains limited to fully adjudicated compatible answers in the fresh episode. Neither
old answers nor private repair metadata enter new requests. Mixed-contract repaired runs do
not seed historical inventories and are not publication eligible. This exception introduces
no provider response cache or claimed savings.

Bounded no-result recovery adds `known-usage-remaining-allowance-v1` to the concise factual
contract's search-budget policy. A retry requires explicit search accounting and the intended
route, preserves all messages, and reduces both provider search caps. This can change the
tool prefix; retain automatic exact-prefix caching without padding or response reuse. Costs
include discarded attempts, and savings remain unmeasured. Standard contracts are unchanged.

The search allowance revision uses `live-web-oracle-v16-search-headroom`. The Oracle prompt
requests `research_query_target` queries (default 3); API limits and local validation derive
their ceiling by adding two. Both values enter the factual-answer contract. Non-default
targets change the rendered research prefix, while the derived tool and response-schema
limits also change the provider prefix. Retries use only the remaining total allowance.
Keep automatic prefix caching, role isolation, and existing route prices without padding or
response caching. Reviewer/Judge prompts and Guesser-visible tokens are unchanged. Existing
metrics retain all actual search use and billing, including bonus calls. This change has
offline validation; it makes no measured claim that extra search cost is offset by avoided
failed games. New executions and compatible ASK-cache inventories require the revised contract.

The scope revision uses `live-web-oracle-v15-property-scope`,
`oracle-reviewer-v10-property-scope`, and `oracle-judge-v13-property-scope`. All three roles distinguish
the named object from its constituent material, preserve each branch of OR/AND, and retain
the question's quantifiers and ordinary scope, including physical state versus shape and
strength. Research-outcome labels in the prefix derive from the schema's enum. The shared fixed prefix is longer; models,
routes, tool budgets, cache namespaces, and configured pricing are unchanged. Keep automatic
prefix caching without padding or response caching. The prompt versions and
`oracle-factual-answer-v4-bounded-format-retry` separate prior ASK contracts. A research format
retry may reuse only exact prefix computation, with its remaining search allowance reflected
in both provider tool-limit fields. Measure fresh role-level usage before claiming any saving.

The `concise_knowledge_v1` policy changes primary/review/Judge prompts, output schemas, and
server-tool limits. New role-specific versions and the factual-contract hash separate it
from earlier policies. The original three-search controls are part of the provider-rendered tool
prefix; bounded retries can use a smaller remaining limit and therefore a different prefix.
Keep automatic prefix caching without padding, explicit storage, or response caching.
Shorter prompts may fall below existing route thresholds; no cache savings are claimed.
Models, routes, and configured pricing remain unchanged. Measure cache reads/writes, actual
billing, and latency with fresh route checks/canaries before the next authorized paid launch.
Decision basis/statements are output/audit data, never later request prefixes. Historical ASK
reuse retains them only with the original fully adjudicated result and compatible contract;
`bounded_unknown` does not seed historical or same-episode reuse.


The `question-id-v1` policy appends an eight-character random ID after the complete Oracle or
Reviewer factual input and changes that ID on a bounded format retry. Fixed policy, subject,
question, evidence, tools, and output schema stay ahead of the changing tail. Existing automatic
prefix caching, role/session namespaces, routes, prices, and thresholds remain configured;
transport retries retain the entire payload including the ID. The metadata instruction and
ID add a small input cost and prevent a complete identical prefix on a format retry. No padding,
response caching, discount, recovery-rate improvement, or net saving is claimed. Measure actual
role-level tokens, cache reads/writes, latency, cost, and format recovery before assessing the
effect. This change has offline validation only. Its version and fixed metadata contract enter
the factual-contract hash, preventing earlier ASK answers from seeding revised executions.
Random IDs are excluded from that deterministic hash and from logical prompt hashes, and are
retained only in privileged actual-request traces. Judge, Guesser, and Validator requests are
unchanged by this policy.

The qualified evidence-context research revision uses primary
`live-web-oracle-v12-evidence-context` and recovery
`live-web-oracle-recovery-v5-evidence-context`. Their fixed extraction instructions request
enough relevant context to assess the claim within the existing excerpt bounds. Only research
prefixes change. Existing role/session namespaces and automatic prompt caching remain; no
padding or response caching is added. The complete factual-contract hash changes, so earlier
ASK evidence packages cannot seed the new execution. Guesser and Validator prefixes remain
unchanged. Longer evidence can increase Reviewer/Judge input cost and change their cache reuse;
measure actual role-level tokens, cache reads/writes, latency and cost in the controlled check
and new run, and do not assume a discount or an accuracy gain from length alone.

A bounded local check on 7 September 2026 made six complete research requests with this
revision and four controlled blind-review requests. The research pipelines reported a total
cost of $0.10561018, including 123,199 cached input tokens and zero cache-write tokens; the
controlled requests cost $0.030327. These cache reads include research tool-loop prefixes and
do not isolate the effect of the extraction change. Reviewer and Judge reads were zero in this
check. Keep automatic caching without padding. The small check does not establish a net saving
or resolve every evidence-coverage concern; its detailed artifacts remain private.

The benchmark supports the user-authorized `historical_ask_v1`, `same_episode_ask_v1`, and
`same_execution_ask_v1` exceptions described in
[Historical Oracle answers](oracle-history-cache.md). New benchmark executions lazily load
compatible, integrity-checked completed ASK answers with original evidence and explicit source
provenance. Dated assessments below describe their original fresh-call policies and recorded
route pricing, not a live price guarantee. Immutable run configurations retain their original
estimates; reassess the exact route before a new paid launch. Provider
response caching, Guesser response reuse, Validator response reuse, and standalone answer
caching remain prohibited. Cache misses keep the existing provider prefix-cache settings;
cache hits make no provider call and do not claim provider prefix-cache savings.

B-0003 uses distinct qualified_v1 prompt versions and schemas in the existing isolated
prefix-cache namespaces. Standard wire schemas remain unchanged. Its prompt revision adds no
separate response cache or presumed savings. See [Five-answer experiment](five-answer-experiment.md).

The opt-in `judge_stable_knowledge_v1` adjudication policy changes the Judge prefix and output
schema only. Its prompt version is `oracle-evidence-judge-v10-stable-knowledge`; the existing
role/version/subject derivation separates its prefix-cache key from the evidence-only Judge.
The structured Judge startup canary also separates the revised policy's cache namespace.
Reviewer, research, recovery, Guesser, and Validator prefixes and schemas stay unchanged.
The new policy is recorded in immutable Oracle configuration, not in blind factual inputs or
Guesser history. Keep automatic prefix caching without padding, response reuse, or shared
sessions. The changed prefix and schema require fresh route measurements before claiming cache
eligibility or savings. Record actual cache reads/writes, latency, and billed cost in audits.

The local Judge policy audit on 6 September 2026 made 24 no-web
Judge calls across the historical, first revised, and final prefixes. All resolved to
`anthropic/claude-opus-5` on Claude Platform on AWS. The reported total cost was $0.368390,
including $0.134025 for the eight final-prefix calls. All calls reported zero cache reads and
writes. This verifies the final schema on that resolved route but does not establish prefix
reuse or a cache discount. Keep automatic best-effort caching with no padding.
The supporting audit is private; these aggregate measurements are its public summary.

The generic five-answer revision changes the fixed text for Guesser, primary research,
recovery, Reviewer, and Judge. Each changed role has a new prompt version in its existing cache
key. Subject, question, and evidence remain in their existing permitted projections after the
fixed prefix; no category-specific prefix or shared role session is added. Keep the configured
automatic prefix-cache controls, thresholds, and prices until a fresh route assessment before
a paid launch. Changed lengths may affect eligibility. No padding, response reuse, or measured
savings are claimed; this revision has only local validation.

## Project rule

The shared Guesser category guide changes the fixed prefix in all three profiles. Their
versions are now `stateful-category-guesser-v14-category-guide`,
`stateful-category-guesser-v15-concise-category-guide`, and
`stateful-category-guesser-v16-five-answer-category-guide`. Each uses its existing cache-key
derivation with the new version; older cache probes cannot certify the revised prefix.
The complete guide is fixed and shared across all subjects, preserving prefix reuse without
encoding subject identities, catalog membership, or activation status. Adjudicator prefixes,
routes, pricing, and session boundaries are unchanged. Keep existing route cache policies and
thresholds, measure actual tokens and billing with fresh required probes before a paid launch,
and do not infer cache eligibility or savings from the increased character count. No padding
or response caching is added.

Subject catalog activation is scheduling-only metadata. Catalog entries are projected to the
unchanged `Subject` contract before any LLM-backed component receives them. Status changes do
not change prompt prefixes, subject identity hashes, session keys, or prompt-cache keys.
Existing route caching policies remain applicable; this change adds no LLM calls or response
reuse and claims no cache savings.

Subject-description clarifications change the trusted snapshots supplied to Oracle, Reviewer,
Judge, and Validator. Existing subject-derived keys and full-snapshot matching separate the
revised descriptions from earlier ASK answers. Guesser inputs and fixed role instructions are
unchanged. Keep automatic prefix caching with the existing route settings and no padding;
changed input lengths have no measured cost or cache benefit. Historical runs and saved suites
retain their original descriptions; comparisons require new snapshots and execution IDs.

The `concise_v1` experiment uses separate versioned prefixes for Guesser, primary research,
recovery, Reviewer, and Judge. Cache keys and probe validation use the selected prompt version.
Shorter prompts may no longer reach a route's minimum prefix length; do not pad them or assume
savings. Keep automatic prefix caching and existing route prices/thresholds, measure actual
read/write tokens, latency, and charged cost, and recheck route pricing before a fresh launch.
The prompt revision adds no answer-reuse mechanism; benchmark cache policies remain separate.
See [experiment details](concise-prompt-experiment.md).

Every Deep20Bench component that calls an LLM must evaluate provider-side prompt caching.
That evaluation is not an instruction to turn caching on: the decision must be based on the
selected model, provider behavior, prompt size, repeated-prefix pattern, cache lifetime, and
measured cost.

Deep20Bench distinguishes three mechanisms:

| Mechanism | Meaning | Project decision |
| --- | --- | --- |
| Provider prompt caching | Reuses computation for an exact prompt prefix while generating a fresh response. | Enabled according to the pinned route and measured per component. |
| OpenRouter response caching | Returns a previous complete response for an identical request. | Prohibited for all benchmark LLM calls. |
| Application/client cache | Reuses fully adjudicated ASK answers from compatible history, the current game, or completed games in the current run. | Benchmark-only `historical_ask_v1`, `same_episode_ask_v1`, and `same_execution_ask_v1`, with source attribution. |

Prompt caching is configured through API request fields; telling the model in natural-language
instructions to remember or cache answers does not create a provider cache.

Bounded transport retries for explicit no-result provider statuses resend the identical request
and may therefore receive a provider prompt-cache read. They never reuse a complete response and
do not change which application ASK policies are allowed. Attempt count and retry timing are
measured as transport telemetry, not added to any prompt or cache key. The Oracle's one
diversified research-recovery attempt is different: it is a new semantic request under a
separate fixed prompt, session, and cache namespace. It is not an identical transport retry.

The Guesser cache namespace includes the versioned branch-aware action schema hash. Invalid
structured output is not invisibly retried. It becomes a scored turn; when budget remains, the
next request appends the canonical `FORMAT_ERROR` while excluding the invalid output,
validation details, and recovery metadata from Guesser-visible state.

## Current Oracle assessment

The batch launcher defaults to per-subject historical-answer discovery across models, matching
direct runs. An explicit `--oracle-history-before` freezes one cutoff across models. Saved
batches retain their recorded mode or cutoff for restarts. This default changes history
discovery timing only: provider prompts, sessions, prefix-cache keys,
thresholds, prices, and response-cache prohibitions remain unchanged. The saved batch plan
never enters model requests. No additional provider cache eligibility or savings are claimed.

Removing the research keyword classifier changes only application failure handling: valid
inconclusive research returns UNKNOWN after recovery. Prompts, schemas, routes, sessions,
provider prefix-cache keys, and pricing settings are unchanged, so no new prefix-cache
measurement or saving is claimed. The factual-answer contract version advances to
`oracle-factual-answer-v2-inconclusive-unknown` and separates historical answer reuse and
execution definitions from the earlier behavior. Existing exclusions still prevent
retrieval-exhausted UNKNOWN results from seeding either ASK cache. Actual provider cache
tokens, latency, and cost remain the evidence for reuse; no padding or response caching is added.

Repository Oracle and benchmark configurations select `parallel_search_mode: fast` for new
runs. Omitted settings still mean Basic for historical configuration compatibility.
The `parallel_search_mode` setting separates non-default search tools with a
`parallel-fast`, `parallel-turbo`, or `parallel-advanced` provider prompt-cache suffix. Basic
preserves the existing `parallel` suffix and omitted mode parameter. Primary and recovery
retain their separate upstream namespaces; no-web roles and Guesser requests are unchanged.
Changing the mode can change provider-rendered tool context, retrieval, and cache eligibility.
Retain automatic prefix caching without padding or response reuse. The early Fast diagnostic
runs and their reported measurements were removed. Fresh route measurements are required
before claiming cache reuse, cost savings, or comparable retrieval quality. Existing route
policies and thresholds remain unchanged; measure actual cache tokens, latency, and billing
on future runs.

The Oracle has useful repeated material across questions about one subject:

- The versioned primary or recovery system policy.
- The subject snapshot.
- The strict output schema.
- The web-search tool definition.

The messages, output schema, and tool definition total approximately 2,500 serialized
characters for the Albert Einstein example, or roughly 630 tokens using a deliberately coarse
four-characters-per-token estimate. That estimate does not include the provider-rendered
server-tool context and is not authoritative.

A live repeated-question test on 26 July 2026 reported 4,859 cached input tokens, zero
cache-write tokens, two fresh web searches, and a fresh generated answer. The preceding
identical request reported 4,859 cache-write tokens. This confirms that automatic provider
prompt caching can activate for the complete server-tool request even though the locally
serialized envelope appears short. It does not yet prove useful cache reuse when successive
questions differ.

OpenAI prompt-cache hits require an exact shared prefix. Static content should precede the
question, and the model, tools, and structured-output schema must remain identical. OpenRouter
can improve routing locality with `prompt_cache_key` or `session_id`, but routing cannot make a
sub-threshold prompt cacheable.

The dated OpenAI assessments below use a 1.25 cache-write multiplier and a separate cache-read
price. The retained Guesser/Validator estimates are frozen accounting inputs, not a claim
about every current OpenAI or OpenRouter route. Padding a short prompt can cost more under
that pricing model, especially if calls are spaced beyond the cache lifetime or few questions
share the exact prefix. Use the exact route's current metadata and actual billing for a new
assessment.

Current decision:

1. Do not enable OpenRouter response caching. It returns a prior response verbatim, conflicts
   with the live-web/fresh-execution contract, and only hits for identical complete requests.
2. Only benchmarks enable ASK answer reuse: historical loading uses `historical_ask_v1`;
   the engine stores live answers for repeated questions in one game under `same_episode_ask_v1`.
   The benchmark adds eligible completed-game answers under `same_execution_ask_v1` for later games.
   A hit makes no provider request; prompt caching on misses remains unchanged.
3. Do not pad the Oracle prompt or add caching-only instructions.
4. Leave provider automatic prompt caching available. Record `cached_input_tokens` and
   `cache_write_tokens` in nested metrics and the full provider usage object in both the
   privileged audit and the sanitized per-call result audit.
5. Use a stable subject/run session key and a prompt cache key derived from the prompt version
   and subject snapshot. Continue measuring realistic sequences of different questions within
   the provider's cache lifetime before claiming savings.

Primary and recovery research use distinct prompt versions, session namespaces, and cache
keys. The recovery request contains the same trusted subject and current question, but no
primary query, answer, evidence, outcome, provider trace, or history. Its fixed prompt selects
alternative strategies by question family. This separation prevents a cache or sticky-routing
hint from becoming a channel for prior research state. Recovery is expected to be uncommon, so
its cache reads, writes, latency, search count, and cost must be measured separately. It is not
padded and no savings are assumed.

Revisit this decision when prompts, search mode, models, routes, prices, retention, or expected
reuse change. Multi-question game metrics are available for these assessments.

## Reviewer and Judge assessment

The no-web Reviewer and Judge each have a stable system policy and structured-output schema,
followed by a variable trusted subject snapshot, question, and numbered evidence excerpts.
Standard and concise prefixes include the bounded, labelled model-knowledge fallback.
Qualified review remains evidence-only; only its Judge can use knowledge under the explicit
`judge_stable_knowledge_v1` policy. The selected versions and schemas keep those prefixes
separate. Their prompts are not padded to cross a provider cache threshold.

The current Reviewer route is `google/gemini-3.5-flash-lite` pinned to Google AI Studio. The
Judge keeps the exact `anthropic/claude-opus-5` model and uses OpenRouter automatic backend
routing. These models were selected independently from the OpenAI research Oracle to reduce
correlated model-family errors. Cache thresholds, write/read pricing, and controls may differ
between the resolved Judge providers, so measurements and savings claims must remain role- and
resolved-provider-specific.

Each role uses a distinct session namespace and a prompt-cache key derived from its role,
prompt version, and subject snapshot. Neither namespace is shared with the Oracle, Guesser,
Guess Validator, or the other quality-control role. Automatic provider prefix caching remains
available. Fresh role calls never reuse a prior response. A benchmark ASK cache hit instead
bypasses the complete adjudication pipeline and retains its original provenance. Every fresh
call records cache reads, writes, input tokens, cost, and latency. No savings are claimed
until representative repeated-question runs demonstrate actual role-specific cache reuse and
a favorable write/read break-even.

## Guess Validator generic-kind assessment

`strict-guess-validator-v2-generic-kinds` adds explicit acceptance rules for general kinds
and their subtypes. It changes only the Validator's fixed system prefix. The existing
Validator cache key already includes its prompt version, configuration ID, and trusted
subject; the new version separates this prefix from v1. Its session and cache namespaces
remain isolated from every other role. Only the subject and current guess follow the fixed
prefix; previous questions, decisions, evidence, and explanations remain absent.

Retain the configured exact GPT-5.6 Luna/OpenAI route and automatic best-effort prompt caching.
The configuration records a 1,024-token threshold and a 300-second observation window.
The local 6 September 2026 targeted validation
made ten fresh calls on that route. Inputs ranged from 581 to 615 tokens, with no cache reads
or writes. Total billed cost was $0.0020352 and summed provider latency was 19.474 seconds.
The endpoint metadata captured for that validation
reported standard prices of $0.20 per million input tokens, $1.20 output, $0.02 cache read,
and $0.25 cache write. These differ from the retained configuration's historical input/cache
price estimates; this check uses actual provider billing and changes no route or catalog price.
The longer prompt remained below the configured threshold, so no cache savings are claimed.
Do not pad, reuse responses, or share privileged conversation state. Historical Validator
calls retain their original version and billing. The validation report and route snapshot
remain private supporting artifacts.

## Guesser assessment and enforcement

The Guesser is one logical episode session, but OpenRouter remains stateless. Deep20Bench sends
the full visible transcript on every call and uses a stable episode `session_id` for sticky
routing. It also sends a stable `prompt_cache_key` derived from the Guesser configuration,
prompt version, and the prompt-relevant `max_questions` value. Reporting and eligibility fields
such as `benchmark_mode`, Oracle-evidence retention, and Guesser-conversation retention are
excluded from the namespace because they do not change the provider request. Hidden provider
reasoning is neither persisted nor replayed.

The default question limit was reduced from 50 to 40 on 6 September 2026. All Guesser profiles
render the configured number through their existing prompt templates; template versions and
schemas are unchanged. The existing `max_questions` cache-key field separates the 40- and
50-question prefixes. The transcript remains append-only, and all privileged role boundaries
remain unchanged. Keep automatic prefix caching, route thresholds, and configured prices;
the shorter maximum episode offers fewer possible prefix reuses, so no cost or cache saving
is assumed. Measure actual tokens, latency, and cost on future runs. No response caching or
padding is added.

Messages are append-only and canonically serialized. The fixed instructions, configured output
format, model parameters, and earlier action/answer messages remain an exact prefix; strict
routes also keep the same structured-output schema. Only the new tail changes. A contract
failure appends the same fixed correction tail for every subject and parser failure; the
malformed response itself is absent. Final-turn enforcement happens in the engine without
changing the configured output format.

Ox Alpha is registered in JSON-object mode because its pinned Stealth endpoint did not
advertise strict JSON Schema support on 23 August 2026. That choice changes only the configured
provider response-format parameter: the stable prompt, local action schema, visible history,
and scored recovery remain unchanged. The endpoint advertised zero input and output prices and
did not advertise implicit prompt caching. Its configuration therefore keeps automatic caching
as best effort, records any reported cache telemetry, and claims no cache savings.

Gemini 3.8 Flash (`M-0021`) uses the Google AI Studio route with automatic best-effort
prefix caching. On 4 September 2026, the
[OpenRouter endpoint metadata](https://openrouter.ai/api/v1/models/google/gemini-3.8-flash/endpoints)
advertised implicit caching, $0.75 per million input tokens, $3.75 per million output tokens,
and $0.075 per million cache-read tokens for that standard route. The saved assessment marked
these introductory prices for reassessment after 31 December 2026; new launches still require
a current route check. The configuration uses a 4,096-token minimum and a 300-second
observation window. Check Google's [context-caching documentation](https://ai.google.dev/gemini-api/docs/caching)
alongside route metadata when reassessing them; implicit retention varies and is not guaranteed. Automatic cache writes
use the normal input rate without explicit cache storage. The existing fixed instructions and
append-only visible transcript supply the shared prefix. Short games may stay below the
threshold, so no padding or explicit cache breakpoint is added and no savings are assumed.
Reported reads, writes, discounts, cost, and latency remain the evidence for actual reuse.

GPT-6 Astra (`M-0022`) uses `openai/gpt-6-astra` pinned to OpenAI with high reasoning
and automatic best-effort prefix caching. On 4 September 2026, the
[OpenRouter endpoint metadata](https://openrouter.ai/api/v1/models/openai/gpt-6-astra/endpoints)
advertised standard-route prices of $10 per million input tokens, $50 per million output
tokens, $1 per million cache-read tokens, and $12.50 per million cache-write tokens.
The saved configuration uses a 1,024-token minimum, a 1,800-second observation window, and
the 1.25 write multiplier. Consult [OpenAI's caching documentation](https://developers.openai.com/api/docs/guides/prompt-caching)
and the exact OpenRouter route before a new assessment; the observation window is not a
guarantee of cache retention. The captured OpenRouter endpoint metadata marked implicit caching as unsupported,
so actual route reuse remains unverified. The existing stable prefix is retained without
padding or explicit breakpoints; no cache savings are assumed.

The local 4 September 2026 opening-turn smoke test
passed the strict Guesser action contract on the expected model/provider with one request,
588 input tokens, 99 output tokens, 6.035 seconds of latency, and $0.01083 cost. It reported
zero cache-read/write tokens and no cache discount. This sub-threshold canary establishes
route and output-contract operation only; it does not establish cache reuse or game performance.
The supporting canary record remains private.

GLM-5.3-Flash (`M-0023`) is a new registration, separate from the historical Ox Alpha
registration (`M-0017`). It uses `z-ai/glm-5.3-flash` pinned to Z.AI with high reasoning,
JSON-object output, and automatic best-effort prefix caching. The
[OpenRouter endpoint metadata](https://openrouter.ai/api/v1/models/z-ai/glm-5.3-flash/endpoints)
on 8 September 2026 advertised $0.075 input, $0.25 output, and $0.015 cache reads per
million tokens. Z.AI's 50% promotion ends on 9 September 2026 at 16:00 UTC; reassess these
estimates before later launches. Undiscounted input/output/cache-read rates are
$0.15/$0.50/$0.03. No separate cache-write rate was advertised.

The endpoint marked implicit caching as unsupported and published no minimum prefix or
retention guarantee. The configuration retains the existing 1,024-token and 300-second
observation defaults, not verified provider thresholds. Keep the fixed instructions and
append-only visible transcript without padding or explicit cache storage. Record actual
reads, writes, discounts, latency, and billing; no cache savings are assumed. JSON-object
mode uses the same strict local action validation and canonical FORMAT_ERROR recovery.
Neither the new route nor its cache namespace introduces privileged Guesser state or
Guesser response reuse.

MiniMax M3 (`M-0024`) uses `minimax/minimax-m3` pinned to CoreWeave with high reasoning
through OpenRouter's generic reasoning control, strict JSON Schema output, and provider seed
support. On 8 September 2026, the
[OpenRouter endpoint metadata](https://openrouter.ai/api/v1/models/minimax/minimax-m3/endpoints)
advertised the CoreWeave FP4 route at $0.23 input, $0.96 output, and $0.05 cache reads per
million tokens, with no separate cache-write price. The route did not advertise implicit
caching or publish a minimum prefix or retention guarantee. The 1,024-token and 300-second
values are observation defaults, not verified provider guarantees.

Keep automatic best-effort exact-prefix caching and the existing fixed instructions and
append-only visible transcript. Do not pad prompts, add explicit cache storage, or reuse
Guesser responses. Record actual cache tokens, discounts, latency, and billed costs; no cache
savings are assumed. The separate configuration namespace preserves all Guesser isolation
boundaries. Recheck this route's prices and capabilities before later launches.

Muse Spark 1.3 Contributor (`M-0026`) uses `meta/muse-spark-1.3-contributor` pinned to
Meta with high reasoning, strict JSON Schema output, and no provider seed. On
9 September 2026, the
[OpenRouter endpoint metadata](https://openrouter.ai/api/v1/models/meta/muse-spark-1.3-contributor/endpoints)
advertised $0.10 input, $0.20 output, and $0.002 cache reads per million tokens, with no
separate cache-write price. The endpoint marked implicit caching as unsupported and did not
publish a minimum prefix or retention guarantee. The 1,024-token and 300-second values are
observation defaults; the 1.00 write multiplier is an accounting estimate, not a measured rate.

Keep automatic best-effort exact-prefix caching with the existing fixed instructions and
append-only visible transcript. The configuration ID separates its Guesser cache namespace.
No padding, explicit cache storage, response reuse, or privileged state is added. This
registration was checked offline against public route metadata; actual cache reads, writes,
discounts, latency, and billed costs remain unmeasured. Recheck the route before a paid launch.
The [Contributor tier](https://openrouter.ai/meta/muse-spark-1.3-contributor) permits Meta to use
submitted prompts and outputs to improve its products; this registration retains that tier
explicitly in its model slug and display name.

Official configurations use `prompt_cache.policy: required` and must supply a compatible
successful cache-probe artifact before a game manifest can be created. The probe makes two
representative append-only requests and requires a cache creation/read, nonzero cached input
on the second request, exact routing, and a fresh generated response. Experimental
configurations use best-effort caching without this gate.

During an episode, an eligible cache miss within the configured TTL does not alter gameplay,
scoring, or publication eligibility. Short episodes that end before a second eligible request
report `not_applicable`. Every call records input, cache-read, cache-write, output and reasoning
tokens, provider cost/discount, latency, and an estimated cache saving using the pricing frozen
in the model configuration.

No production prompt is padded for caching. The probe uses a representative late-game
transcript solely to test the exact route's capability.

## Evaluation checklist

For each LLM integration:

1. Identify the exact prefix shared by successive calls.
2. Measure prompt tokens with the real provider rather than relying on character estimates.
3. Confirm the selected model's minimum cacheable prefix, retention, write price, and read
   discount.
4. Estimate how many calls reuse the prefix within the retention window.
5. Keep variable input after stable content where the API's prefix semantics permit it.
6. Log cache reads and writes next to input tokens, total cost, and latency.
7. Compare a representative uncached run with a representative cached run.
8. Document the decision, including why caching is disabled when it does not break even.

## Provider references

- [OpenAI prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)
- [OpenRouter prompt caching and sticky routing](https://openrouter.ai/docs/guides/best-practices/prompt-caching)
- [OpenRouter response caching](https://openrouter.ai/docs/guides/features/response-caching)
