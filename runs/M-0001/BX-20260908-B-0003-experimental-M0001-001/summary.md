# Deep20Bench Five Answer Experiment

- Execution: `BX-20260908-B-0003-experimental-M0001-001`
- Benchmark: `B-0003`
- Model: `M-0001` - GPT-5.6 Luna (high)
- Exact route: `openai/gpt-5.6-luna`
- Execution commits: `eceee31eef2eee309df803adf99bb6fa5bac3c87`
- Status: completed
- Success rate: 90.0%
- Median counted questions: 21.5
- Subjects: 10
- Iterations per subject: 3
- Trials: 27 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 6 recovered calls / 8 retried calls / 2 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 592 reviewed · agreement `94.4%` · 33 disagreement(s) / 33 Judge call(s) · 24 Oracle answer(s) changed (`72.7%`) · QC cost `1.5821` USD
- Oracle disagreement by question type: `negation` 0/2 (`0.0%`) · `other` 31/574 (`5.4%`) · `temporal_comparison` 2/16 (`12.5%`)
- Terminal failure codes: `ask_after_question_limit`=1
- Average cost per terminal run (USD): Guesser `0.0063` · Oracle `0.1063` · Verifier `0.0002` · Total `0.1128`
- Superseded infrastructure attempts: 2 across 2 trial(s) · cost `0.0260` USD
- Total execution cost (USD): `3.4110`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 21.5 | 20.93 | 6–40 |
| Questions (successful) | 19 | 18.81 | 6–38 |
| Guesser cost (USD) | 0.0056 | 0.0063 | 0.0020–0.0152 |
| Oracle cost (USD) | 0.0988 | 0.1063 | 0.0166–0.2567 |
| Verifier cost (USD) | 0.0002 | 0.0002 | 0.0000–0.0007 |
| Terminal-attempt cost (USD) | 0.1040 | 0.1128 | 0.0187–0.2666 |
| Tokens | 201484.5 | 209420.37 | 42523–461131 |
| LLM latency (ms) | 318519 | 318572.33 | 68980–692906 |
| Trial duration (s) | 318.8 | 318.9 | 69.1–693.5 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 12 | 0.0425 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 100.0% (clean) | 0 | 24 | 0.1673 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 24 | 0.1138 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 7 | 0.0241 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 15 | 0.0700 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 33.3% | 100.0% (clean) | 0 | 40 | 0.2188 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 25 | 0.1583 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 66.7% | 100.0% (clean) | 0 | 26 | 0.1465 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 11 | 0.0617 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 100.0% | 100.0% (clean) | 0 | 25 | 0.1254 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
