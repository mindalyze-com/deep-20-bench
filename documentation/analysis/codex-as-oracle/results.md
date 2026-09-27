# Gemini 3.8 Flash: direct Codex Oracle experiment

Completed on 10 September 2026. Gemini 3.8 Flash (high), model M-0021, played the Guesser. This Codex conversation supplied the support decisions directly.

All 30 games succeeded. Gemini used **435 counted questions with Codex versus 446 with the regular Oracle**, averaging **14.50 versus 14.87 questions per game**. This is **2.47% fewer questions** with Codex.

Seven subject averages improved and three worsened. Across individual iterations, 12 improved, six tied and 12 worsened.

## Results by subject

Each score column lists iterations 1 / 2 / 3. Lower scores are better. Every game succeeded without an incorrect guess or format penalty, so all scores below are counted ASK questions.

| Subject | With Codex | Regular Oracle | Codex average | Regular average | Change with Codex |
| --- | --- | --- | ---: | ---: | --- |
| Albert Einstein | 10 / 11 / 11 | 12 / 11 / 12 | 10.67 | 11.67 | 1.00 fewer |
| Albert Schweitzer | 17 / 15 / 17 | 30 / 16 / 15 | 16.33 | 20.33 | 4.00 fewer |
| Garfield | 10 / 12 / 13 | 12 / 12 / 12 | 11.67 | 12.00 | 0.33 fewer |
| Achilles | 7 / 7 / 8 | 8 / 8 / 8 | 7.33 | 8.00 | 0.67 fewer |
| Genghis Khan | 11 / 13 / 11 | 10 / 12 / 11 | 11.67 | 11.00 | 0.67 more |
| Bike pump | 25 / 23 / 27 | 28 / 29 / 25 | 25.00 | 27.33 | 2.33 fewer |
| Spider web | 12 / 14 / 13 | 11 / 11 / 11 | 13.00 | 11.00 | 2.00 more |
| Eyebrow | 15 / 15 / 10 | 14 / 13 / 14 | 13.33 | 13.67 | 0.33 fewer |
| Moon | 9 / 10 / 10 | 12 / 10 / 10 | 9.67 | 10.67 | 1.00 fewer |
| Door handle | 20 / 33 / 26 | 27 / 23 / 19 | 26.33 | 23.00 | 3.33 more |

## Method

- Ran all 10 active subjects, with three consecutive iterations per subject, in catalog order.
- Used the regular B-0003 `qualified_v1` game policy, scoring, Guesser configuration and benchmark artifact format.
- Collected answers directly for this experiment. Reused no saved question answers: zero ASK cache hits and zero cache loads. Provider prompt-prefix caching remained separate from answer reuse.
- Supplied 435 Oracle decisions, 435 Reviewer decisions and 30 Validator decisions. Oracle and Reviewer agreed on every question, so the normal routing rules required no Judge decisions.
- Kept Gemini's visible information restricted to the normal game instructions, category, paired variation token, its own actions and final answer tokens. All 30 saved visible conversations passed verification.
- Reported progress during the run. The six-minute reporting automation is now paused.

## Interpretation

Gemini used slightly fewer questions overall with Codex in this run. Albert Schweitzer had the largest average improvement, at four fewer questions. Door handle had the largest average worsening, at 3.33 more questions.

This is a descriptive comparison. Codex's support roles shared one conversation and were not independent or blind. The regular run used separate support models and compatible ASK answer reuse. Support policy versions and execution dates also differed, so the result does not isolate Codex as the cause of the improvement.

## Cost and saved data

Recorded Gemini cost was **$2.07634650**: $2.07465825 for the games and $0.00168825 for the startup check. Codex support usage and cost were not measured by the bridge, so these figures do not support a total-cost comparison.

The run completed with no infrastructure failures and no Guesser format violations. Detailed benchmark artifacts, the machine-readable comparison, and verification records remain in the private experiment directory; this public document contains the summary.

| Role | Execution |
| --- | --- |
| Direct Codex experiment | `BX-20260910-B-0003-codex-direct-M0021-001` |
| Regular Oracle reference | `BX-20260908-B-0003-experimental-M0021-001` |

See also the [Akinator question-count comparison](../akinator/README.md) and the [documentation index](../../README.md).
