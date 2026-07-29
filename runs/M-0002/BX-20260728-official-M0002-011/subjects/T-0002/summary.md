# Albert Schweitzer

- Target: `T-0002`
- Success rate: 80.0%
- Counted questions by run: trial-001=17, trial-002=38, trial-003=17, trial-004=50 (ask_after_question_limit), trial-005=11
- Counted questions (scoring-eligible): average `26.6` · minimum `11` · median `17` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.1049` · Oracle `0.2097` · Verifier `0.0003` · Total `0.3149`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `breached` · compliance `79.7%` · 28 violation(s) across 4 trial(s) · 28 counted-turn penalties
- Oracle quality control: 97 reviewed · agreement `71.1%` · 28 disagreement(s) / 28 Judge call(s) · 1 Oracle answer(s) changed (`3.6%`) · QC cost `0.4746` USD
- Oracle disagreement by question type: `other` 28/93 (`30.1%`) · `temporal_comparison` 0/4 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 17 | breached (94.4%) | 1 | 0.2350 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 38 | breached (74.4%) | 10 | 0.4745 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 17 | breached (88.9%) | 2 | 0.1618 | [result](trials/trial-003/result.yml) |
| trial-004 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | breached (70.6%) | 15 | 0.5953 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 11 | clean (100.0%) | 0 | 0.1079 | [result](trials/trial-005/result.yml) |
