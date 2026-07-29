# Deep20Bench Core Subjects

- Execution: `BX-20260728-official-M0009-010`
- Benchmark: `B-0001`
- Model: `M-0009` — Llama 4 Maverick (non-thinking)
- Exact route: `meta-llama/llama-4-maverick`
- Status: completed
- Success rate: 48.6%
- Median counted questions: 38
- Subjects: 7
- Iterations per subject: 5
- Trials: 17 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 6 recovered calls / 6 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 293 reviewed · agreement `85.3%` · 43 disagreement(s) / 43 Judge call(s) · 11 Oracle answer(s) changed (`25.6%`) · QC cost `0.9084` USD
- Oracle disagreement by question type: `other` 43/289 (`14.9%`) · `temporal_comparison` 0/4 (`0.0%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.0086` · Oracle `0.0908` · Verifier `0.0071` · Total `0.1064`
- Total benchmark cost (USD): `3.7251`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 38 | 31.37 | 3–50 |
| Questions (successful) | 11 | 12.35 | 3–30 |
| Guesser cost (USD) | 0.0090 | 0.0086 | 0.0005–0.0160 |
| Oracle cost (USD) | 0.0979 | 0.0908 | 0.0160–0.2126 |
| Verifier cost (USD) | 0.0090 | 0.0071 | 0.0003–0.0136 |
| Total cost (USD) | 0.1125 | 0.1064 | 0.0167–0.2408 |
| Tokens | 177364 | 153292.09 | 21509–325248 |
| LLM latency (ms) | 228674 | 192625.77 | 30699–321322 |
| Trial duration (s) | 231.8 | 194.3 | 31.0–322.9 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 60.0% | 100.0% (clean) | 0 | 12 | 0.0847 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 0.0% | 100.0% (clean) | 0 | 50 | 0.1445 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 0.0% | 100.0% (clean) | 0 | 50 | 0.1715 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 60.0% | 100.0% (clean) | 0 | 30 | 0.1167 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 60.0% | 100.0% (clean) | 0 | 29 | 0.1020 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 60.0% | 100.0% (clean) | 0 | 14 | 0.1057 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 3 | 0.0199 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
