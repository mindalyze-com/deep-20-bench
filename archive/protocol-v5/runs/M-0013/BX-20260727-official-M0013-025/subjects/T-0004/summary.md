# Garfield

- Target: `T-0004`
- Success rate: 50.0%
- Counted questions by run: trial-001=16, trial-002=23 (infrastructure failed), trial-003=50 (ask_after_question_limit), trial-004=3 (infrastructure failed), trial-005=11 (infrastructure failed)
- Counted questions (scoring-eligible): average `33` · minimum `16` · median `33` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.0726` · Oracle `0.1136` · Verifier `0.0001` · Total `0.1862`
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 16 | clean (100.0%) | 0 | 0.0656 | [result](trials/trial-001/result.yml) |
| trial-002 | infrastructure_failed | false | 23 | not_evaluable | n/a | 0.1359 | [result](trials/trial-002/result.yml) |
| trial-003 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 0.6707 | [result](trials/trial-003/result.yml) |
| trial-004 | infrastructure_failed | false | 3 | not_evaluable | n/a | 0.0118 | [result](trials/trial-004/result.yml) |
| trial-005 | infrastructure_failed | false | 11 | not_evaluable | n/a | 0.0472 | [result](trials/trial-005/result.yml) |
