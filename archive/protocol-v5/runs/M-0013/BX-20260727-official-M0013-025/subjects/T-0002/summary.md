# Albert Schweitzer

- Target: `T-0002`
- Success rate: 75.0%
- Counted questions by run: trial-001=41, trial-002=29, trial-003=27 (infrastructure failed), trial-004=50 (ask_after_question_limit), trial-005=40
- Counted questions (scoring-eligible): average `40` · minimum `29` · median `40.5` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.2167` · Oracle `0.1679` · Verifier `0.0009` · Total `0.3856`
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 41 | clean (100.0%) | 0 | 0.4133 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 29 | clean (100.0%) | 0 | 0.2368 | [result](trials/trial-002/result.yml) |
| trial-003 | infrastructure_failed | false | 27 | not_evaluable | n/a | 0.3293 | [result](trials/trial-003/result.yml) |
| trial-004 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 0.4697 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 40 | clean (100.0%) | 0 | 0.4787 | [result](trials/trial-005/result.yml) |
