# Claude Fable 5.1: direct Codex Oracle experiment

Requested and authorized on 10 September 2026 with an $11 total OpenRouter limit.
Status: stopped by the spending guard on 10 September at 23:02:47 UTC
(11 September at 01:02:47 in Zurich). Reported OpenRouter spending was
**$7.53240350**. The next request's conservative reservation did not fit the
remaining $3.46759650. The guard stopped it before sending; it was not retried.

Of 30 scheduled games, **27 completed: 25 successes and two scored model failures**.
Door handle trial 1 reached 40 counted turns, but its final-guess request was
blocked. It is recorded as an infrastructure failure with no score. Door handle
trials 2 and 3 were not started. The experiment process has exited.

Across the same 27 scoring-eligible iterations, the mean score was **14.48 with
Codex versus 14.41 in the regular reference**, a difference of +0.07 counted turns.
Both had 25 successes and two model failures. Codex scored lower in 13 pairs,
the same in three and higher in 11. This incomplete comparison does not establish
an improvement or isolate the Oracle's effect.

Scores include ASK turns, rejected guesses and counted format errors. Correct
guesses add no turn; a scored model failure receives 41. Lower is better.

| Subject | Regular scores | Codex scores | Regular mean | Codex mean |
| --- | --- | --- | ---: | ---: |
| Albert Einstein | 8 / 12 / 9 | 9 / 8 / 10 | 9.67 | 9.00 |
| Albert Schweitzer | 18 / 16 / 20 | 14 / 15 / 17 | 18.00 | 15.33 |
| Garfield | 8 / 6 / 12 | 19 / 13 / 8 | 8.67 | 13.33 |
| Achilles | 8 / 9 / 8 | 8 / 7 / 7 | 8.33 | 7.33 |
| Genghis Khan | 9 / 10 / 9 | 10 / 8 / 8 | 9.33 | 8.67 |
| Bike pump | 41 / 41 / 33 | 31 / 41 / 41 | 38.33 | 37.67 |
| Spider web | 19 / 19 / 12 | 15 / 16 / 20 | 16.67 | 17.00 |
| Eyebrow | 11 / 12 / 13 | 12 / 12 / 12 | 12.00 | 12.00 |
| Moon | 9 / 9 / 8 | 10 / 10 / 10 | 8.67 | 10.00 |
| Door handle | 21 / 15 / 28 | interrupted / unstarted / unstarted | 21.33 | - |

Door handle is excluded from both sides of the paired aggregate. Detailed
comparisons and verification records are retained in the private artifact root.

## Decisions and limitations

Schweitzer's first game included one rejected guess of Norman Borlaug. The
second included UNKNOWN for whether his primary work counted as science when
medicine was omitted, and RATHER_NO for primary religious leadership. The third
used RATHER_YES for hospital/public-health reform: his hospital-building was
established, while the narrower label "reform" was less certain. These decisions
remain part of the original results; the support roles were supplied by the same
conversation and are not independent assessments.

Garfield's first game included the valid but meaningless question "x", answered
UNKNOWN, and a rejected guess of Holly Golightly's cat. Origin questions were
interpreted according to their wording: newspaper comics count as printed
literature, qualified as a broad literary work, but are not an original book or
novel. Speech questions were answered using Jim Davis's distinction between
Garfield's thoughts and words understood by Jon. These interpretations are
recorded as limitations for review; the completed games were not replayed.

Genghis Khan's first game included one counted invalid-action violation. The
normal FORMAT_ERROR recovery succeeded, and the recorded question score is 10.

The first bike-pump game succeeded after 31 questions. Its answers include
UNKNOWN for design-dependent electricity and internal rotary motion, and for
ambiguous wording about improvised weapon use, striking, applying substances
and shaping surfaces. It used RATHER_YES for one-hand size, the hand-tool label
and mostly-metal construction. These are operator interpretations, not a new
adjudicated ground-truth set. The target includes manual and electric pumps.
These scope decisions should be reviewed alongside the scores.

The second bike-pump game failed after exhausting its questions and final guess.
It moved toward heating and detection tools after YES for producing heat during
compression and YES for use in testing and detecting tire air leaks. These
answers preserved broad OR branches and distinguished production from primary
purpose. The final incorrect guess was carbon monoxide detector. The failed
game scores 41 and remains in the results; it was not replaced with another run.

The third bike-pump game answered YES for measuring pressure and for connection
to equipment to display pressure, using ordinary pumps with integrated gauges.
The questions did not require measurement to be the main purpose. Standalone
tire-pressure-gauge and pressure-gauge guesses were rejected because the target
is the complete pump. Questions about electronic pressure sensing received
UNKNOWN because common analog and digital designs differ. These scope decisions
need review alongside the resulting question count. Its final guess was air
pressure gauge; the game failed and scores 41.

