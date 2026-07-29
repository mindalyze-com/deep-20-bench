# Garfield

- Target: `T-0004`
- Success rate: 80.0%
- Counted questions by run: trial-001=8, trial-002=19, trial-003=6, trial-004=31 (consecutive_contract_violations_exhausted), trial-005=15
- Counted questions (scoring-eligible): average `15.8` · minimum `6` · median `15` · maximum `31`
- Average cost per terminal run (USD): Guesser `0.0506` · Oracle `0.1151` · Verifier `0.0004` · Total `0.1661`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `breached` · compliance `86.7%` · 11 violation(s) across 1 trial(s) · 11 counted-turn penalties
- Oracle quality control: 63 reviewed · agreement `93.6%` · 4 disagreement(s) / 4 Judge call(s) · 1 Oracle answer(s) changed (`25.0%`) · QC cost `0.1276` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 4/62 (`6.4%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 8 | clean (100.0%) | 0 | 0.0477 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 19 | clean (100.0%) | 0 | 0.2793 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 6 | clean (100.0%) | 0 | 0.0463 | [result](trials/trial-003/result.yml) |
| trial-004 | guesser_protocol_failure (consecutive_contract_violations_exhausted) | false | 31 | breached (64.5%) | 11 | 0.3272 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 15 | clean (100.0%) | 0 | 0.1302 | [result](trials/trial-005/result.yml) |
