# Muse Spark: direct Codex Oracle experiment

Completed on 11 September 2026. Muse Spark solved all 30 games with this Codex
conversation supplying the support decisions. Its mean score was **19.33**, compared
with **18.37** in the regular reference: **0.97 more counted questions per game**.
The regular reference solved 29 games. This is a descriptive comparison with shared
support context and uneven operator interpretations, not a controlled Oracle-quality test.

## Results

The schedule used all 10 active subjects, three consecutive games per subject and
base seed 0. Lower scores are better. A successful game's score includes ASK turns,
rejected guesses and counted format violations; its correct final guess adds no
question. A scoring-eligible model failure scores 41. Infrastructure failures have
no score. Both sides of this final comparison have 30 eligible records and no
infrastructure failures.

| Subject | Regular scores | Regular mean | Codex scores | Codex mean | Regular minus Codex |
| --- | --- | ---: | --- | ---: | ---: |
| Albert Einstein | 14 / 12 / 14 | 13.33 | 11 / 13 / 14 | 12.67 | +0.67 |
| Albert Schweitzer | 26 / 15 / 19 | 20.00 | 26 / 14 / 28 | 22.67 | -2.67 |
| Garfield | 14 / 15 / 14 | 14.33 | 29 / 17 / 15 | 20.33 | -6.00 |
| Achilles | 9 / 10 / 18 | 12.33 | 8 / 9 / 8 | 8.33 | +4.00 |
| Genghis Khan | 15 / 15 / 13 | 14.33 | 13 / 16 / 16 | 15.00 | -0.67 |
| Bike pump | 31 / 30 / 41 | 34.00 | 37 / 28 / 39 | 34.67 | -0.67 |
| Spider web | 15 / 29 / 15 | 19.67 | 14 / 18 / 15 | 15.67 | +4.00 |
| Eyebrow | 17 / 15 / 19 | 17.00 | 23 / 25 / 17 | 21.67 | -4.67 |
| Moon | 10 / 11 / 9 | 10.00 | 10 / 8 / 8 | 8.67 | +1.33 |
| Door handle | 33 / 26 / 27 | 28.67 | 36 / 26 / 39 | 33.67 | -5.00 |
| All 30 games | Total 551 | 18.37 | Total 580 | 19.33 | -0.97 |

Codex had a lower score in 13 matched iterations, a higher score in 12, and the same
score in five. The regular run's third bike-pump game failed and scores 41; the
corresponding Codex game succeeded at 39. All other regular games succeeded.

## Configuration and method

| Item | Value |
| --- | --- |
| Registered Guesser | `M-0026`, Muse Spark 1.3 Contributor (high) |
| Exact OpenRouter route | `meta/muse-spark-1.3-contributor` / `meta` |
| Guesser reasoning and output | High; 32,768-token output limit; strict structured actions |
| Direct execution | `BX-20260910-B-0003-codex-direct-M0026-002` |
| Regular reference | `BX-20260909-B-0003-experimental-M0026-003` |
| Benchmark | B-0003, paired `qualified_v1`, `concise_knowledge_v1` |
| Guesser prompt | `stateful-category-guesser-v16-five-answer-category-guide` |
| Validator prompt | `strict-guess-validator-v2-generic-kinds` |
| Game start, UTC | 10 September 2026, 19:31:15 |
| Game completion, UTC | 11 September 2026, 02:40:42 |
| Elapsed game schedule | 7 hours, 9 minutes, 27 seconds |
| Private artifact root | `private/reviews/muse-direct-20260910/` |
| Compatibility helper | [src/muse.py](src/muse.py) |

The existing Guesser registration was retained. Saved configurations, game policies,
subject snapshots and base seeds match the reference. Both runs' saved calls use
the prompt versions above. No provider seed is advertised, so the paired variation
token and base seed do not make model generation deterministic.

This run follows the earlier shared-conversation method described in the
[experiment README](README.md). It does not implement the newer blind-worker design
now described there. This conversation acted as Oracle, Reviewer, Judge when needed,
and guess Validator. The adapter identifies those roles as `codex/current-thread`;
it does not record a separate support-model version. The roles share context,
including earlier questions and decisions, and **are not independent blind reviewers**.
The helper transports typed decisions; it does not generate them.

