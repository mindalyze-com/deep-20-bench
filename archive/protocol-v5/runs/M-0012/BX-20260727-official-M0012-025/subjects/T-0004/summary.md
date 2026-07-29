# Garfield

- Target: `T-0004`
- Success rate: 60.0%
- Counted questions by run: trial-001=10, trial-002=50 (ask_after_question_limit), trial-003=50 (ask_after_question_limit), trial-004=11, trial-005=25
- Counted questions (scoring-eligible): average `29.2` · minimum `10` · median `25` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.0715` · Oracle `0.1434` · Verifier `0.0003` · Total `0.2153`
- Output-contract reliability: `breached` · compliance `98.7%` · 2 violation(s) across 2 trial(s) · 2 counted-turn penalties
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 10 | clean (100.0%) | 0 | 0.0617 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | breached (98.0%) | 1 | 0.4269 | [result](trials/trial-002/result.yml) |
| trial-003 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 0.3762 | [result](trials/trial-003/result.yml) |
| trial-004 | success | true | 11 | clean (100.0%) | 0 | 0.0649 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 25 | breached (96.2%) | 1 | 0.1468 | [result](trials/trial-005/result.yml) |
