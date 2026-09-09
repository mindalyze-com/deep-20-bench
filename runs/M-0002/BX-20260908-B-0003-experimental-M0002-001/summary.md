# Deep20Bench Five Answer Experiment

- Execution: `BX-20260908-B-0003-experimental-M0002-001`
- Benchmark: `B-0003`
- Model: `M-0002` - gpt-oss-120B (high)
- Exact route: `openai/gpt-oss-120b`
- Execution commits: `eceee31eef2eee309df803adf99bb6fa5bac3c87`
- Status: completed
- Success rate: 66.7%
- Median counted questions: 18
- Subjects: 10
- Iterations per subject: 3
- Trials: 20 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 4 recovered calls / 7 retried calls / 75 exhausted
- Output-contract reliability: `breached` · compliance `89.3%` · 71 violation(s) across 13 trial(s) · 67 counted-turn penalties
- Oracle quality control: 512 reviewed · agreement `96.5%` · 18 disagreement(s) / 18 Judge call(s) · 8 Oracle answer(s) changed (`44.4%`) · QC cost `1.0376` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 18/508 (`3.5%`) · `temporal_comparison` 0/3 (`0.0%`)
- Terminal failure codes: `ask_after_question_limit`=2, `consecutive_contract_violations_exhausted`=4, `invalid_guesser_output`=4
- Average cost per terminal run (USD): Guesser `0.0682` · Oracle `0.0839` · Verifier `0.0003` · Total `0.1523`
- Superseded infrastructure attempts: 3 across 3 trial(s) · cost `0.4936` USD
- Total execution cost (USD): `5.0629`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 18 | 21.2 | 4–40 |
| Questions (successful) | 12.5 | 12.85 | 4–25 |
| Guesser cost (USD) | 0.0379 | 0.0682 | 0.0047–0.1694 |
| Oracle cost (USD) | 0.0829 | 0.0839 | 0.0089–0.1661 |
| Verifier cost (USD) | 0.0002 | 0.0003 | 0.0000–0.0012 |
| Terminal-attempt cost (USD) | 0.1083 | 0.1523 | 0.0138–0.3147 |
| Tokens | 223835.5 | 272117.7 | 28572–579275 |
| LLM latency (ms) | 251682 | 275656.9 | 29590–545728 |
| Trial duration (s) | 252.0 | 276.0 | 29.6–546.3 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 4 | 0.0213 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 94.4% (breached) | 4 | 25 | 0.1587 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 7 | 0.0563 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 7 | 0.0373 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 15 | 0.1189 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 0.0% | 81.3% (breached) | 23 | 40 | 0.3111 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 33.3% | 87.3% (breached) | 13 | 37 | 0.2643 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 0.0% | 83.3% (breached) | 19 | 40 | 0.2638 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 12 | 0.0682 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 33.3% | 86.7% (breached) | 12 | 30 | 0.2232 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
