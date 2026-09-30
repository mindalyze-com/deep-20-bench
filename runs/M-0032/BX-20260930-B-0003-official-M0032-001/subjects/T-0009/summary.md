# Spider web

- Target: `T-0009`
- Success rate: 66.7%
- Counted questions by run: trial-001=21, trial-002=40, trial-003=22
- Counted questions (scoring-eligible): average `27.67` · minimum `21` · median `22` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.1050` · Oracle `0.1217` · Verifier `0.0006` · Total `0.2273`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 71 reviewed · agreement `94.4%` · 4 disagreement(s) / 4 Judge call(s) · 3 Oracle answer(s) changed (`75.0%`) · QC cost `0.1799` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 4/69 (`5.8%`) · `temporal_comparison` 0/1 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 21 | clean (100.0%) | 0 | 0.1236 | [result](trials/trial-001/result.yml) |
| trial-002 | limit_exhausted | false | 40 | clean (100.0%) | 0 | 0.3771 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 22 | clean (100.0%) | 0 | 0.1812 | [result](trials/trial-003/result.yml) |
