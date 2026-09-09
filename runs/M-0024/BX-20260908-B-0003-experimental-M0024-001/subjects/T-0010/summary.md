# Eyebrow

- Target: `T-0010`
- Success rate: 66.7%
- Counted questions by run: trial-001=40 (ask_after_question_limit), trial-002=27, trial-003=27
- Counted questions (scoring-eligible): average `31.33` · minimum `27` · median `27` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0048` · Oracle `0.1325` · Verifier `0.0004` · Total `0.1376`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `clean` · compliance `100.0%` · 0 violation(s) across 0 trial(s) · 0 counted-turn penalties
- Oracle quality control: 73 reviewed · agreement `94.5%` · 4 disagreement(s) / 4 Judge call(s) · 3 Oracle answer(s) changed (`75.0%`) · QC cost `0.1837` USD
- Oracle disagreement by question type: `negation` 0/4 (`0.0%`) · `other` 4/63 (`6.4%`) · `quantitative_comparison` 0/6 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | clean (100.0%) | 0 | 0.1982 | [result](trials/trial-001/result.yml) |
| trial-002 | success | true | 27 | clean (100.0%) | 0 | 0.1146 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 27 | clean (100.0%) | 0 | 0.1000 | [result](trials/trial-003/result.yml) |
