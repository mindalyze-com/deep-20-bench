# Deep20Bench Edition 1.1

- Edition: `1.1` / `qualified-core-v1`
- Comparison classification: `standard`
- Explicit overrides: none
- Comparison contract: `2fa8c6bfffe0cf577cb6e97e8842a6c225d9b35b9ee22fa5a12461b2bc26fd5a`
- Execution: `BX-20261103-B-0003-official-M0032-001`
- Benchmark: `B-0003`
- Model: `M-0032` - Claude Sonnet 5.5 (high)
- Exact route: `anthropic/claude-sonnet-5.5`
- Execution commits: `4b2fe1656ea7078dcac257f028139cb437727e89`
- Status: completed
- Success rate: 86.7%
- Median counted questions: 13
- Subjects: 10
- Iterations per subject: 3
- Trials: 26 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 2 recovered calls / 2 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 357 reviewed · agreement `93.3%` · 24 disagreement(s) / 24 Judge call(s) · 16 Oracle answer(s) changed (`66.7%`) · QC cost `0.9973` USD
- Oracle disagreement by question type: `negation` 0/7 (`0.0%`) · `other` 21/333 (`6.3%`) · `temporal_comparison` 3/17 (`17.6%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.0475` · Oracle `0.0674` · Verifier `0.0003` · Total `0.1152`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Total execution cost (USD): `3.4570`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 13 | 18.07 | 8–40 |
| Questions (successful) | 12 | 14.69 | 8–35 |
| Guesser cost (USD) | 0.0217 | 0.0475 | 0.0074–0.2073 |
| Oracle cost (USD) | 0.0470 | 0.0674 | 0.0031–0.2090 |
| Verifier cost (USD) | 0.0002 | 0.0003 | 0.0002–0.0012 |
| Terminal-attempt cost (USD) | 0.0646 | 0.1152 | 0.0108–0.3913 |
| Tokens | 107340.5 | 161390.37 | 25868–505845 |
| LLM latency (ms) | 129894 | 212836.13 | 25760–785361 |
| Trial duration (s) | 130.1 | 213.1 | 25.9–786.2 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 12 | 0.0420 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 100.0% (clean) | 0 | 18 | 0.1225 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0364 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0533 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 11 | 0.0434 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 33.3% | 100.0% (clean) | 0 | 40 | 0.3357 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 66.7% | 100.0% (clean) | 0 | 29 | 0.2083 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 100.0% (clean) | 0 | 13 | 0.0712 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0314 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 66.7% | 100.0% (clean) | 0 | 27 | 0.2081 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
