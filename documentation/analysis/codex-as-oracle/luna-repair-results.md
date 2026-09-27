# GPT-5.6 Luna: replay of the five failed games

Completed on 11 September 2026, Europe/Zurich. Each of the five failed cases from the
[original Luna experiment](luna-results.md) received one new attempt. **Three succeeded;
two still failed.** All five completed without infrastructure failure.

The original result remains **25 successes in 30 games, with a mean score of 22.67**.
This is a separate diagnostic replay selected after observing failures. Its results do not
replace the original scores or form a new 30-game benchmark result.

## Results

Iteration numbers below identify the cases selected from the original experiment. All five
share a separate replay execution; each has a fresh episode identity and one attempt only.

| Subject / original iteration | Original score | Replay score | Replay outcome |
| --- | ---: | ---: | --- |
| Albert Schweitzer / 3 | 41 F | 21 | Successful identification |
| Bike pump / 1 | 41 F | 19 | Successful identification |
| Bike pump / 2 | 41 F | 41 F | ASK on the final guess-only opportunity |
| Spider web / 1 | 41 F | 33 | Successful identification |
| Door handle / 1 | 41 F | 41 F | Incorrect final guess: crank handle |

**F** marks a scoring-eligible failure. The five replay scores total 155, for a mean of
31.00 within this selected subset. Successful guesses are uncounted; a model failure scores
41. There were 153 counted turns, 158 Guesser calls, 153 adjudicated ASK actions, and four
validated guesses. The three successful games had no earlier incorrect guesses.

Bike pump / 2 produced valid structured ASK output after its 40 counted turns. The engine
ended it with `ask_after_question_limit`, without another Oracle or Validator call. Door
handle used the final opportunity to guess a generic crank handle for turning a machine
or mechanism. Its description did not identify the building-door fitting, so validation
returned NO. These are retained game outcomes, not interrupted runs awaiting completion.

## Scope and method

The user requested repair of the failed Luna runs under the existing $5 authorization.
The benchmark's [repair policy](../../../source/execution/benchmark/README.md) repairs
infrastructure failures. All five original failures were scoring-eligible model outcomes,
so they were preserved and replayed as separate diagnostic episodes.

- Original execution: `BX-20260910-B-0003-codex-direct-M0001-004`.
- Replay execution: `BX-20260911-B-0003-luna-failed-case-replay-001`.
- Guesser: registered `M-0001`, `openai/gpt-5.6-luna`, high reasoning, pinned to OpenAI
  through OpenRouter with fallbacks disabled.
- Limits: the original 32,768-token output ceiling, 120-second timeout, B-0003
  `qualified_v1` profiles, 40 counted turns, and one final guess-only opportunity.
- Each episode used the original subject and configuration snapshots, base seed 0, and
  original trial number for the paired variation token. Each started a fresh Guesser session.
- Exactly one replay per selected case, no additional startup canary, no ASK-answer reuse,
  and no response caching. Every ASK received fresh research with at most three queries.

The private launch plan froze the five original contexts and the prior spending ledger.
The launcher checked the original artifact-tree hash and registered Guesser configuration
before making paid calls. It saved normal signed trial artifacts through the existing game
engine and artifact store. These five standalone diagnostic results have no separate
30-game schedule or aggregate benchmark manifest. They are not automatic regression inputs.

No engine, public prompt, model setting, or scoring rule was changed for this replay.
The canary cache-key correction described in the original report was already in place.
The launcher claims a fresh replay directory once and rejects a second live launch there.
It does not repeat difficult games until they succeed.

## Interpretation observations

The operator reconsidered ambiguous classifications under the existing Oracle policy.
Unresolved scope could return UNKNOWN, while broad alternatives still required evaluating
every branch. This was manual interpretation, not a versioned prompt correction or an
independently scored answer set.

- **Schweitzer:** early questions about primary fame received UNKNOWN or qualified answers
  across medicine, religion, philosophy, and peace work. The game reached his Nobel Peace
  Prize and medical work before identifying him at score 21.
- **Bike pump / 1:** the game reached a question about transferring liquid or gas. Air
  satisfied the gas branch; subsequent inflation and bicycle-tire questions led to success.
