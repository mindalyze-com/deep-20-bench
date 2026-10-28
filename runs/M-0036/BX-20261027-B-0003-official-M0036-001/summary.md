# Deep20Bench Edition 1.1

- Edition: `1.1` / `qualified-core-v1`
- Comparison classification: `standard`
- Explicit overrides: none
- Comparison contract: `2fa8c6bfffe0cf577cb6e97e8842a6c225d9b35b9ee22fa5a12461b2bc26fd5a`
- Execution: `BX-20261027-B-0003-official-M0036-001`
- Benchmark: `B-0003`
- Model: `M-0036` - GPT-6.1 Terra (high)
- Exact route: `openai/gpt-6.1-terra`
- Execution commits: `f1d0a08a1bb723be0cc035402d05dc2fa1b23d50`
- Status: completed
- Success rate: 90.0%
- Median counted questions: 14
- Subjects: 10
- Iterations per subject: 3
- Trials: 27 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 0 recovered calls / 2 retried calls / 2 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 395 reviewed · agreement `94.4%` · 22 disagreement(s) / 22 Judge call(s) · 17 Oracle answer(s) changed (`77.3%`) · QC cost `0.9966` USD
- Oracle disagreement by question type: `other` 21/384 (`5.5%`) · `temporal_comparison` 1/11 (`9.1%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.0190` · Oracle `0.0704` · Verifier `0.0002` · Total `0.0896`
- Superseded infrastructure attempts: 2 across 2 trial(s) · cost `0.3048` USD
- Total execution cost (USD): `2.9929`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 14 | 18.73 | 7–40 |
| Questions (successful) | 14 | 16.37 | 7–36 |
| Guesser cost (USD) | 0.0130 | 0.0190 | 0.0099–0.0496 |
| Oracle cost (USD) | 0.0351 | 0.0704 | 0.0032–0.2236 |
| Verifier cost (USD) | 0.0002 | 0.0002 | 0.0002–0.0008 |
| Terminal-attempt cost (USD) | 0.0489 | 0.0896 | 0.0137–0.2668 |
| Tokens | 96534 | 152362.23 | 17302–469794 |
| LLM latency (ms) | 132777 | 204837.43 | 27673–586086 |
| Trial duration (s) | 133.0 | 205.1 | 27.7–586.7 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0244 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 33.3% | 100.0% (clean) | 0 | 40 | 0.2232 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 11 | 0.0820 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0269 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 13 | 0.0617 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 100.0% | 100.0% (clean) | 0 | 23 | 0.1223 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 15 | 0.0648 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 66.7% | 100.0% (clean) | 0 | 17 | 0.0909 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0278 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 100.0% | 100.0% (clean) | 0 | 30 | 0.1721 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
