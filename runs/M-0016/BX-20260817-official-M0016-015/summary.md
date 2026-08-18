# Deep20Bench Core Subjects

- Execution: `BX-20260817-official-M0016-015`
- Benchmark: `B-0001`
- Model: `M-0016` - Gemini 3.7 Flash (high)
- Exact route: `google/gemini-3.7-flash`
- Execution commits: `7d637b2e6b711fecfd1783422b1c9cbf0d64a6b7`
- Status: completed
- Success rate: 97.1%
- Median counted questions: 12
- Subjects: 7
- Iterations per subject: 5
- Trials: 34 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 2 recovered calls / 2 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 466 reviewed · agreement `85.6%` · 67 disagreement(s) / 67 Judge call(s) · 5 Oracle answer(s) changed (`7.5%`) · QC cost `1.3262` USD
- Oracle disagreement by question type: `other` 66/397 (`16.6%`) · `temporal_comparison` 1/69 (`1.4%`)
- Terminal failure codes: `ask_after_question_limit`=1
- Average cost per terminal run (USD): Guesser `0.0653` · Oracle `0.2084` · Verifier `0.0001` · Total `0.2737`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Total execution cost (USD): `9.5796`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 12 | 14 | 7–50 |
| Questions (successful) | 12 | 12.94 | 7–26 |
| Guesser cost (USD) | 0.0239 | 0.0653 | 0.0151–1.0007 |
| Oracle cost (USD) | 0.1117 | 0.2084 | 0.0631–1.3583 |
| Verifier cost (USD) | 0.0001 | 0.0001 | 0.0001–0.0005 |
| Terminal-attempt cost (USD) | 0.1391 | 0.2737 | 0.0870–2.3595 |
| Tokens | 112303 | 199163.23 | 66002–1572367 |
| LLM latency (ms) | 153634 | 274328.66 | 93017–2384285 |
| Trial duration (s) | 153.8 | 274.5 | 93.1–2385.0 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 12 | 0.1182 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 100.0% | 100.0% (clean) | 0 | 25 | 0.6031 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 14 | 0.2107 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 100.0% | 100.0% (clean) | 0 | 12 | 0.1502 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 80.0% | 100.0% (clean) | 0 | 8 | 0.6016 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 12 | 0.1168 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 8 | 0.1153 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
