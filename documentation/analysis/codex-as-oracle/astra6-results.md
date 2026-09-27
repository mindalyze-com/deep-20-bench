# GPT-6 Astra with direct Codex adjudication

The run solved **27 of 30 scheduled games**. All 27 completed games succeeded,
with a mean of **14.22 counted questions**. The $9 spending guard interrupted
the first door-handle game after four questions; the other two door-handle games
did not start. This is a partial experiment, not a completed 30-game benchmark.

The same 27 cases in the regular Astra reference run averaged **13.22 questions**.
Direct Codex adjudication used 27 more counted questions overall, or 1.00 more
per game. It performed better on 8 paired iterations, tied on 5, and used more
questions on 14. Both runs solved every matched case. This comparison does not
isolate an Oracle-model effect.

The live execution ran from 19:55 to 22:10 UTC on 10 September 2026, ending at
00:10 on 11 September in Europe/Zurich. Its detached Astra screen session has ended.

## Results

Scores are counted questions; lower is better. A correct terminal guess does not
add a counted question, while a rejected guess does. All numeric entries are
successful games. The interrupted game has no score and is excluded from averages.

| Subject | Regular Astra, iterations 1 / 2 / 3 | Codex support, iterations 1 / 2 / 3 | Regular mean | Codex mean |
| --- | --- | --- | ---: | ---: |
| Albert Einstein | 9 / 10 / 10 | 8 / 8 / 10 | 9.67 | 8.67 |
| Albert Schweitzer | 14 / 18 / 16 | 20 / 22 / 17 | 16.00 | 19.67 |
| Garfield | 7 / 8 / 9 | 10 / 20 / 11 | 8.00 | 13.67 |
| Achilles | 8 / 8 / 8 | 7 / 9 / 8 | 8.00 | 8.00 |
| Genghis Khan | 11 / 8 / 11 | 10 / 10 / 9 | 10.00 | 9.67 |
| Bike pump | 26 / 26 / 27 | 26 / 20 / 31 | 26.33 | 25.67 |
| Spider web | 13 / 25 / 17 | 17 / 16 / 22 | 18.33 | 18.33 |
| Eyebrow | 13 / 13 / 12 | 13 / 15 / 14 | 12.67 | 14.00 |
| Moon | 9 / 10 / 11 | 11 / 10 / 10 | 10.00 | 10.33 |
| Door handle | 20 / 15 / 18 | Interrupted / Not started / Not started | 17.67 | - |
| **Matched 27 games** | **357 total** | **384 total** | **13.22** | **14.22** |

The largest increase was Garfield's second iteration, from 8 to 20 questions.
The largest decrease was the second spider-web iteration, from 25 to 16.
The longest direct game was the third bike-pump iteration, at 31 questions.

| Completed-game metric | Value |
| --- | ---: |
| Scoring-eligible games / successes | 27 / 27 |
| ASK actions | 376 |
| GUESS actions / rejected guesses | 35 / 8 |
| Counted questions, including rejected guesses | 384 |
| Guesser calls | 411 |
| Guesser format violations / retried calls | 0 / 0 |
| Directional ASK answers reviewed | 365 |
| Reviewer agreements / disagreements | 365 / 0 |
| Judge invocations | 0 |
| Final ASK answers: YES / NO | 187 / 171 |
| Final ASK answers: RATHER_YES / RATHER_NO / UNKNOWN | 2 / 5 / 11 |

The benchmark records one infrastructure failure for the budget interruption.
It is not a wrong-answer loss and does not receive the model-failure score of 41.

## Method and scope

This follows the direct-support method in [README.md](README.md) and the earlier
[Gemini experiment](results.md). The user explicitly authorized the live run and
continuation, with a $9 total cap.

- **Guesser:** registered M-0022, `openai/gpt-6-astra`, high reasoning, strict
  structured output, OpenAI backend through OpenRouter, no provider fallback,
  and the unchanged 32,768-token output ceiling.
- **Schedule:** ten active subjects in catalog order, three consecutive games
  per subject, using B-0003 `qualified_v1`, base seed 0, paired variation tokens,
  the 40-question limit and final guess opportunity.
- **Support:** this Codex conversation supplied Oracle and Validator decisions,
  plus Reviewer decisions for every directional ASK answer. Normal Judge routing
  remained available, but no review disagreement occurred.
- **Research:** a fresh web search was issued for every ASK, including repeated
  questions. ASK answer reuse was disabled. Completed-game artifacts retain
  evidence, queries, brief support statements and role audits.
- **Isolation:** only final protocol answer tokens returned to Astra. Sources,
  support explanations, target records and private artifacts were not added to
  the Guesser-visible conversation.

The Guesser prompt recorded throughout the completed games is
`stateful-category-guesser-v16-five-answer-category-guide`. The support route is
`codex_interactive`, model `codex/current-thread`, provider `codex-local`.
All support roles used the same conversation context. **They were not independent
blind reviewers.** Their agreements do not measure independent review accuracy.

Some interpretations materially shaped the search. Gauge-equipped bicycle pumps
received positive answers to pressure-measurement questions, but guesses naming
only a gauge were rejected. Questions specifying an unselected pump construction
or operating subtype sometimes received `UNKNOWN`. A spider web was treated as
an assembled natural structure, distinct from silk as a material or a landform.
Broad vision-related eyebrow questions included its protective function, while
the narrower question about specialized sight receptors received `NO`.
These are recorded adjudication choices, not independently established ground
truth for every wording.

## Spending and interruption

