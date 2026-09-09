# Game usage

New B-0003 executions use `concise_knowledge_v1`: one research attempt requesting
`research_query_target` queries (default 3), with an API ceiling calculated as the target plus
two bonus calls. Valid completed answers within that ceiling retain normal independent
evidence/knowledge decisions and private `evidence`/`other` basis plus a supporting statement. This policy permits source-free directional answers
and retained UNKNOWN context; the earlier evidence/recovery rules below describe historical
policies. See [the current policy](../../../documentation/five-answer-experiment.md#concise-evidenceknowledge-policy).


Benchmark executions support [historical Oracle answer reuse](../../../documentation/oracle-history-cache.md) under the explicit
`historical_ask_v1`, `same_episode_ask_v1`, and `same_execution_ask_v1` policies. The benchmark
lazily loads verified historical trials and adds eligible live ASK answers after each completed,
scoring-eligible game. Later repetitions reuse these answers; resume restores them from verified
trial artifacts. The engine also stores answers immediately for normalized repeats within one
game. Repeats still count as questions. Reused ASK turns retain original evidence and marked
source provenance, with no new adjudicator calls or cost. Each Guesser conversation starts fresh;
cache metadata never enters it. Standalone commands keep fresh-call behavior. Guesser and
Validator responses are never cached. Older manifests retain their recorded cache scope.


The paired qualified_v1 game and Oracle profiles permit RATHER_YES/RATHER_NO for ASK in experimental mode. Identity validation remains three-valued. See [Five-answer experiment](../../../documentation/five-answer-experiment.md).

An experimental game policy may set `prompt_profile: concise_v1` for shorter instructions
about overlapping roles, uncertainty, and reconsidering assumptions. The default `standard`
retains the original prompt. See [Concise prompt experiment](../../../documentation/concise-prompt-experiment.md).

The `deep20-game` package runs one hidden-subject episode. It maintains the Guesser's complete
visible conversation, sends factual questions to the live-web Oracle with blind no-web
Reviewer/Judge quality control, and sends identity proposals to a strict no-web Guess
Validator. The library persists only through an injected typed audit sink and reports progress
only through an injected typed observer.

For the rationale and component boundaries, read the [game engine concept](Concept.md).

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

The default policy is experimental, reveals the subject's broad `entity_type`, permits 40
counted questions, allows one final guess-only call, and includes Oracle evidence in the final
result. It also includes the exact Guesser-visible conversation through the terminal assistant
action. Set `include_oracle_evidence: false` to omit source URLs and excerpts, or
`include_guesser_conversation: false` to emit an empty conversation list in `result.yml`; the
verbose component audits, when enabled, remain unchanged. A correct first guess therefore has
zero counted questions and one Guesser call.

Completed run IDs are immutable because `result.yml` cannot be overwritten. In verbose mode,
the manifest also rejects a changed policy, model configuration, catalog, prompt version, or
cache-probe context before the first paid call. Choose a new run ID for a changed configuration.

The 40-question default replaces 50 for new games. Historical results keep their recorded
limit. The fixed Guesser instructions declare the selected limit from the first request;
reaching it permits one final GUESS without another counted question.

## Compare a different Guesser

The Guesser is the benchmark variable. Give every candidate its own configuration ID and
model/route settings, then select it with `--guesser-config`:

```bash
uv run deep20 game play T-0001 \
  --run-id einstein-candidate-b-001 \
  --guesser-config config/guesser-candidate-b.yaml
```

Keep `config/oracle.yaml` - including its Reviewer and Judge routes - together with
`config/guess-validator.yaml`, `config/game.yaml`, and the subject catalog unchanged across
comparable runs. None of the adjudication roles inherits the Guesser configuration;
`--validator-config` selects the Guess Validator's separate pinned configuration when an
explicit override is needed.

## Guesser protocol

Every Guesser profile includes a fixed guide to `person`, `fictional_character`,
`mythological_figure`, `video_game_character`, and `thing`. The last category is deliberately
broad: it covers natural and human-made entities, living organisms, body parts, materials,
places, celestial bodies, phenomena, and concepts. The target may be a general kind or one
particular instance. These possibilities are examples of scope, not a list of benchmark
subjects. The complete guide is identical in every game; only the category field in `BEGIN`
varies by subject.

The guide uses new Guesser prompt versions in all three profiles. Start fresh execution IDs
for the revised prompts and use new cache probes where required. Historical results keep
their recorded instructions and versions.

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

The provider wire schema is discriminated by `action`: `ASK` requires `question` to be a string
and the two identity fields to be JSON null, while `GUESS` requires `question` to be JSON null
and both identity fields to be strings. This prevents strict-output providers from filling
inactive nullable fields with empty strings that the domain protocol would correctly reject.
Model configurations normally use `structured_output_mode: strict_json_schema`. A registered
route may use `json_object` when the exact provider lacks strict JSON Schema enforcement. It
still receives the same contract instructions and its output is validated locally against the
same branches without repair or response healing.
Active empty strings and every other schema violation create a scored contract-violation turn.
A Guesser provider call that ends without a completed structured action - a `length` finish,
an empty completed response, or another non-`stop` finish - is classified and scored the same
way, attributed to the model under test rather than to infrastructure.
Before the limit the turn is counted, no Oracle, Reviewer, Judge, or Guess Validator call is
made, and the engine appends one fixed `FORMAT_ERROR` event showing the required formats. The
next ordinary Guesser call is its chance to recover. On the final opportunity, malformed output
terminates without another correction.
After the policy's `max_consecutive_contract_violations` counted violations in a row (default
5), the episode terminates as a scoring-eligible protocol failure.

