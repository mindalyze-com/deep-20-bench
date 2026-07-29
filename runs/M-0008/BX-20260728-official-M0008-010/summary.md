# Deep20Bench Core Subjects

- Execution: `BX-20260728-official-M0008-010`
- Benchmark: `B-0001`
- Model: `M-0008` — Grok 4.5 (high)
- Exact route: `x-ai/grok-4.5`
- Status: completed
- Success rate: 94.3%
- Median counted questions: 11
- Subjects: 7
- Iterations per subject: 5
- Trials: 33 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 0 recovered calls / 0 retried calls / 0 exhausted
- Output-contract reliability: `breached` · compliance `98.2%` · 10 violation(s) across 9 trial(s) · 10 counted-turn penalties
- Oracle quality control: 484 reviewed · agreement `88.8%` · 54 disagreement(s) / 54 Judge call(s) · 5 Oracle answer(s) changed (`9.3%`) · QC cost `1.1783` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 52/456 (`11.4%`) · `quantitative_comparison` 0/6 (`0.0%`) · `temporal_comparison` 2/21 (`9.5%`)
- Terminal failure codes: `ask_after_question_limit`=2
- Average cost per terminal run (USD): Guesser `0.0286` · Oracle `0.1137` · Verifier `0.0003` · Total `0.1426`
- Total benchmark cost (USD): `4.9913`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 11 | 15.11 | 4–50 |
| Questions (successful) | 11 | 13 | 4–45 |
| Guesser cost (USD) | 0.0149 | 0.0286 | 0.0059–0.1334 |
| Oracle cost (USD) | 0.0543 | 0.1137 | 0.0190–0.5125 |
| Verifier cost (USD) | 0.0003 | 0.0003 | 0.0003–0.0006 |
| Total cost (USD) | 0.0746 | 0.1426 | 0.0252–0.6237 |
| Tokens | 74233 | 142440 | 26751–666659 |
| LLM latency (ms) | 135801 | 229797.31 | 57257–915739 |
| Trial duration (s) | 136.5 | 230.5 | 57.6–918.6 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 9 | 0.0556 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 100.0% | 97.7% (breached) | 4 | 31 | 0.3879 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 60.0% | 98.0% (breached) | 3 | 15 | 0.3157 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 100.0% | 96.9% (breached) | 2 | 11 | 0.0809 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 7 | 0.0382 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 98.2% (breached) | 1 | 11 | 0.0852 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 4 | 0.0347 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
