# Garfield

- Target: `T-0004`
- Success rate: 60.0%
- Counted questions by run: trial-001=50, trial-002=11, trial-003=30, trial-004=38, trial-005=19
- Counted questions (scoring-eligible): average `29.6` · minimum `11` · median `30` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.0071` · Oracle `0.1030` · Verifier `0.0066` · Total `0.1167`
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 49 reviewed · agreement `87.8%` · 6 disagreement(s) / 6 Judge call(s) · 0 Oracle answer(s) changed (`0.0%`) · QC cost `0.1377` USD
- Oracle disagreement by question type: `other` 6/49 (`12.2%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | limit_exhausted | false | 50 | clean (100.0%) | 0 | 0.1041 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 11 | clean (100.0%) | 0 | 0.0949 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 30 | clean (100.0%) | 0 | 0.1143 | [result](trials/trial-003/result.yml) |
| trial-004 | validator_unknown | false | 38 | clean (100.0%) | 0 | 0.1443 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 19 | clean (100.0%) | 0 | 0.1260 | [result](trials/trial-005/result.yml) |
