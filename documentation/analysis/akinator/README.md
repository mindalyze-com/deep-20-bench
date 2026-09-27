# Akinator question-count comparison

**Analysis date: 10 September 2026.**

For the corresponding experiments with LLM guessers, see the
[Codex versus regular Oracle comparison](../codex-as-oracle/comparison.md), including
subject results and model-ranking changes. That report uses penalized benchmark scores;
the comparison below counts factual questions.

**Average questions per subject: 32.50 with the Oracle, 23.56 with Codex answering, and 18.03 across the 12 tested LLM configurations.** The Oracle and LLM averages cover ten subjects; the Codex average covers nine because Schweitzer ended in a website error.

On the **same nine completed subjects**, the averages are **32.56, 23.56 and 17.48 questions**, respectively. Akinator used 9.00 fewer questions per subject with Codex answering than with the Oracle. The [Oracle analysis](oracle/summary.md) and [Codex analysis](self-answered/summary.md) retain the individual trial counts and answer-quality notes.

## Question-count comparison

The primary measure is the **mean number of factual questions answered per completed game**, including games that reached the limit. Wrong guesses, format errors, Continue clicks and failure penalties are excluded. A lower value means fewer factual questions were used; a limit-stopped game does not establish how many questions identification would have required.

| Subject | Akinator with Oracle: mean questions | Akinator with Codex: mean questions | All tested LLMs: mean questions |
| --- | ---: | ---: | ---: |
| Albert Einstein | 31.5 | 20 | 10.08 |
| Albert Schweitzer | 32.0 | N/A | 22.97 |
| Garfield | 15.5 | 15 | 13.36 |
| Achilles | 35.5 | 24 | 10.56 |
| Genghis Khan | 27.5 | 18 | 14.36 |
| Bike pump | 39.0 | 38 | 32.00 |
| Spider web | 39.0 | 24 | 21.86 |
| Eyebrow | 39.0 | 28 | 19.25 |
| Moon | 27.0 | 15 | 11.47 |
| Door handle | 39.0 | 30 | 24.36 |
| **Average across subjects** | **32.50** | **23.56** | **18.03** |
| **Average across all completed games** | **32.44** | **23.56** | **18.04** |
| **Average across the same nine subjects** | **32.56** | **23.56** | **17.48** |

