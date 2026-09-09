# Genghis Khan

- Target: `T-0006`
- Success rate: 66.7%
- Counted questions by run: trial-001=40 (ask_after_question_limit), trial-002=11, trial-003=36
- Counted questions (scoring-eligible): average `29` · minimum `11` · median `36` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0028` · Oracle `0.1123` · Verifier `0.0004` · Total `0.1155`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `breached` · compliance `93.3%` · 6 violation(s) across 3 trial(s) · 6 counted-turn penalties
- Oracle quality control: 68 reviewed · agreement `97.1%` · 2 disagreement(s) / 2 Judge call(s) · 1 Oracle answer(s) changed (`50.0%`) · QC cost `0.1272` USD
- Oracle disagreement by question type: `other` 2/60 (`3.3%`) · `temporal_comparison` 0/8 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | breached (97.6%) | 1 | 0.1674 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 11 | breached (91.7%) | 1 | 0.0430 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 36 | breached (89.2%) | 4 | 0.1362 | [result](trials/trial-003/result.yml) |
