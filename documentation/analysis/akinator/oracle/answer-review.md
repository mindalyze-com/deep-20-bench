# Akinator answer review

The user asked whether the Oracle gave wrong answers. This is a targeted review of the existing records; it made no further paid model calls.

## Confirmed meaning error

Albert Schweitzer, trial 1, question 4: **Does your character know your name?**

- Oracle: YES. Its evidence establishes that Schweitzer knew his own name.
- Reviewer: NO. It interpreted “your name” as the player's name.
- Judge: YES. It changed the referent to the character's own name and explicitly dismissed the player interpretation.
- Final pipeline answer: YES.
- Website submission: **not submitted**. A fresh mapped check later returned UNKNOWN, which was submitted.

The final YES is unsupported for the actual question. “Your character” denotes the hidden subject; “your name” denotes the player. Knowing one's own name does not establish knowing the player's name. No player identity or relationship was supplied, so the review does not assert an independently verified NO. UNKNOWN is the defensible answer when that required context is unavailable.

The Reviewer detected the referent error, but the blind Judge independently made the same error as the Oracle. The Judge did not receive or override the Reviewer's explanation; the routing selected its independent result after token disagreement.

Record inside [raw-data.zip](raw-data.zip): `oracle-suites/akinator-20260910-T0002-r1-q04/result.yml`. Full prompts and role responses are in that suite's archived audit directory.

## Einstein: ambiguous or debatable cases

