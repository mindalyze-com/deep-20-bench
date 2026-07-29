# Deep20Bench Core Subjects

- Execution: `BX-20260727-official-M0010-025`
- Benchmark: `B-0001`
- Model: `M-0010` — Claude Opus 5 (medium)
- Exact route: `anthropic/claude-opus-5`
- Status: completed
- Success rate: 94.3%
- Median counted questions: 11
- Subjects: 7
- Iterations per subject: 5
- Trials: 33 successful / 35 scoring-eligible / 35 scheduled
- Infrastructure failures: 0
- Recovery: 2 recovered calls / 2 retried calls / 0 exhausted
- Output-contract reliability: `breached` · compliance `99.8%` · 1 violation(s) across 1 trial(s) · 1 counted-turn penalties
- Terminal failure codes: `ask_after_question_limit`=2
- Average cost per terminal run (USD): Guesser `0.0977` · Oracle `0.0572` · Verifier `0.0005` · Total `0.1554`
- Total benchmark cost (USD): `5.4377`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 11 | 15.06 | 5–50 |
| Questions (successful) | 11 | 12.94 | 5–37 |
| Guesser cost (USD) | 0.0403 | 0.0977 | 0.0240–0.8348 |
| Oracle cost (USD) | 0.0368 | 0.0572 | 0.0199–0.2944 |
| Verifier cost (USD) | 0.0003 | 0.0005 | 0.0003–0.0032 |
| Total cost (USD) | 0.0789 | 0.1554 | 0.0466–1.1313 |
| Tokens | 54362 | 92970.51 | 30116–570380 |
| LLM latency (ms) | 126040 | 196359.8 | 67978–988747 |
| Trial duration (s) | 126.4 | 196.8 | 68.1–990.1 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 11 | 0.0698 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 100.0% | 99.3% (breached) | 1 | 22 | 0.2883 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 13 | 0.0845 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 60.0% | 100.0% (clean) | 0 | 22 | 0.4312 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 7 | 0.0663 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0851 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 6 | 0.0622 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
