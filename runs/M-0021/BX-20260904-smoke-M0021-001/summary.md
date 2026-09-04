# Deep20Bench Core Subjects

- Execution: `BX-20260904-smoke-M0021-001`
- Benchmark: `B-0001`
- Model: `M-0021` - Gemini 3.8 Flash (high)
- Exact route: `google/gemini-3.8-flash`
- Execution commits: `2d9a7a4d5f99268ec40b5a8785b5f8ea00d412c9`
- Status: completed
- Success rate: 100.0%
- Median counted questions: 12
- Subjects: 1
- Iterations per subject: 1
- Trials: 1 successful / 1 scoring-eligible / 1 scheduled
- Completeness: 1/1 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 0 recovered calls / 0 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 12 reviewed · agreement `100.0%` · 0 disagreement(s) / 0 Judge call(s) · 0 Oracle answer(s) changed (`n/a`) · QC cost `0.0093` USD
- Oracle disagreement by question type: `other` 0/9 (`0.0%`) · `temporal_comparison` 0/3 (`0.0%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.0499` · Oracle `0.0944` · Verifier `0.0001` · Total `0.1444`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Total execution cost (USD): `0.1444`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 12 | 12 | 12–12 |
| Questions (successful) | 12 | 12 | 12–12 |
| Guesser cost (USD) | 0.0499 | 0.0499 | 0.0499–0.0499 |
| Oracle cost (USD) | 0.0944 | 0.0944 | 0.0944–0.0944 |
| Verifier cost (USD) | 0.0001 | 0.0001 | 0.0001–0.0001 |
| Terminal-attempt cost (USD) | 0.1444 | 0.1444 | 0.1444–0.1444 |
| Tokens | 98914 | 98914 | 98914–98914 |
| LLM latency (ms) | 153241 | 153241 | 153241–153241 |
| Trial duration (s) | 153.4 | 153.4 | 153.4–153.4 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 1 | 100.0% | 100.0% (clean) | 0 | 12 | 0.1444 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |

Each subject report links to every individual typed trial result.
