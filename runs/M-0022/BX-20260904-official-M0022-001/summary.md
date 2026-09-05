# Deep20Bench Core Subjects

- Execution: `BX-20260904-official-M0022-001`
- Benchmark: `B-0001`
- Model: `M-0022` - GPT-6 Astra (high)
- Exact route: `openai/gpt-6-astra`
- Execution commits: `12002aecd849bd65497536188cf94db26ea5e493`
- Status: completed
- Success rate: 94.3%
- Median counted questions: 9
- Subjects: 7
- Iterations per subject: 5
- Trials: 33 successful / 35 scoring-eligible / 35 scheduled
- Completeness: 35/35 scheduled trials scoring-eligible
- Infrastructure failures: 0
- Recovery: 9 recovered calls / 12 retried calls / 3 exhausted
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 454 reviewed · agreement `90.1%` · 45 disagreement(s) / 45 Judge call(s) · 7 Oracle answer(s) changed (`15.6%`) · QC cost `1.1051` USD
- Oracle disagreement by question type: `other` 45/410 (`11.0%`) · `temporal_comparison` 0/44 (`0.0%`)
- Terminal failure codes: none
- Average cost per terminal run (USD): Guesser `0.3279` · Oracle `0.3176` · Verifier `0.0002` · Total `0.6456`
- Superseded infrastructure attempts: 4 across 3 trial(s) · cost `3.1547` USD
- Total execution cost (USD): `25.7505`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 9 | 15.03 | 5–50 |
| Questions (successful) | 9 | 12.91 | 5–41 |
| Guesser cost (USD) | 0.1192 | 0.3279 | 0.0662–2.0382 |
| Oracle cost (USD) | 0.1052 | 0.3176 | 0.0436–1.8310 |
| Verifier cost (USD) | 0.0001 | 0.0002 | 0.0001–0.0009 |
| Terminal-attempt cost (USD) | 0.2189 | 0.6456 | 0.1268–3.8699 |
| Tokens | 93608 | 291855.86 | 39234–1742360 |
| LLM latency (ms) | 143696 | 417327.34 | 71705–2365316 |
| Trial duration (s) | 143.9 | 417.6 | 71.8–2366.5 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 100.0% (clean) | 0 | 9 | 0.1828 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 100.0% | 100.0% (clean) | 0 | 22 | 0.8894 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 60.0% | 100.0% (clean) | 0 | 41 | 2.3877 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 100.0% | 100.0% (clean) | 0 | 9 | 0.5091 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 100.0% (clean) | 0 | 7 | 0.1741 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 9 | 0.2408 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 100.0% (clean) | 0 | 5 | 0.1351 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
