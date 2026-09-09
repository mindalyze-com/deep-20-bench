# Albert Schweitzer

- Target: `T-0002`
- Success rate: 33.3%
- Counted questions by run: trial-001=40 (ask_after_question_limit), trial-002=19, trial-003=40 (ask_after_question_limit)
- Counted questions (scoring-eligible): average `33` · minimum `19` · median `40` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0159` · Oracle `0.1219` · Verifier `0.0009` · Total `0.1387`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `breached` · compliance `99.0%` · 1 violation(s) across 1 trial(s) · 1 counted-turn penalties
- Oracle quality control: 70 reviewed · agreement `97.1%` · 2 disagreement(s) / 2 Judge call(s) · 1 Oracle answer(s) changed (`50.0%`) · QC cost `0.1485` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 2/66 (`3.0%`) · `quantitative_comparison` 0/1 (`0.0%`) · `temporal_comparison` 0/2 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | clean (100.0%) | 0 | 0.1978 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 19 | clean (100.0%) | 0 | 0.0901 | [result](trials/trial-002/result.yml) |
| trial-003 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | breached (97.6%) | 1 | 0.1282 | [result](trials/trial-003/result.yml) |
