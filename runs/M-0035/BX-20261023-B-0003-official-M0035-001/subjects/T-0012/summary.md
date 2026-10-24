# Door handle

- Target: `T-0012`
- Success rate: 33.3%
- Counted questions by run: trial-001=40, trial-002=40 (ask_after_question_limit), trial-003=25
- Counted questions (scoring-eligible): average `35` · minimum `25` · median `40` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0089` · Oracle `0.1690` · Verifier `0.0001` · Total `0.1781`
- Superseded infrastructure attempts: 1 across 1 trial(s) · cost `0.0763` USD
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 95 reviewed · agreement `95.8%` · 4 disagreement(s) / 4 Judge call(s) · 3 Oracle answer(s) changed (`75.0%`) · QC cost `0.2042` USD
- Oracle disagreement by question type: `other` 4/95 (`4.2%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | limit_exhausted | false | 40 | clean (100.0%) | 0 | 0.2461 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | clean (100.0%) | 0 | 0.1918 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 25 | clean (100.0%) | 0 | 0.0964 | [result](trials/trial-003/result.yml) |
