# Door handle

- Target: `T-0012`
- Success rate: 66.7%
- Counted questions by run: trial-001=40 (ask_after_question_limit), trial-002=23, trial-003=19
- Counted questions (scoring-eligible): average `27.33` · minimum `19` · median `23` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0013` · Oracle `0.1270` · Verifier `0.0004` · Total `0.1287`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `breached` · compliance `91.8%` · 7 violation(s) across 3 trial(s) · 7 counted-turn penalties
- Oracle quality control: 61 reviewed · agreement `91.8%` · 5 disagreement(s) / 5 Judge call(s) · 0 Oracle answer(s) changed (`0.0%`) · QC cost `0.1809` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 5/60 (`8.3%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | breached (90.2%) | 4 | 0.1981 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 23 | breached (95.8%) | 1 | 0.1339 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 19 | breached (90.0%) | 2 | 0.0542 | [result](trials/trial-003/result.yml) |
