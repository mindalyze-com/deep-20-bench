# Deep20Bench Five Answer Experiment

- Execution: `BX-20260909-B-0003-experimental-M0026-003`
- Benchmark: `B-0003`
- Model: `M-0026` - Muse Spark 1.3 Contributor (high)
- Exact route: `meta/muse-spark-1.3-contributor`
- Execution commits: `2d5409df2ba6f3060bfb5d4736a40cc987d0800f`, `8281730d927af6a1138cf452948bb26ccee3144f`
- Status: completed
- Success rate: 96.6%
- Median counted questions: 15
- Subjects: 10
- Iterations per subject: 3
- Trials: 28 successful / 29 scoring-eligible / 30 scheduled
- Completeness: 29/30 scheduled trials scoring-eligible
- Infrastructure failures: 1
- Recovery: 8 recovered calls / 10 retried calls / 2 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 467 reviewed · agreement `95.3%` · 22 disagreement(s) / 22 Judge call(s) · 16 Oracle answer(s) changed (`72.7%`) · QC cost `1.1094` USD
- Oracle disagreement by question type: `negation` 0/3 (`0.0%`) · `other` 22/431 (`5.1%`) · `temporal_comparison` 0/33 (`0.0%`)
- Terminal failure codes: `provider_content_filtered`=1
- Average cost per terminal run (USD): Guesser `0.0048` · Oracle `0.0805` · Verifier `0.0002` · Total `0.0854`
- Superseded infrastructure attempts: 1 across 1 trial(s) · cost `0.0091` USD
- Total execution cost (USD): `2.5726`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 15 | 18.48 | 9–40 |
| Questions (successful) | 15 | 17.71 | 9–33 |
| Guesser cost (USD) | 0.0020 | 0.0048 | 0.0003–0.0193 |
| Oracle cost (USD) | 0.0668 | 0.0805 | 0.0119–0.3029 |
| Verifier cost (USD) | 0.0002 | 0.0002 | 0.0000–0.0003 |
| Terminal-attempt cost (USD) | 0.0685 | 0.0854 | 0.0121–0.3222 |
| Tokens | 141777.5 | 191628.63 | 28877–601197 |
| LLM latency (ms) | 291991.5 | 483258.63 | 47039–1718442 |
| Trial duration (s) | 292.4 | 483.7 | 47.1–1719.6 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 13 | 0.0335 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 100.0% (clean) | 0 | 19 | 0.0989 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 14 | 0.0586 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0474 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 15 | 0.0507 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 66.7% | 100.0% (clean) | 0 | 31 | 0.2071 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 15 | 0.1078 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 100.0% (clean) | 0 | 17 | 0.0688 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0238 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 100.0% | 100.0% (clean) | 0 | 27 | 0.1579 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
