# Deep20Bench Core Subjects

- Execution: `BX-20260805-official-M0014-011`
- Benchmark: `B-0001`
- Model: `M-0014` — Claude Fable 5 (high)
- Exact route: `anthropic/claude-fable-5`
- Execution commits: `966cbf7123808a6394ccb6e96a64e683456efbfb`
- Status: completed
- Success rate: 100.0%
- Median counted questions: 9
- Subjects: 7
- Iterations per subject: 5
- Trials: 35 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 2 recovered calls / 2 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 379 reviewed · agreement `91.3%` · 33 disagreement(s) / 33 Judge call(s) · 1 Oracle answer(s) changed (`3.0%`) · QC cost `0.7328` USD
- Oracle disagreement by question type: `negation` 0/4 (`0.0%`) · `other` 33/339 (`9.7%`) · `quantitative_comparison` 0/1 (`0.0%`) · `temporal_comparison` 0/35 (`0.0%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.1776` · Oracle `0.0471` · Verifier `0.0001` · Total `0.2248`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Total execution cost (USD): `7.8664`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 9 | 12.06 | 6–43 |
| Questions (successful) | 9 | 12.06 | 6–43 |
| Guesser cost (USD) | 0.0819 | 0.1776 | 0.0550–1.4680 |
| Oracle cost (USD) | 0.0269 | 0.0471 | 0.0182–0.2400 |
| Verifier cost (USD) | 0.0001 | 0.0001 | 0.0001–0.0007 |
| Terminal-attempt cost (USD) | 0.1112 | 0.2248 | 0.0733–1.7085 |
| Tokens | 73967 | 109434.71 | 47882–602230 |
| LLM latency (ms) | 183467 | 273705.89 | 121374–1217880 |
| Trial duration (s) | 183.7 | 274.0 | 121.5–1218.9 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 10 | 0.1182 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 100.0% | 100.0% (clean) | 0 | 27 | 0.9020 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 11 | 0.1218 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 100.0% | 100.0% (clean) | 0 | 9 | 0.1257 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 8 | 0.1017 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 9 | 0.1051 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 7 | 0.0987 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
