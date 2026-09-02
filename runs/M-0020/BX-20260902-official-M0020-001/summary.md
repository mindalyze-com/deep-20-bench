# Deep20Bench Core Subjects

- Execution: `BX-20260902-official-M0020-001`
- Benchmark: `B-0001`
- Model: `M-0020` - Claude Fable 5.1 (high)
- Exact route: `anthropic/claude-fable-5.1`
- Execution commits: `47e9bc2697624e1d5e7b82c612f34c8b741b7854`
- Status: completed
- Success rate: 97.1%
- Median counted questions: 9
- Subjects: 7
- Iterations per subject: 5
- Trials: 34 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 2 recovered calls / 2 retried calls / 0 exhausted
- Output-contract reliability: `breached` · compliance `99.8%` · 1 violation(s) across 1 trial(s) · 1 counted-turn penalties
- Oracle quality control: 386 reviewed · agreement `81.9%` · 70 disagreement(s) / 70 Judge call(s) · 2 Oracle answer(s) changed (`2.9%`) · QC cost `1.3415` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 70/343 (`20.4%`) · `temporal_comparison` 0/42 (`0.0%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.5014` · Oracle `0.1730` · Verifier `0.0003` · Total `0.6747`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Total execution cost (USD): `23.6136`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 9 | 12.09 | 4–50 |
| Questions (successful) | 9 | 10.97 | 4–32 |
| Guesser cost (USD) | 0.0838 | 0.5014 | 0.0416–13.0285 |
| Oracle cost (USD) | 0.0894 | 0.1730 | 0.0516–0.6150 |
| Verifier cost (USD) | 0.0001 | 0.0003 | 0.0001–0.0039 |
| Terminal-attempt cost (USD) | 0.1695 | 0.6747 | 0.0933–13.5724 |
| Tokens | 90131 | 159784.86 | 49124–895690 |
| LLM latency (ms) | 151811 | 349994 | 69384–4585165 |
| Trial duration (s) | 152.0 | 350.2 | 69.5–4585.9 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 9 | 0.2009 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 100.0% | 100.0% (clean) | 0 | 22 | 0.9209 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 11 | 0.2702 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 80.0% | 98.9% (breached) | 1 | 9 | 2.8743 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 7 | 0.1570 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 9 | 0.1778 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 5 | 0.1217 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
