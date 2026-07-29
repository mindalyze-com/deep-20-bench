# Deep20Bench Core Subjects

- Execution: `BX-20260727-official-M0011-025`
- Benchmark: `B-0001`
- Model: `M-0011` — Kimi K3 (high)
- Exact route: `moonshotai/kimi-k3`
- Status: completed
- Success rate: 100.0%
- Median counted questions: 10
- Subjects: 7
- Iterations per subject: 5
- Trials: 34 successful / 34 scoring-eligible / 35 scheduled
- Infrastructure failures: 1
- Recovery: 9 recovered calls / 9 retried calls / 0 exhausted
- Output-contract reliability: `breached` · compliance `98.2%` · 8 violation(s) across 7 trial(s) · 8 counted-turn penalties
- Terminal failure codes: `provider_request_failed`=1
- Average cost per terminal run (USD): Guesser `0.1476` · Oracle `0.0459` · Verifier `0.0004` · Total `0.1939`
- Total benchmark cost (USD): `6.7855`
- Files: [raw summary](summary.yml) · [full typed result](result.yml) · [live state](state.yml)

## Overall metrics

| Metric | Median | Mean | Range |
|---|---:|---:|---:|
| Questions (eligible) | 10 | 11.94 | 3–29 |
| Questions (successful) | 10 | 11.94 | 3–29 |
| Guesser cost (USD) | 0.0748 | 0.1476 | 0.0274–1.0598 |
| Oracle cost (USD) | 0.0371 | 0.0459 | 0.0099–0.1580 |
| Verifier cost (USD) | 0.0003 | 0.0004 | 0.0003–0.0014 |
| Total cost (USD) | 0.1084 | 0.1939 | 0.0510–1.2186 |
| Tokens | 51796 | 73448.91 | 16327–368279 |
| LLM latency (ms) | 212992 | 402726.69 | 99544–2742260 |
| Trial duration (s) | 213.2 | 403.0 | 99.7–2743.1 |

## Subjects

| Subject | ID | Trials | Success rate | Contract compliance | Violations | Median questions | Mean cost (USD) | Files |
|---|---|---:|---:|---:|---:|---:|---:|---|
| [Albert Einstein](subjects/T-0001/summary.md) | `T-0001` | 5 | 100.0% | 97.9% (breached) | 1 | 8 | 0.0892 | [report](subjects/T-0001/summary.md) · [raw](subjects/T-0001/result.yml) |
| [Albert Schweitzer](subjects/T-0002/summary.md) | `T-0002` | 5 | 100.0% | 99.3% (breached) | 1 | 28 | 0.4432 | [report](subjects/T-0002/summary.md) · [raw](subjects/T-0002/result.yml) |
| [Stephen King](subjects/T-0003/summary.md) | `T-0003` | 5 | 100.0% | 98.5% (breached) | 1 | 13 | 0.1185 | [report](subjects/T-0003/summary.md) · [raw](subjects/T-0003/result.yml) |
| [Garfield](subjects/T-0004/summary.md) | `T-0004` | 5 | 100.0% | 95.2% (breached) | 2 | 10 | 0.3303 | [report](subjects/T-0004/summary.md) · [raw](subjects/T-0004/result.yml) |
| [Achilles](subjects/T-0005/summary.md) | `T-0005` | 5 | 100.0% | 98.1% (breached) | 1 | 8 | 0.1628 | [report](subjects/T-0005/summary.md) · [raw](subjects/T-0005/result.yml) |
| [Genghis Khan](subjects/T-0006/summary.md) | `T-0006` | 5 | 100.0% | 100.0% (clean) | 0 | 11 | 0.1272 | [report](subjects/T-0006/summary.md) · [raw](subjects/T-0006/result.yml) |
| [Mario](subjects/T-0007/summary.md) | `T-0007` | 5 | 100.0% | 93.9% (breached) | 2 | 5 | 0.0859 | [report](subjects/T-0007/summary.md) · [raw](subjects/T-0007/result.yml) |

Each subject report links to every individual typed trial result.
