# Garfield

- Target: `T-0004`
- Success rate: 75.0%
- Counted questions by run: trial-001=11, trial-002=50, trial-003=23, trial-004=14 (infrastructure failed), trial-005=15
- Counted questions (scoring-eligible): average `24.75` · minimum `11` · median `19` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.0095` · Oracle `0.0856` · Verifier `0.0009` · Total `0.0960`
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 11 | clean (100.0%) | 0 | 0.0400 | [result](trials/trial-001/result.yml) |
| trial-002 | limit_exhausted | false | 50 | clean (100.0%) | 0 | 0.2166 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 23 | clean (100.0%) | 0 | 0.1093 | [result](trials/trial-003/result.yml) |
| trial-004 | infrastructure_failed | false | 14 | not_evaluable | n/a | 0.0517 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 15 | clean (100.0%) | 0 | 0.0624 | [result](trials/trial-005/result.yml) |
