# Bike pump

- Target: `T-0008`
- Success rate: 33.3%
- Counted questions by run: trial-001=40 (invalid_guesser_output), trial-002=33, trial-003=40 (ask_after_question_limit)
- Counted questions (scoring-eligible): average `37.67` · minimum `33` · median `40` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0162` · Oracle `0.2176` · Verifier `0.0005` · Total `0.2343`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `breached` · compliance `99.1%` · 1 violation(s) across 1 trial(s) · 0 counted-turn penalties
- Oracle quality control: 68 reviewed · agreement `80.9%` · 13 disagreement(s) / 13 Judge call(s) · 7 Oracle answer(s) changed (`53.8%`) · QC cost `0.3589` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 13/67 (`19.4%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | guesser_protocol_failure (invalid_guesser_output) | false | 40 | breached (97.6%) | 1 | 0.3048 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 33 | clean (100.0%) | 0 | 0.1905 | [result](trials/trial-002/result.yml) |
| trial-003 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | clean (100.0%) | 0 | 0.2078 | [result](trials/trial-003/result.yml) |
