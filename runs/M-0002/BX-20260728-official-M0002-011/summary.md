# Deep20Bench Core Subjects

- Execution: `BX-20260728-official-M0002-011`
- Benchmark: `B-0001`
- Model: `M-0002` — gpt-oss-120B (high)
- Exact route: `openai/gpt-oss-120b`
- Execution commits: `1076abf750e36c619ccbefa3a61908644adeadd0`
- Status: completed
- Success rate: 94.3%
- Median counted questions: 11
- Subjects: 7
- Iterations per subject: 5
- Trials: 33 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 26 recovered calls / 31 retried calls / 46 exhausted
- Output-contract reliability: `breached` · compliance `90.6%` · 46 violation(s) across 7 trial(s) · 46 counted-turn penalties
- Oracle quality control: 389 reviewed · agreement `86.1%` · 54 disagreement(s) / 54 Judge call(s) · 2 Oracle answer(s) changed (`3.7%`) · QC cost `1.0957` USD
- Oracle disagreement by question type: `negation` 0/2 (`0.0%`) · `other` 54/381 (`14.2%`) · `temporal_comparison` 0/6 (`0.0%`)
- Terminal failure codes: `ask_after_question_limit`=1, `consecutive_contract_violations_exhausted`=1
- Average cost per terminal run (USD): Guesser `0.0363` · Oracle `0.0960` · Verifier `0.0004` · Total `0.1326`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Total execution cost (USD): `4.6421`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 11 | 13.03 | 2–50 |
| Questions (successful) | 10 | 11.36 | 2–38 |
| Guesser cost (USD) | 0.0147 | 0.0363 | 0.0027–0.2401 |
| Oracle cost (USD) | 0.0758 | 0.0960 | 0.0070–0.3549 |
| Verifier cost (USD) | 0.0003 | 0.0004 | 0.0000–0.0011 |
| Terminal-attempt cost (USD) | 0.0918 | 0.1326 | 0.0112–0.5953 |
| Tokens | 102064 | 155973.31 | 13990–633931 |
| LLM latency (ms) | 149003 | 228209.83 | 19055–959248 |
| Trial duration (s) | 149.3 | 228.5 | 19.1–959.9 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 6 | 0.0317 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 80.0% | 79.7% (breached) | 28 | 17 | 0.3149 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 12 | 0.1063 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 80.0% | 86.7% (breached) | 11 | 15 | 0.1661 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 91.9% (breached) | 5 | 8 | 0.0946 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 97.8% (breached) | 2 | 16 | 0.1976 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 3 | 0.0173 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
