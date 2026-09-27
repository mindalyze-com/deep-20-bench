# GPT-5.6 Luna: direct Codex Oracle experiment

Completed on 11 September 2026, Europe/Zurich. All 30 requested games finished:
**25 successes, five model failures, and no infrastructure failures**. The mean question
score was **22.67**, compared with **21.03** for the saved regular Luna run. Lower is better.
Codex support therefore did not improve the overall score in this experiment.

The user approved ten active subjects with three consecutive iterations each, one startup
check, and a total $5 OpenRouter cap. Reported charges were **$0.23703388**. An additional
**$2.21056880** remains reserved for ten rejected startup attempts without billing data.
Charges plus that reserve total **$2.44760268**, within the cap. The reserve is not reported
spending. Codex conversation usage and research costs are not measured by this accounting.

A later user-requested [replay of the five failed cases](luna-repair-results.md) produced
three successes and two further failures. It is a separate diagnostic; all original scores
below remain unchanged. The replay report records the cumulative spending under the same $5 cap.

## Results against the saved regular run

The reference is `BX-20260908-B-0003-experimental-M0001-001`. The direct execution is
`BX-20260910-B-0003-codex-direct-M0001-004`. These are separate retained executions.

| Metric | Regular support | Direct Codex support |
| --- | ---: | ---: |
| Completed games | 30 | 30 |
| Successful games | 27 (90.0%) | 25 (83.3%) |
| Model failures | 3 | 5 |
| Infrastructure failures | 0 | 0 |
| Question-score total | 631 | 680 |
| Mean question score | 21.03 | 22.67 |
| Guesser calls | 658 | 705 |
| Adjudicated ASK actions | 624 | 668 |
| Validated guesses | 33 | 36 |
| Incorrect guesses | 6 | 11 |
| Recorded format violations | 0 | 0 |
| Final UNKNOWN answers | 19 | 30 |
| ASK answers reused | 13 | 0 |
| Retained-game Guesser cost | $0.18859194 | $0.23675728 |

A successful game scores its counted turns, including incorrect guesses before success.
The successful guess is uncounted. A model failure scores 41. Infrastructure failures would
have no score. The direct run used 675 counted turns; replacing each of its five failed-game
counts of 40 with the failure score of 41 gives the score total of 680.

In the following table, scores are in iteration order. **F** marks failure. The difference
is direct mean minus regular mean, so a positive value means the direct run used more turns.

| Subject | Regular scores | Direct scores | Regular mean | Direct mean | Difference |
| --- | --- | --- | ---: | ---: | ---: |
| Albert Einstein | 12 / 11 / 12 | 13 / 15 / 16 | 11.67 | 14.67 | +3.00 |
| Albert Schweitzer | 38 / 24 / 19 | 34 / 36 / 41 F | 27.00 | 37.00 | +10.00 |
| Garfield | 25 / 12 / 24 | 23 / 21 / 22 | 20.33 | 22.00 | +1.67 |
| Achilles | 8 / 6 / 7 | 8 / 8 / 7 | 7.00 | 7.67 | +0.67 |
| Genghis Khan | 13 / 15 / 16 | 14 / 13 / 15 | 14.67 | 14.00 | -0.67 |
| Bike pump | 27 / 41 F / 41 F | 41 F / 41 F / 40 | 36.33 | 40.67 | +4.33 |
| Spider web | 25 / 20 / 36 | 41 F / 17 / 18 | 27.00 | 25.33 | -1.67 |
| Eyebrow | 41 F / 23 / 26 | 24 / 33 / 16 | 30.00 | 24.33 | -5.67 |
| Moon | 10 / 13 / 11 | 10 / 11 / 9 | 11.33 | 10.00 | -1.33 |
| Door handle | 23 / 27 / 25 | 41 F / 26 / 26 | 25.00 | 31.00 | +6.00 |

Across matching subject/iteration pairs, 13 improved, 13 worsened, and four tied. The direct
score total was 49 higher, or 1.63 more per game. Eyebrow had the largest mean improvement;
Schweitzer had the largest regression. These are descriptive results from three iterations
per subject, not a causal estimate of Oracle quality.

## Method and comparability

