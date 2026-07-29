# Achilles

- Target: `T-0005`
- Success rate: 60.0%
- Counted questions by run: trial-001=4, trial-002=13, trial-003=20, trial-004=50 (ask_after_question_limit), trial-005=50
- Counted questions (scoring-eligible): average `27.4` · minimum `4` · median `20` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.0009` · Oracle `0.0905` · Verifier `0.0032` · Total `0.0946`
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 4 | clean (100.0%) | 0 | 0.0157 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 13 | clean (100.0%) | 0 | 0.0353 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 20 | clean (100.0%) | 0 | 0.0624 | [result](trials/trial-003/result.yml) |
| trial-004 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 0.1973 | [result](trials/trial-004/result.yml) |
| trial-005 | limit_exhausted | false | 50 | clean (100.0%) | 0 | 0.1624 | [result](trials/trial-005/result.yml) |
