# Garfield

- Target: `T-0004`
- Success rate: 66.7%
- Counted questions by run: trial-001=17, trial-002=40, trial-003=14
- Counted questions (scoring-eligible): average `23.67` · minimum `14` · median `17` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0142` · Oracle `0.0604` · Verifier `0.0010` · Total `0.0755`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `breached` · compliance `98.6%` · 1 violation(s) across 1 trial(s) · 1 counted-turn penalties
- Oracle quality control: 37 reviewed · agreement `100.0%` · 0 disagreement(s) / 0 Judge call(s) · 0 Oracle answer(s) changed (`n/a`) · QC cost `0.0499` USD
- Oracle disagreement by question type: `other` 0/36 (`0.0%`) · `temporal_comparison` 0/1 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 17 | clean (100.0%) | 0 | 0.0613 | [result](trials/trial-001/result.yml) |
| trial-002 | limit_exhausted | false | 40 | clean (100.0%) | 0 | 0.1050 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 14 | breached (93.3%) | 1 | 0.0604 | [result](trials/trial-003/result.yml) |
