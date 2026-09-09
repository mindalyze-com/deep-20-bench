# Bike pump

- Target: `T-0008`
- Success rate: 33.3%
- Counted questions by run: trial-001=27, trial-002=40, trial-003=40 (ask_after_question_limit)
- Counted questions (scoring-eligible): average `35.67` · minimum `27` · median `40` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0125` · Oracle `0.2061` · Verifier `0.0001` · Total `0.2188`
- Superseded infrastructure attempts: 1 across 1 trial(s) · cost `0.0197` USD
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 95 reviewed · agreement `91.6%` · 8 disagreement(s) / 8 Judge call(s) · 8 Oracle answer(s) changed (`100.0%`) · QC cost `0.3268` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 8/94 (`8.5%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 27 | clean (100.0%) | 0 | 0.1932 | [result](trials/trial-001/result.yml) |
| trial-002 | limit_exhausted | false | 40 | clean (100.0%) | 0 | 0.2157 | [result](trials/trial-002/result.yml) |
| trial-003 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | clean (100.0%) | 0 | 0.2474 | [result](trials/trial-003/result.yml) |
