# Achilles

- Target: `T-0005`
- Success rate: 80.0%
- Counted questions by run: trial-001=8, trial-002=8, trial-003=50 (ask_after_question_limit), trial-004=19, trial-005=8
- Counted questions (scoring-eligible): average `18.6` · minimum `8` · median `8` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.2307` · Oracle `0.3707` · Verifier `0.0002` · Total `0.6016`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 79 reviewed · agreement `86.1%` · 11 disagreement(s) / 11 Judge call(s) · 4 Oracle answer(s) changed (`36.4%`) · QC cost `0.2558` USD
- Oracle disagreement by question type: `other` 10/76 (`13.2%`) · `temporal_comparison` 1/3 (`33.3%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 8 | clean (100.0%) | 0 | 0.0907 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 8 | clean (100.0%) | 0 | 0.0916 | [result](trials/trial-002/result.yml) |
| trial-003 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 2.3595 | [result](trials/trial-003/result.yml) |
| trial-004 | success | true | 19 | clean (100.0%) | 0 | 0.3755 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 8 | clean (100.0%) | 0 | 0.0904 | [result](trials/trial-005/result.yml) |
