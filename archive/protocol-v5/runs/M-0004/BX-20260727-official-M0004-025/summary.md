# Deep20Bench Core Subjects

- Execution: `BX-20260727-official-M0004-025`
- Benchmark: `B-0001`
- Model: `M-0004` — GPT-5 Nano (medium)
- Exact route: `openai/gpt-5-nano`
- Status: completed
- Success rate: 88.6%
- Median counted questions: 10
- Subjects: 7
- Iterations per subject: 5
- Trials: 31 successful / 35 scoring-eligible / 35 scheduled
- Infrastructure failures: 0
- Recovery: 1 recovered calls / 1 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Terminal failure codes: `ask_after_question_limit`=4
- Average cost per terminal run (USD): Guesser `0.0150` · Oracle `0.0604` · Verifier `0.0007` · Total `0.0760`
- Total benchmark cost (USD): `2.6603`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 10 | 15.77 | 2–50 |
| Questions (successful) | 9 | 11.35 | 2–28 |
| Guesser cost (USD) | 0.0069 | 0.0150 | 0.0012–0.0732 |
| Oracle cost (USD) | 0.0387 | 0.0604 | 0.0054–0.2962 |
| Verifier cost (USD) | 0.0003 | 0.0007 | 0.0003–0.0040 |
| Total cost (USD) | 0.0462 | 0.0760 | 0.0069–0.3700 |
| Tokens | 64622 | 119465.8 | 9330–621595 |
| LLM latency (ms) | 201241 | 439503.94 | 62731–2120489 |
| Trial duration (s) | 201.7 | 439.9 | 62.9–2121.9 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 6 | 0.0195 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 60.0% | 100.0% (clean) | 0 | 26 | 0.1413 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0381 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 80.0% | 100.0% (clean) | 0 | 18 | 0.1479 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0571 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 80.0% | 100.0% (clean) | 0 | 17 | 0.1032 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 5 | 0.0250 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
