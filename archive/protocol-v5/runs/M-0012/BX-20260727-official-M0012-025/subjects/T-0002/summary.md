# Albert Schweitzer

- Target: `T-0002`
- Success rate: 60.0%
- Counted questions by run: trial-001=32, trial-002=50 (ask_after_question_limit), trial-003=37, trial-004=50 (ask_after_question_limit), trial-005=43
- Counted questions (scoring-eligible): average `42.4` · minimum `32` · median `43` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.1404` · Oracle `0.2093` · Verifier `0.0004` · Total `0.3500`
- Output-contract reliability: `breached` · compliance `98.2%` · 4 violation(s) across 3 trial(s) · 4 counted-turn penalties
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 32 | clean (100.0%) | 0 | 0.2049 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | breached (98.0%) | 1 | 0.5277 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 37 | clean (100.0%) | 0 | 0.2452 | [result](trials/trial-003/result.yml) |
| trial-004 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | breached (98.0%) | 1 | 0.3934 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 43 | breached (95.5%) | 2 | 0.3788 | [result](trials/trial-005/result.yml) |