| Accounting item | USD |
| --- | ---: |
| Guesser charges for 27 completed games | 4.7978075 |
| Guesser charges for interrupted door-handle game | 0.0438000 |
| Successful startup check | 0.0137900 |
| **Total reported provider charges** | **4.8553975** |
| Reservation for earlier startup with unavailable billing | 2.1000000 |
| **Reported charges plus retained reservation** | **6.9553975** |
| User cap | 9.0000000 |

The $2.10 amount is a conservative reservation, not a measured charge. The first
startup failed without retained billing telemetry. Attempts 002 and 003 stopped
locally before a model request, and attempt 004 passed its startup check.

Before every outgoing HTTP attempt, including retries,
[src/astra6_budget.py](src/astra6_budget.py) reserves the full output allowance,
an input bound of twice serialized request bytes plus 8,192 tokens, and a 10%
margin. Reported billing replaces that call's reservation. Unreported calls keep
their reservation. The guard checks the pinned standard route and price limits,
including cache-write pricing; it rejects unverified long-context pricing.

At the stop, $2.0446025 remained after reported charges and the startup reserve.
The next request's maximum allowance did not fit. The guard rejected it before
HTTP transmission with `experiment_spending_cap_reached`. The game wrapper
recorded `provider_request_failed`, and the one-failure circuit breaker stopped
scheduling. No output limit, reserve, or stopping rule was relaxed to continue.
The unsuccessful local request is not an additional billed call.

The ledger contains 417 physical-attempt entries: 416 metered calls from attempt
004, including its startup, and the earlier unmetered startup. The local budget
rejection did not increment this count. There were 415 successfully answered
interactive support requests: 411 in completed games and four in the interrupted
game.

The interrupted door-handle game received `YES`, `YES`, `NO`, `YES` for questions
about being human-made, being hand-carriable, using electricity, and being common
in homes. Its partial metrics are preserved. It has no completed-game transcript
or full completed evidence bundle; a separate local note records these four
decisions from the conversation.

## Reference comparison and caching

The reference is `BX-20260909-B-0003-experimental-M0022-002`. Its complete 30-game
Guesser charge is $5.2672050. For the **same 27 completed cases**, its charge is
$4.6925495 versus $4.7978075 here, an increase of $0.1052580, or 2.24%. This is
Guesser-only billing and excludes both runs' support costs.

The comparison confirms identical Guesser configuration, game policy, completed
subject snapshots, base seed and paired BEGIN messages. Execution dates, support
configuration and policies, support context, and ASK answer reuse differ. Missing
door-handle cases prevent a complete 30-game comparison.

Provider prompt-prefix caching remained automatic and best-effort, with the
registered 1,024-token threshold and 1,800-second observation window. No padding
or response caching was added. For the 27 completed games, telemetry reports:

| Token metric | Count |
| --- | ---: |
| Input tokens | 451,614 |
| Cached input tokens | 246,225 |
| Cache-write tokens | 36,057 |
| Output tokens | 48,151 |
| Reasoning tokens, included in output | 30,331 |

Cached input accounts for 54.52% of reported input. The existing reporting formula
estimates a $2.1258825 net input-cache reduction versus uncached input pricing,
after cache-write premiums. This is a calculated estimate, not a separate billing
credit. Codex support tokens, billing and cache behavior are unmeasured by this
bridge; its zero counters and null costs must not be read as free support.

## Verification and local artifacts

An offline audit loaded every saved trial through the typed artifact store and
verified integrity. All 27 completed Guesser conversations match the exact public
projection: one fixed system message, the permitted BEGIN fields, the model's
own structured actions, and corresponding final answer tokens. Their paired
BEGIN messages match the reference. A correct final guess ends the game without
appending an unused response. Every saved Guesser call resolved to Astra on
OpenAI, stopped normally, and reported no web search or fallback.

Every completed ASK has a research attempt and at least one recorded query.
Saved audits contain 399 model-reported query entries/searches across 376 ASKs.
Sequence 193 repeated a search after context compaction; its unique-query
submission counts one, not both tool invocations. Search provenance is therefore
model-reported rather than an exact independently collected search-call ledger.
The chat retains the actual web tool calls. Raw Guesser HTTP request bodies are
not retained for an independent transport replay audit.

Five focused offline budget/startup tests pass. Lint and strict type checks pass
for the Astra wrapper, budget module and their focused test files. Preparation
also exercised the existing bridge's isolation and routing checks offline.

| Artifact | Location |
| --- | --- |
| Execution ID | `BX-20260910-B-0003-codex-direct-M0022-004` |
| Private root | `private/reviews/astra6-direct-20260910-004/` |
| Frozen helper copies | Private root, `src/` |
| Benchmark state and trial results | Private root, `runs/M-0022/<execution>/` |
| Billing and startup usage | Private root, `budget.json`, `guesser-canary-usage.json` |
| Paired comparison | Private root, `comparison.json`, `comparison.md` |
| Offline verification | Private root, `verify_results.py`, `verification.json` |
| Interrupted-game decision note | Private root, `partial-door-handle.md` |

Earlier startup artifacts remain in `private/reviews/astra6-direct-20260910/`
and its `-002` and `-003` siblings. Raw evidence and supporting records remain
private and ignored by Git. Nothing was committed, pushed or published.

Read-only reporting commands from the repository root:

```sh
.venv/bin/python documentation/analysis/codex-as-oracle/src/astra6.py progress --attempt 4
.venv/bin/python documentation/analysis/codex-as-oracle/src/astra6.py comparison --attempt 4
.venv/bin/python private/reviews/astra6-direct-20260910-004/verify_results.py
```

These commands make no model calls. The old attempt is terminal; the commands
above do not resume it or launch further games.
