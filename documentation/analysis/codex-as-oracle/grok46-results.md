# Grok 4.6 with Codex as Oracle

Completed on 11 September 2026. Grok 4.6 (high) solved **29 of 30 games** with
Codex supplying the support decisions. Its mean question score was **16.40**,
compared with **17.13** and 30 successes in the saved regular-Oracle run.
Reported Grok cost was **$3.946766**, including the startup canary, within the
authorized **$9 maximum**. Codex usage and cost are not included.

This is a descriptive comparison of two support arrangements. The lower mean
does not establish that Codex is a more accurate Oracle: one game failed, and
the support roles in this experiment shared the same conversation.

The experiment followed the [reference method](README.md): all 10 active subjects,
three consecutive iterations per subject, B-0003 `qualified_v1`, base seed 0,
40 counted turns and one final guess-only opportunity. The registered Guesser
was M-0015, `x-ai/grok-4.6`, high reasoning, pinned to the xAI route through
OpenRouter. Its registered model configuration and game policy were retained.
The run used a private snapshot of the experiment helpers. The games ran from
10 September at 19:22:53 UTC to 11 September at 00:25:45 UTC, about five hours.

Each ASK received fresh web research and a new decision, including repeated
questions. All ASK answer reuse was disabled. This Codex conversation supplied
Oracle, Reviewer and identity-validation decisions, with Judge routing available
for disagreements. The support roles were not independent or blind. Grok received
only the standard game transcript, with final protocol tokens and no support
evidence, explanations or private state.

Lower scores are better. Successful identity guesses do not add a counted turn.
A failed game receives the standard score of 41; this is a penalty, not 41 ASK
questions. Positive differences below mean a lower mean with Codex.

| Subject | Regular scores 1 / 2 / 3 | Codex scores 1 / 2 / 3 | Regular mean | Codex mean | Regular minus Codex |
| --- | --- | --- | ---: | ---: | ---: |
| Albert Einstein | 9 / 10 / 12 | 7 / 11 / 8 | 10.33 | 8.67 | 1.67 |
| Albert Schweitzer | 27 / 39 / 25 | 21 / 19 / 41 | 30.33 | 27.00 | 3.33 |
| Garfield | 12 / 14 / 16 | 14 / 11 / 14 | 14.00 | 13.00 | 1.00 |
| Achilles | 8 / 8 / 8 | 8 / 9 / 10 | 8.00 | 9.00 | -1.00 |
| Genghis Khan | 13 / 14 / 14 | 14 / 12 / 16 | 13.67 | 14.00 | -0.33 |
| Bike pump | 31 / 24 / 26 | 20 / 32 / 34 | 27.00 | 28.67 | -1.67 |
| Spider web | 16 / 29 / 21 | 20 / 19 / 19 | 22.00 | 19.33 | 2.67 |
| Eyebrow | 16 / 15 / 17 | 17 / 13 / 18 | 16.00 | 16.00 | 0.00 |
| Moon | 8 / 9 / 8 | 10 / 9 / 9 | 8.33 | 9.33 | -1.00 |
| Door handle | 19 / 21 / 25 | 17 / 22 / 18 | 21.67 | 19.00 | 2.67 |
| **All 30 games** | **30 successes** | **29 successes** | **17.13** | **16.40** | **0.73** |

The total score decreased from 514 to 492. Across paired iterations, Codex had
13 lower scores, 2 equal scores and 15 higher scores. The Guesser configuration,
game policy, base seed and actual saved subject snapshots match the reference.
The support policy versions, execution dates and answer-reuse settings differ.
The regular run uses independent support models and compatible ASK answer reuse;
this run used the shared Codex conversation with no ASK reuse. These differences
prevent attributing the result to one isolated cause.

The third Schweitzer game exhausted 40 counted turns and ended with the rejected
final guess Helmuth Plessner. An earlier guess, Karl Jaspers, was also rejected.
The repair inspection on 11 September found no eligible trials: all 30 games
completed, with zero infrastructure failures. Schweitzer's third trial is a
scoring-eligible `limit_exhausted` result. The benchmark repair policy preserves
such results, so no game was replayed and no additional paid calls were made.
The bike-pump games contained four rejected guesses for a pressure gauge, air
chuck or externally supplied tire inflator. All door-handle games succeeded;
doorknob was accepted as a subtype of the general door-handle target.

