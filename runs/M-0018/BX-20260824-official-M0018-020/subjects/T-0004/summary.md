# Garfield

- Target: `T-0004`
- Success rate: 100.0%
- Counted questions by run: trial-001=50, trial-002=37, trial-003=24, trial-004=46 (infrastructure failed), trial-005=0 (infrastructure failed)
- Counted questions (scoring-eligible): average `37` · minimum `24` · median `37` · maximum `50`
- Average cost per terminal run (USD): Guesser `2.5196` · Oracle `0.5226` · Verifier `0.0004` · Total `3.0426`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `breached` · compliance `97.4%` · 3 violation(s) across 3 trial(s) · 3 counted-turn penalties
- Oracle quality control: 96 reviewed · agreement `92.7%` · 7 disagreement(s) / 7 Judge call(s) · 2 Oracle answer(s) changed (`28.6%`) · QC cost `0.1971` USD
- Oracle disagreement by question type: `other` 7/93 (`7.5%`) · `temporal_comparison` 0/3 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 50 | breached (98.0%) | 1 | 7.6254 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 37 | breached (97.4%) | 1 | 1.8009 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 24 | breached (96.0%) | 1 | 0.7244 | [result](trials/trial-003/result.yml) |
| trial-004 | infrastructure_failed | false | 46 | not_evaluable | n/a | 5.0622 | [result](trials/trial-004/result.yml) |
| trial-005 | infrastructure_failed | false | 0 | not_evaluable | n/a | 0.0000 | [result](trials/trial-005/result.yml) |
