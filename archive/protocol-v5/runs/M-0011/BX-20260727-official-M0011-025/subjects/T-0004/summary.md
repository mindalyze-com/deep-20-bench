# Garfield

- Target: `T-0004`
- Success rate: 100.0%
- Counted questions by run: trial-001=10, trial-002=8, trial-003=10, trial-004=30 (infrastructure failed), trial-005=10
- Counted questions (scoring-eligible): average `9.5` · minimum `8` · median `10` · maximum `10`
- Average cost per terminal run (USD): Guesser `0.2670` · Oracle `0.0628` · Verifier `0.0004` · Total `0.3303`
- Output-contract reliability: `breached` · compliance `95.2%` · 2 violation(s) across 1 trial(s) · 2 counted-turn penalties
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 10 | breached (81.8%) | 2 | 0.1058 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 8 | clean (100.0%) | 0 | 0.1115 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 10 | clean (100.0%) | 0 | 0.1342 | [result](trials/trial-003/result.yml) |
| trial-004 | infrastructure_failed | false | 30 | not_evaluable | n/a | 1.2186 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 10 | clean (100.0%) | 0 | 0.0812 | [result](trials/trial-005/result.yml) |