The spider-web games succeeded with scores of 15, 16 and 20. The first
used UNKNOWN for "remains or products of once-living organisms": biological
production and production by an organism now dead were different readings.
The second asked only about origin from remains and received NO based on the
ordinary immediate origin in newly secreted silk. Both games treated the web as
an external, physical structure of solid fibres, not an organism, body part,
landform, or substance considered apart from its assembled form. The third also
used UNKNOWN for "remains or products of once-living organisms". It answered
YES for shelter use, supported by ordinary web retreats, and YES for the primary
prey-capture role. Questions about ordinary size and physical state used generic
properties rather than requiring every web to share them.

All three eyebrow games succeeded after 12 questions. The second and third used
UNKNOWN for a face-versus-hair contrast because eyebrows fit both categories.
The second also used UNKNOWN for a sensory-organ question that named five senses but
listed four: follicle touch sensitivity raised a broader interpretation than the
listed sight, hearing, smell and taste functions. These are recorded operator
interpretations, not independently adjudicated ground truth.

All three Moon games succeeded with scores of 10. The first included
one counted invalid-action violation and normal FORMAT_ERROR recovery; its nine
ASK questions therefore produced a score of 10. Across the completed games there
were two counted format violations, including Genghis Khan's first game.

The first door-handle game moved into textile work after YES for a documented
macrame cord-anchor use and for doorknobs used as improvised darners. Questions
about a primary textile purpose received NO; questions asking whether the
handle was used for darning received YES, while questions about its design for
darning received NO. Separate textile-tool guesses were rejected. UNKNOWN was
used for hygiene scope, insufficient coverage of ironing assistance, and a shape
question covering both knobs and levers. These broad secondary-use readings may
steer the Guesser away from the fitting's ordinary purpose and require review
alongside the result; they are not independent ground-truth adjudications.
This interrupted game contained 38 valid actions and two counted invalid-action
violations, at turns 10 and 24. No final identity was submitted after the guard
stopped its final-guess request. Its partial cost and events remain in the record;
it is not counted as a model failure or replaced with another game.

Across all played turns, Codex supplied 403 Oracle decisions and 49 identity
validations. Oracle answers were 221 NO, 149 YES, 24 UNKNOWN, eight RATHER_YES and
one RATHER_NO. All 379 directional answers had a Reviewer decision with exact-token
agreement; no Judge decision was invoked. UNKNOWN bypassed review. These routing
checks do not establish reviewer independence: every role used this conversation.

The recorded research total is 431 queries: 380 questions used one query, 18 used
two and five used three. Counts are operator-reported, not search-provider billing.

## Method

Claude Fable 5.1 (high), existing model `M-0020`, plays the Guesser through the
registered `anthropic/claude-fable-5.1` / `anthropic` route. This Codex conversation
supplies Oracle, Reviewer, Judge when required, and identity-validation decisions
using the [shared method](README.md).

The planned schedule was all 10 active subjects with three consecutive games per subject,
base seed 0, B-0003's current paired `qualified_v1` profiles and a 40-question limit.
The registered Guesser configuration is unchanged. Historical, same-episode and
same-execution ASK answer reuse are disabled. Each question receives fresh research.
Only the normal public conversation projection reaches the Guesser.

The support roles share one conversation and are not independent blind reviewers.
The bridge records their route as `codex/current-thread`. This experiment cannot
isolate the causal effect of changing only the Oracle: support-role independence,
answer reuse, policy versions and execution dates also differ from the reference.

## Execution

| Item | Value |
| --- | --- |
| Direct execution | `BX-20260910-B-0003-codex-direct-M0020-001` |
| Regular reference | `BX-20260908-B-0003-experimental-M0020-001` |
| Private artifact root | `private/reviews/fable51-direct-20260910/` |
| Helper | [src/fable51.py](src/fable51.py) |
| Planned games | 30 |
| Scoring-eligible games | 27 |
| Infrastructure failures / unstarted games | 1 / 2 |
| Game execution interval | 10 September 2026, 19:37:35-23:02:47 UTC |
| Paid startup checks | One Guesser structured-action canary |
| Total OpenRouter limit | $11, including startup, retries and failed calls |

From the repository root:

```sh
.venv/bin/python documentation/analysis/codex-as-oracle/src/fable51.py preview
.venv/bin/python documentation/analysis/codex-as-oracle/src/fable51.py pending
.venv/bin/python documentation/analysis/codex-as-oracle/src/fable51.py progress
```

These commands are offline. The `comparison` command requires a direct-run
manifest. The helper's paid launch command is `fable51.py live --live`; its
[budgeted launcher](src/fable51_live.py) enforces the authorized $11 limit.
The saved execution is closed; the launcher refuses to overwrite its ledger or run.
Full launches use detached macOS `screen` with
`nohup /usr/bin/caffeinate -i`, following the
[benchmark launch instructions](../../../source/execution/benchmark/README.md).

