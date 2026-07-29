# LLM caching

## Project rule

Every Deep20Bench component that calls an LLM must evaluate provider-side prompt caching.
That evaluation is not an instruction to turn caching on: the decision must be based on the
selected model, provider behavior, prompt size, repeated-prefix pattern, cache lifetime, and
measured cost.

Deep20Bench distinguishes three mechanisms:

| Mechanism | Meaning | Project decision |
| --- | --- | --- |
| Provider prompt caching | Reuses computation for an exact prompt prefix while generating a fresh response. | Enabled according to the pinned route and measured per component. |
| OpenRouter response caching | Returns a previous complete response for an identical request. | Prohibited for all benchmark LLM calls. |
| Application/client cache | Stores and reuses an earlier answer in Deep20Bench. | Prohibited. |

Prompt caching is configured through API request fields; telling the model in natural-language
instructions to remember or cache answers does not create a provider cache.

Bounded retries for explicit no-result provider statuses resend the identical request and may
therefore receive a provider prompt-cache read. They never reuse a complete response and do not
change the application/response-cache prohibition. Attempt count and retry timing are measured
as transport telemetry, not added to any prompt or cache key.

The Guesser cache namespace includes the versioned branch-aware action schema hash. Invalid
structured output is not invisibly retried. It becomes a scored turn; when budget remains, the
next request appends the canonical `FORMAT_ERROR` while excluding the invalid output,
validation details, and recovery metadata from Guesser-visible state.

## Current Oracle assessment

The Oracle has useful repeated material across questions about one subject:

- The versioned system policy.
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

For GPT-5.6 and later, OpenAI currently bills cache writes at 1.25 times the normal input-token
rate; cache reads are discounted according to the particular model. Padding a short Oracle
prompt to the threshold can therefore cost more, especially if calls are spaced beyond the
cache lifetime or few questions share the exact prefix.

Current decision:

1. Do not enable OpenRouter response caching. It returns a prior response verbatim, conflicts
   with the live-web/fresh-execution contract, and only hits for identical complete requests.
2. Do not add an application answer cache.
3. Do not pad the Oracle prompt or add caching-only instructions.
4. Leave provider automatic prompt caching available. Record `cached_input_tokens` and
   `cache_write_tokens` in nested metrics and the full provider usage object in the audit.
5. Use a stable subject/run session key and a prompt cache key derived from the prompt version
   and subject snapshot. Continue measuring realistic sequences of different questions within
   the provider's cache lifetime before claiming savings.

This decision must be revisited when the game engine creates realistic multi-question runs or
when the default model/provider changes.

## Reviewer and Judge assessment

The no-web Reviewer and Judge each have a stable system policy and structured-output schema,
followed by a variable trusted subject snapshot, question, and numbered evidence excerpts.
Both versioned stable prefixes include the bounded, labelled model-knowledge fallback; this
does not add conversation memory or response reuse. Their prompts are intentionally short and
are not padded to cross a provider cache threshold.

The current Reviewer route is `google/gemini-3.5-flash-lite` pinned to Google AI Studio, while
the Judge route is `anthropic/claude-opus-5` pinned to Anthropic. These routes were selected
independently from the OpenAI research Oracle to reduce correlated model-family errors.
Google AI Studio and Anthropic have different cache thresholds, write/read pricing, and cache
controls; measurements and savings claims must therefore remain role- and provider-specific.

Each role uses a distinct session namespace and a prompt-cache key derived from its role,
prompt version, and subject snapshot. Neither namespace is shared with the Oracle, Guesser,
Guess Validator, or the other quality-control role. Automatic provider prefix caching remains
available, while OpenRouter response caching and application answer caching remain prohibited.
Every call records cache reads, writes, input tokens, cost, and latency. No savings are claimed
until representative repeated-question runs demonstrate actual role-specific cache reuse and
a favorable write/read break-even.

## Guesser assessment and enforcement

The Guesser is one logical episode session, but OpenRouter remains stateless. Deep20Bench sends
the full visible transcript on every call and uses a stable episode `session_id` for sticky
routing. It also sends a stable `prompt_cache_key` derived from the Guesser configuration,
prompt version, and the prompt-relevant `max_questions` value. Reporting and eligibility fields
such as `benchmark_mode`, Oracle-evidence retention, and Guesser-conversation retention are
excluded from the namespace because they do not change the provider request. Hidden provider
reasoning is neither persisted nor replayed.

Messages are append-only and canonically serialized. The fixed instructions, structured-output
schema, model parameters, and earlier action/answer messages remain an exact prefix; only the
new tail changes. A contract failure appends the same fixed correction tail for every subject
and parser failure; the malformed response itself is absent. Final-turn enforcement happens in
the engine without changing the provider schema.

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
