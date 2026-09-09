# Achilles

- Target: `T-0005`
- Success rate: 66.7%
- Counted questions by run: trial-001=6, trial-002=8, trial-003=40 (ask_after_question_limit)
- Counted questions (scoring-eligible): average `18` · minimum `6` · median `8` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0029` · Oracle `0.1063` · Verifier `0.0002` · Total `0.1094`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 44 reviewed · agreement `95.4%` · 2 disagreement(s) / 2 Judge call(s) · 2 Oracle answer(s) changed (`100.0%`) · QC cost `0.1099` USD
- Oracle disagreement by question type: `negation` 0/1 (`0.0%`) · `other` 2/43 (`4.6%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | success | true | 6 | clean (100.0%) | 0 | 0.0176 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 8 | clean (100.0%) | 0 | 0.0246 | [result](trials/trial-002/result.yml) |
| trial-003 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | clean (100.0%) | 0 | 0.2860 | [result](trials/trial-003/result.yml) |
