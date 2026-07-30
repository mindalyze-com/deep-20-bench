# Deep20Bench Core Subjects

- Execution: `BX-20260728-official-M0011-012`
- Benchmark: `B-0001`
- Model: `M-0011` — Qwen3.7 Plus (high)
- Exact route: `qwen/qwen3.7-plus`
- Execution commits: `d7eadbde0e815368131a681fe932cceef6aefa0b`
- Status: completed
- Success rate: 77.1%
- Median counted questions: 17
- Subjects: 7
- Iterations per subject: 5
- Trials: 27 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 8 recovered calls / 8 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 799 reviewed · agreement `90.4%` · 77 disagreement(s) / 77 Judge call(s) · 14 Oracle answer(s) changed (`18.2%`) · QC cost `1.7758` USD
- Oracle disagreement by question type: `negation` 4/8 (`50.0%`) · `other` 71/757 (`9.4%`) · `quantitative_comparison` 0/1 (`0.0%`) · `temporal_comparison` 2/33 (`6.1%`)
- Terminal failure codes: `ask_after_question_limit`=8
- Average cost per terminal run (USD): Guesser `0.0703` · Oracle `0.1978` · Verifier `0.0004` · Total `0.2685`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Total execution cost (USD): `9.3977`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 17 | 25.06 | 1–50 |
| Questions (successful) | 15 | 17.67 | 1–50 |
| Guesser cost (USD) | 0.0287 | 0.0703 | 0.0014–0.3645 |
| Oracle cost (USD) | 0.1441 | 0.1978 | 0.0058–0.6099 |
| Verifier cost (USD) | 0.0003 | 0.0004 | 0.0000–0.0013 |
| Terminal-attempt cost (USD) | 0.1562 | 0.2685 | 0.0075–0.7271 |
| Tokens | 189538 | 295972.09 | 8981–782484 |
| LLM latency (ms) | 599006 | 1209250.71 | 46477–5534990 |
| Trial duration (s) | 599.5 | 1209.8 | 46.5–5535.8 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 80.0% | 100.0% (clean) | 0 | 15 | 0.2054 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 40.0% | 100.0% (clean) | 0 | 50 | 0.4773 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 60.0% | 100.0% (clean) | 0 | 42 | 0.4442 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 60.0% | 100.0% (clean) | 0 | 36 | 0.3819 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 9 | 0.1779 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 13 | 0.0990 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 5 | 0.0938 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
