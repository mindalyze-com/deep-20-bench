# Garfield

- Target: `T-0004`
- Success rate: 50.0%
- Counted questions by run: trial-001=25 (infrastructure failed), trial-002=8, trial-003=40
- Counted questions (scoring-eligible): average `24` · minimum `8` · median `24` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.1009` · Oracle `0.1475` · Verifier `0.0001` · Total `0.2485`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 42 reviewed · agreement `92.9%` · 3 disagreement(s) / 3 Judge call(s) · 2 Oracle answer(s) changed (`66.7%`) · QC cost `0.1317` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 3/39 (`7.7%`) · `temporal_comparison` 0/2 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | infrastructure_failed | false | 25 | not_evaluable | n/a | 0.2406 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 8 | clean (100.0%) | 0 | 0.0387 | [result](trials/trial-002/result.yml) |
| trial-003 | limit_exhausted | false | 40 | clean (100.0%) | 0 | 0.4662 | [result](trials/trial-003/result.yml) |
