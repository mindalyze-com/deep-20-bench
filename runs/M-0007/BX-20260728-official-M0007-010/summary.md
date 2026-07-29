# Deep20Bench Core Subjects

- Execution: `BX-20260728-official-M0007-010`
- Benchmark: `B-0001`
- Model: `M-0007` — Kimi K3 (high)
- Exact route: `moonshotai/kimi-k3`
- Status: completed
- Success rate: 94.3%
- Median counted questions: 9
- Subjects: 7
- Iterations per subject: 5
- Trials: 33 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 3 recovered calls / 3 retried calls / 1 exhausted
- Output-contract reliability: `breached` · compliance `97.7%` · 11 violation(s) across 10 trial(s) · 11 counted-turn penalties
- Oracle quality control: 378 reviewed · agreement `91.8%` · 31 disagreement(s) / 31 Judge call(s) · 3 Oracle answer(s) changed (`9.7%`) · QC cost `0.7370` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 28/326 (`8.6%`) · `temporal_comparison` 3/51 (`5.9%`)
- Terminal failure codes: `ask_after_question_limit`=2
- Average cost per terminal run (USD): Guesser `0.2032` · Oracle `0.0845` · Verifier `0.0005` · Total `0.2882`
- Total benchmark cost (USD): `10.0866`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 9 | 12.69 | 2–50 |
| Questions (successful) | 9 | 10.42 | 2–34 |
| Guesser cost (USD) | 0.0783 | 0.2032 | 0.0259–2.5279 |
| Oracle cost (USD) | 0.0563 | 0.0845 | 0.0150–0.4182 |
| Verifier cost (USD) | 0.0003 | 0.0005 | 0.0003–0.0023 |
| Total cost (USD) | 0.1387 | 0.2882 | 0.0430–2.9436 |
| Tokens | 76664 | 123529.74 | 25523–814944 |
| LLM latency (ms) | 247346 | 542777.57 | 86561–5342342 |
| Trial duration (s) | 247.9 | 543.3 | 86.7–5344.8 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0878 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 80.0% | 99.3% (breached) | 1 | 19 | 0.6917 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 97.3% (breached) | 2 | 13 | 0.1909 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 80.0% | 96.8% (breached) | 3 | 10 | 0.6923 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 95.7% (breached) | 2 | 9 | 0.1155 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 98.2% (breached) | 1 | 10 | 0.1666 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 92.3% (breached) | 2 | 4 | 0.0725 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
