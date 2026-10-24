# Albert Schweitzer

- Target: `T-0002`
- Success rate: 66.7%
- Counted questions by run: trial-001=16, trial-002=40 (ask_after_question_limit), trial-003=19
- Counted questions (scoring-eligible): average `25` · minimum `16` · median `19` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0063` · Oracle `0.1327` · Verifier `0.0003` · Total `0.1393`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 67 reviewed · agreement `92.5%` · 5 disagreement(s) / 5 Judge call(s) · 5 Oracle answer(s) changed (`100.0%`) · QC cost `0.2144` USD
- Oracle disagreement by question type: `other` 3/60 (`5.0%`) · `temporal_comparison` 2/7 (`28.6%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 16 | clean (100.0%) | 0 | 0.0669 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | clean (100.0%) | 0 | 0.2375 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 19 | clean (100.0%) | 0 | 0.1134 | [result](trials/trial-003/result.yml) |
