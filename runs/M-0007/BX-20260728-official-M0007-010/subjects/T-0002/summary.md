# Albert Schweitzer

- Target: `T-0002`
- Success rate: 80.0%
- Counted questions by run: trial-001=15, trial-002=19, trial-003=50 (ask_after_question_limit), trial-004=34, trial-005=17
- Counted questions (scoring-eligible): average `27` · minimum `15` · median `19` · maximum `50`
- Average cost per terminal run (USD): Guesser `0.4938` · Oracle `0.1969` · Verifier `0.0010` · Total `0.6917`
- Output-contract reliability: `breached` · compliance `99.3%` · 1 violation(s) across 1 trial(s) · 1 counted-turn penalties
- Oracle quality control: 109 reviewed · agreement `88.1%` · 13 disagreement(s) / 13 Judge call(s) · 1 Oracle answer(s) changed (`7.7%`) · QC cost `0.2652` USD
- Oracle disagreement by question type: `other` 11/88 (`12.5%`) · `temporal_comparison` 2/21 (`9.5%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 15 | clean (100.0%) | 0 | 0.1875 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 19 | clean (100.0%) | 0 | 0.3581 | [result](trials/trial-002/result.yml) |
| trial-003 | guesser_protocol_failure (ask_after_question_limit) | false | 50 | breached (98.0%) | 1 | 1.4264 | [result](trials/trial-003/result.yml) |
| trial-004 | success | true | 34 | clean (100.0%) | 0 | 1.1944 | [result](trials/trial-004/result.yml) |
| trial-005 | success | true | 17 | clean (100.0%) | 0 | 0.2922 | [result](trials/trial-005/result.yml) |
