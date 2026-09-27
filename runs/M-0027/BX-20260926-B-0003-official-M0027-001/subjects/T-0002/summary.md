# Albert Schweitzer

- Target: `T-0002`
- Success rate: 33.3%
- Counted questions by run: trial-001=40 (ask_after_question_limit), trial-002=40 (ask_after_question_limit), trial-003=33
- Counted questions (scoring-eligible): average `37.67` · minimum `33` · median `40` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0859` · Oracle `0.2809` · Verifier `0.0001` · Total `0.3669`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 95 reviewed · agreement `85.3%` · 14 disagreement(s) / 14 Judge call(s) · 8 Oracle answer(s) changed (`57.1%`) · QC cost `0.4995` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 14/90 (`15.6%`) · `temporal_comparison` 0/4 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | clean (100.0%) | 0 | 0.5002 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | clean (100.0%) | 0 | 0.3664 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 33 | clean (100.0%) | 0 | 0.2342 | [result](trials/trial-003/result.yml) |
