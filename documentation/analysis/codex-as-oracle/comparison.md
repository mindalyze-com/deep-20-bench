# Codex versus regular Oracle: subject results and model rankings

**Analysis date: 11 September 2026.** This is a fixed snapshot of the saved results; partial experiments reflect their recorded coverage at that time. Snapshot collection started at 00:52:37 UTC.

Across the four completed 30-game experiments, Codex support produced a mean score of **17.89 versus 17.78** with the regular Oracle, or **0.66% worse**, with **113 versus 115 successes out of 120 games**. Bike pump, Achilles and spider web had the largest pooled subject improvements; Garfield and Albert Schweitzer worsened most.

The order of the four fully completed models stayed **Gemini, Grok, Opus, Luna**. On the six subjects completed by all eight models, **Gemini overtook Astra**, Opus rose and Muse fell. These restricted-subject ranks are separate from the full benchmark.

See the [experiment method and individual reports](README.md) and the related [Akinator question-count comparison](../akinator/README.md). The Akinator comparison counts factual questions; this report uses the benchmark score, including failure penalties.

Offline analysis of retained trial records. Successful games score counted turns; model failures score 41. Infrastructure failures and unstarted games have no score. Lower is better. All differences below are Codex minus regular: negative favors Codex.

Eight models have scored direct games. Gemini, Grok, Opus and Luna completed all 30 games. Astra and Fable have 27 each, Sol 19, and Muse 23 at this snapshot. GPT OSS was prepared but has no direct game results. Muse's signed trial records supplied the 23 scored games available at this snapshot.

## Each model on its matching completed cases

Rows with different coverage must not be ranked against each other.

| Model | Paired games | Regular score | Codex score | Change | Relative change | Regular successes | Codex successes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT-6 Astra | 27/30 | 13.22 | 14.22 | +1.00 | +7.56% | 27/27 | 27/27 |
| Claude Fable 5.1 | 27/30 | 14.41 | 14.48 | +0.07 | +0.51% | 25/27 | 25/27 |
| Gemini 3.8 Flash | 30/30 | 14.87 | 14.50 | -0.37 | -2.47% | 30/30 | 30/30 |
| Grok 4.6 | 30/30 | 17.13 | 16.40 | -0.73 | -4.28% | 30/30 | 29/30 |
| GPT-5.6 Luna | 30/30 | 21.03 | 22.67 | +1.63 | +7.77% | 27/30 | 25/30 |
| Muse Spark | 23/30 | 18.09 | 18.96 | +0.87 | +4.81% | 22/23 | 23/23 |
| Claude Opus 5 | 30/30 | 18.07 | 18.00 | -0.07 | -0.37% | 28/30 | 29/30 |
| GPT-5.6 Sol | 19/30 | 19.00 | 18.00 | -1.00 | -5.26% | 18/19 | 19/19 |

## Subject comparison using complete subject blocks

Include a model on a subject only when both conditions have all three scored repetitions. Every included model gets equal weight within that subject. The model mix differs between rows, so this table is descriptive and should not be used to estimate one universal Oracle effect.

| Subject | Models | Games per condition | Regular mean | Codex mean | Change | Relative change | Models better / tied / worse |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Albert Einstein | 8 | 24 | 11.04 | 10.92 | -0.12 | -1.13% | 5 / 0 / 3 |
| Albert Schweitzer | 8 | 24 | 22.67 | 24.42 | +1.75 | +7.72% | 3 / 0 / 5 |
| Garfield | 8 | 24 | 13.71 | 16.38 | +2.67 | +19.45% | 3 / 0 / 5 |
| Achilles | 8 | 24 | 10.12 | 9.08 | -1.04 | -10.29% | 5 / 1 / 2 |
| Genghis Khan | 8 | 24 | 12.08 | 11.92 | -0.17 | -1.38% | 4 / 0 / 4 |
| Bike pump | 8 | 24 | 32.29 | 31.17 | -1.12 | -3.48% | 5 / 0 / 3 |
| Spider web | 7 | 21 | 18.62 | 17.81 | -0.81 | -4.35% | 3 / 1 / 3 |
| Eyebrow | 6 | 18 | 16.72 | 16.72 | +0.00 | +0.00% | 2 / 2 / 2 |
| Moon | 6 | 18 | 9.83 | 9.94 | +0.11 | +1.13% | 2 / 0 / 4 |
| Door handle | 4 | 12 | 22.83 | 24.17 | +1.33 | +5.84% | 2 / 0 / 2 |

