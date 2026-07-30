# Garfield

- Target: `T-0004`
- Success rate: 60.0%
- Counted questions by run: trial-001=21, trial-002=36, trial-003=50 (ask_after_question_limit), trial-004=19, trial-005=50 (ask_after_question_limit)
- Counted questions (scoring-eligible): average `35.2` · minimum `19` · median `36` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.0925` · Oracle `0.2889` · Verifier `0.0004` · Total `0.3819`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 160 reviewed · agreement `93.1%` · 11 disagreement(s) / 11 Judge call(s) · 7 Oracle answer(s) changed (`63.6%`) · QC cost `0.3257` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 11/157 (`7.0%`) · `temporal_comparison` 0/2 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 21 | clean (100.0%) | 0 | 0.1868 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 36 | clean (100.0%) | 0 | 0.2832 | [result](trials/trial-002/result.yml) |
| trial-003 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 0.6125 | [result](trials/trial-003/result.yml) |
| trial-004 | success | true | 19 | clean (100.0%) | 0 | 0.1876 | [result](trials/trial-004/result.yml) |
| trial-005 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 0.6391 | [result](trials/trial-005/result.yml) |
