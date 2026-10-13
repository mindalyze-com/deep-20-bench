# Deep20Bench Edition 1.1

- Edition: `1.1` / `qualified-core-v1`
- Comparison classification: `standard`
- Explicit overrides: none
- Comparison contract: `2fa8c6bfffe0cf577cb6e97e8842a6c225d9b35b9ee22fa5a12461b2bc26fd5a`
- Execution: `BX-20261013-B-0003-OFFICIAL-M0033-002`
- Benchmark: `B-0003`
- Model: `M-0033` - Muse Wonder (high)
- Exact route: `meta/muse-wonder`
- Execution commits: `333294db9cacdd730bd7900d770162615d5e33ea`
- Status: completed
- Success rate: 96.7%
- Median counted questions: 18.5
- Subjects: 10
- Iterations per subject: 3
- Trials: 29 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 5 recovered calls / 5 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 412 reviewed · agreement `92.7%` · 30 disagreement(s) / 30 Judge call(s) · 18 Oracle answer(s) changed (`60.0%`) · QC cost `1.2618` USD
- Oracle disagreement by question type: `negation` 0/2 (`0.0%`) · `other` 30/373 (`8.0%`) · `temporal_comparison` 0/37 (`0.0%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.1605` · Oracle `0.0787` · Verifier `0.0002` · Total `0.2394`
- Superseded infrastructure attempts: 5 across 5 trial(s) · cost `0.0719` USD
- Total execution cost (USD): `7.2536`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 18.5 | 19.6 | 7–40 |
| Questions (successful) | 18 | 18.9 | 7–37 |
| Guesser cost (USD) | 0.1160 | 0.1605 | 0.0254–0.7637 |
| Oracle cost (USD) | 0.0648 | 0.0787 | 0.0117–0.2264 |
| Verifier cost (USD) | 0.0002 | 0.0002 | 0.0002–0.0002 |
| Terminal-attempt cost (USD) | 0.1960 | 0.2394 | 0.0423–0.9334 |
| Tokens | 133761.5 | 148309.5 | 37036–380157 |
| LLM latency (ms) | 214508 | 265097.3 | 61585–859617 |
| Trial duration (s) | 214.8 | 265.5 | 61.7–860.2 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 15 | 0.0961 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 100.0% (clean) | 0 | 21 | 0.2684 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 22 | 0.2869 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0654 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 14 | 0.0977 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 66.7% | 100.0% (clean) | 0 | 37 | 0.7288 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 20 | 0.2590 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 100.0% (clean) | 0 | 20 | 0.2341 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0701 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 100.0% | 100.0% (clean) | 0 | 27 | 0.2874 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