## Subject differences for every model

Each cell is Codex mean minus the regular mean on the exact same repetitions. A dagger and parenthesized count indicate fewer than three paired repetitions; all other numbers use three. A dash means no scored direct case.

| Subject | GPT-6 Astra | Claude Fable 5.1 | Gemini 3.8 Flash | Grok 4.6 | GPT-5.6 Luna | Muse Spark | Claude Opus 5 | GPT-5.6 Sol |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Albert Einstein | -1.00 | -0.67 | -1.00 | -1.67 | +3.00 | -0.67 | +0.33 | +0.67 |
| Albert Schweitzer | +3.67 | -2.67 | -4.00 | -3.33 | +10.00 | +2.67 | +5.00 | +2.67 |
| Garfield | +5.67 | +4.67 | -0.33 | -1.00 | +1.67 | +6.00 | -2.00 | +6.67 |
| Achilles | +0.00 | -1.00 | -0.67 | +1.00 | +0.67 | -4.00 | -1.33 | -3.00 |
| Genghis Khan | -0.33 | -0.67 | +0.67 | +0.33 | -0.67 | +0.67 | +0.67 | -2.00 |
| Bike pump | -0.67 | -0.67 | -2.33 | +1.67 | +4.33 | +0.67 | -7.33 | -4.67 |
| Spider web | +0.00 | +0.33 | +2.00 | -2.67 | -1.67 | -4.00 | +0.33 | -20.00 † (1) |
| Eyebrow | +1.33 | +0.00 | -0.33 | +0.00 | -5.67 | +8.00 † (2) | +4.67 | - |
| Moon | +0.33 | +1.33 | -1.00 | +1.00 | -1.33 | - | +0.33 | - |
| Door handle | - | - | +3.33 | -2.67 | +6.00 | - | -1.33 | - |

## Ranking of the four fully completed models

All ten subjects and all 30 cases for every model. Ranks are within these four models.

| Model | Regular rank | Codex rank | Regular score | Codex score | Change |
| --- | ---: | ---: | ---: | ---: | ---: |
| Gemini 3.8 Flash | 1 | 1 | 14.87 | 14.50 | -0.37 |
| Grok 4.6 | 2 | 2 | 17.13 | 16.40 | -0.73 |
| Claude Opus 5 | 3 | 3 | 18.07 | 18.00 | -0.07 |
| GPT-5.6 Luna | 4 | 4 | 21.03 | 22.67 | +1.63 |

Across these four models' 120 games, the mean was 17.7750 regular versus 17.8917 Codex (+0.66%). Successes: 115 regular versus 113 Codex.

## Ranking of all eight models on identical complete coverage

Use only the six subjects completed three times by every model: Albert Einstein, Albert Schweitzer, Garfield, Achilles, Genghis Khan, Bike pump. Each model has 18 games per condition. This is a restricted-subset ranking, not a replacement for the full benchmark.

| Model | Regular rank | Codex rank | Regular score | Codex score | Change |
| --- | ---: | ---: | ---: | ---: | ---: |
| Gemini 3.8 Flash | 2 | 1 | 15.06 | 13.78 | -1.28 |
| GPT-6 Astra | 1 | 2 | 13.00 | 14.22 | +1.22 |
| Claude Fable 5.1 | 3 | 3 | 15.39 | 15.22 | -0.17 |
| Grok 4.6 | 4 | 4 | 17.22 | 16.72 | -0.50 |
| GPT-5.6 Sol | 6 | 5 | 18.11 | 18.17 | +0.06 |
| Claude Opus 5 | 8 | 6 | 19.56 | 18.78 | -0.78 |
| Muse Spark | 5 | 7 | 18.06 | 18.94 | +0.89 |
| GPT-5.6 Luna | 7 | 8 | 19.50 | 22.67 | +3.17 |

