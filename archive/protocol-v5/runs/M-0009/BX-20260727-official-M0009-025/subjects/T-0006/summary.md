# Genghis Khan

- Target: `T-0006`
- Success rate: 80.0%
- Counted questions by run: trial-001=50 (ask_after_question_limit), trial-002=9, trial-003=13, trial-004=15, trial-005=10
- Counted questions (scoring-eligible): average `19.4` · minimum `9` · median `13` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.0567` · Oracle `0.0726` · Verifier `0.0005` · Total `0.1299`
- Output-contract reliability: `breached` · compliance `98.0%` · 2 violation(s) across 2 trial(s) · 2 counted-turn penalties
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 0.4333 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 9 | clean (100.0%) | 0 | 0.0426 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 13 | breached (92.9%) | 1 | 0.0596 | [result](trials/trial-003/result.yml) |
| trial-004 | success | true | 15 | clean (100.0%) | 0 | 0.0698 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 10 | breached (90.9%) | 1 | 0.0440 | [result](trials/trial-005/result.yml) |
