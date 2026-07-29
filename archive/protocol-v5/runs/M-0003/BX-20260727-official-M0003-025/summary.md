# Deep20Bench Core Subjects

- Execution: `BX-20260727-official-M0003-025`
- Benchmark: `B-0001`
- Model: `M-0003` — gpt-oss-120B (medium)
- Exact route: `openai/gpt-oss-120b`
- Status: completed
- Success rate: 94.3%
- Median counted questions: 13
- Subjects: 7
- Iterations per subject: 5
- Trials: 33 successful / 35 scoring-eligible / 35 scheduled
- Infrastructure failures: 0
- Recovery: 71 recovered calls / 71 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Terminal failure codes: `ask_after_question_limit`=2
- Average cost per terminal run (USD): Guesser `0.0149` · Oracle `0.0585` · Verifier `0.0007` · Total `0.0742`
- Total benchmark cost (USD): `2.5957`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 13 | 16.11 | 3–50 |
| Questions (successful) | 12 | 14.06 | 3–37 |
| Guesser cost (USD) | 0.0074 | 0.0149 | 0.0016–0.0909 |
| Oracle cost (USD) | 0.0425 | 0.0585 | 0.0118–0.2399 |
| Verifier cost (USD) | 0.0003 | 0.0007 | 0.0003–0.0051 |
| Total cost (USD) | 0.0502 | 0.0742 | 0.0138–0.3197 |
| Tokens | 54294 | 94215.23 | 16963–510418 |
| LLM latency (ms) | 187588 | 278074.23 | 29971–1056658 |
| Trial duration (s) | 188.4 | 278.5 | 30.1–1057.5 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 7 | 0.0245 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 80.0% | 100.0% (clean) | 0 | 30 | 0.1517 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 14 | 0.0693 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 100.0% | 100.0% (clean) | 0 | 15 | 0.0931 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 7 | 0.0658 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 80.0% | 100.0% (clean) | 0 | 15 | 0.0931 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 4 | 0.0217 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