- **Bike pump / 2:** component questions about a hinged valve-head lever, a check-valve
  spring, and a valve-attachment latch received YES. These did not establish that the pump's
  primary purpose was clamping or gripping. Luna continued exploring other categories and
  failed to use its final guess opportunity. The spring answer has direct support: SILCA
  describes a ball or disc and spring in most modern pump check valves.
  [SILCA valve assembly](https://silca.cc/collections/re-build-kits/products/inner-valve-assembly).
- **Spider web:** the replay distinguished the completed external structure from a body
  part or its raw silk. It eventually reached production by a spider and identified the web.
  It did not repeat the original atmosphere question, so its success does not measure the
  effect of correcting that particular answer.
- **Door handle:** broad manipulation and manual-mechanism questions received YES because
  the handle moves a door and can turn a latch spindle. Schlage describes that spindle
  connection explicitly. Luna explored many rotating tools and ended at crank handle.
  The original question about primarily containing, storing, or holding something did not
  recur. This replay therefore did not directly test a revised answer to that question.
  [Schlage hardware definitions](https://www.schlage.com/en/blog/product_updates/door-hardware-terms-and-parts-of-a-door-lock.html).

The questions and answers differed from the original games. Generation remained stochastic;
the shared variation token is not a supported provider seed. Selecting only previous failures,
changing question paths, and the operator's knowledge of those failures prevent a causal
claim that the three successes demonstrate a repaired Oracle.

Oracle, Reviewer, and Validator decisions still came from the same Codex conversation.
The bridge generated the required blind input projections, but the operator had wider
conversation context. Reviewer agreement is not independent corroboration. That limitation
remains from the original method.

## Research and provider measurements

| Final ASK answer | Count |
| --- | ---: |
| YES | 36 |
| NO | 106 |
| RATHER_YES | 2 |
| RATHER_NO | 1 |
| UNKNOWN | 8 |
| Total | 153 |

All 145 directional answers received matching Reviewer adjudication. UNKNOWN was final
eight times; no disagreement or Judge call occurred. The Oracle recorded 63 evidence-based
decisions and 90 with other basis, including trusted-subject deductions and ordinary knowledge.

There were 158 recorded research queries: 150 questions used one, one used two, and two used
three. There were no duplicate-query accounting exceptions. Research counts and source
summaries are operator records, not independent network telemetry.

Provider prefix caching retained the registered automatic, best-effort policy and append-only
visible history. No padding was added. Cache measurements describe provider computation reuse;
the experiment reused no earlier adjudicated answer.

| Replay Guesser measurement | Value |
| --- | ---: |
| Input tokens | 238,124 |
| Cached input tokens | 197,299 |
| Cache-write tokens | 10,780 |
| Output tokens | 42,642 |
| Reasoning tokens, included in output | 35,069 |
| Calls reporting cache reads | 119 / 158 |
| Calls reporting cache writes | 124 / 158 |
| Summed provider latency | 805.453 seconds |
| Reported cost | $0.06382038 |

All five episodes were cache-compliant under the engine's observation rule. No call reported
an explicit dollar discount, so no measured savings claim is made. The episodes ran from
00:53:10 to 01:52:06 UTC, or 02:53 to 03:52 in Europe/Zurich, including operator research time.

## Cumulative spending

The replay retained the original $5 cap and all earlier charges and reservations.

| Accounting item | USD |
| --- | ---: |
| Original reported charges, including successful canary | 0.23703388 |
| Five replay games | 0.06382038 |
| Cumulative reported charges | 0.30085426 |
| Retained reserve for ten unmetered startup failures | 2.21056880 |
| Charges plus retained reserve | 2.51142306 |
| Authorized total cap | 5.00000000 |

All 158 new Guesser requests returned billing and HTTP 200 on the intended route, without
retries. The cumulative ledger contains 874 attempts, with the same ten unmetered startup
failures. The reserve is not reported spending and was not released on an assumption that
those attempts were free. Codex conversation and research costs remain unmeasured.

The shared spending guard reserved before every HTTP attempt. Its saved route-price bound
used maximum input/cache-write pricing of $1.00 and output pricing of $3.60 per million tokens,
the full output ceiling, conservative request-token estimation, and a 10% margin. Actual
reported billing settled each new reservation. No further paid replay was launched.

## Verification and retained artifacts

The offline verifier loaded all five typed trial results with integrity checks. Each contains
one attempt and no superseded result. It reconstructed and matched all 158 Guesser, 153 Oracle,
145 Reviewer, and four Validator prompt hashes. Guesser histories contained only fixed
instructions, category, the paired variation token, their own actions, and final allowed
tokens. Oracle and review inputs matched their specified blind projections.

No format violation, missing call audit, Guesser web search, provider fallback, response-cache
hit, or ASK-answer reuse was recorded. Raw HTTP bodies were not retained, so this checks saved
typed histories and prompt hashes rather than a separate network capture. The complete
original results tree matched its pre-replay hash. The final ledger reconciled to all replay
charges, preserved the earlier reserve, and remained below $5. Completion was saved, and the
replay's screen session, launcher, and caffeinate process exited.

Before the paid replay, the focused canary, preflight, bridge, and Luna budget checks passed
34 offline tests. The shared spending guard also passed its 18 offline tests. Final artifact
and accounting verification made no paid calls.

Private support artifacts remain ignored under `private/reviews/luna-repair-20260911/`:

| Artifact | Contents |
| --- | --- |
| `plan.json` | Frozen cases, original hashes, and carried budget |
| `runs/M-0001/BX-20260911-B-0003-luna-failed-case-replay-001/` | Five signed trial result trees |
| `decision-0001.json` through `decision-0157.json` | Submitted Oracle/review and Validator decisions |
| `verification.json`, `verify_results.py` | Measurements and offline prompt-hash/accounting verification |
| `budget.json`, `route-pricing.json`, `price-bound.json` | Cumulative accounting and launch-time route bounds |
| `events.jsonl`, `status.json`, `run.log` | Progress and terminal completion |
| `repair.py`, `operate.py`, `launch.sh` | Private replay launcher and operator helpers |

From the repository root, the saved results can be verified offline:

```sh
DEEP20_CODEX_EXPERIMENT=luna .venv/bin/python \
  private/reviews/luna-repair-20260911/verify_results.py
```

The original comparison and scores remain intact. This replay made no public code changes,
commit, push, or publication.
