# Garfield

- Target: `T-0004`
- Success rate: 80.0%
- Counted questions by run: trial-001=18, trial-002=50 (ask_after_question_limit), trial-003=27, trial-004=20, trial-005=12
- Counted questions (scoring-eligible): average `25.4` · minimum `12` · median `20` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.1839` · Oracle `0.1164` · Verifier `0.0003` · Total `0.3006`
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 18 | clean (100.0%) | 0 | 0.1364 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 0.8537 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 27 | clean (100.0%) | 0 | 0.2438 | [result](trials/trial-003/result.yml) |
| trial-004 | success | true | 20 | clean (100.0%) | 0 | 0.1912 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 12 | clean (100.0%) | 0 | 0.0781 | [result](trials/trial-005/result.yml) |
