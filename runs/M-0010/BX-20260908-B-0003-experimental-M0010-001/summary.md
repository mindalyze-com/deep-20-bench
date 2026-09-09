# Deep20Bench Five Answer Experiment

- Execution: `BX-20260908-B-0003-experimental-M0010-001`
- Benchmark: `B-0003`
- Model: `M-0010` - GPT-5.6 Sol (high)
- Exact route: `openai/gpt-5.6-sol`
- Execution commits: `eceee31eef2eee309df803adf99bb6fa5bac3c87`
- Status: completed
- Success rate: 96.7%
- Median counted questions: 15
- Subjects: 10
- Iterations per subject: 3
- Trials: 29 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 10 recovered calls / 11 retried calls / 1 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 488 reviewed · agreement `94.7%` · 26 disagreement(s) / 26 Judge call(s) · 14 Oracle answer(s) changed (`53.8%`) · QC cost `1.2175` USD
- Oracle disagreement by question type: `negation` 0/2 (`0.0%`) · `other` 25/463 (`5.4%`) · `quantitative_comparison` 0/1 (`0.0%`) · `temporal_comparison` 1/22 (`4.6%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.0557` · Oracle `0.0863` · Verifier `0.0002` · Total `0.1423`
- Superseded infrastructure attempts: 1 across 1 trial(s) · cost `0.1135` USD
- Total execution cost (USD): `4.3812`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 15 | 18.03 | 7–40 |
| Questions (successful) | 14 | 17.28 | 7–39 |
| Guesser cost (USD) | 0.0366 | 0.0557 | 0.0232–0.2808 |
| Oracle cost (USD) | 0.0591 | 0.0863 | 0.0217–0.2672 |
| Verifier cost (USD) | 0.0002 | 0.0002 | 0.0002–0.0002 |
| Terminal-attempt cost (USD) | 0.0981 | 0.1423 | 0.0477–0.5481 |
| Tokens | 137248 | 178485.67 | 57675–555184 |
| LLM latency (ms) | 217214.5 | 312286.7 | 109183–1311311 |
| Trial duration (s) | 217.4 | 312.5 | 109.3–1311.9 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0641 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 100.0% (clean) | 0 | 25 | 0.2328 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 12 | 0.0798 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 66.7% | 100.0% (clean) | 0 | 10 | 0.2212 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 11 | 0.0728 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 100.0% | 100.0% (clean) | 0 | 25 | 0.2209 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 19 | 0.1845 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 100.0% (clean) | 0 | 23 | 0.1453 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0521 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 100.0% | 100.0% (clean) | 0 | 18 | 0.1490 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
