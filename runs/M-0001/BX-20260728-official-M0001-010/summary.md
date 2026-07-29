# Deep20Bench Core Subjects

- Execution: `BX-20260728-official-M0001-010`
- Benchmark: `B-0001`
- Model: `M-0001` — GPT-5.6 Luna (high)
- Exact route: `openai/gpt-5.6-luna`
- Status: completed
- Success rate: 91.4%
- Median counted questions: 13
- Subjects: 7
- Iterations per subject: 5
- Trials: 32 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 1 recovered calls / 1 retried calls / 0 exhausted
- Output-contract reliability: `breached` · compliance `99.8%` · 1 violation(s) across 1 trial(s) · 1 counted-turn penalties
- Oracle quality control: 587 reviewed · agreement `87.0%` · 76 disagreement(s) / 76 Judge call(s) · 7 Oracle answer(s) changed (`9.2%`) · QC cost `1.5790` USD
- Oracle disagreement by question type: `negation` 1/4 (`25.0%`) · `other` 72/551 (`13.1%`) · `temporal_comparison` 3/32 (`9.4%`)
- Terminal failure codes: `ask_after_question_limit`=3
- Average cost per terminal run (USD): Guesser `0.0184` · Oracle `0.1494` · Verifier `0.0003` · Total `0.1681`
- Total benchmark cost (USD): `5.8822`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 13 | 17.66 | 5–50 |
| Questions (successful) | 13 | 14.63 | 5–35 |
| Guesser cost (USD) | 0.0106 | 0.0184 | 0.0039–0.0890 |
| Oracle cost (USD) | 0.1039 | 0.1494 | 0.0258–0.5981 |
| Verifier cost (USD) | 0.0003 | 0.0003 | 0.0000–0.0007 |
| Total cost (USD) | 0.1163 | 0.1681 | 0.0311–0.6853 |
| Tokens | 129277 | 181050.94 | 31830–857691 |
| LLM latency (ms) | 218130 | 285560.17 | 76873–1118468 |
| Trial duration (s) | 219.1 | 286.4 | 77.0–1121.0 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0516 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 60.0% | 99.5% (breached) | 1 | 35 | 0.4007 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 18 | 0.1906 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 80.0% | 100.0% (clean) | 0 | 21 | 0.2622 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0660 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 14 | 0.1389 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 6 | 0.0665 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
