# Spider web

- Target: `T-0009`
- Success rate: 33.3%
- Counted questions by run: trial-001=37 (consecutive_contract_violations_exhausted), trial-002=40 (consecutive_contract_violations_exhausted), trial-003=24
- Counted questions (scoring-eligible): average `33.67` · minimum `24` · median `37` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.1249` · Oracle `0.1392` · Verifier `0.0002` · Total `0.2643`
- Superseded infrastructure attempts: 1 across 1 trial(s) · cost `0.1243` USD
- Output-contract reliability: `breached` · compliance `87.3%` · 13 violation(s) across 2 trial(s) · 13 counted-turn penalties
- Oracle quality control: 79 reviewed · agreement `96.2%` · 3 disagreement(s) / 3 Judge call(s) · 0 Oracle answer(s) changed (`0.0%`) · QC cost `0.1652` USD
- Oracle disagreement by question type: `other` 3/79 (`3.8%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | guesser_protocol_failure (consecutive_contract_violations_exhausted) | false | 37 | breached (78.4%) | 8 | 0.2992 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (consecutive_contract_violations_exhausted) | false | 40 | breached (87.5%) | 5 | 0.2979 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 24 | clean (100.0%) | 0 | 0.1958 | [result](trials/trial-003/result.yml) |
