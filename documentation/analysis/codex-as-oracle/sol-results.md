# GPT-5.6 Sol: direct Codex Oracle experiment

Started on 10 September 2026 with explicit user approval. **Stopped by the spending guard.**
The approved schedule is 30 games: all 10 active subjects, three consecutive repetitions
per subject, with a **$9 total paid-provider cap**, including diagnostics and retries.

**19 of 30 games completed, all successful.** Spider web repetition 2 was interrupted after
32 counted questions. The remaining 10 games were not started. The interrupted game is an
infrastructure result with no score, not a Sol failure or a zero. This is a partial experiment.

The successful attempt ran from its canary at **19:54:18 UTC to 22:31:06 UTC on
10 September 2026**. The stop was at 00:31:06 on 11 September in Europe/Zurich.

## Results and paired comparison

Scores count ASK actions and incorrect guesses. A correct final guess costs no turn.
Lower is better. Reference scores are from the regular Sol run, in repetition order.

| Subject | Direct 1 | Direct 2 | Direct 3 | Regular 1, 2, 3 |
| --- | ---: | ---: | ---: | --- |
| Albert Einstein | 10 | 12 | 13 | 10, 10, 13 |
| Albert Schweitzer | 33 | 30 | 22 | 23, 25, 29 |
| Garfield | 36 | 10 | 10 | 13, 11, 12 |
| Achilles | 20 | 10 | 19 | 10, 41 (failed), 7 |
| Genghis Khan | 10 | 11 | 9 | 11, 14, 11 |
| Bike pump | 20 | 27 | 25 | 39, 25, 22 |
| Spider web | 15 | Interrupted | Not started | 35, 13, 19 |
| Eyebrow | Not started | Not started | Not started | 19, 23, 23 |
| Moon | Not started | Not started | Not started | 10, 10, 11 |
| Door handle | Not started | Not started | Not started | 18, 19, 16 |

Across the **19 matching completed games**, the direct mean is **18.00**, compared with
**19.00** for the reference: nine lower scores, eight higher and two ties. Direct play solved
19 of these games; the reference solved 18, with its failed Achilles game scored as 41.

Across only the **six subjects with all three repetitions completed**, the means are
**18.167 direct and 18.111 regular** over 18 games, with eight lower scores, eight higher
and two ties. This complete-subject comparison shows little aggregate difference.
The 19-game comparison additionally includes the short first spider-web game while excluding
its long interrupted second repetition. Neither subset establishes a result for all 30 games.

Garfield repetition 1 included an incorrect guess of Pluto. Achilles repetitions 1 and 3
each included an incorrect guess of Heracles. All three games later succeeded. No completed
game had a format violation.

The saved Guesser configuration, game policy, base seed and completed subject snapshots match
the reference. Support policy versions, execution dates and ASK reuse differ. The regular
run uses separate support models and compatible ASK reuse; this experiment uses this shared
Codex conversation and fresh ASK decisions. The comparison does not isolate an Oracle effect.

## Setup

GPT-5.6 Sol (high), catalog model `M-0010`, is the Guesser through the exact
`openai/gpt-5.6-sol` / `openai` OpenRouter route. This Codex conversation supplies
Oracle, Reviewer, Judge when required, and identity-validation decisions directly.
The named Sol model is the Guesser; support is labeled `codex/current-thread`.

The run uses B-0003 `qualified_v1`, base seed 0, and no historical, same-episode or
same-execution ASK answer reuse. Every ASK receives fresh web research and a typed decision.
Source summaries preserve retrieved facts; any supplementary remembered knowledge is
explicitly labeled with basis `other`, as permitted by the current policy.
Guesses receive identity validation. The bridge returns only the final protocol token to
the Guesser. Private support and research do not enter its conversation.

The support roles share this conversation and are **not independent blind reviewers**.
Results therefore describe these executions without isolating a single causal factor.
The original [Gemini results](results.md) remain a separate experiment.

| Item | Value |
| --- | --- |
| Stopped execution | `BX-20260910-B-0003-codex-direct-M0010-003` |
| Regular Sol reference | `BX-20260908-B-0003-experimental-M0010-001` |
| Private artifacts | `private/reviews/sol-direct-20260910-003/` |
| Shared budget ledger | `private/reviews/sol-budget-20260910/` |
| Run helper | [src/sol.py](src/sol.py) |
| Budget guard and failure diagnostics | [src/sol_live.py](src/sol_live.py) |

