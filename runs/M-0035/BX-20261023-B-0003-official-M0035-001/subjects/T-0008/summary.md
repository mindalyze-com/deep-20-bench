# Bike pump

- Target: `T-0008`
- Success rate: 33.3%
- Counted questions by run: trial-001=40 (ask_after_question_limit), trial-002=40 (ask_after_question_limit), trial-003=31
- Counted questions (scoring-eligible): average `37` · minimum `31` · median `40` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0092` · Oracle `0.1973` · Verifier `0.0004` · Total `0.2068`
- Superseded infrastructure attempts: 1 across 1 trial(s) · cost `0.1189` USD
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 97 reviewed · agreement `90.7%` · 9 disagreement(s) / 9 Judge call(s) · 7 Oracle answer(s) changed (`77.8%`) · QC cost `0.3181` USD
- Oracle disagreement by question type: `other` 9/97 (`9.3%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | clean (100.0%) | 0 | 0.2585 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | clean (100.0%) | 0 | 0.2041 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 31 | clean (100.0%) | 0 | 0.1579 | [result](trials/trial-003/result.yml) |
