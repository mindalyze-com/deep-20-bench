# Deep20Bench Five Answer Experiment

- Execution: `BX-20260908-B-0003-experimental-M0021-001`
- Benchmark: `B-0003`
- Model: `M-0021` - Gemini 3.8 Flash (high)
- Exact route: `google/gemini-3.8-flash`
- Execution commits: `eceee31eef2eee309df803adf99bb6fa5bac3c87`
- Oracle contract revisions: 1; mixed-contract repair, not publication eligible
- Status: completed
- Success rate: 100.0%
- Median counted questions: 12
- Subjects: 10
- Iterations per subject: 3
- Trials: 30 successful / 30 scoring-eligible / 30 scheduled
- Completeness: 30/30 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 2 recovered calls / 4 retried calls / 2 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 437 reviewed · agreement `97.2%` · 12 disagreement(s) / 12 Judge call(s) · 7 Oracle answer(s) changed (`58.3%`) · QC cost `0.7982` USD
- Oracle disagreement by question type: `other` 12/407 (`3.0%`) · `temporal_comparison` 0/30 (`0.0%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.0875` · Oracle `0.0628` · Verifier `0.0002` · Total `0.1505`
- Superseded infrastructure attempts: 2 across 2 trial(s) · cost `0.0299` USD
- Total execution cost (USD): `4.5450`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 12 | 14.87 | 8–30 |
| Questions (successful) | 12 | 14.87 | 8–30 |
| Guesser cost (USD) | 0.0324 | 0.0875 | 0.0184–0.6912 |
| Oracle cost (USD) | 0.0408 | 0.0628 | 0.0268–0.1373 |
| Verifier cost (USD) | 0.0002 | 0.0002 | 0.0002–0.0007 |
| Terminal-attempt cost (USD) | 0.0773 | 0.1505 | 0.0487–0.8281 |
| Tokens | 105631.5 | 154887.33 | 68335–457338 |
| LLM latency (ms) | 162199 | 254683.07 | 103273–1036500 |
| Trial duration (s) | 162.5 | 255.0 | 103.5–1037.1 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 3 | 100.0% | 100.0% (clean) | 0 | 12 | 0.0802 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 3 | 100.0% | 100.0% (clean) | 0 | 16 | 0.3924 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 3 | 100.0% | 100.0% (clean) | 0 | 12 | 0.0880 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 3 | 100.0% | 100.0% (clean) | 0 | 8 | 0.0515 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 3 | 100.0% | 100.0% (clean) | 0 | 11 | 0.0634 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Bike pump](subjects/T-0008/summary.md) | `T-0008` | 3 | 100.0% | 100.0% (clean) | 0 | 28 | 0.3376 | [report](subjects/T-0008/summary.md) · [raw](subjects/T-0008/result.yml) |
| [Spider web](subjects/T-0009/summary.md) | `T-0009` | 3 | 100.0% | 100.0% (clean) | 0 | 11 | 0.0711 | [report](subjects/T-0009/summary.md) · [raw](subjects/T-0009/result.yml) |
| [Eyebrow](subjects/T-0010/summary.md) | `T-0010` | 3 | 100.0% | 100.0% (clean) | 0 | 14 | 0.0999 | [report](subjects/T-0010/summary.md) · [raw](subjects/T-0010/result.yml) |
| [Moon](subjects/T-0011/summary.md) | `T-0011` | 3 | 100.0% | 100.0% (clean) | 0 | 10 | 0.0615 | [report](subjects/T-0011/summary.md) · [raw](subjects/T-0011/result.yml) |
| [Door handle](subjects/T-0012/summary.md) | `T-0012` | 3 | 100.0% | 100.0% (clean) | 0 | 23 | 0.2595 | [report](subjects/T-0012/summary.md) · [raw](subjects/T-0012/result.yml) |

Each subject report links to every individual typed trial result.
