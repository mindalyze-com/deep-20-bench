# Game usage

The `deep20-game` package runs one game (episode) against one hidden subject. It keeps the
Guesser's full visible conversation and routes each action:

- Questions (ASK) go to the live-web Oracle, checked by the no-web Reviewer and Judge.
- Guesses (GUESS) go to a strict no-web Guess Validator.

The library saves data only through an injected typed audit sink and reports progress only
through an injected typed observer. For the reasoning behind this design, read the
[game engine concept](Concept.md).

## Prerequisites

Install the workspace and configure an OpenRouter credential:

```bash
uv sync
```

Credential loading is shared with the Oracle. Set `OPENROUTER_API_KEY`, or create the ignored
`private/openrouter.yml` file described in [Oracle usage](../oracle/Usage.md).

## Run one game

```bash
uv run deep20 game play T-0001 --run-id einstein-development-001
```

Defaults are loaded from:

- `config/game.yaml`
- `config/guesser.yaml`
- `config/guess-validator.yaml`
- `config/oracle.yaml`
- `config/subjects.yaml`

Use the corresponding `--game-config`, `--guesser-config`, `--validator-config`,
`--oracle-config`, and `--catalog-path` options to select other files.
The Reviewer and Judge are not separate CLI configuration files: their independent no-web
models and routing policies are the `reviewer` and `judge` sections of `config/oracle.yaml`.

The default policy:

- is experimental (not official),
- tells the Guesser the subject's broad `entity_type`,
- allows 40 counted questions, then one final guess,
- includes Oracle evidence and the exact Guesser-visible conversation (up to its last action)
  in the result.

Set `include_oracle_evidence: false` to leave out source URLs and excerpts, or
`include_guesser_conversation: false` to write an empty conversation list to `result.yml`.
Verbose component audits, if enabled, are not affected. A correct first guess has zero counted
questions and one Guesser call.

A finished run ID cannot be reused, because `result.yml` is never overwritten. In verbose mode,
the manifest also rejects a changed policy, model configuration, catalog, prompt version, or
cache-probe context before the first paid call. Use a new run ID when the configuration changes.

New games default to 40 questions instead of 50. Older results keep their recorded limit. The
Guesser's instructions state the limit from the first request. At the limit, the Guesser gets
one final GUESS that does not count as a question.

## Current policies

