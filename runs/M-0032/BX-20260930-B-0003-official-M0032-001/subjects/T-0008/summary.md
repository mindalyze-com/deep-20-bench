# Bike pump

- Target: `T-0008`
- Success rate: 66.7%
- Counted questions by run: trial-001=33, trial-002=24, trial-003=40
- Counted questions (scoring-eligible): average `32.33` · minimum `24` · median `33` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.1104` · Oracle `0.1723` · Verifier `0.0005` · Total `0.2832`
- Superseded infrastructure attempts: 1 across 1 trial(s) · cost `0.2402` USD
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 83 reviewed · agreement `90.4%` · 8 disagreement(s) / 8 Judge call(s) · 6 Oracle answer(s) changed (`75.0%`) · QC cost `0.2826` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 8/81 (`9.9%`) · `quantitative_comparison` 0/1 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 33 | clean (100.0%) | 0 | 0.2663 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 24 | clean (100.0%) | 0 | 0.2437 | [result](trials/trial-002/result.yml) |
| trial-003 | limit_exhausted | false | 40 | clean (100.0%) | 0 | 0.3397 | [result](trials/trial-003/result.yml) |