During play, the operator reads `fable51.py pending` or `fable51.py next --after N`,
researches the current question, and uses `fable51.py submit --input <decision.json>`
to submit a locally validated decision. The helper does not generate Codex decisions.
Query counts are operator-reported research counts, not provider telemetry.
Raw artifacts and supporting verification records stay under the ignored private root.

## Caching and accounting

The existing registration keeps best-effort five-minute ephemeral prefix caching,
a 512-token observation threshold, high reasoning and a 32,768-token output ceiling.
It adds no prompt padding or response caching. The prefix consists only of the
fixed Guesser instructions and its allowed append-only conversation. No privileged
support-role information enters the Guesser prefix or cache namespace.

The public [OpenRouter endpoint metadata](https://openrouter.ai/api/v1/models/anthropic/claude-fable-5.1/endpoints)
retrieved on 10 September lists an Anthropic endpoint with structured outputs,
$10 input, $50 output, $0.25 cache reads and $12.50 five-minute cache writes per
million tokens. No provider seed is advertised, matching the registration.
The endpoint marks implicit caching as unsupported; this does not measure the
registration's explicit ephemeral-cache behavior. The exact response is saved
privately as `route-pricing.json`.

The ledger and saved provider usage reconcile exactly:

| Cost component | Reported USD |
| --- | ---: |
| 27 completed games | 6.56948225 |
| Interrupted door-handle game | 0.93610625 |
| Startup Guesser canary | 0.02681500 |
| Total | **7.53240350** |
| Unsettled reservations | 0 |

There were 457 metered HTTP attempts, including the startup check. The 456 game
calls comprise 452 valid actions and four invalid-action outputs. No Guesser
transport retries were recorded. The blocked final request is not a paid attempt.

Including startup, reported usage was 1,009,906 input tokens, of which 936,894
were cache reads and 71,184 cache writes, plus 127,802 output tokens. Reported
reasoning tokens were 103,394 and are included in output, not added again.
Summed Guesser provider latency was 4,059,879 ms, about 67.7 minutes; this excludes
Codex research and operator time. No provider fallback was recorded in the
completed games or startup check.

At the recorded route rates, the observed cache reads and writes imply an
estimated net saving of $8.95675650 against charging all input tokens at the
uncached rate. This includes the cache-write premium and startup. It is a
rate-based estimate, not a provider-reported discount: the discount field was
absent. The observed reads support retaining the existing explicit prefix cache;
no padding was added.

Codex support tokens and cost are not measured by the local adapter. Its zero
cost fields mean unmetered support work, not free work. OpenRouter spending
therefore does not represent the experiment's complete cost.

The shared ledger covers every HTTP attempt from both the canary and games.
Before sending a request, it reserves maximum configured output cost and a
conservative input allowance: four tokens per serialized request byte plus 65,536
tokens for provider rendering, capped at the route's full context. It applies the
five-minute cache-write input rate and 10% headroom. Current route prices must fit
these bounds before startup. Reported billing settles the reservation; missing
billing keeps it charged against the cap. The launcher stops before another
request would exceed the remaining allowance, so it can stop below $11.
The guard changes no model request or game configuration.

## Reference and preparation

The regular reference has 28 successes and two scored model failures across 30
scoring-eligible games, with no final infrastructure failures. Its reported mean
question count is 15.03; the penalized comparison score instead assigns 41 to each
model failure. The reference's mean Guesser cost is approximately $0.28 per terminal
game. These historical figures are context, not a forecast or new result.

The preview selected `M-0020` and 30 games with no paid calls. The pre-launch bridge
tests passed with the Fable selection, covering typed result persistence, qualified
adjudication, format-error recovery and the Guesser's information boundary.
Ruff, strict mypy and whitespace checks passed. The saved reference's Guesser
configuration, game policy and subject snapshots match the prepared run.
The experiment remains outside the default regression suite and automatic jobs.
The final comparison confirms matching Guesser configuration, game policy,
completed-game subject snapshots and base seed. Support policy versions, support
independence, ASK reuse and execution dates differ as described above.

The final offline audit verified the integrity of all 28 retained trial results
and 552 benchmark events, validated all submitted support decisions, and reconciled
their counts and paid costs. Each of the 27 complete-game conversations was rebuilt
from the canonical system prompt and BEGIN, the Guesser's typed actions, final
answer tokens and fixed FORMAT_ERROR messages; every saved conversation matched.
The infrastructure-failed game retains typed turn events and partial metrics but
no full saved Guesser conversation, so that full-history check covers only the
27 completed games. No pending operator request remained after shutdown.
Final offline verification passed seven bridge and budget tests, Ruff, strict
mypy for the Fable helpers, and whitespace checks.

Supporting records are `comparison.json`, `comparison.md`, `final-verification.json`,
`budget.json`, `guesser-canary-usage.json` and the execution's typed results and
events under `private/reviews/fable51-direct-20260910/`. No results were committed,
pushed or published.
