# Deep20Bench Core Subjects

- Execution: `BX-20260728-official-M0005-012`
- Benchmark: `B-0001`
- Model: `M-0005` — Claude Sonnet 5 (high)
- Exact route: `anthropic/claude-sonnet-5`
- Execution commits: `79fde3a043c379044b142784b15588964100df54`
- Status: completed
- Success rate: 100.0%
- Median counted questions: 11
- Subjects: 7
- Iterations per subject: 5
- Trials: 35 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 1 recovered calls / 1 retried calls / 0 exhausted
- Output-contract reliability: `breached` · compliance `97.1%` · 16 violation(s) across 12 trial(s) · 16 counted-turn penalties
- Oracle quality control: 431 reviewed · agreement `90.3%` · 42 disagreement(s) / 42 Judge call(s) · 3 Oracle answer(s) changed (`7.1%`) · QC cost `0.9601` USD
- Oracle disagreement by question type: `negation` 0/10 (`0.0%`) · `other` 42/399 (`10.5%`) · `temporal_comparison` 0/22 (`0.0%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.0493` · Oracle `0.0935` · Verifier `0.0004` · Total `0.1431`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Total execution cost (USD): `5.0082`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 11 | 14.74 | 6–33 |
| Questions (successful) | 11 | 14.74 | 6–33 |
| Guesser cost (USD) | 0.0228 | 0.0493 | 0.0125–0.3666 |
| Oracle cost (USD) | 0.0738 | 0.0935 | 0.0247–0.2518 |
| Verifier cost (USD) | 0.0003 | 0.0004 | 0.0003–0.0014 |
| Terminal-attempt cost (USD) | 0.0949 | 0.1431 | 0.0375–0.5871 |
| Tokens | 91577 | 126283.4 | 38453–417932 |
| LLM latency (ms) | 155063 | 231941.49 | 64539–828682 |
| Trial duration (s) | 155.2 | 232.2 | 64.7–829.2 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 96.5% (breached) | 2 | 10 | 0.0604 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 100.0% | 97.9% (breached) | 3 | 28 | 0.2785 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 97.6% (breached) | 2 | 16 | 0.1274 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 100.0% | 94.6% (breached) | 6 | 22 | 0.3007 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0525 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 97.0% (breached) | 2 | 12 | 0.1056 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 97.8% (breached) | 1 | 8 | 0.0765 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
