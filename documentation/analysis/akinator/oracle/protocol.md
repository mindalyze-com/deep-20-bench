# Akinator web comparison - Oracle protocol

This is the historical Oracle protocol. The later user request superseded its private-storage restriction and renewed the self-answered arm, limited to one attempt per active subject. See the [current overview](../README.md) and [self-answered protocol](../self-answered/protocol.md). Oracle answers, costs and mapping provenance remain unchanged.

Requested on 10 September 2026. The user authorized the paid Oracle infrastructure.

The user subsequently set a total OpenRouter spending cap of **$7**, including retries and failed calls. This supersedes the earlier $10 suggestion. See `budget.json` for the latest recorded spending.

- Website: https://en.akinator.com/ in English, using the visible web interface.
- Subjects: the ten active entries in `config/subjects.yaml`; Stephen King and Mario are inactive.
- Planned repetitions: three per subject. Complete one pass through all active subjects in catalog order, then repeat for passes two and three.
- Themes: Characters for persons and fictional/mythological characters; Objects for things.
- Answers: the current B-0003 `qualified_v1` / `concise_knowledge_v1` Oracle, Reviewer and Judge configuration, frozen in local configuration snapshots. Initially each question was sent unchanged through the production `test-oracle --live` harness. Following the user-authorized correction, Schweitzer trial 1 question 4 and later questions use `akinator-player-references-v1`: public player and character references are made explicit in the Oracle input, while the original website wording is preserved. Only the final adjudicated answer is submitted to the website.
- Mapping: YES = Yes; NO = No; UNKNOWN = Don't know; RATHER_YES = Probably; RATHER_NO = Probably not.
- Guesses: record Akinator's displayed name and description, and validate them using the production Guess Validator with only the trusted subject and current guess.
- Limits: record identification within 20 answered questions and within 40 counted actions. Count factual questions and rejected guesses; a correct terminal guess does not add a counted action. Stop after 40 counted actions, allowing only an immediately displayed final guess. If the website requires another factual answer to produce a guess, record a limit stop.
- Each game starts from the theme selection. Do not supply the subject's name, clues, descriptions, or evidence to Akinator. Do not add missing characters or train the website with a target name after failure.
- Record the exact displayed questions, button answers, guesses, correctness, question counts, rejected guesses, terminal reason, elapsed time and available API costs.
- Preserve failed infrastructure attempts separately. Do not use a provisional answer after a required-role failure and do not count infrastructure failures as Akinator failures.
- This is an external web comparison. Akinator's category system, internal state, sampling, training and guess timing are uncontrolled. Its Probably labels are mapped to our qualified tokens but their internal meanings are unknown. Results are not official benchmark/leaderboard entries.
- Repeated web games may be correlated. Fresh games do not prove independent server state or prevent Akinator from learning from confirmation feedback.
- Existing automatic provider prefix caching remains unchanged. No application answer reuse, response caching, padding, provider-policy changes or savings claims are added.
- Keep all transcripts, results and supporting records local under `private/reviews/`. No publication or source changes are part of this run.

The first Oracle attempt could not resolve the provider host inside the sandbox. Its failure is retained as `akinator-20260910-T0001-r1-q01`. A separate network-enabled attempt, `akinator-20260910-T0001-r1-q01-net`, succeeded. The failed attempt returned no answer and no website input was submitted from it.

The initial Schweitzer question 4 call misread the player's name as the character's own name. Its YES was not submitted. The user authorized correcting the mapping and continuing. A fresh mapped check returned UNKNOWN, which was submitted. Both paid calls remain in the spending total. The completed Einstein trial retains its original answers and protocol; it is not silently rewritten or rerun.

After the Oracle-backed experiment is finished, the user requested another run over the subjects with Codex answering every question itself. Record that as a separate answering arm, with its own transcripts and scores. It must not invoke the paid Oracle/Reviewer/Judge pipeline. Keep answer-quality and protocol differences explicit when comparing the arms.

Mapping version 2 extends the same target-reference rule to `your object` and `your animal`, so those phrases cannot be mistaken for the player's possessions. It was enabled before the Objects games. Character wording is otherwise unchanged; earlier mapping records retain version 1.

Achilles trial 1 question 16 exhausted its built-in structured-output retry. Both failed attempts cost $0.008619680000000001 and were audited before one fresh blind retry. The fresh retry returned UNKNOWN and was submitted. The discarded invalid outputs never entered Akinator or the fresh Oracle request. The bridge supports at most one such fresh retry per action, with the budget and failure-review checks still applied.

The subsequent self-answered arm is one additional game per active subject (ten games), as stated during the Oracle arm. It uses the same themes and stopping rules, records Codex's answers directly, and makes no OpenRouter calls. Its sample size is reported separately from the three planned Oracle trials per subject.

Mapping version 3 was introduced after Spider web trial 1 Q17 revealed an adapter error: generic object-use “Do you...” had been personalized as “Does the player...”. Bounded generic use/ability templates now use “Do people...” / “Can a person...”, provided no further personal or time cue occurs. The original website wording remains preserved. Spider web trial 1 retains and flags the already submitted Q17 UNKNOWN; no earlier game is silently rewritten.

Mapping version 4 was introduced after Door handle trial 1 Q13 exposed the same personalization issue in a generic school-bag question. Bounded container comparisons now refer to generic clothing pockets or school bags unless personal/time cues make the question specific. Door handle trial 1 Q13 remains flagged with its originally submitted UNKNOWN. Earlier mappings and answers remain immutable in the records.

The user stopped the experiment after 18 completed games and one partial Moon trial. All remaining Oracle trials and the self-answered arm were canceled for this run. No further website answers were submitted. Final status and costs are in summary.md and experiment-status.json.
