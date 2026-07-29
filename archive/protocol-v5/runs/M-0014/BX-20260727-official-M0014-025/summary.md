# Deep20Bench Core Subjects

- Execution: `BX-20260727-official-M0014-025`
- Benchmark: `B-0001`
- Model: `M-0014` — Llama 4 Maverick (non-thinking)
- Exact route: `meta-llama/llama-4-maverick`
- Status: completed
- Success rate: 45.7%
- Median counted questions: 50
- Subjects: 7
- Iterations per subject: 5
- Trials: 16 successful / 35 scoring-eligible / 35 scheduled
- Infrastructure failures: 0
- Recovery: 22 recovered calls / 22 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.0086` · Oracle `0.0466` · Verifier `0.0073` · Total `0.0625`
- Total benchmark cost (USD): `2.1884`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 50 | 31.46 | 3–50 |
| Questions (successful) | 7.5 | 9.44 | 3–27 |
| Guesser cost (USD) | 0.0137 | 0.0086 | 0.0004–0.0161 |
| Oracle cost (USD) | 0.0468 | 0.0466 | 0.0122–0.0912 |
| Verifier cost (USD) | 0.0113 | 0.0073 | 0.0003–0.0142 |
| Total cost (USD) | 0.0724 | 0.0625 | 0.0129–0.1174 |
| Tokens | 137140 | 106805.31 | 14846–231559 |
| LLM latency (ms) | 180699 | 154530.14 | 21223–309552 |
| Trial duration (s) | 182.9 | 155.7 | 21.5–311.4 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 60.0% | 100.0% (clean) | 0 | 8 | 0.0478 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 0.0% | 100.0% (clean) | 0 | 50 | 0.0974 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 0.0% | 100.0% (clean) | 0 | 50 | 0.1013 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 0.0% | 100.0% (clean) | 0 | 50 | 0.0788 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 60.0% | 100.0% (clean) | 0 | 27 | 0.0559 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 12 | 0.0406 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 3 | 0.0158 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
