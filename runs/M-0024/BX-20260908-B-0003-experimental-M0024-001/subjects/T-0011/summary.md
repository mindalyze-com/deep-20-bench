# Moon

- Target: `T-0011`
- Success rate: 66.7%
- Counted questions by run: trial-001=34, trial-002=40 (ask_after_question_limit), trial-003=21
- Counted questions (scoring-eligible): average `31.67` · minimum `21` · median `34` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0061` · Oracle `0.0653` · Verifier `0.0009` · Total `0.0723`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `breached` · compliance `98.0%` · 2 violation(s) across 2 trial(s) · 2 counted-turn penalties
- Oracle quality control: 55 reviewed · agreement `100.0%` · 0 disagreement(s) / 0 Judge call(s) · 0 Oracle answer(s) changed (`n/a`) · QC cost `0.0629` USD
- Oracle disagreement by question type: `negation` 0/2 (`0.0%`) · `other` 0/48 (`0.0%`) · `quantitative_comparison` 0/2 (`0.0%`) · `temporal_comparison` 0/3 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 34 | breached (97.1%) | 1 | 0.0997 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | breached (97.6%) | 1 | 0.0643 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 21 | clean (100.0%) | 0 | 0.0530 | [result](trials/trial-003/result.yml) |
