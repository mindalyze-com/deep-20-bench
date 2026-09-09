# Bike pump

- Target: `T-0008`
- Success rate: 33.3%
- Counted questions by run: trial-001=40, trial-002=40, trial-003=33
- Counted questions (scoring-eligible): average `37.67` · minimum `33` · median `40` · maximum `40`
- Average cost per terminal run (USD): Guesser `1.4730` · Oracle `0.1965` · Verifier `0.0007` · Total `1.6703`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `breached` · compliance `99.1%` · 1 violation(s) across 1 trial(s) · 1 counted-turn penalties
- Oracle quality control: 100 reviewed · agreement `92.0%` · 8 disagreement(s) / 8 Judge call(s) · 6 Oracle answer(s) changed (`75.0%`) · QC cost `0.2973` USD
- Oracle disagreement by question type: `other` 8/100 (`8.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | limit_exhausted | false | 40 | clean (100.0%) | 0 | 1.7767 | [result](trials/trial-001/result.yml) |
| trial-002 | limit_exhausted | false | 40 | clean (100.0%) | 0 | 2.0006 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 33 | breached (97.1%) | 1 | 1.2335 | [result](trials/trial-003/result.yml) |
