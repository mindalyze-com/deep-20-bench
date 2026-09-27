# Deep20Bench Edition 1.1

- Edition: `1.1` / `qualified-core-v1`
- Comparison classification: `standard`
- Explicit overrides: none
- Comparison contract: `2fa8c6bfffe0cf577cb6e97e8842a6c225d9b35b9ee22fa5a12461b2bc26fd5a`
- Execution: `BX-20260926-B-0003-official-M0027-001`
- Benchmark: `B-0003`
- Model: `M-0027` - Grok 4.7 (high)
- Exact route: `x-ai/grok-4.7`
- Execution commits: `6e46fb003ebf43423c802cbb37f69bdc8b321ddf`
- Status: completed
- Success rate: 73.3%
- Median counted questions: 16.5
- Subjects: 10
- Iterations per subject: 3
- Trials: 22 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 2 recovered calls / 2 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 458 reviewed · agreement `91.7%` · 38 disagreement(s) / 38 Judge call(s) · 24 Oracle answer(s) changed (`63.2%`) · QC cost `1.4875` USD
- Oracle disagreement by question type: `negation` 1/3 (`33.3%`) · `other` 37/444 (`8.3%`) · `temporal_comparison` 0/11 (`0.0%`)
- Terminal failure codes: `ask_after_question_limit`=8
- Average cost per terminal run (USD): Guesser `0.0432` · Oracle `0.0930` · Verifier `0.0001` · Total `0.1364`
- Superseded infrastructure attempts: 1 across 1 trial(s) · cost `0.1124` USD
- Total execution cost (USD): `4.2032`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 16.5 | 21.97 | 7–40 |
| Questions (successful) | 12.5 | 15.41 | 7–33 |
| Guesser cost (USD) | 0.0323 | 0.0432 | 0.0116–0.0977 |
| Oracle cost (USD) | 0.0482 | 0.0930 | 0.0033–0.4135 |
| Verifier cost (USD) | 0.0002 | 0.0001 | 0.0000–0.0003 |
| Terminal-attempt cost (USD) | 0.0801 | 0.1364 | 0.0158–0.5002 |
| Tokens | 129771 | 203728.2 | 25434–671118 |
| LLM latency (ms) | 127238.5 | 200014.6 | 22091–678515 |
| Trial duration (s) | 127.4 | 200.3 | 22.1–679.0 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 11 | 0.0318 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 33.3% | 100.0% (clean) | 0 | 40 | 0.3669 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 12 | 0.0774 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0346 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 14 | 0.0602 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 0.0% | 100.0% (clean) | 0 | 40 | 0.2513 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 28 | 0.1577 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 100.0% (clean) | 0 | 20 | 0.0797 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0243 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 0.0% | 100.0% (clean) | 0 | 40 | 0.2798 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
