# Garfield

- Target: `T-0004`
- Success rate: 40.0%
- Counted questions by run: trial-001=20, trial-002=50, trial-003=50, trial-004=14, trial-005=50 (ask_after_question_limit)
- Counted questions (scoring-eligible): average `36.8` · minimum `14` · median `50` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.0012` · Oracle `0.1696` · Verifier `0.0037` · Total `0.1746`
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 20 | clean (100.0%) | 0 | 0.0988 | [result](trials/trial-001/result.yml) |
| trial-002 | limit_exhausted | false | 50 | clean (100.0%) | 0 | 0.2589 | [result](trials/trial-002/result.yml) |
| trial-003 | limit_exhausted | false | 50 | clean (100.0%) | 0 | 0.0607 | [result](trials/trial-003/result.yml) |
| trial-004 | success | true | 14 | clean (100.0%) | 0 | 0.0672 | [result](trials/trial-004/result.yml) |
| trial-005 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 0.3873 | [result](trials/trial-005/result.yml) |
