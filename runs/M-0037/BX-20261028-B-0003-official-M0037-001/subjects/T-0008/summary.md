# Bike pump

- Target: `T-0008`
- Success rate: 66.7%
- Counted questions by run: trial-001=40, trial-002=39, trial-003=40
- Counted questions (scoring-eligible): average `39.67` · minimum `39` · median `40` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0254` · Oracle `0.2111` · Verifier `0.0005` · Total `0.2370`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `breached` · compliance `98.4%` · 2 violation(s) across 2 trial(s) · 2 counted-turn penalties
- Oracle quality control: 101 reviewed · agreement `92.1%` · 8 disagreement(s) / 8 Judge call(s) · 6 Oracle answer(s) changed (`75.0%`) · QC cost `0.3130` USD
- Oracle disagreement by question type: `other` 8/101 (`7.9%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | limit_exhausted | false | 40 | breached (97.6%) | 1 | 0.2952 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 39 | breached (97.5%) | 1 | 0.1659 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 40 | clean (100.0%) | 0 | 0.2499 | [result](trials/trial-003/result.yml) |
