# Deep20Bench Core Subjects

- Execution: `BX-20260824-smoke-M0018-001`
- Benchmark: `B-0001`
- Model: `M-0018` - Claude Opus 4.6 (high)
- Exact route: `anthropic/claude-opus-4.6`
- Execution commits: `9854ff545db548543675a047c36582dccf4009eb`
- Status: completed
- Success rate: 100.0%
- Median counted questions: 13
- Subjects: 1
- Iterations per subject: 1
- Trials: 1 successful / 1 scoring-eligible / 1 scheduled
- Completeness: 1/1 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 0 recovered calls / 0 retried calls / 0 exhausted
- Output-contract reliability: `breached` · compliance `92.9%` · 1 violation(s) across 1 trial(s) · 1 counted-turn penalties
- Oracle quality control: 12 reviewed · agreement `100.0%` · 0 disagreement(s) / 0 Judge call(s) · 0 Oracle answer(s) changed (`n/a`) · QC cost `0.0089` USD
- Oracle disagreement by question type: `other` 0/9 (`0.0%`) · `temporal_comparison` 0/3 (`0.0%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.1243` · Oracle `0.0942` · Verifier `0.0001` · Total `0.2187`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Total execution cost (USD): `0.2187`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 13 | 13 | 13–13 |
| Questions (successful) | 13 | 13 | 13–13 |
| Guesser cost (USD) | 0.1243 | 0.1243 | 0.1243–0.1243 |
| Oracle cost (USD) | 0.0942 | 0.0942 | 0.0942–0.0942 |
| Verifier cost (USD) | 0.0001 | 0.0001 | 0.0001–0.0001 |
| Terminal-attempt cost (USD) | 0.2187 | 0.2187 | 0.2187–0.2187 |
| Tokens | 96922 | 96922 | 96922–96922 |
| LLM latency (ms) | 212648 | 212648 | 212648–212648 |
| Trial duration (s) | 212.9 | 212.9 | 212.9–212.9 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 1 | 100.0% | 92.9% (breached) | 1 | 13 | 0.2187 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |

Each subject report links to every individual typed trial result.
