# Achilles

- Target: `T-0005`
- Success rate: 60.0%
- Counted questions by run: trial-001=19, trial-002=29, trial-003=50, trial-004=50, trial-005=25
- Counted questions (scoring-eligible): average `34.6` · minimum `19` · median `29` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.0089` · Oracle `0.0849` · Verifier `0.0082` · Total `0.1020`
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 44 reviewed · agreement `93.2%` · 3 disagreement(s) / 3 Judge call(s) · 2 Oracle answer(s) changed (`66.7%`) · QC cost `0.0946` USD
- Oracle disagreement by question type: `other` 3/44 (`6.8%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 19 | clean (100.0%) | 0 | 0.1047 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 29 | clean (100.0%) | 0 | 0.1076 | [result](trials/trial-002/result.yml) |
| trial-003 | limit_exhausted | false | 50 | clean (100.0%) | 0 | 0.1276 | [result](trials/trial-003/result.yml) |
| trial-004 | limit_exhausted | false | 50 | clean (100.0%) | 0 | 0.0727 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 25 | clean (100.0%) | 0 | 0.0974 | [result](trials/trial-005/result.yml) |