## Coverage sensitivity

Exclude only Sol: seven models share seven complete subjects (21 games each).

| Model | Regular rank | Codex rank | Regular score | Codex score | Change |
| --- | ---: | ---: | ---: | ---: | ---: |
| Gemini 3.8 Flash | 2 | 1 | 14.48 | 13.67 | -0.81 |
| GPT-6 Astra | 1 | 2 | 13.76 | 14.81 | +1.05 |
| Claude Fable 5.1 | 3 | 3 | 15.57 | 15.48 | -0.10 |
| Grok 4.6 | 4 | 4 | 17.90 | 17.10 | -0.81 |
| Claude Opus 5 | 6 | 5 | 19.00 | 18.38 | -0.62 |
| Muse Spark | 5 | 6 | 18.29 | 18.48 | +0.19 |
| GPT-5.6 Luna | 7 | 7 | 20.57 | 23.05 | +2.48 |

Exclude Sol and Muse: six models share nine complete subjects (27 games each).

| Model | Regular rank | Codex rank | Regular score | Codex score | Change |
| --- | ---: | ---: | ---: | ---: | ---: |
| Gemini 3.8 Flash | 2 | 1 | 13.96 | 13.19 | -0.78 |
| GPT-6 Astra | 1 | 2 | 13.22 | 14.22 | +1.00 |
| Claude Fable 5.1 | 3 | 3 | 14.41 | 14.48 | +0.07 |
| Grok 4.6 | 4 | 4 | 16.63 | 16.11 | -0.52 |
| Claude Opus 5 | 5 | 5 | 17.67 | 17.74 | +0.07 |
| GPT-5.6 Luna | 6 | 6 | 20.59 | 21.74 | +1.15 |

## Limits and verification

All direct trial envelopes and reference benchmark results were integrity checked and validated into the repository's typed models. Guesser configuration, game policy, base seed and saved subject snapshots match each reference. Muse uses its integrity-checked reference-at-start snapshot; every matched score also agrees with the current repaired reference.

Matching repetition numbers share variation tokens, not necessarily identical random samples. Three repetitions per subject provide limited evidence for stable rank changes. Partial runs stopped or were observed in catalog order, so their missing cases are not a random sample. Sol's 19-case improvement includes a 15-point spider-web success against 35 in the reference while its next long game was interrupted; on its six complete subjects, Sol changes from 18.11 to 18.17.

Codex supplied Oracle, Reviewer, Judge when required, and Validator decisions in shared conversations. Those roles were not independent blind assessments. The regular references used separate support models and compatible ASK answer reuse; direct runs used fresh answers. Support policies, research practice and dates also differed. Scores measure Guesser outcomes under each support arrangement, not independently audited Oracle answer accuracy. The data do not isolate a causal Oracle-model effect.

The comparison was calculated offline. Supporting analysis code, source snapshots and raw run artifacts remain in ignored private storage. This public report retains the aggregate results, execution provenance and exact paired scores.

## Input provenance

