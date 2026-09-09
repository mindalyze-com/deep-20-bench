# Deep20Bench Five Answer Experiment

- Execution: `BX-20260909-B-0003-experimental-M0022-002`
- Benchmark: `B-0003`
- Model: `M-0022` - GPT-6 Astra (high)
- Exact route: `openai/gpt-6-astra`
- Execution commits: `2d5409df2ba6f3060bfb5d4736a40cc987d0800f`
- Status: completed
- Success rate: 100.0%
- Median counted questions: 11.5
- Subjects: 10
- Iterations per subject: 3
- Trials: 30 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 2 recovered calls / 3 retried calls / 1 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 258 reviewed · agreement `95.4%` · 12 disagreement(s) / 12 Judge call(s) · 11 Oracle answer(s) changed (`91.7%`) · QC cost `0.6614` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 11/248 (`4.4%`) · `quantitative_comparison` 0/1 (`0.0%`) · `temporal_comparison` 1/8 (`12.5%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.1756` · Oracle `0.0470` · Verifier `0.0002` · Total `0.2228`
- Superseded infrastructure attempts: 1 across 1 trial(s) · cost `0.1744` USD
- Total execution cost (USD): `6.8583`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 11.5 | 13.67 | 7–27 |
| Questions (successful) | 11.5 | 13.67 | 7–27 |
| Guesser cost (USD) | 0.1361 | 0.1756 | 0.1097–0.3489 |
| Oracle cost (USD) | 0.0356 | 0.0470 | 0.0000–0.1330 |
| Verifier cost (USD) | 0.0002 | 0.0002 | 0.0002–0.0004 |
| Terminal-attempt cost (USD) | 0.1711 | 0.2228 | 0.1186–0.4692 |
| Tokens | 79823 | 101444.53 | 9765–265736 |
| LLM latency (ms) | 125839.5 | 185396.3 | 39942–485355 |
| Trial duration (s) | 126.0 | 185.6 | 40.0–485.7 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.1576 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 100.0% (clean) | 0 | 16 | 0.3253 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 8 | 0.1318 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 8 | 0.1292 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 11 | 0.1763 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 100.0% | 100.0% (clean) | 0 | 26 | 0.4279 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 17 | 0.2986 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 100.0% (clean) | 0 | 13 | 0.1653 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.1320 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 100.0% | 100.0% (clean) | 0 | 18 | 0.2840 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
