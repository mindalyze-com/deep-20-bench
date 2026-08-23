# Deep20Bench Core Subjects

- Execution: `BX-20260823-official-M0017-018`
- Benchmark: `B-0001`
- Model: `M-0017` - Ox Alpha (high)
- Exact route: `stealth/ox-alpha`
- Execution commits: `d9c61bce0822d51541a76c5df2ac343bb862a667`
- Status: completed
- Success rate: 91.4%
- Median counted questions: 13
- Subjects: 7
- Iterations per subject: 5
- Trials: 32 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 33 recovered calls / 40 retried calls / 7 exhausted
- Output-contract reliability: `breached` · compliance `92.7%` · 47 violation(s) across 35 trial(s) · 47 counted-turn penalties
- Oracle quality control: 530 reviewed · agreement `81.7%` · 97 disagreement(s) / 97 Judge call(s) · 4 Oracle answer(s) changed (`4.1%`) · QC cost `1.8099` USD
- Oracle disagreement by question type: `negation` 0/2 (`0.0%`) · `other` 96/493 (`19.5%`) · `temporal_comparison` 1/35 (`2.9%`)
- Terminal failure codes: `ask_after_question_limit`=3
- Average cost per terminal run (USD): Guesser `0.0000` · Oracle `0.2791` · Verifier `0.0002` · Total `0.2793`
- Superseded infrastructure attempts: 4 across 4 trial(s) · cost `2.5314` USD
- Total execution cost (USD): `12.3071`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 13 | 17.51 | 6–50 |
| Questions (successful) | 12.5 | 14.47 | 6–41 |
| Guesser cost (USD) | 0.0000 | 0.0000 | 0.0000–0.0000 |
| Oracle cost (USD) | 0.1655 | 0.2791 | 0.0364–1.1304 |
| Verifier cost (USD) | 0.0001 | 0.0002 | 0.0001–0.0005 |
| Terminal-attempt cost (USD) | 0.1656 | 0.2793 | 0.0366–1.1308 |
| Tokens | 147216 | 239830.6 | 35498–979688 |
| LLM latency (ms) | 341461 | 536442.8 | 87325–2647998 |
| Trial duration (s) | 341.8 | 536.8 | 87.5–2648.9 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 88.9% (breached) | 6 | 9 | 0.0709 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 40.0% | 96.2% (breached) | 8 | 50 | 0.8615 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 92.4% (breached) | 7 | 16 | 0.2396 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 100.0% | 92.9% (breached) | 7 | 14 | 0.3177 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 89.5% (breached) | 6 | 10 | 0.1334 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 93.1% (breached) | 7 | 17 | 0.2810 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 83.8% (breached) | 6 | 6 | 0.0511 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
