# Deep20Bench Core Subjects

- Execution: `BX-20260814-official-M0015-013`
- Benchmark: `B-0001`
- Model: `M-0015` - Grok 4.6 (high)
- Exact route: `x-ai/grok-4.6`
- Execution commits: `4e197a516062010a95d9a2120177485ebb31286d`, `6ad3614bb535217c0e56a989b25da4187416a475`
- Status: completed
- Success rate: 100.0%
- Median counted questions: 13
- Subjects: 7
- Iterations per subject: 5
- Trials: 35 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 1 recovered calls / 7 retried calls / 6 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 483 reviewed · agreement `83.2%` · 81 disagreement(s) / 81 Judge call(s) · 4 Oracle answer(s) changed (`4.9%`) · QC cost `1.5531` USD
- Oracle disagreement by question type: `other` 81/460 (`17.6%`) · `quantitative_comparison` 0/1 (`0.0%`) · `temporal_comparison` 0/22 (`0.0%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.0653` · Oracle `0.1703` · Verifier `0.0001` · Total `0.2357`
- Superseded infrastructure attempts: 6 across 6 trial(s) · cost `1.2481` USD
- Total execution cost (USD): `9.4967`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 13 | 14.29 | 5–48 |
| Questions (successful) | 13 | 14.29 | 5–48 |
| Guesser cost (USD) | 0.0369 | 0.0653 | 0.0153–0.4962 |
| Oracle cost (USD) | 0.1221 | 0.1703 | 0.0462–0.7948 |
| Verifier cost (USD) | 0.0001 | 0.0001 | 0.0001–0.0001 |
| Terminal-attempt cost (USD) | 0.1589 | 0.2357 | 0.0630–1.2911 |
| Tokens | 112949 | 141032.06 | 41878–592831 |
| LLM latency (ms) | 213800 | 338472.4 | 89097–2186452 |
| Trial duration (s) | 214.1 | 338.8 | 89.2–2187.5 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 9 | 0.1078 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 100.0% | 100.0% (clean) | 0 | 27 | 0.7034 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 15 | 0.1944 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 100.0% | 100.0% (clean) | 0 | 15 | 0.2464 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 8 | 0.1071 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 15 | 0.1971 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 6 | 0.0936 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
