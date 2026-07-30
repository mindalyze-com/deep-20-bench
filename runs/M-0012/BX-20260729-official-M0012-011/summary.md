# Deep20Bench Core Subjects

- Execution: `BX-20260729-official-M0012-011`
- Benchmark: `B-0001`
- Model: `M-0012` — Mistral Medium 3.5 (high)
- Exact route: `mistralai/mistral-medium-3-5`
- Execution commits: `e90f98eeaed0a3527664e24b0aa4e03a85977fc0`, `8eb67e8010f16af769f46ee997a618fcee5aec0f`
- Status: completed
- Success rate: 88.6%
- Median counted questions: 14
- Subjects: 7
- Iterations per subject: 5
- Trials: 31 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 6 recovered calls / 13 retried calls / 9 exhausted
- Output-contract reliability: `breached` · compliance `99.7%` · 2 violation(s) across 1 trial(s) · 2 counted-turn penalties
- Oracle quality control: 508 reviewed · agreement `93.1%` · 35 disagreement(s) / 35 Judge call(s) · 8 Oracle answer(s) changed (`22.9%`) · QC cost `0.9686` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 34/475 (`7.2%`) · `temporal_comparison` 1/32 (`3.1%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.4113` · Oracle `0.1170` · Verifier `0.0017` · Total `0.5300`
- Superseded infrastructure attempts: 7 across 7 trial(s) · cost `1.7222` USD
- Total execution cost (USD): `20.2708`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 14 | 19.94 | 6–50 |
| Questions (successful) | 12 | 16.06 | 6–47 |
| Guesser cost (USD) | 0.0853 | 0.4113 | 0.0224–3.3640 |
| Oracle cost (USD) | 0.0882 | 0.1170 | 0.0314–0.3570 |
| Verifier cost (USD) | 0.0003 | 0.0017 | 0.0003–0.0094 |
| Terminal-attempt cost (USD) | 0.1821 | 0.5300 | 0.0644–3.6286 |
| Tokens | 103416 | 206537.31 | 42045–872929 |
| LLM latency (ms) | 263694 | 1077441.51 | 79765–6533171 |
| Trial duration (s) | 264.0 | 1078.0 | 80.0–6534.1 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 12 | 0.1835 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 60.0% | 100.0% (clean) | 0 | 47 | 1.3143 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 13 | 0.3096 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 100.0% | 100.0% (clean) | 0 | 8 | 0.1255 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0947 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 80.0% | 100.0% (clean) | 0 | 37 | 0.8277 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 80.0% | 97.8% (breached) | 2 | 7 | 0.8544 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