| Model | Direct execution | Regular execution | Experiment report |
| --- | --- | --- | --- |
| GPT-6 Astra | `BX-20260910-B-0003-codex-direct-M0022-004` | `BX-20260909-B-0003-experimental-M0022-002` | [GPT-6 Astra](astra6-results.md) |
| Claude Fable 5.1 | `BX-20260910-B-0003-codex-direct-M0020-001` | `BX-20260908-B-0003-experimental-M0020-001` | [Claude Fable 5.1](fable51-results.md) |
| Gemini 3.8 Flash | `BX-20260910-B-0003-codex-direct-M0021-001` | `BX-20260908-B-0003-experimental-M0021-001` | [Gemini 3.8 Flash](results.md) |
| Grok 4.6 | `BX-20260910-B-0003-codex-direct-M0015-001` | `BX-20260908-B-0003-experimental-M0015-001` | [Grok 4.6](grok46-results.md) |
| GPT-5.6 Luna | `BX-20260910-B-0003-codex-direct-M0001-004` | `BX-20260908-B-0003-experimental-M0001-001` | [GPT-5.6 Luna](luna-results.md) |
| Muse Spark | `BX-20260910-B-0003-codex-direct-M0026-002` | `BX-20260909-B-0003-experimental-M0026-003` | [Muse Spark](muse-results.md) |
| Claude Opus 5 | `BX-20260910-B-0003-codex-direct-M0006-001` | `BX-20260907-B-0003-experimental-M0006-002` | [Claude Opus 5](opus5-results.md) |
| GPT-5.6 Sol | `BX-20260910-B-0003-codex-direct-M0010-003` | `BX-20260908-B-0003-experimental-M0010-001` | [GPT-5.6 Sol](sol-results.md) |

## Exact paired game scores

