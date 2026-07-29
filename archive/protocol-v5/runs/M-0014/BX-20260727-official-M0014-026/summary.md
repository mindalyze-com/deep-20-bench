# Deep20Bench Core Subjects

- Execution: `BX-20260727-official-M0014-026`
- Benchmark: `B-0001`
- Model: `M-0014` — Llama 4 Maverick (non-thinking)
- Exact route: `meta-llama/llama-4-maverick`
- Status: completed
- Success rate: 51.4%
- Median counted questions: 23
- Subjects: 7
- Iterations per subject: 5
- Trials: 18 successful / 35 scoring-eligible / 35 scheduled
- Infrastructure failures: 0
- Recovery: 18 recovered calls / 18 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.0077` · Oracle `0.0448` · Verifier `0.0064` · Total `0.0589`
- Total benchmark cost (USD): `2.0623`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 23 | 28.49 | 3–50 |
| Questions (successful) | 8.5 | 9.44 | 3–23 |
| Guesser cost (USD) | 0.0044 | 0.0077 | 0.0004–0.0161 |
| Oracle cost (USD) | 0.0437 | 0.0448 | 0.0100–0.0952 |
| Verifier cost (USD) | 0.0053 | 0.0064 | 0.0003–0.0142 |
| Total cost (USD) | 0.0549 | 0.0589 | 0.0108–0.1217 |
| Tokens | 70674 | 99825.26 | 11584–269625 |
| LLM latency (ms) | 118861 | 140201.83 | 21991–319077 |
| Trial duration (s) | 120.0 | 141.3 | 22.2–320.6 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 80.0% | 100.0% (clean) | 0 | 8 | 0.0326 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 0.0% | 100.0% (clean) | 0 | 50 | 0.0948 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 0.0% | 100.0% (clean) | 0 | 50 | 0.1024 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 40.0% | 100.0% (clean) | 0 | 50 | 0.0703 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 40.0% | 100.0% (clean) | 0 | 27 | 0.0556 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 12 | 0.0421 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 3 | 0.0146 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
