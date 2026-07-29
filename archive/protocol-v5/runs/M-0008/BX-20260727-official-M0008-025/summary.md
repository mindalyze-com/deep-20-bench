# Deep20Bench Core Subjects

- Execution: `BX-20260727-official-M0008-025`
- Benchmark: `B-0001`
- Model: `M-0008` — Qwen3.6 35B-A3B (thinking)
- Exact route: `qwen/qwen3.6-35b-a3b`
- Status: completed
- Success rate: 100.0%
- Median counted questions: 10
- Subjects: 7
- Iterations per subject: 5
- Trials: 25 successful / 25 scoring-eligible / 35 scheduled
- Infrastructure failures: 10
- Recovery: 32 recovered calls / 41 retried calls / 9 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Terminal failure codes: `provider_output_limit_exceeded`=9, `provider_request_failed`=1
- Average cost per terminal run (USD): Guesser `0.0464` · Oracle `0.0536` · Verifier `0.0003` · Total `0.1003`
- Total benchmark cost (USD): `3.5117`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 10 | 11.96 | 3–27 |
| Questions (successful) | 10 | 11.96 | 3–27 |
| Guesser cost (USD) | 0.0335 | 0.0464 | 0.0014–0.2166 |
| Oracle cost (USD) | 0.0514 | 0.0536 | 0.0048–0.1408 |
| Verifier cost (USD) | 0.0003 | 0.0003 | 0.0000–0.0009 |
| Total cost (USD) | 0.0770 | 0.1003 | 0.0140–0.3531 |
| Tokens | 86153 | 114145.86 | 14999–398785 |
| LLM latency (ms) | 219926 | 382828.91 | 26502–1766988 |
| Trial duration (s) | 220.3 | 383.2 | 26.7–1767.6 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 7.5 | 0.0591 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 100.0% | 100.0% (clean) | 0 | 25.5 | 0.1930 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 15.5 | 0.1320 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 100.0% | 100.0% (clean) | 0 | 13.5 | 0.0867 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0458 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 18 | 0.1437 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 4 | 0.0422 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
