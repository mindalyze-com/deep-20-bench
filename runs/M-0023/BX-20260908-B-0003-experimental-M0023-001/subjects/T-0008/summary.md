# Bike pump

- Target: `T-0008`
- Success rate: 0.0%
- Counted questions by run: trial-001=40 (ask_after_question_limit), trial-002=40 (ask_after_question_limit), trial-003=40 (ask_after_question_limit)
- Counted questions (scoring-eligible): average `40` · minimum `40` · median `40` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.0047` · Oracle `0.1754` · Verifier `0.0005` · Total `0.1807`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `breached` · compliance `95.1%` · 6 violation(s) across 3 trial(s) · 6 counted-turn penalties
- Oracle quality control: 87 reviewed · agreement `93.1%` · 6 disagreement(s) / 6 Judge call(s) · 5 Oracle answer(s) changed (`83.3%`) · QC cost `0.2436` USD
- Oracle disagreement by question type: `other` 6/86 (`7.0%`) · `quantitative_comparison` 0/1 (`0.0%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | breached (95.1%) | 2 | 0.1656 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | breached (95.1%) | 2 | 0.1511 | [result](trials/trial-002/result.yml) |
| trial-003 | guesser_protocol_failure (ask_after_question_limit) | false | 40 | breached (95.1%) | 2 | 0.2253 | [result](trials/trial-003/result.yml) |
