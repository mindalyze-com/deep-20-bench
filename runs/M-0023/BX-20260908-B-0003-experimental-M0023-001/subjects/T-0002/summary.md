# Albert Schweitzer

- Target: `T-0002`
- Success rate: 66.7%
- Counted questions by run: trial-001=40 (ask_after_question_limit), trial-002=17, trial-003=40
- Counted questions (scoring-eligible): average `32.33` · minimum `17` · median `40` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0023` · Oracle `0.1534` · Verifier `0.0005` · Total `0.1562`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `breached` · compliance `97.0%` · 3 violation(s) across 3 trial(s) · 3 counted-turn penalties
- Oracle quality control: 75 reviewed · agreement `90.7%` · 7 disagreement(s) / 7 Judge call(s) · 7 Oracle answer(s) changed (`100.0%`) · QC cost `0.2363` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 5/61 (`8.2%`) · `temporal_comparison` 2/13 (`15.4%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | breached (97.6%) | 1 | 0.2751 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 17 | breached (94.4%) | 1 | 0.0419 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 40 | breached (97.6%) | 1 | 0.1515 | [result](trials/trial-003/result.yml) |
