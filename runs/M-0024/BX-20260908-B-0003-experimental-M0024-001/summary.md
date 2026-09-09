# Deep20Bench Five Answer Experiment

- Execution: `BX-20260908-B-0003-experimental-M0024-001`
- Benchmark: `B-0003`
- Model: `M-0024` - MiniMax M3 (high)
- Exact route: `minimax/minimax-m3`
- Execution commits: `eceee31eef2eee309df803adf99bb6fa5bac3c87`
- Status: completed
- Success rate: 50.0%
- Median counted questions: 37
- Subjects: 10
- Iterations per subject: 3
- Trials: 15 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 23 recovered calls / 25 retried calls / 7 exhausted
- Output-contract reliability: `breached` · compliance `99.1%` · 8 violation(s) across 8 trial(s) · 7 counted-turn penalties
- Oracle quality control: 602 reviewed · agreement `91.2%` · 53 disagreement(s) / 53 Judge call(s) · 34 Oracle answer(s) changed (`64.2%`) · QC cost `1.9951` USD
- Oracle disagreement by question type: `negation` 3/24 (`12.5%`) · `other` 50/559 (`8.9%`) · `quantitative_comparison` 0/9 (`0.0%`) · `temporal_comparison` 0/10 (`0.0%`)
- Terminal failure codes: `ask_after_question_limit`=9, `invalid_guesser_output`=1
- Average cost per terminal run (USD): Guesser `0.0100` · Oracle `0.1344` · Verifier `0.0006` · Total `0.1450`
- Superseded infrastructure attempts: 2 across 2 trial(s) · cost `0.1812` USD
- Total execution cost (USD): `4.5304`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 37 | 28.67 | 6–40 |
| Questions (successful) | 17 | 17.33 | 6–34 |
| Guesser cost (USD) | 0.0064 | 0.0100 | 0.0009–0.0384 |
| Oracle cost (USD) | 0.1011 | 0.1344 | 0.0131–0.3549 |
| Verifier cost (USD) | 0.0004 | 0.0006 | 0.0000–0.0026 |
| Terminal-attempt cost (USD) | 0.1120 | 0.1450 | 0.0146–0.3630 |
| Tokens | 282201.5 | 276193.17 | 36157–689612 |
| LLM latency (ms) | 342272 | 359401.77 | 44036–761603 |
| Trial duration (s) | 342.5 | 359.8 | 44.1–762.3 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 96.2% (breached) | 1 | 8 | 0.0278 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 33.3% | 99.0% (breached) | 1 | 40 | 0.1387 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 66.7% | 98.6% (breached) | 1 | 17 | 0.0755 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 66.7% | 100.0% (clean) | 0 | 8 | 0.1094 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 66.7% | 100.0% (clean) | 0 | 19 | 0.1225 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 33.3% | 99.1% (breached) | 1 | 40 | 0.2343 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 0.0% | 100.0% (clean) | 0 | 40 | 0.3030 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 66.7% | 100.0% (clean) | 0 | 27 | 0.1376 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 66.7% | 98.0% (breached) | 2 | 34 | 0.0723 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 0.0% | 98.4% (breached) | 2 | 40 | 0.2284 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
