# Deep20Bench Five Answer Experiment

- Execution: `BX-20260908-B-0003-experimental-M0020-001`
- Benchmark: `B-0003`
- Model: `M-0020` - Claude Fable 5.1 (high)
- Exact route: `anthropic/claude-fable-5.1`
- Execution commits: `eceee31eef2eee309df803adf99bb6fa5bac3c87`
- Status: completed
- Success rate: 93.3%
- Median counted questions: 12
- Subjects: 10
- Iterations per subject: 3
- Trials: 28 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 5 recovered calls / 7 retried calls / 2 exhausted
- Output-contract reliability: `breached` · compliance `99.4%` · 3 violation(s) across 3 trial(s) · 3 counted-turn penalties
- Oracle quality control: 388 reviewed · agreement `95.4%` · 18 disagreement(s) / 18 Judge call(s) · 12 Oracle answer(s) changed (`66.7%`) · QC cost `0.8724` USD
- Oracle disagreement by question type: `negation` 0/5 (`0.0%`) · `other` 18/368 (`4.9%`) · `temporal_comparison` 0/15 (`0.0%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.2772` · Oracle `0.0634` · Verifier `0.0003` · Total `0.3408`
- Superseded infrastructure attempts: 2 across 2 trial(s) · cost `1.5437` USD
- Total execution cost (USD): `11.7685`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 12 | 15.03 | 6–40 |
| Questions (successful) | 11.5 | 13.25 | 6–33 |
| Guesser cost (USD) | 0.0964 | 0.2772 | 0.0405–1.7865 |
| Oracle cost (USD) | 0.0418 | 0.0634 | 0.0152–0.2164 |
| Verifier cost (USD) | 0.0002 | 0.0003 | 0.0002–0.0018 |
| Terminal-attempt cost (USD) | 0.1493 | 0.3408 | 0.0615–2.0006 |
| Tokens | 108102.5 | 153415.57 | 50047–530585 |
| LLM latency (ms) | 193209 | 313354.37 | 98198–1274844 |
| Trial duration (s) | 193.4 | 313.6 | 98.3–1275.5 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.1392 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 96.5% (breached) | 2 | 18 | 0.3210 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 8 | 0.1476 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 8 | 0.1079 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.1041 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 33.3% | 99.1% (breached) | 1 | 40 | 1.6703 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 19 | 0.2991 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 100.0% (clean) | 0 | 12 | 0.1368 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0753 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 100.0% | 100.0% (clean) | 0 | 21 | 0.4069 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
