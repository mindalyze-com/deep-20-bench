# Deep20Bench Five Answer Experiment

- Execution: `BX-20260908-B-0003-experimental-M0016-001`
- Benchmark: `B-0003`
- Model: `M-0016` - Gemini 3.7 Flash (high)
- Exact route: `google/gemini-3.7-flash`
- Execution commits: `eceee31eef2eee309df803adf99bb6fa5bac3c87`
- Status: completed
- Success rate: 93.3%
- Median counted questions: 12
- Subjects: 10
- Iterations per subject: 3
- Trials: 28 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 5 recovered calls / 5 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 458 reviewed · agreement `95.4%` · 21 disagreement(s) / 21 Judge call(s) · 11 Oracle answer(s) changed (`52.4%`) · QC cost `1.0242` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 21/430 (`4.9%`) · `temporal_comparison` 0/27 (`0.0%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.0525` · Oracle `0.0739` · Verifier `0.0002` · Total `0.1267`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Total execution cost (USD): `3.8007`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 12 | 16.5 | 8–40 |
| Questions (successful) | 12 | 14.82 | 8–32 |
| Guesser cost (USD) | 0.0281 | 0.0525 | 0.0141–0.2408 |
| Oracle cost (USD) | 0.0460 | 0.0739 | 0.0172–0.2404 |
| Verifier cost (USD) | 0.0002 | 0.0002 | 0.0002–0.0005 |
| Terminal-attempt cost (USD) | 0.0726 | 0.1267 | 0.0416–0.4817 |
| Tokens | 106973 | 159215.87 | 48738–486935 |
| LLM latency (ms) | 151248 | 226135.6 | 70425–727911 |
| Trial duration (s) | 151.4 | 226.4 | 70.5–728.5 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 12 | 0.0600 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 100.0% (clean) | 0 | 18 | 0.1571 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 11 | 0.0666 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0473 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 12 | 0.0664 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 66.7% | 100.0% (clean) | 0 | 25 | 0.2691 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 13 | 0.0770 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 100.0% (clean) | 0 | 19 | 0.1444 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 11 | 0.0553 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 66.7% | 100.0% (clean) | 0 | 32 | 0.3237 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
