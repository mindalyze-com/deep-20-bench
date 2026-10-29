# Door handle

- Target: `T-0012`
- Success rate: 33.3%
- Counted questions by run: trial-001=40 (ask_after_question_limit), trial-002=40, trial-003=23
- Counted questions (scoring-eligible): average `34.33` · minimum `23` · median `40` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0290` · Oracle `0.1584` · Verifier `0.0002` · Total `0.1876`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `breached` · compliance `99.1%` · 1 violation(s) across 1 trial(s) · 1 counted-turn penalties
- Oracle quality control: 95 reviewed · agreement `95.8%` · 4 disagreement(s) / 4 Judge call(s) · 3 Oracle answer(s) changed (`75.0%`) · QC cost `0.2079` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 4/94 (`4.3%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | breached (97.6%) | 1 | 0.2011 | [result](trials/trial-001/result.yml) |
| trial-002 | limit_exhausted | false | 40 | clean (100.0%) | 0 | 0.2564 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 23 | clean (100.0%) | 0 | 0.1055 | [result](trials/trial-003/result.yml) |
