# Achilles

- Target: `T-0005`
- Success rate: 100.0%
- Counted questions by run: trial-001=9, trial-002=7, trial-003=9, trial-004=7, trial-005=9
- Counted questions (scoring-eligible): average `8.2` · minimum `7` · median `9` · maximum `9`
- Average cost per terminal run (USD): Guesser `0.0737` · Oracle `0.0414` · Verifier `0.0004` · Total `0.1155`
- Output-contract reliability: `breached` · compliance `95.7%` · 2 violation(s) across 2 trial(s) · 2 counted-turn penalties
- Oracle quality control: 36 reviewed · agreement `100.0%` · 0 disagreement(s) / 0 Judge call(s) · 0 Oracle answer(s) changed (`n/a`) · QC cost `0.0304` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 0/35 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 9 | breached (90.0%) | 1 | 0.1387 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 7 | clean (100.0%) | 0 | 0.0790 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 9 | breached (90.0%) | 1 | 0.1412 | [result](trials/trial-003/result.yml) |
| trial-004 | success | true | 7 | clean (100.0%) | 0 | 0.0887 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 9 | clean (100.0%) | 0 | 0.1299 | [result](trials/trial-005/result.yml) |
