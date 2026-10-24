# Deep20Bench Edition 1.1

- Edition: `1.1` / `qualified-core-v1`
- Comparison classification: `standard`
- Explicit overrides: none
- Comparison contract: `2fa8c6bfffe0cf577cb6e97e8842a6c225d9b35b9ee22fa5a12461b2bc26fd5a`
- Execution: `BX-20261023-B-0003-official-M0035-001`
- Benchmark: `B-0003`
- Model: `M-0035` - Claude Haiku 5.5 (high)
- Exact route: `anthropic/claude-haiku-5.5`
- Execution commits: `bac364f4de6b3a8fc0dd049cf55f4da9ef2f8500`
- Status: completed
- Success rate: 83.3%
- Median counted questions: 16.5
- Subjects: 10
- Iterations per subject: 3
- Trials: 25 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 4 recovered calls / 5 retried calls / 2 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 517 reviewed · agreement `95.6%` · 23 disagreement(s) / 23 Judge call(s) · 17 Oracle answer(s) changed (`73.9%`) · QC cost `1.1687` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 21/505 (`4.2%`) · `temporal_comparison` 2/11 (`18.2%`)
- Terminal failure codes: `ask_after_question_limit`=4
- Average cost per terminal run (USD): Guesser `0.0046` · Oracle `0.0876` · Verifier `0.0003` · Total `0.0925`
- Superseded infrastructure attempts: 2 across 2 trial(s) · cost `0.1952` USD
- Total execution cost (USD): `2.9688`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 16.5 | 19.83 | 5–40 |
| Questions (successful) | 15 | 15.8 | 5–38 |
| Guesser cost (USD) | 0.0030 | 0.0046 | 0.0006–0.0147 |
| Oracle cost (USD) | 0.0752 | 0.0876 | 0.0031–0.2447 |
| Verifier cost (USD) | 0.0002 | 0.0003 | 0.0000–0.0008 |
| Terminal-attempt cost (USD) | 0.0787 | 0.0925 | 0.0041–0.2585 |
| Tokens | 151912 | 218062.6 | 18898–558587 |
| LLM latency (ms) | 183824 | 275937.27 | 21534–822111 |
| Trial duration (s) | 184.1 | 276.3 | 21.6–822.7 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 7 | 0.0273 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 66.7% | 100.0% (clean) | 0 | 19 | 0.1393 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 7 | 0.0187 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 6 | 0.0099 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 15 | 0.0999 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 33.3% | 100.0% (clean) | 0 | 40 | 0.2068 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 30 | 0.1257 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 100.0% (clean) | 0 | 20 | 0.0970 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0218 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 33.3% | 100.0% (clean) | 0 | 40 | 0.1781 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
