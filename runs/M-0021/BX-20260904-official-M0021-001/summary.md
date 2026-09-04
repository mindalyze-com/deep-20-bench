# Deep20Bench Core Subjects

- Execution: `BX-20260904-official-M0021-001`
- Benchmark: `B-0001`
- Model: `M-0021` - Gemini 3.8 Flash (high)
- Exact route: `google/gemini-3.8-flash`
- Execution commits: `fc441117537d09c0b71428aedce99c8583795fa6`
- Status: completed
- Success rate: 100.0%
- Median counted questions: 12
- Subjects: 7
- Iterations per subject: 5
- Trials: 35 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 6 recovered calls / 6 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 439 reviewed · agreement `86.8%` · 58 disagreement(s) / 58 Judge call(s) · 6 Oracle answer(s) changed (`10.3%`) · QC cost `1.2097` USD
- Oracle disagreement by question type: `other` 57/363 (`15.7%`) · `temporal_comparison` 1/76 (`1.3%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.1128` · Oracle `0.1963` · Verifier `0.0001` · Total `0.3093`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Total execution cost (USD): `10.8243`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 12 | 13.14 | 6–37 |
| Questions (successful) | 12 | 13.14 | 6–37 |
| Guesser cost (USD) | 0.0351 | 0.1128 | 0.0177–0.8966 |
| Oracle cost (USD) | 0.1280 | 0.1963 | 0.0669–0.6864 |
| Verifier cost (USD) | 0.0001 | 0.0001 | 0.0001–0.0007 |
| Terminal-attempt cost (USD) | 0.1665 | 0.3093 | 0.0887–1.4899 |
| Tokens | 124593 | 192844.29 | 65096–782963 |
| LLM latency (ms) | 174960 | 295589.2 | 90803–1408556 |
| Trial duration (s) | 175.1 | 295.8 | 90.9–1409.2 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 12 | 0.1421 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 100.0% | 100.0% (clean) | 0 | 26 | 0.9412 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 13 | 0.2381 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 100.0% | 100.0% (clean) | 0 | 10 | 0.1624 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 8 | 0.3900 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 12 | 0.1455 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 8 | 0.1456 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