The full reference has 29 successful games out of 30. Its failed Achilles repetition has
penalized score 41; its 40 counted questions are not treated as a successful score.

## Adjudication observations

The 19 completed games contain **339 ASK actions**, with 151 YES, 165 NO, four RATHER_YES,
eight RATHER_NO and 11 UNKNOWN answers. All 328 directional answers received a matching
Reviewer token. Unknown answers bypassed review; no Judge was invoked. Reviewer agreement
here is a routing fact, not evidence of independent corroboration.

The saved audits record 380 search queries across those ASK actions: 308 used one query,
21 used two and 10 used three. They contain 127 distinct evidence URLs. Oracle basis was
`evidence` for 274 decisions and `other` for 65. All 339 Oracle attempts record prompt
`live-web-oracle-v17-labelled-source-context`. Query counts and source summaries are
operator-reported; the benchmark does not independently log the external search service.

Several decisions depended on exact wording or scope:

- Garfield's pre-syndication origin and later adaptations mattered. Canonical horror and
  resurrection stories were within the target's unrestricted scope.
- Achilles could be worshipped as a deity while being primarily known as a mortal hero.
  Ancient cult evidence supported the former; questions about his primary identity differed.
- Bike-pump questions distinguished moving air from applying a substance onto a surface,
  and primary tire inflation from incidental alternative uses.
- For spider web, the target was the assembled structure, not silk as a material. The second
  repetition answered YES to location within near-surface atmosphere. Sol then pursued many
  atmospheric possibilities. That observed sequence does not establish a causal explanation.
- The interrupted repetition used UNKNOWN for whole-web movement, light emission and a
  contained moving object. Visible fluorescence measured in silk did not settle the question
  about ordinary emission by an unspecified assembled web. Its final answer was YES to
  occurrence when the Sun is near the horizon, supported by a sunrise web; the question did
  not say that occurrence was exclusive to that time.

The operator used the policy's permission for concrete remembered knowledge more broadly
after re-reading it during the Schweitzer games. Earlier answers were retained. Evidence
sufficiency and ordinary-language judgments were therefore not mechanically uniform across
the run. These judgments and the shared support conversation limit comparability.

## Operation and verification

Offline inspection from the repository root:

```sh
.venv/bin/python documentation/analysis/codex-as-oracle/src/sol.py pending --attempt 3
.venv/bin/python documentation/analysis/codex-as-oracle/src/sol.py progress --attempt 3
.venv/bin/python documentation/analysis/codex-as-oracle/src/sol.py comparison --attempt 3
```

The helper defaults to attempt 2, so the explicit attempt flag is required for this run.
Attempt 1 has no directory suffix; later attempts have `-002` and `-003` suffixes.

Paid execution requires `sol.py live --live --attempt 3`. The stopped run was launched in a
detached macOS `screen` session with `nohup /usr/bin/caffeinate -i`. Route preflight,
the live processes, manifest and first turn were verified. Its startup canary produced a
valid ASK, stop finish reason, 125 output tokens and 3,541 ms latency. Do not relaunch the
same execution; a new experiment needs fresh identifiers.

The operator researches pending questions and submits typed decisions with the exact
sequence and request hash. Unknown answers bypass review. Directional answers require
a Reviewer; exact-token disagreement requires a Judge. A circuit breaker stops after
one infrastructure-failed game.

Eight offline tests passed in the final check for the bridge and Sol budget guard. They cover visible
Guesser projections, qualified-answer routing, persisted results, format recovery,
pre-transmission budget rejection, unknown-bill retention, failed and successful charges,
request bounds and sanitized failure extraction. Ruff and strict mypy passed for the
Sol helpers; the final Ruff check also passed.

The final audit integrity-loaded all 19 completed trial records and the interrupted record.
For each completed game it checked the saved Guesser conversation against fixed instructions,
the category and seed/trial-derived BEGIN token, its own typed actions and final answer tokens.
It found no extra support content. All 361 completed-game Guesser calls reported stop finish
reasons and the OpenAI route, with no fallback. These checks cover saved conversations and
audit projections, not a recording of every outbound HTTP request. Raw Guesser reasoning was
not read.

