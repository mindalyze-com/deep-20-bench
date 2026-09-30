# Deep20Bench Edition 1.1

- Edition: `1.1` / `qualified-core-v1`
- Comparison classification: `standard`
- Explicit overrides: none
- Comparison contract: `2fa8c6bfffe0cf577cb6e97e8842a6c225d9b35b9ee22fa5a12461b2bc26fd5a`
- Execution: `BX-20260930-B-0003-official-M0032-001`
- Benchmark: `B-0003`
- Model: `M-0032` - Claude Sonnet 5.5 (high)
- Exact route: `anthropic/claude-sonnet-5.5`
- Execution commits: `4226b32547752fd1c5126d7bd1efb68069d7c880`
- Status: completed
- Success rate: 90.0%
- Median counted questions: 13
- Subjects: 10
- Iterations per subject: 3
- Trials: 27 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 4 recovered calls / 6 retried calls / 2 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 394 reviewed · agreement `93.9%` · 24 disagreement(s) / 24 Judge call(s) · 20 Oracle answer(s) changed (`83.3%`) · QC cost `1.0841` USD
- Oracle disagreement by question type: `negation` 0/8 (`0.0%`) · `other` 23/370 (`6.2%`) · `quantitative_comparison` 0/1 (`0.0%`) · `temporal_comparison` 1/15 (`6.7%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.0460` · Oracle `0.0698` · Verifier `0.0003` · Total `0.1160`
- Superseded infrastructure attempts: 3 across 3 trial(s) · cost `0.3688` USD
- Total execution cost (USD): `3.8500`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 13 | 17.73 | 8–40 |
| Questions (successful) | 12 | 15.26 | 8–33 |
| Guesser cost (USD) | 0.0221 | 0.0460 | 0.0090–0.2184 |
| Oracle cost (USD) | 0.0372 | 0.0698 | 0.0109–0.1869 |
| Verifier cost (USD) | 0.0002 | 0.0003 | 0.0002–0.0013 |
| Terminal-attempt cost (USD) | 0.0590 | 0.1160 | 0.0218–0.3771 |
| Tokens | 98515.5 | 153911.2 | 40930–439134 |
| LLM latency (ms) | 118130 | 197819.7 | 46751–611003 |
| Trial duration (s) | 118.5 | 198.2 | 46.9–612.1 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0424 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 100.0% (clean) | 0 | 21 | 0.1485 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 11 | 0.0519 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0442 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0409 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 66.7% | 100.0% (clean) | 0 | 33 | 0.2832 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 66.7% | 100.0% (clean) | 0 | 22 | 0.2273 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 100.0% (clean) | 0 | 14 | 0.0595 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0238 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 66.7% | 100.0% (clean) | 0 | 29 | 0.2387 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