| Model | Subject | Repetition | Regular | Codex | Regular success | Codex success |
| --- | --- | ---: | ---: | ---: | --- | --- |
| GPT-6 Astra | Albert Einstein | 1 | 9 | 8 | True | True |
| GPT-6 Astra | Albert Einstein | 2 | 10 | 8 | True | True |
| GPT-6 Astra | Albert Einstein | 3 | 10 | 10 | True | True |
| GPT-6 Astra | Albert Schweitzer | 1 | 14 | 20 | True | True |
| GPT-6 Astra | Albert Schweitzer | 2 | 18 | 22 | True | True |
| GPT-6 Astra | Albert Schweitzer | 3 | 16 | 17 | True | True |
| GPT-6 Astra | Garfield | 1 | 7 | 10 | True | True |
| GPT-6 Astra | Garfield | 2 | 8 | 20 | True | True |
| GPT-6 Astra | Garfield | 3 | 9 | 11 | True | True |
| GPT-6 Astra | Achilles | 1 | 8 | 7 | True | True |
| GPT-6 Astra | Achilles | 2 | 8 | 9 | True | True |
| GPT-6 Astra | Achilles | 3 | 8 | 8 | True | True |
| GPT-6 Astra | Genghis Khan | 1 | 11 | 10 | True | True |
| GPT-6 Astra | Genghis Khan | 2 | 8 | 10 | True | True |
| GPT-6 Astra | Genghis Khan | 3 | 11 | 9 | True | True |
| GPT-6 Astra | Bike pump | 1 | 26 | 26 | True | True |
| GPT-6 Astra | Bike pump | 2 | 26 | 20 | True | True |
| GPT-6 Astra | Bike pump | 3 | 27 | 31 | True | True |
| GPT-6 Astra | Spider web | 1 | 13 | 17 | True | True |
| GPT-6 Astra | Spider web | 2 | 25 | 16 | True | True |
| GPT-6 Astra | Spider web | 3 | 17 | 22 | True | True |
| GPT-6 Astra | Eyebrow | 1 | 13 | 13 | True | True |
| GPT-6 Astra | Eyebrow | 2 | 13 | 15 | True | True |
| GPT-6 Astra | Eyebrow | 3 | 12 | 14 | True | True |
| GPT-6 Astra | Moon | 1 | 9 | 11 | True | True |
| GPT-6 Astra | Moon | 2 | 10 | 10 | True | True |
| GPT-6 Astra | Moon | 3 | 11 | 10 | True | True |
| Claude Fable 5.1 | Albert Einstein | 1 | 8 | 9 | True | True |
| Claude Fable 5.1 | Albert Einstein | 2 | 12 | 8 | True | True |
| Claude Fable 5.1 | Albert Einstein | 3 | 9 | 10 | True | True |
| Claude Fable 5.1 | Albert Schweitzer | 1 | 18 | 14 | True | True |
| Claude Fable 5.1 | Albert Schweitzer | 2 | 16 | 15 | True | True |
| Claude Fable 5.1 | Albert Schweitzer | 3 | 20 | 17 | True | True |
| Claude Fable 5.1 | Garfield | 1 | 8 | 19 | True | True |
| Claude Fable 5.1 | Garfield | 2 | 6 | 13 | True | True |
| Claude Fable 5.1 | Garfield | 3 | 12 | 8 | True | True |
| Claude Fable 5.1 | Achilles | 1 | 8 | 8 | True | True |
| Claude Fable 5.1 | Achilles | 2 | 9 | 7 | True | True |
| Claude Fable 5.1 | Achilles | 3 | 8 | 7 | True | True |
| Claude Fable 5.1 | Genghis Khan | 1 | 9 | 10 | True | True |
| Claude Fable 5.1 | Genghis Khan | 2 | 10 | 8 | True | True |
| Claude Fable 5.1 | Genghis Khan | 3 | 9 | 8 | True | True |
| Claude Fable 5.1 | Bike pump | 1 | 41 | 31 | False | True |
| Claude Fable 5.1 | Bike pump | 2 | 41 | 41 | False | False |
| Claude Fable 5.1 | Bike pump | 3 | 33 | 41 | True | False |
| Claude Fable 5.1 | Spider web | 1 | 19 | 15 | True | True |
| Claude Fable 5.1 | Spider web | 2 | 19 | 16 | True | True |
| Claude Fable 5.1 | Spider web | 3 | 12 | 20 | True | True |
| Claude Fable 5.1 | Eyebrow | 1 | 11 | 12 | True | True |
| Claude Fable 5.1 | Eyebrow | 2 | 12 | 12 | True | True |
| Claude Fable 5.1 | Eyebrow | 3 | 13 | 12 | True | True |
| Claude Fable 5.1 | Moon | 1 | 9 | 10 | True | True |
| Claude Fable 5.1 | Moon | 2 | 9 | 10 | True | True |
| Claude Fable 5.1 | Moon | 3 | 8 | 10 | True | True |
| Gemini 3.8 Flash | Albert Einstein | 1 | 12 | 10 | True | True |
| Gemini 3.8 Flash | Albert Einstein | 2 | 11 | 11 | True | True |
| Gemini 3.8 Flash | Albert Einstein | 3 | 12 | 11 | True | True |
| Gemini 3.8 Flash | Albert Schweitzer | 1 | 30 | 17 | True | True |
| Gemini 3.8 Flash | Albert Schweitzer | 2 | 16 | 15 | True | True |
| Gemini 3.8 Flash | Albert Schweitzer | 3 | 15 | 17 | True | True |
| Gemini 3.8 Flash | Garfield | 1 | 12 | 10 | True | True |
| Gemini 3.8 Flash | Garfield | 2 | 12 | 12 | True | True |
| Gemini 3.8 Flash | Garfield | 3 | 12 | 13 | True | True |
| Gemini 3.8 Flash | Achilles | 1 | 8 | 7 | True | True |
| Gemini 3.8 Flash | Achilles | 2 | 8 | 7 | True | True |
| Gemini 3.8 Flash | Achilles | 3 | 8 | 8 | True | True |
| Gemini 3.8 Flash | Genghis Khan | 1 | 10 | 11 | True | True |
| Gemini 3.8 Flash | Genghis Khan | 2 | 12 | 13 | True | True |
| Gemini 3.8 Flash | Genghis Khan | 3 | 11 | 11 | True | True |
| Gemini 3.8 Flash | Bike pump | 1 | 28 | 25 | True | True |
| Gemini 3.8 Flash | Bike pump | 2 | 29 | 23 | True | True |
| Gemini 3.8 Flash | Bike pump | 3 | 25 | 27 | True | True |
| Gemini 3.8 Flash | Spider web | 1 | 11 | 12 | True | True |
| Gemini 3.8 Flash | Spider web | 2 | 11 | 14 | True | True |
| Gemini 3.8 Flash | Spider web | 3 | 11 | 13 | True | True |
| Gemini 3.8 Flash | Eyebrow | 1 | 14 | 15 | True | True |
| Gemini 3.8 Flash | Eyebrow | 2 | 13 | 15 | True | True |
| Gemini 3.8 Flash | Eyebrow | 3 | 14 | 10 | True | True |
| Gemini 3.8 Flash | Moon | 1 | 12 | 9 | True | True |
| Gemini 3.8 Flash | Moon | 2 | 10 | 10 | True | True |
| Gemini 3.8 Flash | Moon | 3 | 10 | 10 | True | True |
| Gemini 3.8 Flash | Door handle | 1 | 27 | 20 | True | True |
| Gemini 3.8 Flash | Door handle | 2 | 23 | 33 | True | True |
| Gemini 3.8 Flash | Door handle | 3 | 19 | 26 | True | True |
| Grok 4.6 | Albert Einstein | 1 | 9 | 7 | True | True |
| Grok 4.6 | Albert Einstein | 2 | 10 | 11 | True | True |
| Grok 4.6 | Albert Einstein | 3 | 12 | 8 | True | True |
| Grok 4.6 | Albert Schweitzer | 1 | 27 | 21 | True | True |
| Grok 4.6 | Albert Schweitzer | 2 | 39 | 19 | True | True |
| Grok 4.6 | Albert Schweitzer | 3 | 25 | 41 | True | False |
| Grok 4.6 | Garfield | 1 | 12 | 14 | True | True |
| Grok 4.6 | Garfield | 2 | 14 | 11 | True | True |
| Grok 4.6 | Garfield | 3 | 16 | 14 | True | True |
| Grok 4.6 | Achilles | 1 | 8 | 8 | True | True |
| Grok 4.6 | Achilles | 2 | 8 | 9 | True | True |
| Grok 4.6 | Achilles | 3 | 8 | 10 | True | True |
| Grok 4.6 | Genghis Khan | 1 | 13 | 14 | True | True |
| Grok 4.6 | Genghis Khan | 2 | 14 | 12 | True | True |
| Grok 4.6 | Genghis Khan | 3 | 14 | 16 | True | True |
| Grok 4.6 | Bike pump | 1 | 31 | 20 | True | True |
| Grok 4.6 | Bike pump | 2 | 24 | 32 | True | True |
| Grok 4.6 | Bike pump | 3 | 26 | 34 | True | True |
| Grok 4.6 | Spider web | 1 | 16 | 20 | True | True |
| Grok 4.6 | Spider web | 2 | 29 | 19 | True | True |
| Grok 4.6 | Spider web | 3 | 21 | 19 | True | True |
| Grok 4.6 | Eyebrow | 1 | 16 | 17 | True | True |
| Grok 4.6 | Eyebrow | 2 | 15 | 13 | True | True |
| Grok 4.6 | Eyebrow | 3 | 17 | 18 | True | True |
| Grok 4.6 | Moon | 1 | 8 | 10 | True | True |
| Grok 4.6 | Moon | 2 | 9 | 9 | True | True |
| Grok 4.6 | Moon | 3 | 8 | 9 | True | True |
| Grok 4.6 | Door handle | 1 | 19 | 17 | True | True |
| Grok 4.6 | Door handle | 2 | 21 | 22 | True | True |
| Grok 4.6 | Door handle | 3 | 25 | 18 | True | True |
| GPT-5.6 Luna | Albert Einstein | 1 | 12 | 13 | True | True |
| GPT-5.6 Luna | Albert Einstein | 2 | 11 | 15 | True | True |
| GPT-5.6 Luna | Albert Einstein | 3 | 12 | 16 | True | True |
| GPT-5.6 Luna | Albert Schweitzer | 1 | 38 | 34 | True | True |
| GPT-5.6 Luna | Albert Schweitzer | 2 | 24 | 36 | True | True |
| GPT-5.6 Luna | Albert Schweitzer | 3 | 19 | 41 | True | False |
| GPT-5.6 Luna | Garfield | 1 | 25 | 23 | True | True |
| GPT-5.6 Luna | Garfield | 2 | 12 | 21 | True | True |
| GPT-5.6 Luna | Garfield | 3 | 24 | 22 | True | True |
| GPT-5.6 Luna | Achilles | 1 | 8 | 8 | True | True |
| GPT-5.6 Luna | Achilles | 2 | 6 | 8 | True | True |
| GPT-5.6 Luna | Achilles | 3 | 7 | 7 | True | True |
| GPT-5.6 Luna | Genghis Khan | 1 | 13 | 14 | True | True |
| GPT-5.6 Luna | Genghis Khan | 2 | 15 | 13 | True | True |
| GPT-5.6 Luna | Genghis Khan | 3 | 16 | 15 | True | True |
| GPT-5.6 Luna | Bike pump | 1 | 27 | 41 | True | False |
| GPT-5.6 Luna | Bike pump | 2 | 41 | 41 | False | False |
| GPT-5.6 Luna | Bike pump | 3 | 41 | 40 | False | True |
| GPT-5.6 Luna | Spider web | 1 | 25 | 41 | True | False |
| GPT-5.6 Luna | Spider web | 2 | 20 | 17 | True | True |
| GPT-5.6 Luna | Spider web | 3 | 36 | 18 | True | True |
| GPT-5.6 Luna | Eyebrow | 1 | 41 | 24 | False | True |
| GPT-5.6 Luna | Eyebrow | 2 | 23 | 33 | True | True |
| GPT-5.6 Luna | Eyebrow | 3 | 26 | 16 | True | True |
| GPT-5.6 Luna | Moon | 1 | 10 | 10 | True | True |
| GPT-5.6 Luna | Moon | 2 | 13 | 11 | True | True |
| GPT-5.6 Luna | Moon | 3 | 11 | 9 | True | True |
| GPT-5.6 Luna | Door handle | 1 | 23 | 41 | True | False |
| GPT-5.6 Luna | Door handle | 2 | 27 | 26 | True | True |
| GPT-5.6 Luna | Door handle | 3 | 25 | 26 | True | True |
| Muse Spark | Albert Einstein | 1 | 14 | 11 | True | True |
| Muse Spark | Albert Einstein | 2 | 12 | 13 | True | True |
| Muse Spark | Albert Einstein | 3 | 14 | 14 | True | True |
| Muse Spark | Albert Schweitzer | 1 | 26 | 26 | True | True |
| Muse Spark | Albert Schweitzer | 2 | 15 | 14 | True | True |
| Muse Spark | Albert Schweitzer | 3 | 19 | 28 | True | True |
| Muse Spark | Garfield | 1 | 14 | 29 | True | True |
| Muse Spark | Garfield | 2 | 15 | 17 | True | True |
| Muse Spark | Garfield | 3 | 14 | 15 | True | True |
| Muse Spark | Achilles | 1 | 9 | 8 | True | True |
| Muse Spark | Achilles | 2 | 10 | 9 | True | True |
| Muse Spark | Achilles | 3 | 18 | 8 | True | True |
| Muse Spark | Genghis Khan | 1 | 15 | 13 | True | True |
| Muse Spark | Genghis Khan | 2 | 15 | 16 | True | True |
| Muse Spark | Genghis Khan | 3 | 13 | 16 | True | True |
| Muse Spark | Bike pump | 1 | 31 | 37 | True | True |
| Muse Spark | Bike pump | 2 | 30 | 28 | True | True |
| Muse Spark | Bike pump | 3 | 41 | 39 | False | True |
| Muse Spark | Spider web | 1 | 15 | 14 | True | True |
| Muse Spark | Spider web | 2 | 29 | 18 | True | True |
| Muse Spark | Spider web | 3 | 15 | 15 | True | True |
| Muse Spark | Eyebrow | 1 | 17 | 23 | True | True |
| Muse Spark | Eyebrow | 2 | 15 | 25 | True | True |
| Claude Opus 5 | Albert Einstein | 1 | 10 | 11 | True | True |
| Claude Opus 5 | Albert Einstein | 2 | 13 | 12 | True | True |
| Claude Opus 5 | Albert Einstein | 3 | 10 | 11 | True | True |
| Claude Opus 5 | Albert Schweitzer | 1 | 18 | 41 | True | False |
| Claude Opus 5 | Albert Schweitzer | 2 | 28 | 27 | True | True |
| Claude Opus 5 | Albert Schweitzer | 3 | 26 | 19 | True | True |
| Claude Opus 5 | Garfield | 1 | 13 | 27 | True | True |
| Claude Opus 5 | Garfield | 2 | 24 | 19 | True | True |
| Claude Opus 5 | Garfield | 3 | 24 | 9 | True | True |
| Claude Opus 5 | Achilles | 1 | 10 | 7 | True | True |
| Claude Opus 5 | Achilles | 2 | 12 | 9 | True | True |
| Claude Opus 5 | Achilles | 3 | 8 | 10 | True | True |
| Claude Opus 5 | Genghis Khan | 1 | 11 | 10 | True | True |
| Claude Opus 5 | Genghis Khan | 2 | 13 | 13 | True | True |
| Claude Opus 5 | Genghis Khan | 3 | 11 | 14 | True | True |
| Claude Opus 5 | Bike pump | 1 | 39 | 31 | True | True |
| Claude Opus 5 | Bike pump | 2 | 41 | 39 | False | True |
| Claude Opus 5 | Bike pump | 3 | 41 | 29 | False | True |
| Claude Opus 5 | Spider web | 1 | 18 | 14 | True | True |
| Claude Opus 5 | Spider web | 2 | 16 | 12 | True | True |
| Claude Opus 5 | Spider web | 3 | 13 | 22 | True | True |
| Claude Opus 5 | Eyebrow | 1 | 11 | 11 | True | True |
| Claude Opus 5 | Eyebrow | 2 | 19 | 18 | True | True |
| Claude Opus 5 | Eyebrow | 3 | 18 | 33 | True | True |
| Claude Opus 5 | Moon | 1 | 10 | 11 | True | True |
| Claude Opus 5 | Moon | 2 | 10 | 10 | True | True |
| Claude Opus 5 | Moon | 3 | 10 | 10 | True | True |
| Claude Opus 5 | Door handle | 1 | 29 | 20 | True | True |
| Claude Opus 5 | Door handle | 2 | 19 | 25 | True | True |
| Claude Opus 5 | Door handle | 3 | 17 | 16 | True | True |
| GPT-5.6 Sol | Albert Einstein | 1 | 10 | 10 | True | True |
| GPT-5.6 Sol | Albert Einstein | 2 | 10 | 12 | True | True |
| GPT-5.6 Sol | Albert Einstein | 3 | 13 | 13 | True | True |
| GPT-5.6 Sol | Albert Schweitzer | 1 | 23 | 33 | True | True |
| GPT-5.6 Sol | Albert Schweitzer | 2 | 25 | 30 | True | True |
| GPT-5.6 Sol | Albert Schweitzer | 3 | 29 | 22 | True | True |
| GPT-5.6 Sol | Garfield | 1 | 13 | 36 | True | True |
| GPT-5.6 Sol | Garfield | 2 | 11 | 10 | True | True |
| GPT-5.6 Sol | Garfield | 3 | 12 | 10 | True | True |
| GPT-5.6 Sol | Achilles | 1 | 10 | 20 | True | True |
| GPT-5.6 Sol | Achilles | 2 | 41 | 10 | False | True |
| GPT-5.6 Sol | Achilles | 3 | 7 | 19 | True | True |
| GPT-5.6 Sol | Genghis Khan | 1 | 11 | 10 | True | True |
| GPT-5.6 Sol | Genghis Khan | 2 | 14 | 11 | True | True |
| GPT-5.6 Sol | Genghis Khan | 3 | 11 | 9 | True | True |
| GPT-5.6 Sol | Bike pump | 1 | 39 | 20 | True | True |
| GPT-5.6 Sol | Bike pump | 2 | 25 | 27 | True | True |
| GPT-5.6 Sol | Bike pump | 3 | 22 | 25 | True | True |
| GPT-5.6 Sol | Spider web | 1 | 35 | 15 | True | True |
