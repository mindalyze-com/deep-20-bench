# Deep20Bench Five Answer Experiment

- Execution: `BX-20260908-B-0003-experimental-M0023-001`
- Benchmark: `B-0003`
- Model: `M-0023` - GLM-5.3-Flash (high)
- Exact route: `z-ai/glm-5.3-flash`
- Execution commits: `eceee31eef2eee309df803adf99bb6fa5bac3c87`
- Status: completed
- Success rate: 73.3%
- Median counted questions: 18
- Subjects: 10
- Iterations per subject: 3
- Trials: 22 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 34 recovered calls / 36 retried calls / 3 exhausted
- Output-contract reliability: `breached` · compliance `93.2%` · 49 violation(s) across 30 trial(s) · 49 counted-turn penalties
- Oracle quality control: 501 reviewed · agreement `94.0%` · 30 disagreement(s) / 30 Judge call(s) · 17 Oracle answer(s) changed (`56.7%`) · QC cost `1.2737` USD
- Oracle disagreement by question type: `negation` 0/3 (`0.0%`) · `other` 28/473 (`5.9%`) · `quantitative_comparison` 0/1 (`0.0%`) · `temporal_comparison` 2/24 (`8.3%`)
- Terminal failure codes: `ask_after_question_limit`=8
- Average cost per terminal run (USD): Guesser `0.0016` · Oracle `0.0941` · Verifier `0.0003` · Total `0.0959`
- Superseded infrastructure attempts: 2 across 2 trial(s) · cost `0.0174` USD
- Total execution cost (USD): `2.8955`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 18 | 23 | 8–40 |
| Questions (successful) | 13 | 16.82 | 8–40 |
| Guesser cost (USD) | 0.0007 | 0.0016 | 0.0003–0.0104 |
| Oracle cost (USD) | 0.0539 | 0.0941 | 0.0134–0.2729 |
| Verifier cost (USD) | 0.0002 | 0.0003 | 0.0000–0.0014 |
| Terminal-attempt cost (USD) | 0.0548 | 0.0959 | 0.0139–0.2751 |
| Tokens | 126520.5 | 205666.7 | 38070–486337 |
| LLM latency (ms) | 190568.5 | 319963.57 | 55641–1107045 |
| Trial duration (s) | 190.7 | 320.2 | 55.7–1107.5 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 90.9% (breached) | 3 | 9 | 0.0195 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 66.7% | 97.0% (breached) | 3 | 40 | 0.1562 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 89.2% (breached) | 4 | 12 | 0.0273 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 93.5% (breached) | 3 | 12 | 0.0650 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 66.7% | 93.3% (breached) | 6 | 36 | 0.1155 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 0.0% | 95.1% (breached) | 6 | 40 | 0.1807 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 33.3% | 92.5% (breached) | 8 | 40 | 0.1651 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 90.9% (breached) | 6 | 16 | 0.0810 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 91.2% (breached) | 3 | 10 | 0.0206 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 66.7% | 91.8% (breached) | 7 | 23 | 0.1287 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
