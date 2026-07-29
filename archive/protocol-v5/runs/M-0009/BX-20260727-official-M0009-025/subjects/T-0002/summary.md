# Albert Schweitzer

- Target: `T-0002`
- Success rate: 80.0%
- Counted questions by run: trial-001=50, trial-002=27, trial-003=29, trial-004=50 (ask_after_question_limit), trial-005=38
- Counted questions (scoring-eligible): average `38.8` · minimum `27` · median `38` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.1302` · Oracle `0.1311` · Verifier `0.0006` · Total `0.2619`
- Output-contract reliability: `breached` · compliance `97.0%` · 6 violation(s) across 4 trial(s) · 6 counted-turn penalties
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 50 | breached (98.0%) | 1 | 0.4383 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 27 | clean (100.0%) | 0 | 0.1456 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 29 | breached (96.7%) | 1 | 0.1586 | [result](trials/trial-003/result.yml) |
| trial-004 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | breached (98.0%) | 1 | 0.3623 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 38 | breached (92.3%) | 3 | 0.2049 | [result](trials/trial-005/result.yml) |
