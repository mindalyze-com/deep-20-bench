# Claude Opus 5: direct Codex Oracle experiment

Completed on 10 September 2026 at 22:15 UTC (11 September, 00:15 in Zurich).
All 30 scheduled games finished: **29 successes, one model failure and no
infrastructure failures**. The mean question score was **18.00**, compared with
**18.07** for the saved regular-Oracle reference. Lower is better. This run does
not establish an overall improvement from changing the Oracle.

## Results

Each subject had three consecutive games. Successful scores include ASK turns,
rejected guesses and counted contract violations. The successful final guess
adds no question. A model failure scores 41.

| Subject | Codex iterations | Codex mean | Regular iterations | Regular mean |
| --- | --- | ---: | --- | ---: |
| Albert Einstein | 11 / 12 / 11 | 11.33 | 10 / 13 / 10 | 11.00 |
| Albert Schweitzer | 41 (failure) / 27 / 19 | 29.00 | 18 / 28 / 26 | 24.00 |
| Garfield | 27 / 19 / 9 | 18.33 | 13 / 24 / 24 | 20.33 |
| Achilles | 7 / 9 / 10 | 8.67 | 10 / 12 / 8 | 10.00 |
| Genghis Khan | 10 / 13 / 14 | 12.33 | 11 / 13 / 11 | 11.67 |
| Bike pump | 31 / 39 / 29 | 33.00 | 39 / 41 (failure) / 41 (failure) | 40.33 |
| Spider web | 14 / 12 / 22 | 16.00 | 18 / 16 / 13 | 15.67 |
| Eyebrow | 11 / 18 / 33 | 20.67 | 11 / 19 / 18 | 16.00 |
| Moon | 11 / 10 / 10 | 10.33 | 10 / 10 / 10 | 10.00 |
| Door handle | 20 / 25 / 16 | 20.33 | 29 / 19 / 17 | 21.67 |
| **All 30 games** | **29 successes** | **18.00** | **28 successes** | **18.07** |

Total scores were 540 and 542. Direct Codex support produced a lower score on
16 paired iterations, the same score on four and a higher score on ten.
The largest subject differences favored Codex on bike pump (7.33 fewer points)
and the regular reference on Schweitzer (5.00 fewer) and eyebrow (4.67 fewer).
Three repetitions per subject are too few to treat these differences as stable
estimates.

The raw counted-question total was 539. Its mean, 17.97, differs from the score
because the failed game used 40 counted turns but scores 41. Successful games
averaged 17.21 counted questions.

## Method

Claude Opus 5 (high), M-0006, was the live Guesser through OpenRouter's exact
Anthropic route. The run used B-0003, all ten active subjects, three iterations
per subject, seed 0 and paired `qualified_v1` profiles. The registered
configuration used high reasoning, a 32,768-token output limit, a 120-second
request timeout and the registered recovery policy. No provider seed was sent;
the initial variation token supplied the paired trial variation.

This Codex conversation supplied the Oracle, Reviewer and identity-validation
decisions directly. It was also responsible for Judge decisions if required;
none were invoked. **The support roles shared one conversation and were not
independent blind reviewers.** Reviewer records commonly repeat the Oracle's
supporting statement. Their agreement count is a routing record, not independent
evidence of answer accuracy.

Each ASK received fresh research and a recorded decision, without saved-answer
reuse. The operator submitted 1,607 search queries: 524 questions used three
queries and seven used five. These are recorded submitted-query counts, not
independently measured search-engine executions or OpenRouter search usage.
Page opens are not additional search queries.

Of 531 Oracle decisions, 266 used the evidence basis and 265 used the other
basis, including background-knowledge explanations and UNKNOWN decisions.
Fresh searches therefore do not mean every answer had an attached citation.
Recorded excerpts are source summaries marked `model_reported`, not
independently verified quotations.

The run used detached `screen` with `caffeinate`. Games ran from 19:21:25 to
22:15:12 UTC on 10 September, including time spent waiting for Codex research
and decisions. The launcher saved a completed status with no pending decision.

## Behavior and qualifications

The first Schweitzer game exhausted 40 counted turns, including incorrect
guesses of Karl Marx and Friedrich Engels. On the final guess-only opportunity,
Opus asked whether the subject had won a Nobel Prize. The engine recorded
`ask_after_question_limit`, a scoring-eligible model failure. No Oracle answer
was supplied for that disallowed action, and the game was not replayed.

The second Schweitzer game had one counted format violation, followed by
continued play and success. The seven rejected guesses across the run were the
two above, Chester Cheetah, tire pressure gauge, lighter, horn and ossicone.

Opus submitted 15 literal `x` questions and one literal `placeholder`. These
were structurally valid ASK actions without a factual proposition. They received
UNKNOWN and consumed a question, rather than triggering FORMAT_ERROR. The 25
UNKNOWN decisions comprised 20 ambiguous questions and five cases of
insufficient coverage.

