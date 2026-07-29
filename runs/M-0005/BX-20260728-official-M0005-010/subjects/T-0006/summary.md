# Genghis Khan

- Target: `T-0006`
- Success rate: 100.0%
- Counted questions by run: trial-001=9, trial-002=10, trial-003=12, trial-004=18, trial-005=17
- Counted questions (scoring-eligible): average `13.2` · minimum `9` · median `12` · maximum `18`
- Average cost per terminal run (USD): Guesser `0.0232` · Oracle `0.1002` · Verifier `0.0003` · Total `0.1237`
- Output-contract reliability: `breached` · compliance `98.6%` · 1 violation(s) across 1 trial(s) · 1 counted-turn penalties
- Oracle quality control: 63 reviewed · agreement `90.5%` · 6 disagreement(s) / 6 Judge call(s) · 3 Oracle answer(s) changed (`50.0%`) · QC cost `0.1477` USD
- Oracle disagreement by question type: `negation` 0/2 (`0.0%`) · `other` 6/54 (`11.1%`) · `temporal_comparison` 0/7 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 9 | clean (100.0%) | 0 | 0.0594 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 10 | clean (100.0%) | 0 | 0.0987 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 12 | clean (100.0%) | 0 | 0.1278 | [result](trials/trial-003/result.yml) |
| trial-004 | success | true | 18 | clean (100.0%) | 0 | 0.1962 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 17 | breached (94.4%) | 1 | 0.1366 | [result](trials/trial-005/result.yml) |
