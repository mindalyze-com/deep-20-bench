# Deep20Bench Core Subjects

- Execution: `BX-20260727-official-M0012-025`
- Benchmark: `B-0001`
- Model: `M-0012` — Grok 4.5 (medium)
- Exact route: `x-ai/grok-4.5`
- Status: completed
- Success rate: 88.6%
- Median counted questions: 11
- Subjects: 7
- Iterations per subject: 5
- Trials: 31 successful / 35 scoring-eligible / 35 scheduled
- Infrastructure failures: 0
- Recovery: 0 recovered calls / 0 retried calls / 0 exhausted
- Output-contract reliability: `breached` · compliance `99.1%` · 6 violation(s) across 5 trial(s) · 6 counted-turn penalties
- Terminal failure codes: `ask_after_question_limit`=4
- Average cost per terminal run (USD): Guesser `0.0403` · Oracle `0.0732` · Verifier `0.0003` · Total `0.1138`
- Total benchmark cost (USD): `3.9827`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 11 | 17.23 | 5–50 |
| Questions (successful) | 10 | 13 | 5–43 |
| Guesser cost (USD) | 0.0149 | 0.0403 | 0.0054–0.2175 |
| Oracle cost (USD) | 0.0388 | 0.0732 | 0.0155–0.3099 |
| Verifier cost (USD) | 0.0003 | 0.0003 | 0.0000–0.0007 |
| Total cost (USD) | 0.0551 | 0.1138 | 0.0212–0.5277 |
| Tokens | 49990 | 109176.51 | 20077–536321 |
| LLM latency (ms) | 107836 | 227702.31 | 42095–1151629 |
| Trial duration (s) | 108.2 | 228.2 | 42.3–1152.6 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0455 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 60.0% | 98.2% (breached) | 4 | 43 | 0.3500 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 14 | 0.0742 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 60.0% | 98.7% (breached) | 2 | 25 | 0.2153 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 7 | 0.0346 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 12 | 0.0512 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 5 | 0.0257 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
