# Deep20Bench Edition 1.1

- Edition: `1.1` / `qualified-core-v1`
- Comparison classification: `standard`
- Explicit overrides: none
- Comparison contract: `2fa8c6bfffe0cf577cb6e97e8842a6c225d9b35b9ee22fa5a12461b2bc26fd5a`
- Execution: `BX-20261120-B-0003-official-M0042-001`
- Benchmark: `B-0003`
- Model: `M-0042` - Gemini 4 Neon (high)
- Exact route: `google/gemini-4-neon`
- Execution commits: `e0c007c6a42c982dbc731ae8e65fa899c8d5fa7e`
- Status: completed
- Success rate: 100.0%
- Median counted questions: 12
- Subjects: 10
- Iterations per subject: 3
- Trials: 30 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 0 recovered calls / 0 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 253 reviewed · agreement `92.9%` · 18 disagreement(s) / 18 Judge call(s) · 9 Oracle answer(s) changed (`50.0%`) · QC cost `0.7523` USD
- Oracle disagreement by question type: `negation` 0/2 (`0.0%`) · `other` 17/225 (`7.6%`) · `temporal_comparison` 1/26 (`3.8%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.2511` · Oracle `0.0543` · Verifier `0.0002` · Total `0.3057`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Total execution cost (USD): `9.1701`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 12 | 13.9 | 7–35 |
| Questions (successful) | 12 | 13.9 | 7–35 |
| Guesser cost (USD) | 0.1621 | 0.2511 | 0.0823–1.2255 |
| Oracle cost (USD) | 0.0321 | 0.0543 | 0.0088–0.2008 |
| Verifier cost (USD) | 0.0002 | 0.0002 | 0.0002–0.0005 |
| Terminal-attempt cost (USD) | 0.1917 | 0.3057 | 0.0914–1.4265 |
| Tokens | 96451 | 140530.47 | 36759–528053 |
| LLM latency (ms) | 151602.5 | 231155.4 | 60841–1009187 |
| Trial duration (s) | 151.8 | 231.4 | 60.9–1010.0 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 11 | 0.1741 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 100.0% (clean) | 0 | 16 | 0.3648 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.1460 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 8 | 0.1188 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 11 | 0.1595 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 100.0% | 100.0% (clean) | 0 | 23 | 1.0003 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 12 | 0.2537 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 100.0% (clean) | 0 | 13 | 0.2001 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 11 | 0.1540 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 100.0% | 100.0% (clean) | 0 | 19 | 0.4854 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