Some question paths depended on wording and scope:

- In spider-web iteration 3, “a geographical feature or natural structure”
  received YES for its natural-structure branch. Opus then asked several landform
  questions before returning to animal-built structures. Its score was 22,
  versus 14 and 12 in the other games.
- In eyebrow iteration 2, involvement in any sense received RATHER_YES for touch
  sensitivity. Being a sensory organ for sight, hearing or smell received NO.
  Iteration 3 distinguished the whole hair-bearing region from individual hairs
  and analogous animal markings; it finished at 33 after two wrong guesses.
- Bike-pump and door-handle answers allowed for manual versus electronic
  variants, materials and operating forms. A knob-versus-lever question was
  UNKNOWN because the target specified no shape. “Doorknob” was accepted as a
  conventional subtype of the general door-handle target.
- Broad heat wording received different qualifications: bike-pump compression
  was treated as producing incidental heat, while ordinary door-handle operation
  received RATHER_NO with friction and fire-door applications noted. This is an
  interpretation-sensitive distinction, not a controlled comparison.

These are audit observations. No independent post-run factual adjudication was
performed, and the answers were not retrospectively changed.

## Isolation and verification

Exact visible-projection checks passed for all 30 saved Guesser conversations.
They contained fixed instructions, broad category and paired initial variation,
canonical Guesser actions, final answer tokens and canonical FORMAT_ERROR where
required. Private subject data, evidence and support explanations were excluded
from that projection.

| Recorded operation | Count |
| --- | ---: |
| Guesser game calls | 569 |
| Startup canary calls | 1 |
| Oracle decisions | 531 |
| Reviewer decisions / agreements | 506 / 506 |
| Reviewer disagreements / Judge invocations | 0 / 0 |
| Identity-validation decisions | 36 |
| Counted format violations | 1 |
| Rejected guesses | 7 |
| ASK answer-cache hits / loads | 0 / 0 |
| Guesser retries / provider fallbacks | 0 / 0 |

Final ASK tokens were YES 193, NO 244, RATHER_YES 33, RATHER_NO 36 and UNKNOWN 25.
Every directional answer had a Reviewer record; UNKNOWN bypassed review.

Offline bridge tests passed after completion (three tests). The saved comparison
confirmed matching Guesser configuration, game policy, subject snapshots and
base seed. Scoped lint and strict type checks passed before launch. No additional
paid verification was run.

## Caching and cost

The registered configuration retained best-effort five-minute ephemeral prefix
caching, a 1,024-token observation threshold and no prompt padding. It reused
prompt-prefix computation only, not previous answers.

The route check advertised $5 input, $25 output, $0.50 cached input and $6.25
five-minute cache writes per million tokens. See the
[route metadata](https://openrouter.ai/api/v1/models/anthropic/claude-opus-5/endpoints)
and [provider caching documentation](https://platform.claude.com/docs/en/build-with-claude/prompt-caching).

| Measured Guesser usage | Games only |
| --- | ---: |
| Input tokens, including cached input | 1,235,288 |
| Cache-read input tokens | 1,158,223 |
| Cache-write input tokens | 75,927 |
| Output tokens | 87,586 |
| Reported reasoning tokens, included in output | 60,460 |
| Reported cost | $3.24899525 |

The startup canary cost $0.01324750, bringing total measured OpenRouter cost to
**$3.26224275**, below the authorized **$9** provider-spending cap. Every game
call reported Anthropic as its resolved provider.
Cache reads covered about 93.76% of input tokens. The saved pricing-based
estimate of cache savings was $5.11709475 for the games, including the cache-write
premium. This is not a separately measured uncached run or a latency claim.

Codex support usage, research cost and caching within this conversation were not
measured. Zero support costs in bridge artifacts are accounting placeholders,
not evidence that the work was free. The Opus amount is not a full experiment cost.

## Saved artifacts and comparison limits

Private data is under `private/reviews/opus5-direct-20260910/`, covered by the
repository's `/private/` ignore rule.

| Role | Execution |
| --- | --- |
| Direct Codex experiment | `BX-20260910-B-0003-codex-direct-M0006-001` |
| Regular Oracle reference | `BX-20260907-B-0003-experimental-M0006-002` |

The private folder contains the completed manifest and results, 567 operator
decision files, startup and route records, `comparison.json`, `comparison.md`,
`verification.json` and `accounting.json`. One evidence URL in decision 275 was
copied from a truncated search result. `source-notes.md` records full supporting
manufacturer URLs; the original decision remains unchanged.

The regular reference uses independent support models and compatible ASK-answer
reuse. It includes earlier mixed-contract repairs and is not publication
eligible. The direct run is also marked not publication eligible. Execution
dates, support policies, independence and answer reuse differ despite the
matching Guesser and game settings. The close aggregate scores and individual
subject differences do not isolate the causal effect of Codex.

This experiment ran only on demand. It was not added to regression tests or
automatic jobs, and no publication output was generated.
