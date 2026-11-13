# Deep20Bench Edition 1.1

- Edition: `1.1` / `qualified-core-v1`
- Comparison classification: `standard`
- Explicit overrides: none
- Comparison contract: `2fa8c6bfffe0cf577cb6e97e8842a6c225d9b35b9ee22fa5a12461b2bc26fd5a`
- Execution: `BX-20261113-B-0003-official-M0040-001`
- Benchmark: `B-0003`
- Model: `M-0040` - Gemini 4 Hydrogen (high)
- Exact route: `google/gemini-4-hydrogen`
- Execution commits: `e2d2fb337b6d762d2ffcdb69f7ea850f9c7f76cb`
- Status: completed
- Success rate: 100.0%
- Median counted questions: 13
- Subjects: 10
- Iterations per subject: 3
- Trials: 30 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 0 recovered calls / 2 retried calls / 2 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 303 reviewed · agreement `95.7%` · 13 disagreement(s) / 13 Judge call(s) · 7 Oracle answer(s) changed (`53.8%`) · QC cost `0.6841` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 13/267 (`4.9%`) · `quantitative_comparison` 0/3 (`0.0%`) · `temporal_comparison` 0/32 (`0.0%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.1238` · Oracle `0.0507` · Verifier `0.0002` · Total `0.1747`
- Superseded infrastructure attempts: 2 across 2 trial(s) · cost `0.2115` USD
- Total execution cost (USD): `5.4537`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 13 | 14.93 | 7–40 |
| Questions (successful) | 13 | 14.93 | 7–40 |
| Guesser cost (USD) | 0.0670 | 0.1238 | 0.0347–0.8635 |
| Oracle cost (USD) | 0.0349 | 0.0507 | 0.0066–0.2533 |
| Verifier cost (USD) | 0.0002 | 0.0002 | 0.0002–0.0002 |
| Terminal-attempt cost (USD) | 0.0988 | 0.1747 | 0.0488–1.1170 |
| Tokens | 91730 | 128013.53 | 36981–548245 |
| LLM latency (ms) | 131128.5 | 196907.97 | 56703–1135574 |
| Trial duration (s) | 131.3 | 197.1 | 56.8–1136.3 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 12 | 0.0835 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 100.0% (clean) | 0 | 15 | 0.1253 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 11 | 0.0733 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0566 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 13 | 0.0964 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 100.0% | 100.0% (clean) | 0 | 30 | 0.4866 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 13 | 0.1269 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 100.0% (clean) | 0 | 14 | 0.1155 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0703 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 100.0% | 100.0% (clean) | 0 | 20 | 0.5130 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
