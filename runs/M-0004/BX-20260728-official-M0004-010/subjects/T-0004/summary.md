# Garfield

- Target: `T-0004`
- Success rate: 80.0%
- Counted questions by run: trial-001=22, trial-002=50 (ask_after_question_limit), trial-003=12, trial-004=43, trial-005=40
- Counted questions (scoring-eligible): average `33.4` · minimum `12` · median `40` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.7201` · Oracle `0.2421` · Verifier `0.0006` · Total `0.9628`
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 153 reviewed · agreement `94.8%` · 8 disagreement(s) / 8 Judge call(s) · 2 Oracle answer(s) changed (`25.0%`) · QC cost `0.2397` USD
- Oracle disagreement by question type: `other` 8/138 (`5.8%`) · `temporal_comparison` 0/15 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 22 | clean (100.0%) | 0 | 0.3819 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | clean (100.0%) | 0 | 1.2163 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 12 | clean (100.0%) | 0 | 0.1163 | [result](trials/trial-003/result.yml) |
| trial-004 | success | true | 43 | clean (100.0%) | 0 | 1.3270 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 40 | clean (100.0%) | 0 | 1.7725 | [result](trials/trial-005/result.yml) |
