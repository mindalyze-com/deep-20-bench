# Stephen King

- Target: `T-0003`
- Success rate: 60.0%
- Counted questions by run: trial-001=42, trial-002=17, trial-003=19, trial-004=50 (ask_after_question_limit), trial-005=50 (ask_after_question_limit)
- Counted questions (scoring-eligible): average `35.6` · minimum `17` · median `42` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.1203` · Oracle `0.3235` · Verifier `0.0004` · Total `0.4442`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 169 reviewed · agreement `81.7%` · 31 disagreement(s) / 31 Judge call(s) · 2 Oracle answer(s) changed (`6.4%`) · QC cost `0.5942` USD
- Oracle disagreement by question type: `negation` 3/6 (`50.0%`) · `other` 27/160 (`16.9%`) · `temporal_comparison` 1/3 (`33.3%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 42 | clean (100.0%) | 0 | 0.5811 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 17 | clean (100.0%) | 0 | 0.1562 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 19 | clean (100.0%) | 0 | 0.2099 | [result](trials/trial-003/result.yml) |
| trial-004 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 0.7107 | [result](trials/trial-004/result.yml) |
| trial-005 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 0.5630 | [result](trials/trial-005/result.yml) |
