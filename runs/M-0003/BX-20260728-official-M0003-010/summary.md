# Deep20Bench Core Subjects

- Execution: `BX-20260728-official-M0003-010`
- Benchmark: `B-0001`
- Model: `M-0003` — GPT-5 Nano (medium)
- Exact route: `openai/gpt-5-nano`
- Status: completed
- Success rate: 94.3%
- Median counted questions: 12
- Subjects: 7
- Iterations per subject: 5
- Trials: 33 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 1 recovered calls / 1 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 490 reviewed · agreement `86.5%` · 66 disagreement(s) / 66 Judge call(s) · 1 Oracle answer(s) changed (`1.5%`) · QC cost `1.2997` USD
- Oracle disagreement by question type: `other` 66/475 (`13.9%`) · `quantitative_comparison` 0/2 (`0.0%`) · `temporal_comparison` 0/13 (`0.0%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.0138` · Oracle `0.1167` · Verifier `0.0006` · Total `0.1311`
- Total benchmark cost (USD): `4.5882`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 12 | 15.43 | 2–50 |
| Questions (successful) | 11 | 13.33 | 2–48 |
| Guesser cost (USD) | 0.0079 | 0.0138 | 0.0015–0.0587 |
| Oracle cost (USD) | 0.0870 | 0.1167 | 0.0067–0.4150 |
| Verifier cost (USD) | 0.0003 | 0.0006 | 0.0003–0.0030 |
| Total cost (USD) | 0.0985 | 0.1311 | 0.0085–0.4747 |
| Tokens | 115307 | 167686.94 | 12782–574240 |
| LLM latency (ms) | 327264 | 505595.66 | 52057–1860708 |
| Trial duration (s) | 327.9 | 506.3 | 52.1–1861.8 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 4 | 0.0170 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 60.0% | 100.0% (clean) | 0 | 48 | 0.4045 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 12 | 0.0984 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 100.0% | 100.0% (clean) | 0 | 15 | 0.1395 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 11 | 0.0972 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 15 | 0.1208 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 5 | 0.0402 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