The regular reference instead uses GPT-5.6 Luna (medium) as Oracle and Validator,
Gemini 3.5 Flash Lite (medium) as Reviewer, and Claude Opus 5 (medium) as Judge.
It records 56 ASK-cache hits under the historical, same-episode and same-execution
reuse policies. The direct run disables all three and records zero ASK-cache hits.

Every ASK received fresh research: 561 questions used three search queries and
12 used five, for **1,743 queries**. Source opens and finds are excluded from this
count. These are recorded operator query counts, not provider search telemetry.
There were 573 Oracle decisions, 544 reviews, one Judge decision and 31 guess
validations. Directional Oracle tokens required review; exact-token disagreement
required the Judge. The 29 Oracle UNKNOWN answers skipped both stages. Guess
validation used the trusted identity and saved contract without web research.

The final ASK tokens were 232 YES, 291 NO, 11 RATHER_YES, 10 RATHER_NO and 29 UNKNOWN.
The validator contract accepts a recognized subtype of a general kind when its
function is preserved. Accordingly, the first door-handle game's "Doorknob" guess
was accepted. The first eyebrow game's broader "Human hair" guess was rejected;
Muse subsequently identified the eyebrow.

## Accounting and caching

| Measured item | Value |
| --- | ---: |
| Guesser game charges | $0.200458516 |
| One startup Guesser check | $0.000246900 |
| Total reported OpenRouter Guesser charges | **$0.200705416** |
| Reserve for one retry with missing billing | $0.122552320 |
| Reported charges plus reserve | **$0.323257736** |
| User spending cap | **$9.00** |
| Logical Guesser game calls | 610 |
| Guesser game request attempts, including retries | 612 |
| Game input tokens | 816,390 |
| Cached input tokens, included above | 634,708 |
| Game output tokens | 908,312 |
| Reasoning tokens, included above | 855,120 |
| Game Guesser latency, including invalid calls and retries | 11,375.359 seconds |
| Estimated prompt-cache savings | $0.062201384 |

The startup check additionally used 797 input and 836 output tokens, including
749 reasoning tokens. Codex support tokens, searches and charges are not metered
by this adapter. **The experiment's total cost is unavailable**; the reported
OpenRouter amount covers only the Guesser. The user authorized a **$9 maximum**.
The compatibility helper did not record an enforced dollar budget; execution was
bounded to the 30 scheduled games and one startup check, with existing in-game
recovery. The completed-run accounting below is a retrospective cap check.
No additional paid verification was run.

The completion audit found one earlier request within a retried call whose billing
is missing. Its enclosing call reports zero cost, but the recovery merger sums
available costs and does not prove the missing request was free. A conservative
$0.122552320 reserve covers one full 1,048,576-token context at the saved input price,
32,768 output tokens at the saved output price, and a 10% margin. The Guesser had no
web-search tools. Reported provider charges plus this reserve are $0.323257736,
below the $9 cap. The reserve is a budget allowance, not an observed charge, and
does not measure Codex support billing.

