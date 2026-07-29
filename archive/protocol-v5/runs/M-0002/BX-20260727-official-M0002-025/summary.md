# Deep20Bench Core Subjects

- Execution: `BX-20260727-official-M0002-025`
- Benchmark: `B-0001`
- Model: `M-0002` — DeepSeek V4 Flash (high)
- Exact route: `deepseek/deepseek-v4-flash`
- Status: completed
- Success rate: 87.9%
- Median counted questions: 13
- Subjects: 7
- Iterations per subject: 5
- Trials: 29 successful / 33 scoring-eligible / 35 scheduled
- Infrastructure failures: 2
- Recovery: 25 recovered calls / 25 retried calls / 0 exhausted
- Output-contract reliability: `breached` · compliance `99.8%` · 1 violation(s) across 1 trial(s) · 1 counted-turn penalties
- Terminal failure codes: `provider_request_failed`=2
- Average cost per terminal run (USD): Guesser `0.0049` · Oracle `0.0657` · Verifier `0.0008` · Total `0.0714`
- Total benchmark cost (USD): `2.4989`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 13 | 16.82 | 3–50 |
| Questions (successful) | 12 | 12.24 | 3–30 |
| Guesser cost (USD) | 0.0010 | 0.0049 | 0.0002–0.0389 |
| Oracle cost (USD) | 0.0443 | 0.0657 | 0.0104–0.2615 |
| Verifier cost (USD) | 0.0003 | 0.0008 | 0.0000–0.0053 |
| Total cost (USD) | 0.0455 | 0.0714 | 0.0109–0.2828 |
| Tokens | 51126 | 111336.34 | 12480–524771 |
| LLM latency (ms) | 201248 | 933014.71 | 42831–5912526 |
| Trial duration (s) | 201.8 | 933.6 | 43.0–5914.2 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 80.0% | 100.0% (clean) | 0 | 8 | 0.0779 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 50.0% | 100.0% (clean) | 0 | 40 | 0.1630 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 17 | 0.0649 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 75.0% | 100.0% (clean) | 0 | 19 | 0.0960 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0327 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 98.6% (breached) | 1 | 14 | 0.0457 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 5 | 0.0196 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
