# Deep20Bench Core Subjects

- Execution: `BX-20260728-official-M0006-010`
- Benchmark: `B-0001`
- Model: `M-0006` — Claude Opus 5 (high)
- Exact route: `anthropic/claude-opus-5`
- Status: completed
- Success rate: 100.0%
- Median counted questions: 11
- Subjects: 7
- Iterations per subject: 5
- Trials: 35 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 0 recovered calls / 0 retried calls / 0 exhausted
- Output-contract reliability: `breached` · compliance `99.4%` · 3 violation(s) across 2 trial(s) · 3 counted-turn penalties
- Oracle quality control: 404 reviewed · agreement `89.8%` · 41 disagreement(s) / 41 Judge call(s) · 4 Oracle answer(s) changed (`9.8%`) · QC cost `0.9075` USD
- Oracle disagreement by question type: `other` 40/375 (`10.7%`) · `quantitative_comparison` 0/2 (`0.0%`) · `temporal_comparison` 1/27 (`3.7%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.0705` · Oracle `0.0854` · Verifier `0.0003` · Total `0.1562`
- Total benchmark cost (USD): `5.4676`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 11 | 12.34 | 5–27 |
| Questions (successful) | 11 | 12.34 | 5–27 |
| Guesser cost (USD) | 0.0476 | 0.0705 | 0.0286–0.2560 |
| Oracle cost (USD) | 0.0762 | 0.0854 | 0.0319–0.3052 |
| Verifier cost (USD) | 0.0003 | 0.0003 | 0.0003–0.0007 |
| Total cost (USD) | 0.1279 | 0.1562 | 0.0643–0.5013 |
| Tokens | 95057 | 111703.17 | 47974–281007 |
| LLM latency (ms) | 172063 | 212687.03 | 85091–496878 |
| Trial duration (s) | 172.5 | 213.2 | 85.4–497.7 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 96.2% (breached) | 2 | 9 | 0.0963 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 100.0% | 100.0% (clean) | 0 | 24 | 0.3797 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 12 | 0.1313 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 100.0% | 100.0% (clean) | 0 | 12 | 0.1805 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 7 | 0.0749 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 98.6% (breached) | 1 | 13 | 0.1398 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 6 | 0.0911 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
