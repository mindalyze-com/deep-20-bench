# Bike pump

- Target: `T-0008`
- Success rate: 0.0%
- Counted questions by run: trial-001=40 (invalid_guesser_output), trial-002=40 (ask_after_question_limit), trial-003=40 (invalid_guesser_output)
- Counted questions (scoring-eligible): average `40` · minimum `40` · median `40` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.1658` · Oracle `0.1452` · Verifier `0.0001` · Total `0.3111`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `breached` · compliance `81.3%` · 23 violation(s) across 3 trial(s) · 21 counted-turn penalties
- Oracle quality control: 88 reviewed · agreement `96.6%` · 3 disagreement(s) / 3 Judge call(s) · 1 Oracle answer(s) changed (`33.3%`) · QC cost `0.1629` USD
- Oracle disagreement by question type: `other` 3/88 (`3.4%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | guesser_protocol_failure (invalid_guesser_output) | false | 40 | breached (78.0%) | 9 | 0.3040 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | breached (82.9%) | 7 | 0.3147 | [result](trials/trial-002/result.yml) |
| trial-003 | guesser_protocol_failure (invalid_guesser_output) | false | 40 | breached (82.9%) | 7 | 0.3145 | [result](trials/trial-003/result.yml) |
