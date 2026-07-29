# Albert Schweitzer

- Target: `T-0002`
- Success rate: 60.0%
- Counted questions by run: trial-001=20, trial-002=50 (ask_after_question_limit), trial-003=50 (ask_after_question_limit), trial-004=35, trial-005=30
- Counted questions (scoring-eligible): average `37` · minimum `20` · median `35` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.0419` · Oracle `0.3585` · Verifier `0.0003` · Total `0.4007`
- Output-contract reliability: `breached` · compliance `99.5%` · 1 violation(s) across 1 trial(s) · 1 counted-turn penalties
- Oracle quality control: 179 reviewed · agreement `77.1%` · 41 disagreement(s) / 41 Judge call(s) · 2 Oracle answer(s) changed (`4.9%`) · QC cost `0.7200` USD
- Oracle disagreement by question type: `other` 39/170 (`22.9%`) · `temporal_comparison` 2/9 (`22.2%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 20 | clean (100.0%) | 0 | 0.1553 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | breached (98.0%) | 1 | 0.5579 | [result](trials/trial-002/result.yml) |
| trial-003 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 0.5271 | [result](trials/trial-003/result.yml) |
| trial-004 | success | true | 35 | clean (100.0%) | 0 | 0.4303 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 30 | clean (100.0%) | 0 | 0.3328 | [result](trials/trial-005/result.yml) |
