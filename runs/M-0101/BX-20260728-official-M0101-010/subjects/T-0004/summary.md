# Garfield

- Target: `T-0004`
- Success rate: 60.0%
- Counted questions by run: trial-001=38, trial-002=50, trial-003=28, trial-004=50 (ask_after_question_limit), trial-005=11
- Counted questions (scoring-eligible): average `35.4` · minimum `11` · median `38` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.0305` · Oracle `0.3654` · Verifier `0.0007` · Total `0.3966`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 149 reviewed · agreement `83.9%` · 24 disagreement(s) / 24 Judge call(s) · 3 Oracle answer(s) changed (`12.5%`) · QC cost `0.4849` USD
- Oracle disagreement by question type: `negation` 1/3 (`33.3%`) · `other` 23/144 (`16.0%`) · `temporal_comparison` 0/2 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 38 | clean (100.0%) | 0 | 0.3951 | [result](trials/trial-001/result.yml) |
| trial-002 | limit_exhausted | false | 50 | clean (100.0%) | 0 | 0.5409 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 28 | clean (100.0%) | 0 | 0.3383 | [result](trials/trial-003/result.yml) |
| trial-004 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 0.6225 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 11 | clean (100.0%) | 0 | 0.0862 | [result](trials/trial-005/result.yml) |
