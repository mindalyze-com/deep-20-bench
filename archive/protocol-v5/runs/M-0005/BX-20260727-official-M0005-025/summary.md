# Deep20Bench Core Subjects

- Execution: `BX-20260727-official-M0005-025`
- Benchmark: `B-0001`
- Model: `M-0005` — Mistral Small 3.2 24B (non-thinking)
- Exact route: `mistralai/mistral-small-3.2-24b-instruct`
- Status: completed
- Success rate: 57.1%
- Median counted questions: 25
- Subjects: 7
- Iterations per subject: 5
- Trials: 20 successful / 35 scoring-eligible / 35 scheduled
- Infrastructure failures: 0
- Recovery: 1 recovered calls / 1 retried calls / 0 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Terminal failure codes: `ask_after_question_limit`=2
- Average cost per terminal run (USD): Guesser `0.0009` · Oracle `0.0890` · Verifier `0.0042` · Total `0.0941`
- Total benchmark cost (USD): `3.2949`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 25 | 28.51 | 3–50 |
| Questions (successful) | 12 | 13.6 | 3–42 |
| Guesser cost (USD) | 0.0007 | 0.0009 | 0.0001–0.0020 |
| Oracle cost (USD) | 0.0662 | 0.0890 | 0.0090–0.3856 |
| Verifier cost (USD) | 0.0019 | 0.0042 | 0.0000–0.0137 |
| Total cost (USD) | 0.0672 | 0.0941 | 0.0094–0.3873 |
| Tokens | 111870 | 142637.91 | 11323–540789 |
| LLM latency (ms) | 177686 | 201686.69 | 18038–553059 |
| Trial duration (s) | 179.5 | 202.7 | 18.2–555.1 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0291 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 20.0% | 100.0% (clean) | 0 | 50 | 0.1406 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 0.0% | 100.0% (clean) | 0 | 50 | 0.1167 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 40.0% | 100.0% (clean) | 0 | 50 | 0.1746 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 60.0% | 100.0% (clean) | 0 | 20 | 0.0946 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 80.0% | 100.0% (clean) | 0 | 25 | 0.0831 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 4 | 0.0202 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