- **Answer research.** New B-0003 runs use `concise_knowledge_v1`: one research attempt that
  asks for `research_query_target` search queries (default 3), with an API limit of that target
  plus two extra calls. A valid answer within that limit keeps its independent evidence or
  knowledge decision, a private `evidence`/`other` basis, and a supporting statement. This
  policy allows directional answers without sources and keeps context for UNKNOWN answers. The
  older evidence and recovery rules further down describe earlier policies. See
  [the current policy](../../../documentation/five-answer-experiment.md#concise-evidenceknowledge-policy).
- **Answer reuse.** Benchmark runs can
  [reuse earlier Oracle answers](../../../documentation/oracle-history-cache.md) under the
  explicit `historical_ask_v1`, `same_episode_ask_v1`, and `same_execution_ask_v1` policies.
  The benchmark loads verified earlier rounds when first needed and adds eligible new ASK
  answers after each finished, scored game. Later rounds reuse them, and a resumed run restores
  them from verified round artifacts. Within one game, the engine also stores answers at once so
  that a repeated (normalized) question reuses them. Repeated questions still count. Reused
  turns keep their original evidence and a source label, with no new answer-checking calls or
  cost. Each Guesser conversation starts fresh, and cache details never enter it. Standalone
  commands always make new calls. Guesser and Validator responses are never cached. Older
  manifests keep their recorded cache scope.
- **Five answers.** The paired `qualified_v1` game and Oracle profiles allow RATHER_YES and
  RATHER_NO for ASK in official edition 1.1 and in explicit experimental variants. Guess
  validation still uses three answers. See
  [Five-answer profile](../../../documentation/five-answer-experiment.md).
- **Concise prompt.** An experimental game policy may set `prompt_profile: concise_v1` for
  shorter instructions about overlapping roles, uncertainty, and rethinking assumptions. The
  default `standard` profile keeps the original prompt. See
  [Concise prompt experiment](../../../documentation/concise-prompt-experiment.md).
- **Edition 1.2 backend.** The main benchmark can combine this engine with the inactive
  [edition 1.2 backend interfaces](../../../documentation/edition-1.2-draft.md). Standalone game
  defaults do not change. Mock outcomes are synthetic and not scored. Synthetic and interactive
  roles cannot use answer caches. Only final checked answer tokens reach the Guesser, also when
  another role is played interactively.

## Compare a different Guesser

The Guesser is the benchmark variable. Give every candidate its own configuration ID and
model/route settings, then select it with `--guesser-config`:

```bash
uv run deep20 game play T-0001 \
  --run-id einstein-candidate-b-001 \
  --guesser-config config/guesser-candidate-b.yaml
```

For comparable runs, keep `config/oracle.yaml` (including its Reviewer and Judge routes),
`config/guess-validator.yaml`, `config/game.yaml`, and the subject catalog unchanged. No
answer-checking role inherits the Guesser configuration. Use `--validator-config` only if you
need to override the Guess Validator's separate pinned configuration.

## Guesser protocol

Every Guesser profile includes a fixed guide to the categories `person`,
`fictional_character`, `mythological_figure`, `video_game_character`, and `thing`. The `thing`
category is deliberately broad: natural and human-made objects, living things, body parts,
materials, places, celestial bodies, phenomena, and concepts. The subject may be a general kind
or one specific instance. These are examples of scope, not a list of benchmark subjects. The
guide is the same in every game; only the category in `BEGIN` changes by subject.

The guide came with new Guesser prompt versions in all three profiles. Use new execution IDs
for the revised prompts, and new cache probes where needed. Older results keep their recorded
instructions and versions.

The Guesser returns exactly one stable `result` envelope:

```json
{"result":{"action":"ASK","question":"Was this person born before 1900?","name":null,"description":null}}
```

or:

```json
{
  "result": {
    "action": "GUESS",
    "question": null,
    "name": "Albert Einstein",
    "description": "The theoretical physicist associated with relativity."
  }
}
```

The provider schema branches on `action`. `ASK` requires `question` to be a string and both
identity fields to be JSON null. `GUESS` requires `question` to be JSON null and both identity
fields to be strings. This stops strict-output providers from filling unused fields with empty
strings, which the protocol would reject.

Model configurations normally use `structured_output_mode: strict_json_schema`. A registered
route may use `json_object` if its provider does not enforce strict JSON Schema. It gets the
same instructions, and its output is validated locally against the same branches, with no
repair or response healing.

An empty string in a used field, or any other schema violation, creates a scored
contract-violation turn. So does a Guesser call that ends without a complete structured action:
a `length` finish, an empty response, or any other non-`stop` finish. These count against the
model under test, not as infrastructure failures.

Before the question limit, such a turn is counted, no Oracle, Reviewer, Judge, or Guess
Validator call is made, and the engine appends one fixed `FORMAT_ERROR` event that shows the
required formats. The Guesser's next normal call is its chance to recover. At the final guess,
invalid output ends the game with no further correction. After
`max_consecutive_contract_violations` counted violations in a row (default 5), the game ends as
a scored protocol failure.

The engine starts with fixed instructions and a structured `BEGIN` message such as
`{"category":"person","event":"BEGIN","variation_token":"EAQCORIU"}`. After each action it
appends the canonical action and exactly one final answer: one of three tokens for
standard/concise ASK and for every GUESS, or one of five for qualified ASK. The whole visible
transcript is sent again on every call.

The only other entry is the fixed `FORMAT_ERROR` event after invalid output. The invalid output
itself and any validation details are not added. The transcript never contains the subject's
identity or description, Oracle evidence, Reviewer or Judge decisions, disagreement state,
Validator explanations, provider traces, raw output, or hidden reasoning.

If valid Oracle research is still inconclusive after its recovery attempt, the Guesser gets
only `UNKNOWN`. The question counts normally and play continues. Question keywords no longer
decide whether a game is excluded from scoring. Real technical failures still end as
infrastructure failures. Use new run IDs for the revised answer rules; existing results keep
their recorded outcomes.

## Identity acceptance

The Guess Validator uses `strict-guess-validator-v2-generic-kinds`. It judges the proposed
name and description together against the hidden subject's identity and explicit restrictions.
For a general kind, a recognized subtype or design variant is accepted if it keeps the defining
kind or function. Missing details about shape, material, size, or design are no reason to
reject or answer UNKNOWN. A specific entity still requires that exact entity. The rule is the
same for all subjects; the fixed prompt does not list catalog answers.

Examples under the current catalog definitions:

| Target | Proposed identity and consistent description | Expected answer |
| --- | --- | --- |
| Door handle | Doorknob, a round handle turned to open a door | YES |
| Door handle | Lever handle used by hand to open a building door | YES |
| Door handle | Door, the hinged panel closing a doorway | NO |
| Door handle | Latch, the catch holding a door closed | NO |
| Door handle | Hardware, the general class of fittings | NO |
| Bike pump | Floor bicycle pump for inflating bicycle tires | YES |
| Earth's Moon | Luna, Earth's natural satellite | YES |
| Earth's Moon | Titan, Saturn's natural satellite | NO |
| Earth's Moon | Natural satellite, a generic category without identifying which one | NO |

If a subject has an explicit restriction, a subtype that contradicts it is not accepted.
`UNKNOWN` is still available when the identity is unclear or conflicting, and it still ends the
game. It never counts as success and is never turned into `YES`. ASK answers are separate: an
earlier Reviewer or Judge YES is not an identity decision and is not passed to the Validator.
Explanations are kept for audits only.

Use new execution IDs for the revised policy, keep old results with their original Validator
version, and tell versions apart when comparing runs. The v2 policy does not reclassify the
original Door handle canary.

## Session and prompt caching

Every Guesser call in a game uses the same OpenRouter `session_id`. The `prompt_cache_key`
depends only on the Guesser configuration, the prompt version, and `max_questions` (which
appears in the prompt). Reporting-only fields such as `benchmark_mode` do not change it. These
values help keep calls on the same provider and reuse cached prompt prefixes. They do not give
the provider any memory of the conversation.

Model configuration freezes the cache policy, cache control, minimum cacheable tokens, TTL,
and input/cache-write/cache-read pricing. Per-call audit records contain actual cache reads,
writes, provider discounts, cost, and latency. Guesser and Validator response caching is never
enabled. The benchmark's historical and same-game ASK policies are separate from provider
prompt caching and are disabled in standalone game commands.

The model configuration fixes a typed retry policy:

- Within a shared 300-second allowance, the adapter makes at most eight requests for transport
  failures and OpenRouter 408/429/500/502/503/504/524/529 responses, and honors `Retry-After`.
- It retries an empty or incomplete response once. A response cut off by the output limit
  (`length`) is not sent again, because the same request would hit the same limit. For the
  Guesser this becomes a scored contract-violation turn; for the Guess Validator it stays an
  infrastructure failure.
- The Oracle, Reviewer, Judge, and Guess Validator may retry invalid structured output a
  limited number of times internally. If a required check still fails, that is an
  infrastructure failure; the provisional Oracle answer is never used instead.
- The Guesser never retries invalid output invisibly. The engine counts a contract-violation
  turn and, if turns remain, continues with the fixed `FORMAT_ERROR` event.
- Exact transport retries keep the same route, messages, schema, session, cache key, and seed.
  Failed output and retry details are never added to the Guesser's history.

Attempts, grouped reasons, recovered and exhausted counts, retry usage, latency, and cost are
reporting-only telemetry. The allowance covers one logical model call and its exact retries.
Separate CLI processes and independent calls have separate in-memory budgets; concurrent
benchmark runs must still use different execution IDs.

Output limits for reasoning models must leave room for hidden reasoning as well as the small
JSON action. Reasoning routes use 16,384 output tokens (DeepSeek V4 Flash keeps 65,536);
non-thinking routes use 4,096. The default Oracle, Reviewer, Judge, and Guess Validator calls
use 4,096. Each logical call has a hard time limit: its generation timeout plus the retry
allowance.

To measure an exact route:

```bash
uv run deep20 game cache-probe \
  --guesser-config config/guesser-official.yaml \
  --output cache-probes/luna-medium.json
```

The probe makes two typical calls, the second extending the first. It succeeds only if the
route is exact, the second request reports cached input, and the response is newly generated.

For an official run, set `benchmark_mode: official` in the game policy and
`prompt_cache.policy: required` in the Guesser configuration. Run the probe with exactly that
Guesser configuration, then pass its output file:

```bash
uv run deep20 game play T-0001 \
  --run-id einstein-official-001 \
  --game-config config/game-official.yaml \
  --guesser-config config/guesser-official.yaml \
  --cache-probe cache-probes/luna-medium.json
```

An unexpected cache miss does not change play, scoring, or whether the game can be published.
A short game with no second eligible request reports `cache_status=not_applicable`.

## Result

Whenever a game ends in a controlled way, the command prints one schema-v9 `EpisodeResult`
JSON object and writes the same content to `result.yml`. Its top-level sections are:

- `run`: IDs, subject, timestamps, and wall-clock `duration_ms`.
- `outcome`: success, terminal reason, scoring eligibility, and publication eligibility.
- `summary`: turn/question counters, cache status, component/all-in costs, and component/all-in
  token totals, plus Oracle quality-control agreement, disagreement, Judge outcome,
  answer-change, final-`UNKNOWN`, and Reviewer/Judge cost totals.
- `models.under_test`, identifying the Guesser configuration, requested and actually resolved
  model/provider routes, reasoning effort, and prompt version being benchmarked, alongside the
  aggregate Oracle and Validator version information.
- `turns`: the ordered transcript. Each action has a nested adjudication containing its answer,
  component call ID, Oracle evidence or Validator explanation, and counting state. Oracle turns
  also contain the provisional Oracle decision, optional Reviewer/Judge decisions,
  disagreement flag, decision path, question type, and final answer.
- `guesser_conversation`: the exact system/user/assistant role and content visible to and
  produced by the Guesser. Assistant actions retain the canonical `{"result": {...}}` provider
  envelope, ending with its terminal action and excluding the terminal
  adjudication it never saw. Reporting-only `turn_number` metadata links each assistant action
  and returned answer to the corresponding resolved turn; it is absent from the system and
  `BEGIN` entries and is never sent to the Guesser.
- `llm_details`: deeply nested immutable configuration and aggregate call, token, cache, cost,
  and latency metrics for Guesser, the complete Oracle pipeline, and Validator. The Oracle
  configuration includes the independently pinned Reviewer and Judge routes; quality-control
  costs are also separated in the summary. Component `total_tokens` is input plus output;
  reasoning tokens remain a separate subset and are not counted twice.
- `audit`: a versioned chronological call log. Each entry has its component call ID and turn,
  prompt version/hash, safe provider route and completion state, usage, recovery, output length,
  and bounded search/citation/router telemetry. Oracle calls contain separate primary,
  optional research-recovery, Reviewer, and Judge entries. Their research summary records the
  deterministic question class, strategy, outcome, resolution, evidence count, and bounded
  query strings labelled `model_reported`. It contains no prompt or response body, raw output,
  citation URL,
  session, cache key, response ID, credential, header, or router endpoint. Its
  `unavailable_call_count` makes missing safe traces explicit. Older schema-v9 results may omit
  the additive `audit` section.

The Python boundary is fully typed: `EpisodeResult` and every nested run, outcome, summary,
model-version, turn, adjudication, evidence, component-configuration, and metric object is a
Pydantic model. Dictionaries are introduced only by explicit JSON/YAML serialization.

The result includes the trusted subject snapshot, the full resolved transcript, and, by
default, the Guesser's system prompt and visible chat. Oracle, Reviewer, Judge, and Validator
prompts, raw provider responses, and full per-call traces appear only in component audits.
`result.yml` keeps only the limited `audit.calls` summary. The research data kept there is for
reporting only. It is never reused by the Guesser, a later Oracle attempt, the Reviewer, Judge,
Validator, or another round.

## Run artifacts

By default, a game writes only its terminal result:

```text
runs/<run-id>/
└── result.yml
```

Pass `--verbose` to keep all auxiliary artifacts:

```bash
uv run deep20 game play T-0001 --run-id development-game-001 --verbose
```

Verbose mode also writes the schema-v2 `manifest.json`, `oracle-calls.jsonl`,
`guesser-calls.jsonl`, `guess-validator-calls.jsonl`, and `episode-events.jsonl`. Component logs
keep complete requests and responses (without credentials) and call telemetry. Each Oracle call
record contains its Reviewer and optional Judge traces; there are no separate files per role.
Episode events reference component call IDs and contain the validated action, final answer,
counters, cache status, and final result.

`result.yml` is always written atomically with an integrity hash. Every verbose record also has
an integrity hash, and duplicate IDs are rejected. In verbose mode, controlled failures get a
final event; a started game without one counts as interrupted and is not resumed.

All components share `RunArtifactPolicy`. It only controls what is saved. It does not change
prompts, provider requests, Guesser-visible history, sessions, prompt-cache namespaces, answer
checks, scoring, or `result.yml`.

Inspect a completed episode without exposing full call details:

```bash
jq -c \
  'select(.event_type == "episode_finished") | .payload.result' \
  runs/einstein-development-001/episode-events.jsonl
```

## Python contract

The engine's public boundary is:

```python
result = engine.play(GameRequest(run_id="einstein-development-001", subject=subject))
```

`GameEngine` receives separately built Guesser, Oracle facade, and Guess Validator clients, a
`GameAuditSink`, an `ExecutionObserver`, the component configurations, and the game policy. The
Oracle facade gets separate Oracle, Reviewer, and Judge providers. In production, the benchmark
control plane wires everything together. For development, the standalone CLI in
`source/execution/game/src/deep20_game/cli.py` does this and may choose its own artifact path and
logging policy.

## Test the package

Run the deterministic suite:

```bash
uv run pytest source/execution/game/tests
uv run ruff check source/execution/game
```

The paid Einstein end-to-end test is opt-in; the normal test command skips it.
