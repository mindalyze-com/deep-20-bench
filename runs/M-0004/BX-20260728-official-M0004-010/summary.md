# Deep20Bench Core Subjects

- Execution: `BX-20260728-official-M0004-010`
- Benchmark: `B-0001`
- Model: `M-0004` — Gemini 3.6 Flash (high)
- Exact route: `google/gemini-3.6-flash`
- Status: completed
- Success rate: 97.1%
- Median counted questions: 15
- Subjects: 7
- Iterations per subject: 5
- Trials: 34 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 0 recovered calls / 0 retried calls / 0 exhausted
- Output-contract reliability: `breached` · compliance `99.8%` · 1 violation(s) across 1 trial(s) · 1 counted-turn penalties
- Oracle quality control: 559 reviewed · agreement `93.2%` · 38 disagreement(s) / 38 Judge call(s) · 3 Oracle answer(s) changed (`7.9%`) · QC cost `0.9336` USD
- Oracle disagreement by question type: `other` 38/475 (`8.0%`) · `quantitative_comparison` 0/1 (`0.0%`) · `temporal_comparison` 0/83 (`0.0%`)
- Terminal failure codes: `ask_after_question_limit`=1
- Average cost per terminal run (USD): Guesser `0.1705` · Oracle `0.1107` · Verifier `0.0004` · Total `0.2816`
- Total benchmark cost (USD): `9.8555`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 15 | 16.86 | 7–50 |
| Questions (successful) | 14.5 | 15.88 | 7–43 |
| Guesser cost (USD) | 0.0735 | 0.1705 | 0.0367–1.4365 |
| Oracle cost (USD) | 0.0798 | 0.1107 | 0.0331–0.3732 |
| Verifier cost (USD) | 0.0003 | 0.0004 | 0.0003–0.0011 |
| Total cost (USD) | 0.1601 | 0.2816 | 0.0713–1.7725 |
| Tokens | 117794 | 159845.97 | 48029–620805 |
| LLM latency (ms) | 183439 | 294184.91 | 86876–1410853 |
| Trial duration (s) | 183.9 | 295.0 | 87.4–1413.6 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 14 | 0.1539 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 100.0% | 100.0% (clean) | 0 | 20 | 0.2931 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 98.9% (breached) | 1 | 17 | 0.2175 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 80.0% | 100.0% (clean) | 0 | 40 | 0.9628 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0819 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 14 | 0.1417 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 8 | 0.1202 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
