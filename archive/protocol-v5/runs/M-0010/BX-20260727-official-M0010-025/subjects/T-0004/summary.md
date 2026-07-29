# Garfield

- Target: `T-0004`
- Success rate: 60.0%
- Counted questions by run: trial-001=22, trial-002=50 (ask_after_question_limit), trial-003=12, trial-004=9, trial-005=50 (ask_after_question_limit)
- Counted questions (scoring-eligible): average `28.6` · minimum `9` · median `22` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.2960` · Oracle `0.1340` · Verifier `0.0012` · Total `0.4312`
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 22 | clean (100.0%) | 0 | 0.1882 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 1.1313 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 12 | clean (100.0%) | 0 | 0.0915 | [result](trials/trial-003/result.yml) |
| trial-004 | success | true | 9 | clean (100.0%) | 0 | 0.0654 | [result](trials/trial-004/result.yml) |
| trial-005 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 0.6797 | [result](trials/trial-005/result.yml) |
