# Garfield

- Target: `T-0004`
- Success rate: 80.0%
- Counted questions by run: trial-001=9, trial-002=7, trial-003=7, trial-004=13, trial-005=50
- Counted questions (scoring-eligible): average `17.2` · minimum `7` · median `9` · maximum `50`
- Average cost per terminal run (USD): Guesser `2.6788` · Oracle `0.1946` · Verifier `0.0009` · Total `2.8743`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `breached` · compliance `98.9%` · 1 violation(s) across 1 trial(s) · 1 counted-turn penalties
- Oracle quality control: 59 reviewed · agreement `98.3%` · 1 disagreement(s) / 1 Judge call(s) · 0 Oracle answer(s) changed (`0.0%`) · QC cost `0.0762` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 1/55 (`1.8%`) · `temporal_comparison` 0/3 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 9 | clean (100.0%) | 0 | 0.1695 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 7 | clean (100.0%) | 0 | 0.1513 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 7 | clean (100.0%) | 0 | 0.1574 | [result](trials/trial-003/result.yml) |
| trial-004 | success | true | 13 | clean (100.0%) | 0 | 0.3208 | [result](trials/trial-004/result.yml) |
| trial-005 | limit_exhausted | false | 50 | breached (98.0%) | 1 | 13.5724 | [result](trials/trial-005/result.yml) |