The LLM column includes all 12 model configurations with a saved final run under the comparable B-0003, five-answer, 40-action rules on these ten subjects. It uses the latest run of each configuration: 11 published edition 1.1 runs plus the later Muse Spark run. The one infrastructure-failed Muse Einstein trial is excluded, leaving 359 scored games: 35 for Einstein and 36 for every other subject. Earlier three-answer or 50-action experiments and superseded repeats of a model are not mixed into this column. See the [source snapshot](llm-question-counts.json) and [selection details](#llm-reference-population).

For each LLM subject value, first average that model's completed trials, then average the 12 model means with equal weight. The subject-average row gives each available subject equal weight. The game-average row pools all completed games and therefore weights every trial equally: 584 questions across 18 Oracle games, 212 across nine self-answered games, and 6,477 across 359 LLM games. The LLM subject and game averages differ slightly because Muse has only two completed Einstein trials.

The Oracle subject average covers ten subjects; the self-answered average covers nine. The last row excludes Schweitzer from all three columns and gives each of the remaining nine subjects equal weight. Each self-answered subject has only one completed trial, so its question count and mean are identical. The unfinished Oracle Moon trial had 23 confirmed answers and is excluded. The self-answered Schweitzer attempt had 18 confirmed answers before a website error, plus one attempted answer whose acceptance is unknown; it is also excluded.

All Oracle limit failures used 39 factual questions and one wrong guess; the self-answered Bike pump used 38 factual questions and two wrong guesses. LLM model failures are included at their actual ASK count. For terminology, the [published Deep20Bench question score](../../../source/publication/README.md) uses counted actions on identification and a value of 41 on failure under these rules. This report retains actual factual question counts as requested. Fewer questions can also reflect earlier termination or actions spent on guesses or format errors.

## Trials behind the question averages

| Subject | Oracle completed trials | Codex completed trials | LLM completed trials |
| --- | ---: | ---: | ---: |
| Albert Einstein | 2 | 1 | 35 |
| Albert Schweitzer | 2 | 0 | 36 |
| Garfield | 2 | 1 | 36 |
| Achilles | 2 | 1 | 36 |
| Genghis Khan | 2 | 1 | 36 |
| Bike pump | 2 | 1 | 36 |
| Spider web | 2 | 1 | 36 |
| Eyebrow | 2 | 1 | 36 |
| Moon | 1 | 1 | 36 |
| Door handle | 1 | 1 | 36 |
| **Total** | **18** | **9** | **359** |

The Oracle arm made 19 starts, including the unfinished second Moon trial. The Codex arm made exactly one attempt per subject, including the interrupted Schweitzer game. No third Oracle trials or Codex repeats were run. Each LLM configuration scheduled three trials per subject; the one infrastructure failure is excluded.

## Interpreting the question-count difference

On the same nine subjects, Akinator averaged **32.56 questions with the Oracle and 23.56 with Codex**, a difference of **9.00 questions per subject**. Codex answering reduced the recorded question count on every comparable subject. The largest reductions were Spider web (15 questions), Moon (12), Einstein and Achilles (11.5 each), and Eyebrow (11). Garfield changed by only 0.5 question; Bike pump changed by one question and still reached the action limit.

The LLM mean was lower on every subject in the table. On the same nine subjects, it was **17.48 questions**, or **6.08 fewer than Akinator with Codex**. These are observed question-use differences across small, unequal samples. They include limit-stopped and other completed failures, so they do not by themselves rank identification ability.

The records suggest that the Oracle and its question adapter contributed substantially to the poorer paths. Broad associations produced YES answers to sexuality questions for Spider web, Eyebrow and Moon; Codex used an ordinary game interpretation and answered NO. The adapter also personalized generic washing-machine and school-bag questions, producing unnecessary UNKNOWN answers. Other answers shifted between what is possible and what is typical. See the [Oracle answer review](oracle/answer-review.md). The confirmed Schweitzer name-reference error was corrected before submission, so that particular wrong answer did not affect the website game.

Across confirmed factual answers, the Oracle returned UNKNOWN 119 times out of 607 (19.6%), compared with 11 out of 230 (4.8%) for Codex. UNKNOWN is not inherently wrong, and the question sets differ, but more uncertain answers can leave less information for narrowing candidates. Independent review did not always resolve the intended meaning of an ambiguous question.

Akinator also showed weaknesses. In [Eyebrow Oracle trial 1](oracle/games/T-0010-r1.md), answers placed the feature on the face, hairy, paired and related to eyes, yet Akinator guessed a nipple after Q30. In the self-answered Door handle game, it asked whether the object opened a door at Q15 but continued with unrelated questions before identifying it at Q30. These observations do not isolate a single cause for the overall result.

Codex knew the earlier Oracle outcomes and used contextual answer judgments without independent review. The Oracle used blind per-question calls and independent adjudication. Akinator's internal state and question paths were uncontrolled. The small, unequal samples do not establish that Akinator is generally worse than LLM guessers, or that all of the observed difference was caused by Oracle answer quality.

## Completion context and spending

There were **29 Akinator game starts and 27 completed games**. Of the completed games, ten Oracle games and the Codex Bike pump game ended at the 40-action limit without exact identification. Their observed question counts remain in the averages. The unfinished Oracle Moon game and the Codex website-error game are excluded. Raw game records retain exact outcomes and rejected guesses for interpreting these counts.

Recorded OpenRouter spending for the Akinator experiment was **$3.72214452**, below the **$7 cap**. All of it belongs to the Oracle arm; the Codex arm made no OpenRouter calls. Codex usage cost was not measured. The LLM column reuses earlier benchmark results, whose historical costs are outside this Akinator spending total.

## LLM reference population

The LLM column is a saved-results comparison as of 10 September 2026. It includes each tested model configuration once, using its newest final B-0003 result with qualified answers, a 40-action ceiling and the same ten target IDs. A final run may contain infrastructure failures; those individual games are excluded, consistently with the Akinator summaries. No new benchmark or provider call was made.

| Model configuration | Included games | Saved execution |
| --- | ---: | --- |
| GPT-5.6 Luna (high) | 30 | `BX-20260908-B-0003-experimental-M0001-001` |
| gpt-oss-120B (high) | 30 | `BX-20260908-B-0003-experimental-M0002-001` |
| Claude Opus 5 (high) | 30 | `BX-20260907-B-0003-experimental-M0006-002` |
| GPT-5.6 Sol (high) | 30 | `BX-20260908-B-0003-experimental-M0010-001` |
| Grok 4.6 (high) | 30 | `BX-20260908-B-0003-experimental-M0015-001` |
| Gemini 3.7 Flash (high) | 30 | `BX-20260908-B-0003-experimental-M0016-001` |
| Claude Fable 5.1 (high) | 30 | `BX-20260908-B-0003-experimental-M0020-001` |
| Gemini 3.8 Flash (high) | 30 | `BX-20260908-B-0003-experimental-M0021-001` |
| GPT-6 Astra (high) | 30 | `BX-20260909-B-0003-experimental-M0022-002` |
| GLM-5.3-Flash (high) | 30 | `BX-20260908-B-0003-experimental-M0023-001` |
| MiniMax M3 (high) | 30 | `BX-20260908-B-0003-experimental-M0024-001` |
| Muse Spark 1.3 Contributor (high) | 29 | `BX-20260909-B-0003-experimental-M0026-003` |

The 11 published models contribute 30 games each. Muse Spark contributes 29: Einstein trial 1 ended with a provider-content-filtered infrastructure failure. Its local run is complete but is not part of the saved edition 1.1 leaderboard. This analysis includes its completed games because the comparison requests all tested models under these rules; it does not change publication eligibility.

All input data was read locally. The published dataset was validated with its existing typed schema, and every episode ASK count was checked against its action transcript. The additional Muse result was loaded with the benchmark reader, including its integrity check, and its ASK counts were also recounted. [The supporting snapshot](llm-question-counts.json) retains model names, execution IDs, source paths and hashes, per-trial counts, per-model subject means, exact aggregate fractions and exclusions.

The LLM baseline is comparable in subjects, answer vocabulary and action ceiling, but is not an identical task. LLM guessers receive a more specific initial category for characters, such as person or mythological figure, whereas Akinator starts with Characters. The native benchmark also supplies a guaranteed final guess opportunity, handles format errors, and can reuse compatible adjudicated ASK answers. Akinator controls its own question and guess timing. The retained LLM runs include accepted Oracle prompt and adjudication revisions. These differences limit a direct ranking interpretation of the three averages.

## Retained files

- `oracle/`: final summary, answer review, protocol, 19 game records and transcripts, raw submitted web events, the unsubmitted paid answer, cost/configuration snapshots, and the full original raw audit archive.
- `self-answered/`: final summary, protocol, 10 game records and transcripts, separate raw questions and answers, all web events, aggregate results, and two WebP screenshots.
- [Oracle raw archive](oracle/raw-data.zip): 4,929 files, 23,112,081 compressed bytes. It includes provider prompts, evidence, responses and failed/retried calls, but no provider credential files. The unchanged archive is a historical snapshot from the paid arm's stop; its internal private paths and earlier status statements describe that point in time.
- [LLM question-count snapshot](llm-question-counts.json): source selection and 359 per-game factual question counts for the third comparison column.
- [Offline verification script](verify.py): checks game counts, submission states, score arithmetic, cost reconciliation, raw-event completeness, archive integrity, and the LLM snapshot's source hashes and question-count averages without provider calls.

No benchmark configuration, production prompt, scheduled test or generated site output was changed. The retention request covers a local Git commit; no remote push or deployment was requested.
