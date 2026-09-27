# Deep20Bench Edition 1.1

- Edition: `1.1` / `qualified-core-v1`
- Comparison classification: `standard`
- Explicit overrides: none
- Comparison contract: `2fa8c6bfffe0cf577cb6e97e8842a6c225d9b35b9ee22fa5a12461b2bc26fd5a`
- Execution: `BX-20260926-B-0003-official-M0029-001`
- Benchmark: `B-0003`
- Model: `M-0029` - GPT-6 Sol (high)
- Exact route: `openai/gpt-6-sol`
- Execution commits: `6e46fb003ebf43423c802cbb37f69bdc8b321ddf`
- Status: completed
- Success rate: 100.0%
- Median counted questions: 13
- Subjects: 10
- Iterations per subject: 3
- Trials: 30 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 5 recovered calls / 5 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 405 reviewed · agreement `93.3%` · 27 disagreement(s) / 27 Judge call(s) · 22 Oracle answer(s) changed (`81.5%`) · QC cost `1.1252` USD
- Oracle disagreement by question type: `other` 26/393 (`6.6%`) · `quantitative_comparison` 0/1 (`0.0%`) · `temporal_comparison` 1/11 (`9.1%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.0398` · Oracle `0.0716` · Verifier `0.0002` · Total `0.1116`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Total execution cost (USD): `3.3476`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 13 | 18.03 | 7–40 |
| Questions (successful) | 13 | 18.03 | 7–40 |
| Guesser cost (USD) | 0.0288 | 0.0398 | 0.0198–0.0886 |
| Oracle cost (USD) | 0.0389 | 0.0716 | 0.0088–0.2469 |
| Verifier cost (USD) | 0.0002 | 0.0002 | 0.0002–0.0005 |
| Terminal-attempt cost (USD) | 0.0690 | 0.1116 | 0.0288–0.3356 |
| Tokens | 85918.5 | 136785.3 | 27073–414061 |
| LLM latency (ms) | 125101.5 | 192424.13 | 40642–549213 |
| Trial duration (s) | 125.3 | 192.6 | 40.7–549.7 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 11 | 0.0505 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 100.0% (clean) | 0 | 30 | 0.2356 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 13 | 0.0647 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0532 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 13 | 0.0771 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 100.0% | 100.0% (clean) | 0 | 34 | 0.2326 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 16 | 0.0856 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 100.0% (clean) | 0 | 13 | 0.0613 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0329 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 100.0% | 100.0% (clean) | 0 | 29 | 0.2224 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
