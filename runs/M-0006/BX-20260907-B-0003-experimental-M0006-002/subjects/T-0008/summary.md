# Bike pump

- Target: `T-0008`
- Success rate: 33.3%
- Counted questions by run: trial-001=39, trial-002=40, trial-003=40 (ask_after_question_limit)
- Counted questions (scoring-eligible): average `39.67` · minimum `39` · median `40` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.2254` · Oracle `0.2501` · Verifier `0.0003` · Total `0.4758`
- Superseded infrastructure attempts: 3 across 3 trial(s) · cost `0.1523` USD
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 89 reviewed · agreement `85.4%` · 13 disagreement(s) / 13 Judge call(s) · 11 Oracle answer(s) changed (`84.6%`) · QC cost `0.3990` USD
- Oracle disagreement by question type: `other` 13/89 (`14.6%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 39 | clean (100.0%) | 0 | 0.3592 | [result](trials/trial-001/result.yml) |
| trial-002 | limit_exhausted | false | 40 | clean (100.0%) | 0 | 0.6069 | [result](trials/trial-002/result.yml) |
| trial-003 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | clean (100.0%) | 0 | 0.4614 | [result](trials/trial-003/result.yml) |