The engine starts with fixed instructions and a structured `BEGIN` message such as
`{"category":"person","event":"BEGIN","variation_token":"EAQCORIU"}`. It then appends the
canonical action and exactly one
profile-specific final answer response: three tokens for standard/concise ASK and all GUESS
actions, or five for qualified ASK. The entire visible transcript is resent on every call. The
only exception is the fixed `FORMAT_ERROR` event after invalid output. The malformed output and
dynamic validation details are not appended. The subject's identity and description, Oracle
evidence, Reviewer/Judge decisions or disagreement state, Validator explanations, provider
traces, raw output, and hidden reasoning never enter that transcript.

When valid Oracle research remains inconclusive after its recovery attempt, the Guesser
receives only `UNKNOWN`. That ASK counts normally and play continues. Question keywords no
longer determine whether the game is excluded from scoring. Actual technical failures still
end as infrastructure failures. Use fresh run IDs for the revised factual contract; existing
results keep their recorded outcomes.

## Identity acceptance

The Guess Validator uses `strict-guess-validator-v2-generic-kinds`. It judges the proposed
name and description together against the hidden subject's identity and explicit restrictions.
A general kind accepts a recognized subtype or design variant when the defining kind/function
is preserved. Unspecified shape, material, size, or design is not grounds for rejection or
uncertainty. A particular entity still requires that exact entity. The rule is shared across
subjects; the fixed prompt does not list catalog answers.

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

An explicitly restricted target does not accept a subtype that contradicts that restriction.
`UNKNOWN` remains available for unresolved or conflicting identity and still terminates the
game. It is never treated as success or automatically replaced with `YES`. ASK decisions
remain separate; an earlier Reviewer/Judge YES is not an identity verdict and is not passed
to the Validator. Explanations remain audit-only.

Use fresh execution IDs for the revised policy, retain old results with their original
Validator version, and distinguish versions when comparing runs. The v2 policy does not
retroactively reclassify the original Door handle canary.

## Session and prompt caching

Every Guesser call in an episode uses the same OpenRouter `session_id`. The
`prompt_cache_key` is stable for the Guesser configuration, prompt version, and prompt-relevant
`max_questions` value. Reporting-only policy fields, including `benchmark_mode`, do not change
the cache namespace.
These values improve sticky routing and prefix-cache reuse; they do not provide server-side
conversation memory.

Model configuration freezes the cache policy, cache control, minimum cacheable tokens, TTL,
and input/cache-write/cache-read pricing. Per-call audit records contain actual cache reads,
writes, provider discounts, cost, and latency. Guesser and Validator response caching is never
enabled. The benchmark's historical and same-game ASK policies are separate from provider
prompt caching and are disabled in standalone game commands.

