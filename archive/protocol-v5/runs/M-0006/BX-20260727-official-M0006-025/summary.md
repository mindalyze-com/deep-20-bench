# Deep20Bench Core Subjects

- Execution: `BX-20260727-official-M0006-025`
- Benchmark: `B-0001`
- Model: `M-0006` — Gemini 3.6 Flash (medium)
- Exact route: `google/gemini-3.6-flash`
- Status: completed
- Success rate: 97.1%
- Median counted questions: 15
- Subjects: 7
- Iterations per subject: 5
- Trials: 34 successful / 35 scoring-eligible / 35 scheduled
- Infrastructure failures: 0
- Recovery: 0 recovered calls / 0 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Terminal failure codes: `ask_after_question_limit`=1
- Average cost per terminal run (USD): Guesser `0.0846` · Oracle `0.0617` · Verifier `0.0003` · Total `0.1466`
- Total benchmark cost (USD): `5.1298`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 15 | 16 | 6–50 |
| Questions (successful) | 14.5 | 15 | 6–32 |
| Guesser cost (USD) | 0.0407 | 0.0846 | 0.0156–0.5720 |
| Oracle cost (USD) | 0.0471 | 0.0617 | 0.0241–0.2817 |
| Verifier cost (USD) | 0.0003 | 0.0003 | 0.0000–0.0013 |
| Total cost (USD) | 0.0920 | 0.1466 | 0.0446–0.8537 |
| Tokens | 57214 | 84464.74 | 26819–464444 |
| LLM latency (ms) | 130215 | 184314.91 | 56265–894235 |
| Trial duration (s) | 130.4 | 184.7 | 56.5–895.6 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 13 | 0.0855 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 100.0% | 100.0% (clean) | 0 | 27 | 0.2612 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 100.0% (clean) | 0 | 16 | 0.1045 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 80.0% | 100.0% (clean) | 0 | 20 | 0.3006 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0523 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 13 | 0.0872 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 8 | 0.1347 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
