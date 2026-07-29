# Deep20Bench Core Subjects

- Execution: `BX-20260727-official-M0001-025`
- Benchmark: `B-0001`
- Model: `M-0001` — GPT-5.6 Luna (medium)
- Exact route: `openai/gpt-5.6-luna`
- Status: completed
- Success rate: 100.0%
- Median counted questions: 14
- Subjects: 7
- Iterations per subject: 5
- Trials: 35 successful / 35 scoring-eligible / 35 scheduled
- Infrastructure failures: 0
- Recovery: 2 recovered calls / 2 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.0146` · Oracle `0.0769` · Verifier `0.0004` · Total `0.0919`
- Total benchmark cost (USD): `3.2153`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 14 | 19.46 | 4–48 |
| Questions (successful) | 14 | 19.46 | 4–48 |
| Guesser cost (USD) | 0.0110 | 0.0146 | 0.0029–0.0438 |
| Oracle cost (USD) | 0.0549 | 0.0769 | 0.0175–0.2140 |
| Verifier cost (USD) | 0.0003 | 0.0004 | 0.0003–0.0010 |
| Total cost (USD) | 0.0639 | 0.0919 | 0.0207–0.2464 |
| Tokens | 78449 | 104670.49 | 21708–325483 |
| LLM latency (ms) | 160797 | 213177.17 | 41561–635137 |
| Trial duration (s) | 161.3 | 213.8 | 41.8–635.9 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 11 | 0.0368 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 100.0% | 100.0% (clean) | 0 | 41 | 0.1937 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 31 | 0.1438 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 100.0% | 100.0% (clean) | 0 | 24 | 0.1240 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 7 | 0.0300 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 14 | 0.0820 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 5 | 0.0328 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
