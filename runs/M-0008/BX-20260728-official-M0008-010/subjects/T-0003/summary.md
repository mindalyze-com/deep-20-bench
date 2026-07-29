# Stephen King

- Target: `T-0003`
- Success rate: 60.0%
- Counted questions by run: trial-001=50 (ask_after_question_limit), trial-002=15, trial-003=15, trial-004=50 (ask_after_question_limit), trial-005=14
- Counted questions (scoring-eligible): average `28.8` · minimum `14` · median `15` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.0626` · Oracle `0.2528` · Verifier `0.0004` · Total `0.3157`
- Output-contract reliability: `breached` · compliance `98.0%` · 3 violation(s) across 2 trial(s) · 3 counted-turn penalties
- Oracle quality control: 121 reviewed · agreement `85.1%` · 18 disagreement(s) / 18 Judge call(s) · 2 Oracle answer(s) changed (`11.1%`) · QC cost `0.3809` USD
- Oracle disagreement by question type: `other` 18/116 (`15.5%`) · `quantitative_comparison` 0/3 (`0.0%`) · `temporal_comparison` 0/2 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | breached (98.0%) | 1 | 0.6229 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 15 | clean (100.0%) | 0 | 0.1011 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 15 | breached (87.5%) | 2 | 0.1171 | [result](trials/trial-003/result.yml) |
| trial-004 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 0.6237 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 14 | clean (100.0%) | 0 | 0.1140 | [result](trials/trial-005/result.yml) |
