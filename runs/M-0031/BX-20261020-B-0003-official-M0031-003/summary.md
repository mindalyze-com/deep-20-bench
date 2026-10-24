# Deep20Bench Edition 1.1

- Edition: `1.1` / `qualified-core-v1`
- Comparison classification: `standard`
- Explicit overrides: none
- Comparison contract: `2fa8c6bfffe0cf577cb6e97e8842a6c225d9b35b9ee22fa5a12461b2bc26fd5a`
- Execution: `BX-20261020-B-0003-official-M0031-003`
- Benchmark: `B-0003`
- Model: `M-0031` - GPT-6.1 Sol (high)
- Exact route: `openai/gpt-6.1-sol`
- Execution commits: `bb0a7cf8459c995d3b334ed1780510d15c3b9f68`
- Status: completed
- Success rate: 93.1%
- Median counted questions: 14
- Subjects: 10
- Iterations per subject: 3
- Trials: 27 successful / 29 scoring-eligible / 30 scheduled
- Completeness: 29/30 scheduled trials scoring-eligible
- Infrastructure failures: 1
- Recovery: 2 recovered calls / 2 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 357 reviewed · agreement `95.2%` · 17 disagreement(s) / 17 Judge call(s) · 10 Oracle answer(s) changed (`58.8%`) · QC cost `0.8481` USD
- Oracle disagreement by question type: `negation` 1/4 (`25.0%`) · `other` 15/343 (`4.4%`) · `temporal_comparison` 1/10 (`10.0%`)
- Terminal failure codes: `web_search_budget_exceeded`=1
- Average cost per terminal run (USD): Guesser `0.0462` · Oracle `0.0670` · Verifier `0.0002` · Total `0.1135`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Total execution cost (USD): `3.4051`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 14 | 16.93 | 8–40 |
| Questions (successful) | 14 | 15.22 | 8–38 |
| Guesser cost (USD) | 0.0314 | 0.0462 | 0.0221–0.1978 |
| Oracle cost (USD) | 0.0424 | 0.0670 | 0.0063–0.2837 |
| Verifier cost (USD) | 0.0002 | 0.0002 | 0.0000–0.0007 |
| Terminal-attempt cost (USD) | 0.0740 | 0.1135 | 0.0308–0.4662 |
| Tokens | 106952 | 142742.47 | 23858–537028 |
| LLM latency (ms) | 189263.5 | 272410.8 | 56560–1271568 |
| Trial duration (s) | 189.6 | 272.8 | 56.7–1272.5 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0362 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 100.0% (clean) | 0 | 18 | 0.1015 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 50.0% | 100.0% (clean) | 0 | 24 | 0.2485 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0430 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 14 | 0.0810 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 100.0% | 100.0% (clean) | 0 | 26 | 0.2257 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 66.7% | 100.0% (clean) | 0 | 14 | 0.1848 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 100.0% (clean) | 0 | 15 | 0.0577 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0464 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 100.0% | 100.0% (clean) | 0 | 21 | 0.1103 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
