# Garfield

- Target: `T-0004`
- Success rate: 100.0%
- Counted questions by run: trial-001=11, trial-002=13, trial-003=11, trial-004=13, trial-005=11
- Counted questions (scoring-eligible): average `11.8` · minimum `11` · median `11` · maximum `13`
- Average cost per terminal run (USD): Guesser `0.0196` · Oracle `0.0609` · Verifier `0.0003` · Total `0.0809`
- Output-contract reliability: `breached` · compliance `96.9%` · 2 violation(s) across 2 trial(s) · 2 counted-turn penalties
- Oracle quality control: 56 reviewed · agreement `100.0%` · 0 disagreement(s) / 0 Judge call(s) · 0 Oracle answer(s) changed (`n/a`) · QC cost `0.0448` USD
- Oracle disagreement by question type: `other` 0/56 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 11 | clean (100.0%) | 0 | 0.0698 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 13 | clean (100.0%) | 0 | 0.0969 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 11 | breached (91.7%) | 1 | 0.0764 | [result](trials/trial-003/result.yml) |
| trial-004 | success | true | 13 | breached (92.9%) | 1 | 0.0867 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 11 | clean (100.0%) | 0 | 0.0746 | [result](trials/trial-005/result.yml) |
