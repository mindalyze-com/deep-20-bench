# Spider web

- Target: `T-0009`
- Success rate: 0.0%
- Counted questions by run: trial-001=40, trial-002=40 (ask_after_question_limit), trial-003=40
- Counted questions (scoring-eligible): average `40` · minimum `40` · median `40` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0077` · Oracle `0.2946` · Verifier `0.0007` · Total `0.3030`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 102 reviewed · agreement `84.3%` · 16 disagreement(s) / 16 Judge call(s) · 12 Oracle answer(s) changed (`75.0%`) · QC cost `0.5377` USD
- Oracle disagreement by question type: `negation` 1/5 (`20.0%`) · `other` 15/97 (`15.5%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | limit_exhausted | false | 40 | clean (100.0%) | 0 | 0.3302 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | clean (100.0%) | 0 | 0.3630 | [result](trials/trial-002/result.yml) |
| trial-003 | limit_exhausted | false | 40 | clean (100.0%) | 0 | 0.2158 | [result](trials/trial-003/result.yml) |
