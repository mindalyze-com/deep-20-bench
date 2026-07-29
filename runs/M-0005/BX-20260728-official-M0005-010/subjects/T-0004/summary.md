# Garfield

- Target: `T-0004`
- Success rate: 60.0%
- Counted questions by run: trial-001=47, trial-002=27, trial-003=50 (ask_after_question_limit), trial-004=50 (ask_after_question_limit), trial-005=15
- Counted questions (scoring-eligible): average `37.8` · minimum `15` · median `47` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.3406` · Oracle `0.2795` · Verifier `0.0015` · Total `0.6216`
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 142 reviewed · agreement `96.5%` · 5 disagreement(s) / 5 Judge call(s) · 2 Oracle answer(s) changed (`40.0%`) · QC cost `0.2292` USD
- Oracle disagreement by question type: `negation` 0/7 (`0.0%`) · `other` 5/134 (`3.7%`) · `temporal_comparison` 0/1 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 47 | clean (100.0%) | 0 | 0.6945 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 27 | clean (100.0%) | 0 | 0.2781 | [result](trials/trial-002/result.yml) |
| trial-003 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 0.9837 | [result](trials/trial-003/result.yml) |
| trial-004 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 1.0394 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 15 | clean (100.0%) | 0 | 0.1122 | [result](trials/trial-005/result.yml) |
