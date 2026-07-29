# Garfield

- Target: `T-0004`
- Success rate: 80.0%
- Counted questions by run: trial-001=10, trial-002=11, trial-003=50 (ask_after_question_limit), trial-004=9, trial-005=8
- Counted questions (scoring-eligible): average `17.6` · minimum `8` · median `10` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.5660` · Oracle `0.1256` · Verifier `0.0007` · Total `0.6923`
- Output-contract reliability: `breached` · compliance `96.8%` · 3 violation(s) across 2 trial(s) · 3 counted-turn penalties
- Oracle quality control: 65 reviewed · agreement `96.9%` · 2 disagreement(s) / 2 Judge call(s) · 1 Oracle answer(s) changed (`50.0%`) · QC cost `0.0844` USD
- Oracle disagreement by question type: `other` 2/59 (`3.4%`) · `temporal_comparison` 0/6 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 10 | clean (100.0%) | 0 | 0.1258 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 11 | breached (91.7%) | 1 | 0.1332 | [result](trials/trial-002/result.yml) |
| trial-003 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | breached (96.1%) | 2 | 2.9436 | [result](trials/trial-003/result.yml) |
| trial-004 | success | true | 9 | clean (100.0%) | 0 | 0.1448 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 8 | clean (100.0%) | 0 | 0.1144 | [result](trials/trial-005/result.yml) |