- Guesser: existing `M-0001`, GPT-5.6 Luna (high), `openai/gpt-5.6-luna`, pinned to OpenAI
  through OpenRouter, with fallbacks disabled.
- Sampling and limits: high reasoning, 32,768 output tokens, 120-second request timeout,
  no provider seed, base seed 0, and the existing paired trial variation token.
- Game: B-0003 with paired `qualified_v1` profiles, 40 counted turns and one final
  guess-only opportunity. Subjects ran in catalog order, three consecutive games each.
- Support: this Codex conversation supplied Oracle, Reviewer, any required Judge, and
  Validator decisions through the typed bridge under `concise_knowledge_v1`.
- Every ASK received fresh research, with a maximum of three queries. There was no ASK-answer
  reuse. Source summaries and ordinary knowledge were recorded with their respective bases.
- Guesses were validated against the trusted subject's name, description, aliases, and
  restrictions. Compatible designs of a general kind were accepted; broader classes and
  different identities were rejected.

The saved Guesser configuration, game policy, subject snapshots, and base seed match the
regular reference. The main prompt versions also match: Guesser
`stateful-category-guesser-v16-five-answer-category-guide`, Oracle
`live-web-oracle-v17-labelled-source-context`, and Validator
`strict-guess-validator-v2-generic-kinds`. Both runs used Reviewer prompt
`oracle-reviewer-v12-labelled-source-context`.

The regular run used Luna as Oracle and Validator, Gemini 3.5 Flash Lite as Reviewer, and
Claude Opus 5 as Judge. It reused 13 compatible ASK answers. The direct run replaced these
support roles with this conversation and disabled reuse. The runs occurred on different dates.
The variation tokens were paired, but Luna's unsupported provider seed means its generation
was not made deterministic.

The direct support roles shared one conversation. The bridge generated blind role inputs,
but the operator already knew earlier decisions and the game context. Reviewer agreement
therefore does not establish independent corroboration. Manual interpretation consistency and
factual correctness were not independently scored. Scores were retained as played, without
retrospectively changing answers or restarting difficult games.

## Failures and incorrect guesses

| Subject / iteration | Terminal action | Outcome |
| --- | --- | --- |
| Schweitzer / 3 | GUESS Rudolf Otto | Incorrect final guess; score 41 |
| Bike pump / 1 | GUESS binder clip | Incorrect final guess; score 41 |
| Bike pump / 2 | GUESS floor jack | Incorrect final guess; score 41 |
| Spider web / 1 | ASK about an explosion or rapid combustion | ASK forbidden on the final guess-only opportunity; score 41 |
| Door handle / 1 | GUESS carabiner | Incorrect final guess; score 41 |

The spider-web action was valid structured output, but violated the final-opportunity rule
(`ask_after_question_limit`). It produced no Oracle call or Validator call. This explains the
zero recorded format violations alongside one Guesser protocol failure. There were 705
Guesser calls but only 704 support decisions: 668 ASK adjudications and 36 guess validations.

Seven other incorrect guesses were followed by continued play: Heinrich Grüber for
Schweitzer; caulking gun and hand air pump for bike pump; eyelashes, hair, and human hair for
eyebrow; and key for door handle. The bike-pump third iteration eventually succeeded on the
final opportunity, scoring 40. Its earlier “hand air pump” description covered tires, balls,
and other objects without identifying the bicycle-specific kind, so it was rejected.
The two successful door-handle games accepted a lever handle as a compatible design.

## Interpretation observations

These examples describe operator decisions and their subsequent game paths. They are not
independently established ground truth or proof that one answer caused a failure.

- **Schweitzer:** questions about primary fame, Christian significance, and theology were
  difficult to resolve consistently across his medical, philosophical, religious, and musical
  roles. Broad classifications and incomplete historical coverage sometimes returned UNKNOWN
  or a qualified answer. The third game spent turns exploring other religious traditions.
- **Bike pump:** air was treated as a substance under broad “dispense a substance” wording.
  Luna then explored several liquid and material dispensers before finding air in the third
  game. A workshop counted under “office or workplace.” These inclusive readings did not
  establish the narrower categories Luna subsequently explored.
