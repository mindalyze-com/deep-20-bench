# Eyebrow

- Target: `T-0010`
- Success rate: 0.0%
- Counted questions by run: trial-001=32 (consecutive_contract_violations_exhausted), trial-002=40 (invalid_guesser_output), trial-003=40 (invalid_guesser_output)
- Counted questions (scoring-eligible): average `37.33` · minimum `32` · median `40` · maximum `40`
- Average cost per terminal run (USD): Guesser `0.1391` · Oracle `0.1238` · Verifier `0.0009` · Total `0.2638`
- Superseded infrastructure attempts: 0 across 0 trial(s) · cost `0.0000` USD
- Output-contract reliability: `breached` · compliance `83.3%` · 19 violation(s) across 3 trial(s) · 17 counted-turn penalties
- Oracle quality control: 77 reviewed · agreement `97.4%` · 2 disagreement(s) / 2 Judge call(s) · 1 Oracle answer(s) changed (`50.0%`) · QC cost `0.1515` USD
- Oracle disagreement by question type: `other` 2/77 (`2.6%`)
- Files: [raw result](result.yml)

| Trial | Status | Success | Questions | Contract | Violations | Cost (USD) | Result |
|---|---|---:|---:|---|---:|---:|---|
| trial-001 | guesser_protocol_failure (consecutive_contract_violations_exhausted) | false | 32 | breached (78.1%) | 7 | 0.2621 | [result](trials/trial-001/result.yml) |
| trial-002 | guesser_protocol_failure (invalid_guesser_output) | false | 40 | breached (80.5%) | 8 | 0.2557 | [result](trials/trial-002/result.yml) |
| trial-003 | guesser_protocol_failure (invalid_guesser_output) | false | 40 | breached (90.2%) | 4 | 0.2737 | [result](trials/trial-003/result.yml) |
