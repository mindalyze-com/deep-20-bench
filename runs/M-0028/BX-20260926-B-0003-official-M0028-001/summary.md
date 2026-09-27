# Deep20Bench Edition 1.1

- Edition: `1.1` / `qualified-core-v1`
- Comparison classification: `standard`
- Explicit overrides: none
- Comparison contract: `2fa8c6bfffe0cf577cb6e97e8842a6c225d9b35b9ee22fa5a12461b2bc26fd5a`
- Execution: `BX-20260926-B-0003-official-M0028-001`
- Benchmark: `B-0003`
- Model: `M-0028` - GPT-6 Luna (high)
- Exact route: `openai/gpt-6-luna`
- Execution commits: `6e46fb003ebf43423c802cbb37f69bdc8b321ddf`
- Status: completed
- Success rate: 80.0%
- Median counted questions: 15.5
- Subjects: 10
- Iterations per subject: 3
- Trials: 24 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 2 recovered calls / 2 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 494 reviewed · agreement `94.3%` · 28 disagreement(s) / 28 Judge call(s) · 18 Oracle answer(s) changed (`64.3%`) · QC cost `1.2727` USD
- Oracle disagreement by question type: `negation` 0/2 (`0.0%`) · `other` 28/481 (`5.8%`) · `quantitative_comparison` 0/1 (`0.0%`) · `temporal_comparison` 0/10 (`0.0%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.0031` · Oracle `0.0844` · Verifier `0.0002` · Total `0.0877`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Total execution cost (USD): `2.6315`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 15.5 | 20.97 | 8–40 |
| Questions (successful) | 13.5 | 16.21 | 8–39 |
| Guesser cost (USD) | 0.0018 | 0.0031 | 0.0012–0.0096 |
| Oracle cost (USD) | 0.0562 | 0.0844 | 0.0089–0.2663 |
| Verifier cost (USD) | 0.0002 | 0.0002 | 0.0002–0.0007 |
| Terminal-attempt cost (USD) | 0.0586 | 0.0877 | 0.0107–0.2733 |
| Tokens | 104948.5 | 169244.77 | 31810–433208 |
| LLM latency (ms) | 144451.5 | 227033.3 | 46408–601808 |
| Trial duration (s) | 144.6 | 227.3 | 46.5–602.3 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 11 | 0.0158 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 66.7% | 100.0% (clean) | 0 | 30 | 0.1366 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 13 | 0.0478 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0456 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 15 | 0.0461 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 0.0% | 100.0% (clean) | 0 | 40 | 0.1856 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 16 | 0.0706 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 66.7% | 100.0% (clean) | 0 | 39 | 0.1342 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0178 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 66.7% | 100.0% (clean) | 0 | 31 | 0.1771 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
