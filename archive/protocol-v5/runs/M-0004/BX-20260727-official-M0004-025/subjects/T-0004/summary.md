# Garfield

- Target: `T-0004`
- Success rate: 80.0%
- Counted questions by run: trial-001=18, trial-002=50 (ask_after_question_limit), trial-003=10, trial-004=28, trial-005=13
- Counted questions (scoring-eligible): average `23.8` · minimum `10` · median `18` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.0269` · Oracle `0.1203` · Verifier `0.0007` · Total `0.1479`
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 18 | clean (100.0%) | 0 | 0.0877 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 0.3700 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 10 | clean (100.0%) | 0 | 0.0496 | [result](trials/trial-003/result.yml) |
| trial-004 | success | true | 28 | clean (100.0%) | 0 | 0.1808 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 13 | clean (100.0%) | 0 | 0.0514 | [result](trials/trial-005/result.yml) |
