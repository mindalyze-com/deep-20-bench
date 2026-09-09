# Deep20Bench Five Answer Experiment

- Execution: `BX-20260908-B-0003-experimental-M0015-001`
- Benchmark: `B-0003`
- Model: `M-0015` - Grok 4.6 (high)
- Exact route: `x-ai/grok-4.6`
- Execution commits: `eceee31eef2eee309df803adf99bb6fa5bac3c87`
- Status: completed
- Success rate: 100.0%
- Median counted questions: 15.5
- Subjects: 10
- Iterations per subject: 3
- Trials: 30 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 9 recovered calls / 12 retried calls / 3 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 494 reviewed · agreement `95.8%` · 21 disagreement(s) / 21 Judge call(s) · 10 Oracle answer(s) changed (`47.6%`) · QC cost `1.1158` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 20/476 (`4.2%`) · `temporal_comparison` 1/17 (`5.9%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.1367` · Oracle `0.0818` · Verifier `0.0002` · Total `0.2187`
- Superseded infrastructure attempts: 4 across 3 trial(s) · cost `0.5298` USD
- Total execution cost (USD): `7.0921`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 15.5 | 17.13 | 8–39 |
| Questions (successful) | 15.5 | 17.13 | 8–39 |
| Guesser cost (USD) | 0.0837 | 0.1367 | 0.0254–0.4698 |
| Oracle cost (USD) | 0.0643 | 0.0818 | 0.0248–0.1858 |
| Verifier cost (USD) | 0.0002 | 0.0002 | 0.0002–0.0004 |
| Terminal-attempt cost (USD) | 0.1424 | 0.2187 | 0.0504–0.6352 |
| Tokens | 152786.5 | 191964.63 | 67529–429526 |
| LLM latency (ms) | 384062 | 613405.9 | 135889–1814996 |
| Trial duration (s) | 384.5 | 613.8 | 136.1–1815.5 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0701 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 100.0% (clean) | 0 | 27 | 0.3933 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 14 | 0.1561 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0623 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 14 | 0.1060 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 100.0% | 100.0% (clean) | 0 | 26 | 0.4842 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 21 | 0.3500 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 100.0% (clean) | 0 | 16 | 0.1428 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0657 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 100.0% | 100.0% (clean) | 0 | 21 | 0.3569 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
