# Akinator with the Oracle - question-count analysis

**Analysis date: 10 September 2026.**

**Akinator averaged 32.50 factual questions per subject with the Oracle, or 32.44 per completed game.** The 18 completed games used 584 questions across ten subjects. Per-subject means ranged from 15.5 for Garfield to 39.0 for Bike pump, Spider web, Eyebrow and Door handle.

The paid arm stopped on 10 September 2026. One additional Moon game was unfinished and is excluded from the averages. The separate [Codex-answered comparison](../self-answered/summary.md) averaged 23.56 questions across nine completed subjects.

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

The LLM column includes all 12 model configurations with a saved final run under the comparable B-0003, five-answer, 40-action rules on these ten subjects. It uses the latest run of each configuration: 11 published edition 1.1 runs plus the later Muse Spark run. The one infrastructure-failed Muse Einstein trial is excluded, leaving 359 scored games: 35 for Einstein and 36 for every other subject. Earlier three-answer or 50-action experiments and superseded repeats of a model are not mixed into this column. See the [source snapshot](../llm-question-counts.json) and [selection details](../README.md#llm-reference-population).

For each LLM subject value, first average that model's completed trials, then average the 12 model means with equal weight. The subject-average row gives each available subject equal weight. The game-average row pools all completed games and therefore weights every trial equally: 584 questions across 18 Oracle games, 212 across nine self-answered games, and 6,477 across 359 LLM games. The LLM subject and game averages differ slightly because Muse has only two completed Einstein trials.

The Oracle subject average covers ten subjects; the self-answered average covers nine. The last row excludes Schweitzer from all three columns and gives each of the remaining nine subjects equal weight. Each self-answered subject has only one completed trial, so its question count and mean are identical. The unfinished Oracle Moon trial had 23 confirmed answers and is excluded. The self-answered Schweitzer attempt had 18 confirmed answers before a website error, plus one attempted answer whose acceptance is unknown; it is also excluded.

All Oracle limit failures used 39 factual questions and one wrong guess; the self-answered Bike pump used 38 factual questions and two wrong guesses. LLM model failures are included at their actual ASK count. The published Deep20Bench question score uses counted actions on identification and a value of 41 on failure under these rules; this report retains actual factual question counts as requested. Fewer questions can also reflect earlier termination or actions spent on guesses or format errors. See the [combined metric explanation](../README.md#question-count-comparison).

## Question totals and trial coverage

The plan was 3 Oracle-backed trials for each of 10 active subjects, followed by one self-answered game per subject. We stopped after 19 starts: 18 completed games and Moon trial 2 unfinished. No third Oracle trials started. The self-answered arm began later under a renewed user request.

| Question measure | Value |
| --- | ---: |
| Mean questions, equal weight per subject | **32.50** |
| Mean questions per completed game | **32.44** |
| Factual questions in 18 completed games | 584 |
| Character games: 284 questions across 10 games | 28.40 per game |
| Object games: 300 questions across 8 games | 37.50 per game |
| Confirmed questions in the unfinished Moon game, excluded | 23 |
| Confirmed questions across all 19 starts | 607 |

The games also used 11 rejected guesses. Each consumed an action under the 40-action cap but is excluded from the factual-question totals. A correct terminal guess consumed no action. Ten completed games reached the cap without identification; their observed question counts are retained.

## Questions by subject and trial

| Subject | Mean questions | Completed trials | Trial 1 questions | Trial 2 questions |
| --- | ---: | ---: | ---: | ---: |
| Albert Einstein | **31.5** | 2 | 39* | 24 |
| Albert Schweitzer | **32.0** | 2 | 39* | 25 |
| Garfield | **15.5** | 2 | 17 | 14 |
| Achilles | **35.5** | 2 | 39* | 32 |
| Genghis Khan | **27.5** | 2 | 29 | 26 |
| Bike pump | **39.0** | 2 | 39* | 39* |
| Spider web | **39.0** | 2 | 39* | 39* |
| Eyebrow | **39.0** | 2 | 39* | 39* |
| Moon | **27.0** | 1 | 27 | 23 partial; excluded |
| Door handle | **39.0** | 1 | 39* | Not started |

An asterisk marks a game that reached 40 actions with 39 questions and one rejected guess. Other completed games ended in exact identification. Achilles trial 2 used 32 factual questions plus one rejected guess, so its question count is 32 and its action count is 33. Means exclude the partial Moon game. No third trials started.

## Where the questions accumulated

Garfield required the fewest questions: 17 and 14, averaging **15.5**. Moon averaged **27.0** from one completed trial, followed by Genghis Khan at **27.5**. Einstein and Schweitzer averaged **31.5** and **32.0**. Achilles averaged **35.5**, including one limit-stopped trial and a second trial with an incorrect Odysseus guess before identification.

Bike pump, Spider web, Eyebrow and Door handle each averaged **39.0 questions**, with every completed trial at the action limit. Across completed games, objects used **37.50 questions on average**, compared with **28.40** for characters. For the five character subjects, the second trial used fewer questions in every case. Different question paths, Oracle variation, mapping versions and uncontrolled Akinator state prevent attributing that change to learning.

Across the same nine subjects completed in the Codex arm, the Oracle mean was **32.56 questions**, compared with **23.56 for Codex** and **17.48 for the tested LLMs**. The records below help explain why some Oracle paths consumed so many questions.

Rejected guesses are retained as context for the question paths and the action limit:

| Target | Incorrect guesses recorded in completed games |
| --- | --- |
| Albert Einstein | Jascha Heifetz |
| Albert Schweitzer | Sviatoslav Teofilovich Richter |
| Achilles | Oedipus; Odysseus / Ulysses |
| Bike pump | A Dyson vaccum; Rube Goldberg Machine |
| Spider web | 67; A tentacle |
| Eyebrow | A nipple; The skin |
| Door handle | An electric lock |

## Answer quality and limitations

These results measure Akinator using our Oracle/Reviewer/Judge answers. They do not isolate Akinator's ability from the quality and interpretation of those answers.

- Confirmed Oracle/Judge referent error: Schweitzer knowing the player's name was misread as knowing his own name. The wrong YES was caught before submission, retained with its cost, and replaced by a freshly adjudicated UNKNOWN after the user approved a mapping fix.
- Two submitted adapter errors in pass 1 personalized generic object questions: Spider web's washing-machine question and Door handle's school-bag question. Those games remain flagged, and the original answers were not rewritten.
- Broad associations sometimes changed the game path: Einstein's musical activities; spider courtship or human appearance in sex-related questions; Achilles's superhero associations; and possibility versus typical location for Bike pump.
- Answer variation was observed under the frozen configuration. Bike pump's electrical-operation question returned YES in trial 1 and UNKNOWN in trial 2. Achilles's Marvel association and Moon's near-duplicate sex-related questions also differed.
- Required-role failures were retained and costed. No invalid or provisional answer was submitted; reviewed failures received at most one fresh blind retry.
- Sample sizes are only one or two completed games per subject. Repeated web games can share uncontrolled server state. Theme selection, guess timing and the meaning of Akinator's answer buttons are not controlled. Mapping versions changed during pass 1. No speed claim is made from wall time, which includes operation and review pauses.

See [the detailed answer review](answer-review.md), [protocol](protocol.md), and [combined interpretation of the question-count difference](../README.md#interpreting-the-question-count-difference).

## Unfinished game and final spending

Moon trial 2 stopped after Q23, “Is it black?”, answered NO. The next question was “Is it bigger than Earth?”. Its paid adjudication had already completed with NO, costing $0.00383228, but that answer was **not submitted** after the user requested stopping. This game is unscored, not a failure.

Final known OpenRouter cost: **$3.72214452**. The total includes all roles, built-in retries, failed suites, fresh retries, the discarded Schweitzer answer, Validators, and the unsubmitted Moon answer. It reconciles with the saved per-game costs. The original DNS-only failure had no reported provider usage. No costs remain unresolved.

## Saved data

- [Raw-data archive](raw-data.zip): all experiment Oracle suite records and audits, Validator records, bridge jobs, original-to-Oracle question mappings, game records, frozen configurations, cost ledger and summaries.
- [Submitted web events](raw-web-events.jsonl): one record for each submitted question, guess or continuation, with subject/trial provenance and source run identifiers.
- [Unsubmitted paid answer](unsubmitted-adjudications.jsonl): the final Moon answer, kept separately from submitted events.
- [Final status](experiment-status.json) and [budget](budget.json).
- [Archive inventory](raw-data-inventory.json): file paths and sizes.

The user explicitly requested retaining this analysis and its raw data in the public repository documentation. The archive contains experiment evidence, prompts and model responses, and excludes provider credential files. It is the unchanged snapshot made when the Oracle arm stopped: statements inside that historical snapshot about private storage or a canceled self arm describe that earlier point in time. Archive paths are relative to the original reviews directory. These files were prepared for a local Git commit; no remote push or site deployment is part of this task.

## Question transcripts

- [Albert Einstein, trial 1](games/T-0001-r1.md) - completed.
- [Albert Einstein, trial 2](games/T-0001-r2.md) - completed.
- [Albert Schweitzer, trial 1](games/T-0002-r1.md) - completed.
- [Albert Schweitzer, trial 2](games/T-0002-r2.md) - completed.
- [Garfield, trial 1](games/T-0004-r1.md) - completed.
- [Garfield, trial 2](games/T-0004-r2.md) - completed.
- [Achilles, trial 1](games/T-0005-r1.md) - completed.
- [Achilles, trial 2](games/T-0005-r2.md) - completed.
- [Genghis Khan, trial 1](games/T-0006-r1.md) - completed.
- [Genghis Khan, trial 2](games/T-0006-r2.md) - completed.
- [Bike pump, trial 1](games/T-0008-r1.md) - completed.
- [Bike pump, trial 2](games/T-0008-r2.md) - completed.
- [Spider web, trial 1](games/T-0009-r1.md) - completed.
- [Spider web, trial 2](games/T-0009-r2.md) - completed.
- [Eyebrow, trial 1](games/T-0010-r1.md) - completed.
- [Eyebrow, trial 2](games/T-0010-r2.md) - completed.
- [Moon, trial 1](games/T-0011-r1.md) - completed.
- [Moon, trial 2](games/T-0011-r2.md) - stopped_by_user.
- [Door handle, trial 1](games/T-0012-r1.md) - completed.
