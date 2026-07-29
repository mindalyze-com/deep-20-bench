# Deep20Bench Core Subjects

- Execution: `BX-20260727-official-M0009-025`
- Benchmark: `B-0001`
- Model: `M-0009` — Claude Sonnet 5 (medium)
- Exact route: `anthropic/claude-sonnet-5`
- Status: completed
- Success rate: 94.3%
- Median counted questions: 15
- Subjects: 7
- Iterations per subject: 5
- Trials: 33 successful / 35 scoring-eligible / 35 scheduled
- Infrastructure failures: 0
- Recovery: 1 recovered calls / 1 retried calls / 0 exhausted
- Output-contract reliability: `breached` · compliance `97.3%` · 19 violation(s) across 14 trial(s) · 19 counted-turn penalties
- Terminal failure codes: `ask_after_question_limit`=2
- Average cost per terminal run (USD): Guesser `0.0577` · Oracle `0.0668` · Verifier `0.0005` · Total `0.1251`
- Total benchmark cost (USD): `4.3769`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 15 | 18.97 | 4–50 |
| Questions (successful) | 15 | 17.09 | 4–50 |
| Guesser cost (USD) | 0.0233 | 0.0577 | 0.0073–0.2615 |
| Oracle cost (USD) | 0.0450 | 0.0668 | 0.0168–0.2200 |
| Verifier cost (USD) | 0.0003 | 0.0005 | 0.0003–0.0029 |
| Total cost (USD) | 0.0698 | 0.1251 | 0.0244–0.4383 |
| Tokens | 69373 | 112051.14 | 26013–379923 |
| LLM latency (ms) | 151386 | 241839.57 | 47470–848151 |
| Trial duration (s) | 151.8 | 242.4 | 47.7–849.1 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 95.3% (breached) | 3 | 10 | 0.0573 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 80.0% | 97.0% (breached) | 6 | 38 | 0.2619 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 97.8% (breached) | 2 | 16 | 0.0807 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 100.0% | 95.8% (breached) | 6 | 25 | 0.2135 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 7 | 0.0343 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 80.0% | 98.0% (breached) | 2 | 13 | 0.1299 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 6 | 0.0978 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