- **Spider web:** the first game received YES for being located in Earth's atmosphere,
  interpreting an exposed web as suspended in near-surface air. Luna then spent many turns
  exploring weather and atmospheric phenomena. The later games reached an animal-produced
  external structure and succeeded. The atmosphere answer is a useful example of an ordinary
  spatial reading that may be unhelpful or too literal for classification.
- **Eyebrow:** the target remained the localized body feature, not hair in general or
  eyelashes. All three games recovered successfully from their incorrect broader or nearby
  guesses. This subject had the strongest average improvement over the reference.
- **Door handle:** “hold something” received YES because the fitting provides a handhold for
  controlling the door. The first game then explored storage and gripping devices and failed.
  The final game received YES to a broad “strike, press, or crush” question on the interpretation
  that pressing included transmitting hand force to push the door. This reading, and the
  distinction between “a tool” and “used as a tool,” illustrate judgment-sensitive answers.
  A stricter ordinary-use interpretation could disagree with them.

The supporting door-handle sources describe both its
[grip function](https://dictionary.cambridge.org/us/dictionary/english/handle) and
[knob/lever operation](https://www.schlage.com/en/home/products/knobs.html). They do not by
themselves settle every category interpretation above. Private turn records retain the exact
questions, final tokens, source summaries, and support statements for further examination.

## Research and adjudication totals

| Final ASK answer | Count |
| --- | ---: |
| YES | 240 |
| NO | 390 |
| RATHER_YES | 4 |
| RATHER_NO | 4 |
| UNKNOWN | 30 |
| Total | 668 |

All 638 directional answers received Reviewer adjudication, with agreement on every token.
UNKNOWN was final on 30 questions. There were no disagreements or Judge invocations.
The primary Oracle recorded 572 decisions with evidence basis and 96 with other basis.

The records contain 698 search queries: 641 questions used one, 24 used two, and three used
three. On two questions, a query was repeated after conversation compaction; search counts
retain both calls while attempted-query lists contain the unique query text. These occurred
on bike pump iteration 2, turn 15, and door handle iteration 1, turn 5. Research counts and
source summaries are operator-reported, not provider-verified search telemetry.

## Spending and startup correction

| Accounting item | USD |
| --- | ---: |
| 705 retained-game Guesser calls | 0.23675728 |
| One successful startup canary | 0.00027660 |
| Total reported billing | 0.23703388 |
| Reserve for ten unmetered rejected startup attempts | 2.21056880 |
| Reported billing plus retained reserve | 2.44760268 |
| Authorized cap | 5.00000000 |

The ledger contains 716 HTTP attempts in total. All 705 game requests and the successful
canary returned billing, used the intended model/provider, and needed no retries. Earlier
startup attempts returned HTTP 400 without usage or billing. They are not assumed free.

Startup failed because the qualified canary prompt-cache key contained 78 characters,
exceeding OpenAI's 64-character limit (`string_above_max_length`). The fix hashes the canary
role and prompt version to 64 characters. The standard canary key and game cache keys remain
unchanged. Prompts, schemas, sessions, and sampling were not changed by this fix. The failed
startup artifacts remain under the earlier private Luna directories; the corrected run used
a fresh execution ending in `004`.

The [Luna launcher](src/luna_live.py) reserves spending before every HTTP attempt, including
retries and failures. Its conservative bound uses four tokens per serialized request byte,
65,536 tokens of overhead, the full 32,768-token output ceiling, maximum advertised input or
cache-write pricing of $1.00 per million tokens, output pricing of $3.60 per million, and a
10% margin, capped at a separately checked $2 full-context bound. Reported billing settles a
reservation; missing billing leaves it reserved. A request cannot start unless billing,
outstanding reservations, and its new reservation fit within $5.

The ten earlier 4,365-byte rejected canary requests each retain a $0.22105688 reservation.
They were carried into the final execution's ledger rather than assigned a fresh budget.

## Provider prompt caching and timing

The registered Guesser prefix-cache configuration stayed at automatic, best-effort caching,
with a 1,024-token threshold and 300-second TTL expectation. Fixed instructions and the
append-only visible transcript were preserved. No padding or response caching was added.

| Retained-game Guesser measurement | Value |
| --- | ---: |
| Input tokens | 968,226 |
| Cached input tokens | 733,214 |
| Cache-write tokens | 52,652 |
| Output tokens | 143,715 |
| Reasoning tokens, included in output | 110,874 |
| Calls reporting cache reads | 469 / 705 |
| Calls reporting cache writes | 499 / 705 |
| Summed provider latency | 2,829.682 seconds |
| Mean provider latency per call | 4.01 seconds |

About 75.7% of input tokens were reported cached. No call supplied an explicit cache-discount
amount, so this report makes no measured dollar-savings claim. The saved catalog's estimated
savings use different rate assumptions and are not used as actual billing here.
The launch-time route snapshot listed ordinary OpenAI pricing of $0.20 input, $0.02 cached
input, $0.25 cache writes, and $1.20 output per million tokens, with higher long-context and
fast-route tiers. The spending guard used the maximum tier bounds above.

The engine marked 26 games cache-compliant, three noncompliant, and one not applicable.
Here “noncompliant” means a zero-cache-read call occurred after an eligible prior request
within the configured TTL. It is a prefix-cache observation, not evidence of answer reuse
or a Guesser information leak. Best-effort misses did not cause infrastructure failures.

Games ran from 10 September 19:43:20 UTC to 23:44:41 UTC, about 4 hours 1 minute including
manual research and operator time. In Europe/Zurich this was 21:43 on 10 September to 01:44
on 11 September. Support latency includes human-in-the-loop waiting and is not comparable
with a standalone model's inference latency.

## Verification and retained artifacts

All 30 trial results were loaded through the typed artifact store with integrity checks.
Every subject has three completed iterations, no superseded game attempts, and no missing
call audit. Offline reconstruction matched:

- all 705 Guesser prompt hashes to the canonical fixed system prompt, category and paired
  variation token, the Guesser's own structured actions, and final allowed reply tokens;
- all 668 Oracle hashes to trusted subject plus current question;
- all 638 Reviewer hashes to trusted subject, current question, and numbered evidence,
  without the Oracle answer or prior game history;
- all 36 Validator hashes to trusted subject plus current proposed identity.

The complete saved Guesser conversations matched those reconstructions after removing
report-only turn links. Raw HTTP bodies are not retained in regular benchmark artifacts;
this verifies the saved prompt hashes and typed histories, not a separate network capture.
No ASK cache source, response-cache hit, Guesser web search, provider fallback, or game retry
was recorded. The launch status and log show completion, and the Luna screen, launcher,
and live process had exited.

Before launch, 33 focused offline tests passed across the canary, preflight, bridge, and
Luna budget checks. The final check of those files passed all 34 currently collected tests.
Strict type checks passed again for the changed canary and Luna launcher.
The bridge checks cover required disagreement routing, format recovery, persistence, and
Guesser isolation using offline fixtures. The final artifact audit is also offline.

Private artifacts remain ignored under `private/reviews/luna-direct-20260910-004/`:

| Artifact | Contents |
| --- | --- |
| `runs/M-0001/BX-20260910-B-0003-codex-direct-M0001-004/` | Manifest, benchmark result, subject and trial results, summaries, events |
| `comparison.json`, `comparison.md` | Paired regular/direct scores and configuration checks |
| `verification.json`, `verify_results.py` | Final measurements and reproducible offline prompt-hash audit |
| `baseline-verification.json` | Reference-run aggregate measurements and support configuration |
| `budget.json`, `previous-budget.json` | Final accounting and carried startup reservations |
| `route-pricing.json`, `route-preflight.json` | Launch-time route metadata and capability check |
| `guesser-canary.json`, `guesser-canary-usage.json` | Successful startup validation and billing |
| `launch-status.json`, `run.log` | Terminal completion state |

Compatibility helper commands require `DEEP20_CODEX_EXPERIMENT=luna`; the default selects
the separate historical Gemini run. From the repository root, this audit makes no paid calls:

```sh
DEEP20_CODEX_EXPERIMENT=luna .venv/bin/python \
  private/reviews/luna-direct-20260910-004/verify_results.py
```

The documentation and supporting changes are local. No commit, push, or publication was made.
