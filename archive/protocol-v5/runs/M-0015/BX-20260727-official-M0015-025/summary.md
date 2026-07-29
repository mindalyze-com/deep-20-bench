# Deep20Bench Core Subjects

- Execution: `BX-20260727-official-M0015-025`
- Benchmark: `B-0001`
- Model: `M-0015` — Gemma 4 26B-A4B (thinking)
- Exact route: `google/gemma-4-26b-a4b-it`
- Status: completed
- Success rate: 100.0%
- Median counted questions: 10
- Subjects: 7
- Iterations per subject: 5
- Trials: 5 successful / 5 scoring-eligible / 35 scheduled
- Infrastructure failures: 30
- Recovery: 11 recovered calls / 40 retried calls / 29 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Terminal failure codes: `provider_empty_response`=1, `provider_incomplete_response`=1, `provider_output_limit_exceeded`=27, `provider_request_failed`=1
- Average cost per terminal run (USD): Guesser `0.0139` · Oracle `0.0144` · Verifier `0.0001` · Total `0.0283`
- Total benchmark cost (USD): `0.9915`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 10 | 9.4 | 5–12 |
| Questions (successful) | 10 | 9.4 | 5–12 |
| Guesser cost (USD) | 0.0132 | 0.0139 | 0.0000–0.0658 |
| Oracle cost (USD) | 0.0000 | 0.0144 | 0.0000–0.1956 |
| Verifier cost (USD) | 0.0000 | 0.0001 | 0.0000–0.0006 |
| Total cost (USD) | 0.0132 | 0.0283 | 0.0000–0.2620 |
| Tokens | 33558 | 52886.17 | 0–430552 |
| LLM latency (ms) | 273803 | 351069.4 | 76163–1758644 |
| Trial duration (s) | 273.8 | 351.1 | 76.2–1759.3 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 10.5 | 0.0230 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | n/a | n/a (not_evaluable) | 0 | n/a | 0.0200 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | n/a | n/a (not_evaluable) | 0 | n/a | 0.0227 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | n/a | n/a (not_evaluable) | 0 | n/a | 0.0748 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0162 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | n/a | n/a (not_evaluable) | 0 | n/a | 0.0132 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 8.5 | 0.0284 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