The model configuration freezes a typed recovery policy. Within a shared 300-second allowance,
the adapter makes at most eight requests for transport failures and OpenRouter
408/429/500/502/503/504/524/529 responses, honoring `Retry-After`. It retries an empty or
incomplete response once; an output-limited (`length`) response is not re-sent, because an
identical request would deterministically exhaust the same output budget. For the Guesser it
becomes a scored contract-violation turn; for the Guess Validator it remains an
infrastructure failure. Oracle, Reviewer, Judge, and Guess Validator invalid structured output
may use their own bounded internal schema retry; a required quality-control call that still
fails is an infrastructure failure and never falls back to the provisional Oracle answer. The
Guesser does not invisibly retry invalid structured output: the engine charges a
contract-violation turn and, when budget remains, continues through the fixed `FORMAT_ERROR`
protocol. Exact transport replays keep the same route, messages, schema, session, cache key,
and seed. Failed output and recovery diagnostics are never appended to Guesser-visible history.
Attempts, grouped reasons,
recovered/exhausted counts, retry usage, latency, and cost remain reporting-only telemetry.
The allowance is scoped to one logical model call and its exact replays. Concurrent CLI
processes and independent calls have separate in-memory budgets; concurrent benchmark runs
must still use distinct immutable execution IDs.

Reasoning-model output ceilings must leave room for hidden reasoning as well as the small JSON
action. Reasoning routes use 16,384 output tokens, except DeepSeek V4 Flash, which retains
65,536; non-thinking routes use 4,096. The default Oracle, Reviewer, Judge, and Guess Validator
calls use 4,096. A hard wall-clock deadline bounds each logical call by its generation timeout
plus the recovery allowance.

To measure an exact route:

```bash
uv run deep20 game cache-probe \
  --guesser-config config/guesser-official.yaml \
  --output cache-probes/luna-medium.json
```

The probe uses two representative append-only calls. It succeeds only when the route is exact,
the second request reports cached input, and the response is freshly generated.

For an official run, first set `benchmark_mode: official` in the game policy and
`prompt_cache.policy: required` in the Guesser configuration. Run the probe with that exact
Guesser configuration, then pass the compatible artifact:

```bash
uv run deep20 game play T-0001 \
  --run-id einstein-official-001 \
  --game-config config/game-official.yaml \
  --guesser-config config/guesser-official.yaml \
  --cache-probe cache-probes/luna-medium.json
```

An unexpected eligible cache miss does not change play, scoring, or publication eligibility.
A short game without a second eligible request reports `cache_status=not_applicable`.

## Result

On every controlled terminal path, the command prints one schema-v9 `EpisodeResult` JSON
object and writes the same content to `result.yml`. Its top-level sections are:

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

The final result includes the trusted subject snapshot, complete resolved transcript, and - by
default - the Guesser's rendered system prompt and visible chat. Oracle, Reviewer, Judge, and
Validator prompts, raw provider responses, and full per-call provider traces remain
component-audit-only. Only the bounded `audit.calls` projection is retained in `result.yml`.
The retained research data is reporting-only and is never reused by the Guesser, a later Oracle
attempt, Reviewer, Judge, Validator, or another trial.

## Run artifacts

By default, a game writes only its terminal result:

```text
runs/<run-id>/
└── result.yml
```

Pass the general `--verbose` flag to retain all auxiliary artifacts:

```bash
uv run deep20 game play T-0001 --run-id development-game-001 --verbose
```

Verbose mode additionally writes the schema-v2 `manifest.json`, `oracle-calls.jsonl`,
`guesser-calls.jsonl`, `guess-validator-calls.jsonl`, and `episode-events.jsonl`. Component logs
retain complete credential-free requests/responses and call telemetry. Each Oracle-call record
contains its nested Reviewer and optional Judge audit traces rather than creating separate
role-specific files. Episode events reference component call IDs and contain the validated
action, final answer, counters, cache status, and terminal result.

`result.yml` is always atomically written with an integrity hash. Every verbose artifact record
also has an integrity hash and duplicate IDs are rejected. Controlled failures receive terminal
events in verbose mode; a recorded started episode without one is considered interrupted and is
not resumed.

`RunArtifactPolicy` is shared by every component. Its setting changes persistence only: it does
not change prompts, provider requests, Guesser-visible history, sessions, prompt-cache
namespaces, adjudication, scoring, or `result.yml`.

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

`GameEngine` receives independently constructed Guesser, Oracle facade, and Guess Validator
clients, a `GameAuditSink`, an `ExecutionObserver`, the component configurations, and the game
policy. The Oracle facade itself receives separate Oracle, Reviewer, and Judge providers. The
benchmark control plane is the production composition root. The CLI in
`source/execution/game/src/deep20_game/cli.py` is the standalone development composition root
and may select its own artifact path and logging policy.

## Test the package

Run the deterministic suite:

```bash
uv run pytest source/execution/game/tests
uv run ruff check source/execution/game
```

The paid Einstein end-to-end test is opt-in and is skipped by the normal test command.
