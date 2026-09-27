# Deep20Bench Edition 1.1

- Edition: `1.1` / `qualified-core-v1`
- Comparison classification: `standard`
- Explicit overrides: none
- Comparison contract: `2fa8c6bfffe0cf577cb6e97e8842a6c225d9b35b9ee22fa5a12461b2bc26fd5a`
- Execution: `BX-20260926-B-0003-official-M0030-001`
- Benchmark: `B-0003`
- Model: `M-0030` - Claude Opus 5.5 (high)
- Exact route: `anthropic/claude-opus-5.5`
- Execution commits: `6e46fb003ebf43423c802cbb37f69bdc8b321ddf`
- Status: completed
- Success rate: 96.7%
- Median counted questions: 10
- Subjects: 10
- Iterations per subject: 3
- Trials: 29 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 1 recovered calls / 2 retried calls / 1 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 307 reviewed · agreement `94.1%` · 18 disagreement(s) / 18 Judge call(s) · 13 Oracle answer(s) changed (`72.2%`) · QC cost `0.7851` USD
- Oracle disagreement by question type: `negation` 0/4 (`0.0%`) · `other` 18/286 (`6.3%`) · `temporal_comparison` 0/17 (`0.0%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.0751` · Oracle `0.0528` · Verifier `0.0003` · Total `0.1281`
- Superseded infrastructure attempts: 1 across 1 trial(s) · cost `0.1110` USD
- Total execution cost (USD): `3.9543`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 10 | 14.97 | 7–40 |
| Questions (successful) | 10 | 14.1 | 7–30 |
| Guesser cost (USD) | 0.0372 | 0.0751 | 0.0162–0.3257 |
| Oracle cost (USD) | 0.0360 | 0.0528 | 0.0038–0.1319 |
| Verifier cost (USD) | 0.0002 | 0.0003 | 0.0002–0.0017 |
| Terminal-attempt cost (USD) | 0.0717 | 0.1281 | 0.0201–0.4210 |
| Tokens | 80263.5 | 122130.5 | 21550–327026 |
| LLM latency (ms) | 103656 | 178362.4 | 38915–513205 |
| Trial duration (s) | 103.8 | 178.6 | 39.0–513.8 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0498 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 100.0% (clean) | 0 | 20 | 0.1810 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.1303 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 7 | 0.0427 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0648 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 66.7% | 100.0% (clean) | 0 | 30 | 0.3299 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 19 | 0.1841 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0598 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 7 | 0.0284 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 100.0% | 100.0% (clean) | 0 | 24 | 0.2103 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
