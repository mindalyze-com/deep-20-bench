# Albert Schweitzer

- Target: `T-0002`
- Success rate: 40.0%
- Counted questions by run: trial-001=50 (ask_after_question_limit), trial-002=27, trial-003=50 (ask_after_question_limit), trial-004=50 (ask_after_question_limit), trial-005=26
- Counted questions (scoring-eligible): average `40.6` · minimum `26` · median `50` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.0000` · Oracle `0.8613` · Verifier `0.0002` · Total `0.8615`
- Superseded infrastructure attempts: 1 across 1 trial(s) · cost `0.3074` USD
- Output-contract reliability: `breached` · compliance `96.2%` · 8 violation(s) across 5 trial(s) · 8 counted-turn penalties
- Oracle quality control: 175 reviewed · agreement `60.0%` · 70 disagreement(s) / 70 Judge call(s) · 0 Oracle answer(s) changed (`0.0%`) · QC cost `1.1379` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 69/164 (`42.1%`) · `temporal_comparison` 1/10 (`10.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | breached (96.1%) | 2 | 1.1202 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 27 | breached (96.4%) | 1 | 0.5369 | [result](trials/trial-002/result.yml) |
| trial-003 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | breached (94.1%) | 3 | 1.1308 | [result](trials/trial-003/result.yml) |
| trial-004 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | breached (98.0%) | 1 | 0.9942 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 26 | breached (96.3%) | 1 | 0.5254 | [result](trials/trial-005/result.yml) |
