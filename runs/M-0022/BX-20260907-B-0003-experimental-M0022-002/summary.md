# Deep20Bench Five Answer Experiment

- Execution: `BX-20260907-B-0003-experimental-M0022-002`
- Benchmark: `B-0003`
- Model: `M-0022` - GPT-6 Astra (high)
- Exact route: `openai/gpt-6-astra`
- Execution commits: `8b1a8f9b017e2ca74880535ee0b3adeef745b34f`
- Status: completed
- Success rate: 100.0%
- Median counted questions: 11.5
- Subjects: 10
- Iterations per subject: 3
- Trials: 30 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 1 recovered calls / 2 retried calls / 1 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 372 reviewed · agreement `89.0%` · 41 disagreement(s) / 41 Judge call(s) · 28 Oracle answer(s) changed (`68.3%`) · QC cost `1.0770` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 40/353 (`11.3%`) · `temporal_comparison` 1/18 (`5.6%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.1648` · Oracle `0.0692` · Verifier `0.0002` · Total `0.2342`
- Superseded infrastructure attempts: 1 across 1 trial(s) · cost `0.0273` USD
- Total execution cost (USD): `7.0540`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 11.5 | 12.73 | 7–25 |
| Questions (successful) | 11.5 | 12.73 | 7–25 |
| Guesser cost (USD) | 0.1351 | 0.1648 | 0.1042–0.3948 |
| Oracle cost (USD) | 0.0479 | 0.0692 | 0.0240–0.1647 |
| Verifier cost (USD) | 0.0002 | 0.0002 | 0.0002–0.0009 |
| Terminal-attempt cost (USD) | 0.1756 | 0.2342 | 0.1286–0.5596 |
| Tokens | 87868.5 | 126091.87 | 64611–255947 |
| LLM latency (ms) | 144804.5 | 212388.87 | 100162–540970 |
| Trial duration (s) | 145.0 | 212.6 | 100.3–541.5 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.1616 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 100.0% (clean) | 0 | 15 | 0.3660 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.1585 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 8 | 0.1437 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.1584 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 100.0% | 100.0% (clean) | 0 | 20 | 0.3520 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 14 | 0.2713 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 100.0% (clean) | 0 | 12 | 0.1850 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 11 | 0.1472 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 100.0% | 100.0% (clean) | 0 | 19 | 0.3984 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
