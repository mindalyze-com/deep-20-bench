# Garfield

- Target: `T-0004`
- Success rate: 80.0%
- Counted questions by run: trial-001=25, trial-002=50 (ask_after_question_limit), trial-003=21, trial-004=16, trial-005=21
- Counted questions (scoring-eligible): average `26.6` · minimum `16` · median `21` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.0302` · Oracle `0.2317` · Verifier `0.0002` · Total `0.2622`
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 125 reviewed · agreement `90.4%` · 12 disagreement(s) / 12 Judge call(s) · 3 Oracle answer(s) changed (`25.0%`) · QC cost `0.2778` USD
- Oracle disagreement by question type: `negation` 1/3 (`33.3%`) · `other` 10/115 (`8.7%`) · `temporal_comparison` 1/7 (`14.3%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 25 | clean (100.0%) | 0 | 0.1810 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 0.6853 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 21 | clean (100.0%) | 0 | 0.1425 | [result](trials/trial-003/result.yml) |
| trial-004 | success | true | 16 | clean (100.0%) | 0 | 0.1163 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 21 | clean (100.0%) | 0 | 0.1858 | [result](trials/trial-005/result.yml) |