- Q19, “Is your character a musician?”: YES was supported by evidence that Einstein was an amateur musician. This is defensible under a broad meaning. It can steer Akinator toward professional musicians, but that effect alone does not make it a factual error. [Oxford's account](https://www.physics.ox.ac.uk/news/commentary-professor-foster-einstein-and-music) corroborates his substantial violin playing.
- Q10, “Is your character related to music?”: YES is well supported by his musical activities.
- Q21, “Does your character play the piano?”: YES is supported by the recorded biographical source; the transcript does not justify calling this false.
- Q6, “Is your character American?”: YES used his U.S. citizenship. Q35, “Is your character German?”: UNKNOWN invoked uncertainty between origin, former citizenship and later citizenship. This is inconsistent in interpretive approach, but the German answer is not a simple false factual assertion.
- Q15/Q32, “famous for writing essays/books”: the NO rationales silently emphasize what Einstein is *chiefly* famous for. The question does not say chiefly. This is a scope concern; the present review does not establish the correct binary answer.

The shared current factual policy requires ordinary meaning and prohibits substituting a nearby claim. It does not define Akinator's player/character pronouns. The profession-specific instruction from the standalone standard prompt is not present in the selected concise knowledge policy.

## User-authorized local mapping

Preserve every original website question in the transcript. For the Oracle input only, make the public referents explicit: “your character” means “the hidden subject”; other second-person references in Akinator's question refer to the player. For example:

> Does the hidden subject know the player's name?

This must not include the player's identity, private data, earlier questions, earlier answers, or the Reviewer's decisions. Recheck the current question with fresh blind adjudication, retain the original faulty call and its cost, and record the mapping version. Do not silently replace previously submitted answers or rewrite completed games. Ambiguous occupations and nationality need separate interpretation decisions; this pronoun mapping does not solve them.

The user chose to fix the Akinator question mapping and continue. The local `ask_akinator.py` preserves quoted text and the original wording, makes public player/character references explicit, and rejects ambiguous contractions or unbalanced quotations for manual review. Ten offline mapping checks, Ruff and strict Mypy passed. A fresh check of the corrected question returned UNKNOWN; that token was submitted and the website advanced to question 5. The original wrong YES and its cost remain recorded.

No production prompts or configurations have been changed. The experiment's user-specified total OpenRouter cap is **$7**, including retries and failed calls. The local single-question wrapper checks recorded spending before each new paid call, stops on unresolved costs, and requires review once known charges exceed $5, leaving a conservative $2 allowance below the cap. This is a local review threshold, not a provider-side billing limit.


## Achilles question 16 infrastructure failure

The Oracle twice returned an UNKNOWN result with an incompatible evidence basis. Local validation rejected both outputs; no website answer was submitted. The retained provider usage includes both attempts: $0.008619680000000001. This is an infrastructure failure, not an Akinator error or an accepted factual answer. The exact immutable failure audit was reviewed before allowing one new, blind attempt of the current question. No prompts or validation rules were changed. The spending guard includes the failed attempts and continues to stop on other unreviewed failures.

## Bike pump: electrical-operation scope

Trial 1 returned UNKNOWN to Q2 “Is it electronic?” (after the reviewed format failure and fresh retry) and Q9 “Is it an electronic device?”, but YES to Q22 “Does it work with electricity?”. The trusted subject includes both manual and electric bicycle pumps. For Q22, the Oracle explicitly treated the existence of electric variants as sufficient for the entire category, and the Reviewer agreed on that same basis. No Judge was invoked.

This is a likely quantifier/scope problem: Q22 does not explicitly ask whether some variants can work electrically. At minimum, the three responses reveal an interpretation inconsistency that can influence Akinator. This is not the same kind of clear referent error as Schweitzer's player-name question. The submitted YES is preserved, and no retrospective answer was substituted. Source record: `akinator-20260910-auto-T0008-r1-a22`.

Bike pump Q2 also exhausted a built-in output-format retry. The two failed provider attempts cost $0.00599062, were checked against the immutable audit, and are included in the ledger. One fresh blind attempt returned a valid UNKNOWN and was submitted.

Bike pump Q32 exhausted its configured research budget. The two paid attempts cost $0.00955028 and produced no submitted answer. The exact audit and all role costs were verified before one fresh blind attempt.


## Confirmed adapter error: generic object use

Spider web trial 1 Q17 was “Do you put it in the washing machine?”. Version 2 mapped this to “Does the player put it in the washing machine?”. The Oracle's UNKNOWN explicitly depended on the unspecified player's habits, despite noting that spider webs are not ordinarily laundry items. This was an adapter error introduced by treating every second-person phrase as personally referential. The UNKNOWN had already been submitted, and the transcript is preserved and flagged.

Mapping version 3 recognizes bounded, generic object-use templates such as “Do you put it...” and “Can you use it...”, when they have no additional personal reference or time cue. These become “Do people put it...” and “Can a person use it...”. Personal questions and other wording retain the earlier explicit-player treatment. The fix changes neither factual hints nor Oracle prompts, models, evidence handling, or adjudication. Offline checks cover the failing example, generic ability, personal familiarity, country, possessions, timing, and quoted literals. No extra paid replay of Q17 was launched.

Moon Q1 failed because the required Judge twice exceeded its supporting-statement length limit. No answer was submitted. The complete failed-pipeline cost was $0.05319924: Oracle $0.00442904, Reviewer $0.0023302, Judge including retry $0.04644. All role traces and the immutable audit were verified before one fresh blind attempt.


## Door handle: generic container reference

Trial 1 Q13, “Does it go in your school bag?”, became a question about the player's school bag. The Oracle's UNKNOWN explicitly cited the unidentified player and uncertainty about whether ordinary carrying was intended. The submitted answer is preserved and flagged as another adapter issue. Q11's pocket question also mentioned the player, but its UNKNOWN was independently supported by the range of handle sizes and designs.

Version 4 extends the bounded generic-use mapping to “your pocket(s)” and “your school bag(s)” in fit/go/belong questions or generic use/put/hold templates. It uses generic clothing pockets or school bags without adding facts or answer hints. Explicit personal or time cues keep the earlier player reference. Quoted literals remain unchanged. No retrospective paid replay was launched.

Einstein trial 2 Q11 exhausted its research budget after two attempts. The failed Oracle cost was $0.011129280000000001. No answer was submitted; the exact audit and cost were reviewed before one fresh blind retry.

## Achilles: interpretation variation between trials

The repeated question “Is your character related to Marvel?” returned YES in trial 1 and UNKNOWN in trial 2 Q8. Trial 2 distinguished the mythological target from a separate comic character and cited uncertainty about a direct affiliation. This is answer variation under the frozen configuration, not evidence that every YES or UNKNOWN is factually false. Trial 2 Q10, “Is your character associated with a Superhero?”, returned YES after a RATHER_YES/YES disagreement and blind Judge review, based on Achilles supplying courage to Shazam. The loose wording permits broader associations than a question about the character's origin. Both results and their paths are preserved.

## Bike pump trial 2: possibility versus typical location

Q36, “Can it be found in a kitchen?”, returned YES because a portable bicycle pump could be stored in a kitchen, even though that is not its characteristic location. The Reviewer agreed. This is logically possible but may differ from the ordinary game interpretation of where an item is normally found. Q38, “Can we find it in a bathroom?”, instead returned RATHER_NO. These nearby questions merit a scope-consistency review; their submitted answers remain unchanged. Trial 2 Q39, “Does it work with electricity?”, returned UNKNOWN, unlike the first trial's YES and consistent with the other electrical questions in trial 2. No extra paid replays were launched.

Spider web trial 2 Q16 exhausted its structured-output retry. The two failed attempts cost $0.00656128, and no answer was submitted. The exact audit and complete role cost were reviewed before one fresh blind retry.

Eyebrow trial 2 Q5 received no completed provider choice after two attempts, with a provider-content-filtered status. The failed cost was $0.0056321600000000007. No answer was submitted; the exact audit and cost were reviewed before one fresh request with the same question and unchanged prompts.

Eyebrow trial 2 Q30 exhausted its structured-output retry. The two failed attempts cost $0.0093117999999999995, and no answer was submitted. The exact audit and complete role cost were reviewed before one fresh blind retry.

## Moon trial 2: near-duplicate association questions

Q1, “Does it have a relation with sex?”, returned YES. Q9, “Does it have a relationship with sexe?”, returned UNKNOWN and explicitly cited ambiguity between sexual activity, biological sex, gender and other meanings. This shows a within-game interpretation change for near-duplicate wording. The independently checked answers remain unchanged; neither prior answer was sent into the later Oracle request.
