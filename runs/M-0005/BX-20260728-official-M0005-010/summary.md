# Deep20Bench Core Subjects

- Execution: `BX-20260728-official-M0005-010`
- Benchmark: `B-0001`
- Model: `M-0005` — Claude Sonnet 5 (high)
- Exact route: `anthropic/claude-sonnet-5`
- Status: completed
- Success rate: 94.1%
- Median counted questions: 12.5
- Subjects: 7
- Iterations per subject: 5
- Trials: 32 successful / 34 scoring-eligible / 35 scheduled
- Completeness: 34/35 scheduled trials scoring-eligible
- Infrastructure failures: 1
- Recovery: 1 recovered calls / 1 retried calls / 0 exhausted
- Output-contract reliability: `breached` · compliance `99.8%` · 1 violation(s) across 1 trial(s) · 1 counted-turn penalties
- Oracle quality control: 513 reviewed · agreement `87.3%` · 65 disagreement(s) / 65 Judge call(s) · 7 Oracle answer(s) changed (`10.8%`) · QC cost `1.4088` USD
- Oracle disagreement by question type: `negation` 0/13 (`0.0%`) · `other` 63/479 (`13.2%`) · `temporal_comparison` 2/21 (`9.5%`)
- Terminal failure codes: `ask_after_question_limit`=2, `provider_invalid_request`=1
- Average cost per terminal run (USD): Guesser `0.0756` · Oracle `0.1338` · Verifier `0.0005` · Total `0.2099`
- Total benchmark cost (USD): `7.3451`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 12.5 | 17 | 6–50 |
| Questions (successful) | 11.5 | 14.94 | 6–50 |
| Guesser cost (USD) | 0.0225 | 0.0756 | 0.0109–0.6849 |
| Oracle cost (USD) | 0.0924 | 0.1338 | 0.0261–0.4712 |
| Verifier cost (USD) | 0.0003 | 0.0005 | 0.0000–0.0027 |
| Total cost (USD) | 0.1152 | 0.2099 | 0.0401–1.0394 |
| Tokens | 119980 | 179932.54 | 42146–800071 |
| LLM latency (ms) | 194316 | 334395.71 | 79536–1493752 |
| Trial duration (s) | 195.1 | 335.2 | 80.0–1496.6 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 11 | 0.0717 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 100.0% | 100.0% (clean) | 0 | 28 | 0.3836 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 16 | 0.1528 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 60.0% | 100.0% (clean) | 0 | 47 | 0.6216 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 7 | 0.0459 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 98.6% (breached) | 1 | 12 | 0.1237 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 6 | 0.0697 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
