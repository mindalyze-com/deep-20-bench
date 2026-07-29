# Deep20Bench Core Subjects

- Execution: `BX-20260727-official-M0013-025`
- Benchmark: `B-0001`
- Model: `M-0013` — GLM 5.2 (high)
- Exact route: `z-ai/glm-5.2`
- Status: completed
- Success rate: 93.6%
- Median counted questions: 13
- Subjects: 7
- Iterations per subject: 5
- Trials: 29 successful / 31 scoring-eligible / 35 scheduled
- Infrastructure failures: 4
- Recovery: 123 recovered calls / 127 retried calls / 4 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Terminal failure codes: `ask_after_question_limit`=2, `provider_output_limit_exceeded`=1, `provider_rate_limited`=3
- Average cost per terminal run (USD): Guesser `0.0490` · Oracle `0.0721` · Verifier `0.0004` · Total `0.1215`
- Total benchmark cost (USD): `4.2526`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 13 | 16.77 | 7–50 |
| Questions (successful) | 11 | 14.48 | 7–41 |
| Guesser cost (USD) | 0.0076 | 0.0490 | 0.0011–0.3241 |
| Oracle cost (USD) | 0.0448 | 0.0721 | 0.0106–0.3467 |
| Verifier cost (USD) | 0.0003 | 0.0004 | 0.0000–0.0019 |
| Total cost (USD) | 0.0510 | 0.1215 | 0.0118–0.6707 |
| Tokens | 54376 | 106962.34 | 11115–657152 |
| LLM latency (ms) | 149708 | 305456.94 | 71045–1479840 |
| Trial duration (s) | 150.0 | 305.9 | 71.3–1481.4 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0367 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 75.0% | 100.0% (clean) | 0 | 40.5 | 0.3856 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 14 | 0.0521 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 50.0% | 100.0% (clean) | 0 | 33 | 0.1862 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0422 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 18 | 0.0870 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0607 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