The benchmark retains only partial metrics for the interrupted trial, without its full
conversation or per-call support audit. A separate `partial-operator-record.json` reconstructs
its 32 questions and answers from this conversation and labels that provenance. It records
34 fresh search queries, 29 matching directional reviews and three unreviewed UNKNOWNs.
Across completed and interrupted play, 371 ASK actions received fresh research.

Private supporting files under `private/reviews/sol-direct-20260910-003/` include
`comparison.json`, `comparison.md`, `saved-results-audit.json`, `audit_saved_results.py`,
`partial-operator-record.json`, and sanitized provider-failure records. They remain ignored.
The run's screen session and its original Python and caffeinate processes have exited;
there is no pending decision.

## Caching and costs

The registered Guesser uses automatic best-effort provider prompt caching, a configured
1,024-token eligibility threshold and 300-second retention assumption, without padding
or response caching. Actual provider usage determines measured cache reads and billed cost.
The 19 completed games report **431,718 input tokens**, including **281,744 cache-read tokens**,
plus **28,249 cache-write tokens** and **69,567 output tokens**, of which 53,989 are reasoning
tokens. Cache-write counts are reported separately and are not added again to input totals.
The interrupted game adds 36,158 cache-read and 2,027 cache-write tokens. The canary reports
no cache reads or writes.

All 361 completed-game response-cache status and cache-discount fields were unavailable.
No response-cache use or measured monetary discount can be inferred from those nulls.
Catalog prices produce estimated savings only; the report does not treat those estimates as
measured discounts. Codex support tokens, cost and prefix-cache behavior are not measured by
the bridge, and serialized zero support costs are not proof that support was free.

| Reported paid-provider charges | USD |
| --- | ---: |
| 19 completed games | 1.0660913 |
| Interrupted spider-web repetition | 0.1661431 |
| Successful startup canary | 0.0027680 |
| **Total reported** | **1.2350024** |

The guard checks public endpoint pricing and reserves an upper charge before every HTTP
request, including retries, in a locked ledger shared across attempts. It bounds input by
complete UTF-8 request size plus 4,096 framing tokens, caps input at 100,000 and output at
32,768 tokens, checks the exact text-only OpenAI route and includes a 10% rate margin.
It does not depend on cache discounts. Reported charges replace reservations; unknown
billing retains them. A request that could exceed $9 is blocked before transmission.

The ledger retains a conservative **$6.20 reservation** for unmetered attempt-1 calls
and **$0.767426** for attempt 2. These are protective allowances, **not measured spending**.
Reported charges plus reservations total **$8.2024284**, leaving **$0.7975716** of protected
headroom. The next request's upper bound exceeded that headroom, so the guard raised
`experiment_spending_cap_reached` before transport. The game wrapper recorded
`provider_request_failed`, and the one-failure circuit breaker ended the experiment.
The stop does not mean that $9 was actually spent or that OpenRouter rejected that request.

The ledger has 395 reserved transport attempts since attempt 2: its one unmetered failure,
the successful canary and 393 metered game calls. The final locally blocked request did not
increase that counter or reserve another charge. Reported charges reconcile exactly with
completed games, interrupted-game metrics and the canary. Earlier unknown billing remains
unresolved; continuation cannot be treated as covered simply by subtracting measured charges
from $9.

## Earlier startup failures

Attempts 1 and 2 failed with `provider_invalid_request` before any game began. They are
infrastructure startup failures, not Sol game scores, and their artifacts are preserved.

Attempt 1 ran from 19:24:48 to 19:26:50 UTC. Route preflight passed, but its canary returned
no usable action. The earlier helper discarded detailed failure usage and attempt counts.
Default zero-token and zero-latency fields do not establish zero usage or a free call.
The $6.20 allowance bounds up to eight configured attempts at the inspected maximum rates.

Attempt 2 made exactly one recorded HTTP request. It received HTTP 400 in 456 ms with
`Provider returned error`, no resolved model/provider, and no cost record. Its reservation
remains held. An account-activity inspection reached a sign-in page and supplied no billing
details. Attempt 3 added sanitized nested-upstream diagnostics before launch.

Automatic approval review initially rejected another paid canary. The user then explicitly
approved additional diagnostics, retries and the full experiment under the $9 cap. Attempt 3
subsequently launched successfully. That earlier approval block is resolved.
