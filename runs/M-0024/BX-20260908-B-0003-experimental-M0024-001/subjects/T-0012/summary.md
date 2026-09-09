# Door handle

- Target: `T-0012`
- Success rate: 0.0%
- Counted questions by run: trial-001=40 (ask_after_question_limit), trial-002=40 (ask_after_question_limit), trial-003=40
- Counted questions (scoring-eligible): average `40` · minimum `40` · median `40` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0170` · Oracle `0.2109` · Verifier `0.0005` · Total `0.2284`
- Superseded infrastructure attempts: 1 across 1 trial(s) · cost `0.1740` USD
- Output-contract reliability: `breached` · compliance `98.4%` · 2 violation(s) across 2 trial(s) · 2 counted-turn penalties
- Oracle quality control: 82 reviewed · agreement `86.6%` · 11 disagreement(s) / 11 Judge call(s) · 6 Oracle answer(s) changed (`54.6%`) · QC cost `0.3487` USD
- Oracle disagreement by question type: `negation` 2/9 (`22.2%`) · `other` 9/73 (`12.3%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | breached (97.6%) | 1 | 0.2656 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | breached (97.6%) | 1 | 0.1825 | [result](trials/trial-002/result.yml) |
| trial-003 | limit_exhausted | false | 40 | clean (100.0%) | 0 | 0.2373 | [result](trials/trial-003/result.yml) |
