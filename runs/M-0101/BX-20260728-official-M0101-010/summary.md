# Deep20Bench Core Subjects

- Execution: `BX-20260728-official-M0101-010`
- Benchmark: `B-0001`
- Model: `M-0101` — GPT-5.6 Luna (medium)
- Exact route: `openai/gpt-5.6-luna`
- Execution commits: `5db0c78e58c323773a2c6fc3727a35c061a88486`
- Status: completed
- Success rate: 91.4%
- Median counted questions: 13
- Subjects: 7
- Iterations per subject: 5
- Trials: 32 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 1 recovered calls / 1 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 580 reviewed · agreement `85.5%` · 84 disagreement(s) / 84 Judge call(s) · 15 Oracle answer(s) changed (`17.9%`) · QC cost `1.7307` USD
- Oracle disagreement by question type: `negation` 1/4 (`25.0%`) · `other` 82/554 (`14.8%`) · `temporal_comparison` 1/22 (`4.6%`)
- Terminal failure codes: `ask_after_question_limit`=1
- Average cost per terminal run (USD): Guesser `0.0128` · Oracle `0.1565` · Verifier `0.0004` · Total `0.1697`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Total execution cost (USD): `5.9392`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 13 | 17.74 | 4–50 |
| Questions (successful) | 11 | 14.72 | 4–40 |
| Guesser cost (USD) | 0.0090 | 0.0128 | 0.0028–0.0450 |
| Oracle cost (USD) | 0.0978 | 0.1565 | 0.0226–0.5790 |
| Verifier cost (USD) | 0.0003 | 0.0004 | 0.0003–0.0016 |
| Terminal-attempt cost (USD) | 0.1075 | 0.1697 | 0.0261–0.6225 |
| Tokens | 107393 | 182864.4 | 29246–714921 |
| LLM latency (ms) | 174121 | 276274.03 | 57794–905895 |
| Trial duration (s) | 174.8 | 277.2 | 58.2–908.7 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0511 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 100.0% | 100.0% (clean) | 0 | 26 | 0.2750 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 16 | 0.1336 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 60.0% | 100.0% (clean) | 0 | 38 | 0.3966 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0432 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 80.0% | 100.0% (clean) | 0 | 18 | 0.2383 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 5 | 0.0501 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
