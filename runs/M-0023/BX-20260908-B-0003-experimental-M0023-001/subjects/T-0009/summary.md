# Spider web

- Target: `T-0009`
- Success rate: 33.3%
- Counted questions by run: trial-001=23, trial-002=40 (ask_after_question_limit), trial-003=40 (ask_after_question_limit)
- Counted questions (scoring-eligible): average `34.33` · minimum `23` · median `40` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0019` · Oracle `0.1631` · Verifier `0.0001` · Total `0.1651`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `breached` · compliance `92.5%` · 8 violation(s) across 3 trial(s) · 8 counted-turn penalties
- Oracle quality control: 81 reviewed · agreement `93.8%` · 5 disagreement(s) / 5 Judge call(s) · 4 Oracle answer(s) changed (`80.0%`) · QC cost `0.2228` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 5/80 (`6.2%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 23 | breached (95.8%) | 1 | 0.1286 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | breached (90.2%) | 4 | 0.1852 | [result](trials/trial-002/result.yml) |
| trial-003 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | breached (92.7%) | 3 | 0.1814 | [result](trials/trial-003/result.yml) |
