# Door handle

- Target: `T-0012`
- Success rate: 33.3%
- Counted questions by run: trial-001=40 (ask_after_question_limit), trial-002=30 (consecutive_contract_violations_exhausted), trial-003=18
- Counted questions (scoring-eligible): average `29.33` · minimum `18` · median `30` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0991` · Oracle `0.1240` · Verifier `0.0001` · Total `0.2232`
- Superseded infrastructure attempts: 1 across 1 trial(s) · cost `0.2202` USD
- Output-contract reliability: `breached` · compliance `86.7%` · 12 violation(s) across 2 trial(s) · 12 counted-turn penalties
- Oracle quality control: 72 reviewed · agreement `94.4%` · 4 disagreement(s) / 4 Judge call(s) · 3 Oracle answer(s) changed (`75.0%`) · QC cost `0.1766` USD
- Oracle disagreement by question type: `other` 4/72 (`5.6%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | breached (82.9%) | 7 | 0.2925 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (consecutive_contract_violations_exhausted) | false | 30 | breached (83.3%) | 5 | 0.2718 | [result](trials/trial-002/result.yml) |
| trial-003 | success | true | 18 | clean (100.0%) | 0 | 0.1054 | [result](trials/trial-003/result.yml) |
