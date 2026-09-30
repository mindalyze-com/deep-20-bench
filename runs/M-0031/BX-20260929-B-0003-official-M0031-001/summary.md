# Deep20Bench Edition 1.1

- Edition: `1.1` / `qualified-core-v1`
- Comparison classification: `standard`
- Explicit overrides: none
- Comparison contract: `2fa8c6bfffe0cf577cb6e97e8842a6c225d9b35b9ee22fa5a12461b2bc26fd5a`
- Execution: `BX-20260929-B-0003-official-M0031-001`
- Benchmark: `B-0003`
- Model: `M-0031` - GPT-6.1 Sol (high)
- Exact route: `openai/gpt-6.1-sol`
- Execution commits: `4226b32547752fd1c5126d7bd1efb68069d7c880`
- Status: completed
- Success rate: 96.7%
- Median counted questions: 11.5
- Subjects: 10
- Iterations per subject: 3
- Trials: 29 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 6 recovered calls / 7 retried calls / 1 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 315 reviewed · agreement `93.3%` · 21 disagreement(s) / 21 Judge call(s) · 14 Oracle answer(s) changed (`66.7%`) · QC cost `0.9096` USD
- Oracle disagreement by question type: `negation` 0/2 (`0.0%`) · `other` 20/303 (`6.6%`) · `temporal_comparison` 1/10 (`10.0%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.0376` · Oracle `0.0579` · Verifier `0.0002` · Total `0.0957`
- Superseded infrastructure attempts: 3 across 2 trial(s) · cost `0.5393` USD
- Total execution cost (USD): `3.4104`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 11.5 | 15.2 | 8–40 |
| Questions (successful) | 11 | 14.34 | 8–40 |
| Guesser cost (USD) | 0.0293 | 0.0376 | 0.0219–0.1323 |
| Oracle cost (USD) | 0.0363 | 0.0579 | 0.0107–0.2395 |
| Verifier cost (USD) | 0.0002 | 0.0002 | 0.0002–0.0006 |
| Terminal-attempt cost (USD) | 0.0651 | 0.0957 | 0.0347–0.3371 |
| Tokens | 87468.5 | 109959.17 | 32999–377455 |
| LLM latency (ms) | 127012 | 195157.2 | 62519–771023 |
| Trial duration (s) | 127.3 | 195.5 | 62.7–772.1 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0455 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 100.0% (clean) | 0 | 19 | 0.1650 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0534 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0496 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0584 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 100.0% | 100.0% (clean) | 0 | 21 | 0.1129 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 16 | 0.1242 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 100.0% (clean) | 0 | 15 | 0.0654 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0411 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 66.7% | 100.0% (clean) | 0 | 40 | 0.2414 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
