# Deep20Bench Five Answer Experiment

- Execution: `BX-20260907-B-0003-experimental-M0006-002`
- Benchmark: `B-0003`
- Model: `M-0006` - Claude Opus 5 (high)
- Exact route: `anthropic/claude-opus-5`
- Execution commits: `04dde57c39066c9345ab0d8be27e1a33c76da3e6`, `eceee31eef2eee309df803adf99bb6fa5bac3c87`
- Oracle contract revisions: 2; mixed-contract repair, not publication eligible
- Status: completed
- Success rate: 93.3%
- Median counted questions: 14.5
- Subjects: 10
- Iterations per subject: 3
- Trials: 28 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 1 recovered calls / 5 retried calls / 4 exhausted
- Output-contract reliability: `breached` · compliance `99.6%` · 2 violation(s) across 1 trial(s) · 2 counted-turn penalties
- Oracle quality control: 485 reviewed · agreement `92.6%` · 36 disagreement(s) / 36 Judge call(s) · 28 Oracle answer(s) changed (`77.8%`) · QC cost `1.3156` USD
- Oracle disagreement by question type: `negation` 0/2 (`0.0%`) · `other` 32/459 (`7.0%`) · `temporal_comparison` 4/24 (`16.7%`)
- Terminal failure codes: `ask_after_question_limit`=1
- Average cost per terminal run (USD): Guesser `0.0934` · Oracle `0.0915` · Verifier `0.0002` · Total `0.1852`
- Superseded infrastructure attempts: 7 across 7 trial(s) · cost `0.7565` USD
- Total execution cost (USD): `6.3114`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 14.5 | 18 | 8–40 |
| Questions (successful) | 13 | 16.43 | 8–39 |
| Guesser cost (USD) | 0.0722 | 0.0934 | 0.0394–0.3338 |
| Oracle cost (USD) | 0.0674 | 0.0915 | 0.0265–0.2960 |
| Verifier cost (USD) | 0.0002 | 0.0002 | 0.0000–0.0004 |
| Terminal-attempt cost (USD) | 0.1422 | 0.1852 | 0.0701–0.6069 |
| Tokens | 155739 | 194753.4 | 73422–520790 |
| LLM latency (ms) | 224378 | 271562.43 | 106730–769366 |
| Trial duration (s) | 224.7 | 271.9 | 106.9–770.3 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0920 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 100.0% (clean) | 0 | 26 | 0.2675 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 24 | 0.2577 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0890 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 11 | 0.0983 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 33.3% | 100.0% (clean) | 0 | 40 | 0.4758 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 16 | 0.1601 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 96.1% (breached) | 2 | 18 | 0.1292 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0708 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 100.0% | 100.0% (clean) | 0 | 19 | 0.2111 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
