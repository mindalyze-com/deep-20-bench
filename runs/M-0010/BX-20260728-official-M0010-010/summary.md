# Deep20Bench Core Subjects

- Execution: `BX-20260728-official-M0010-010`
- Benchmark: `B-0001`
- Model: `M-0010` — GPT-5.6 Sol (high)
- Exact route: `openai/gpt-5.6-sol`
- Execution commits: `c5358232b0d99ceeea6b596daaf830230dd9a980`
- Status: completed
- Success rate: 100.0%
- Median counted questions: 12
- Subjects: 7
- Iterations per subject: 5
- Trials: 35 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 0 recovered calls / 0 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 459 reviewed · agreement `94.3%` · 26 disagreement(s) / 26 Judge call(s) · 7 Oracle answer(s) changed (`26.9%`) · QC cost `0.7614` USD
- Oracle disagreement by question type: `other` 24/376 (`6.4%`) · `temporal_comparison` 2/83 (`2.4%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.1711` · Oracle `0.1135` · Verifier `0.0004` · Total `0.2849`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Total execution cost (USD): `9.9727`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 12 | 14.4 | 6–33 |
| Questions (successful) | 12 | 14.4 | 6–33 |
| Guesser cost (USD) | 0.0928 | 0.1711 | 0.0537–1.0405 |
| Oracle cost (USD) | 0.0678 | 0.1135 | 0.0289–0.3453 |
| Verifier cost (USD) | 0.0003 | 0.0004 | 0.0003–0.0009 |
| Terminal-attempt cost (USD) | 0.1661 | 0.2849 | 0.0845–1.3865 |
| Tokens | 91418 | 172395.54 | 40039–641540 |
| LLM latency (ms) | 184770 | 302293.14 | 89232–1403655 |
| Trial duration (s) | 185.4 | 303.0 | 89.6–1405.3 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 11 | 0.1541 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 100.0% | 100.0% (clean) | 0 | 22 | 0.4135 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 22 | 0.7577 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 100.0% | 100.0% (clean) | 0 | 12 | 0.2240 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 8 | 0.1008 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 13 | 0.1857 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 7 | 0.1588 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