There were 486 ASK decisions: 212 `YES`, 205 `NO`, 36 `RATHER_YES`,
28 `RATHER_NO` and 5 `UNKNOWN`. All 481 directional answers received an explicit
Reviewer decision. All reviews agreed, so no Judge was invoked. This agreement
count is not evidence of independent confirmation. The five unknowns concerned
Schweitzer's philosophical classification, typical bike-pump size, and three
questions about a typical door-handle shape or mechanism. The general object
targets did not specify a particular design or region.

Ordinary-use and classification questions sometimes required interpretation.
For example, eyebrows protect the eyes without forming visual images, and door
handles can operate lock mechanisms while also existing as non-locking fittings.
The [National Eye Institute](https://www.nei.nih.gov/eye-health-information/healthy-vision/nei-for-kids/your-eyes-natural-defenses)
describes eyebrow protection; [Schlage's function descriptions](https://www.schlage.com/en/home/products/knobs/all-knobs.html)
distinguish locking and non-locking handles.
The private audit records these qualifications and distinguishes source-supported
facts from additional interpretation. These decisions have not received an
independent accuracy audit.

| Recorded Grok usage | Value |
| --- | ---: |
| Calls / request attempts | 521 / 521 |
| Input tokens | 760,102 |
| Cached input tokens, included above | 450,304 |
| Cache-write tokens | 0 |
| Output tokens | 515,513 |
| Reasoning tokens, included in output | 498,563 |
| Total input plus output tokens | 1,275,615 |
| Reported game cost | $3.937826 |
| Additional startup canary | $0.008940 |
| **Combined reported Grok cost** | **$3.946766** |
| Authorized spending cap | $9.00 |
| Unspent amount below the cap | $5.053234 |

Provider recovery telemetry recorded no retries or exhausted calls. The separate
startup canary passed on its first request, making 522 paid Guesser requests in
total. The games completed without infrastructure failures or format violations.
There were six rejected identity guesses, including the final failed guess, and
491 actual counted turns across the run.

The prompt-cache assessment retained the registered best-effort automatic prefix
cache configuration, with its 1,024-token observation threshold and 300-second
TTL. No padding or response cache was added. Actual reported cache reads covered
59.24% of game input tokens. The recorded rate-based estimate of avoided input
cost was $0.675456, using the route's $2.00 input and $0.50 cache-read prices per
million tokens. Output was priced at $6.00 per million tokens. This estimate is
already reflected in the reported cost, not an additional credit. The route
metadata snapshot is retained privately; its source is the
[OpenRouter route metadata endpoint](https://openrouter.ai/api/v1/models/x-ai/grok-4.6/endpoints).
Codex support caching, tokens and cost remain unmeasured; zero support counters
in bridge artifacts are placeholders, not evidence of free support.

Final checks validated the standard result and all 30 trial integrity hashes,
reconstructed every saved Guesser-visible transcript from the public contract,
and confirmed zero ASK cache hits. The two offline bridge tests passed, including
isolation and disagreement routing. The launch status and run log report normal
completion. This experiment remains outside the regular independent-support
benchmark cohort and is not publication-eligible.

| Artifact role | Execution |
| --- | --- |
| Direct Codex experiment | `BX-20260910-B-0003-codex-direct-M0015-001` |
| Regular Oracle reference | `BX-20260908-B-0003-experimental-M0015-001` |

Detailed artifacts remain local and ignored under
`private/reviews/grok46-direct-20260910/`. They include the standard benchmark
artifacts, frozen helpers, route and canary records, `comparison.json`,
`final-verification.json`, `pairing-verification.json`, `final-summary.json`
and `completion-audit.json`. The completion audit rechecked the full schedule,
saved scores, trial integrity and reported charges against the $9 cap without
making further paid calls.
The later repair inspection is recorded in `repair-inspection.md` in the same
private directory.