The existing registration retains automatic best-effort exact-prefix caching,
without padding or response caching. Its 1,024-token threshold and 300-second
retention are observation defaults, not verified Meta guarantees. The public
[route metadata](https://openrouter.ai/api/v1/models/meta/muse-spark-1.3-contributor/endpoints)
checked before startup on 10 September reported an active Meta endpoint, strict
structured outputs, and prices per million tokens of $0.10 input, $0.20 output and
$0.002 cache reads. It marked implicit caching as unsupported. The saved usage
nevertheless reports cached tokens; both observations are retained.

The savings figure is an adapter estimate using configured prices. The provider's
separate cache-discount field is null, so the estimate is not a measured discount.
The exact metadata response is saved privately. See the
[repository cache assessment](../../llm-caching.md) and
[OpenRouter caching documentation](https://openrouter.ai/docs/guides/best-practices/prompt-caching).

Recorded support latency is 14,121.754 seconds for the Oracle mailbox and 258.666
seconds for validation. These include operator waiting and research. Reviewer and
Judge extraction timings are not independent model-call latency measurements.
The manual support times are not directly comparable with automated provider times.

## Recovery and verification

All 30 results passed typed loading and recorded-integrity checks. Canonical
reconstruction matched every saved Guesser conversation and all **610 Guesser
request-prompt hashes**, including requests after format violations. This checks
that the Guesser received the fixed public instructions, broad category, paired
initial variation token, its own actions, final answer tokens and canonical
FORMAT_ERROR messages. Support evidence and malformed output did not enter those
saved public histories. It does not certify factual correctness of the support decisions.

There were six counted format violations. The first bike-pump game had two
incomplete outputs and two outputs that exhausted the 32,768-token limit. Each
incomplete call made one automatic retry before becoming a counted violation.
The first door-handle game had two further output-limit violations. All six used
the fixed FORMAT_ERROR channel and both games eventually succeeded. Their scores
were 37 and 36 respectively, including four and two violation penalties. There
were no infrastructure failures or additional format violations.

The first bike-pump game's Guesser calls took 3,317.766 seconds and cost
$0.042798584. The first door-handle game's calls took 1,410.371 seconds and cost
$0.027690028. These include all calls in those games, not just invalid outputs.

The three current offline bridge tests passed with the Muse selection, covering
saved-result round trips, qualified adjudication, format recovery and Guesser
isolation. Ruff and strict mypy passed for the Muse helper. These checks used no
paid provider calls. The final state records 30 scheduled, started and terminal
games, status completed, and no current game or last failure. The benchmark's
screen, Python and caffeinate processes exited.

## Interpretation and reference provenance

The shared support context, different support models, fresh-search procedure,
answer-reuse settings and execution dates prevent attributing the score difference
to one cause. Three repetitions per subject also provide limited evidence about
stable performance differences.

Operator adjudication was uneven in some general-kind questions. The first two
bike-pump games received RATHER_YES for primarily-metal construction. The third
received UNKNOWN after research surfaced a plastic SKS ROOKIE alongside metal
pumps. The original answers and scores remain unchanged.

Door-handle questions exposed a further limitation. Several operation and mechanism
questions received UNKNOWN because fixed pulls and rotating handles differ. A later
normal-use question about gripping and turning received YES. Some earlier UNKNOWNs
may have treated ordinary generic claims too strictly, despite the prompt's rule
that every instance need not satisfy a generic claim. That uneven treatment may
have lengthened the games. Room comparisons also depended on operator interpretation:
"bathroom rather than bedroom/laundry" was treated as characteristic room-specific
use, while "commonly used in a bedroom" received YES. The interior-versus-entry
RATHER_YES used a remembered house-layout inference, not measured prevalence.
These decisions are retained for inspection, not presented as independently audited
answer labels.

The initial preparation check recorded 28 reference successes, one model failure
and one infrastructure failure. The reference was then repaired by another task;
its saved completion time is 10 September, 19:35:39 UTC. The private file named
`reference-result-at-start.yml` was saved at 19:37:40 UTC and already contains the
repaired reference: 29 successes and one model failure. It is not a snapshot of
the earlier preparation state. The final table uses that repaired 30-game reference,
which matches the current integrity-checked reference result.

## Local artifacts and commands

The report is in the requested analysis folder. Raw decisions, source excerpts,
queries, audits, manifests, results and supporting verification stay in the ignored
private artifact root. The final summaries are `comparison.json`, `comparison.md`,
`verified-summary.json`, `final-comparison-verification.json` and
`final-execution-verification.json` under that root. The final artifact checks are
recorded in `final-report-verification.json`. Private files and directories have
owner-only access. The later cap and retry-billing audit is recorded in
`goal-completion-audit.json`.

From the repository root, these commands inspect saved data offline:

```sh
.venv/bin/python documentation/analysis/codex-as-oracle/src/muse.py progress
.venv/bin/python documentation/analysis/codex-as-oracle/src/muse.py comparison
.venv/bin/python private/reviews/muse-direct-20260910/summarize.py
```

The paid entry point requires `muse.py live --live`; the existing completed execution
has already claimed its launch. The successful run used a detached macOS screen
session with `nohup /usr/bin/caffeinate -i`, following the
[benchmark launch instructions](../../../source/execution/benchmark/README.md).
An earlier launch attempt created no process, canary or manifest; the fresh `002`
execution was used for the completed run. Exact-route preflight, the one structured
startup ASK, the manifest and the first game turn were verified before continuing.
