# Five-answer experiment

B-0003 uses the opt-in `qualified_v1` profile for the Guesser, Oracle, recovery Oracle,
Reviewer, and Judge. It retains the registered models, routes, sampling, scoring rule, action
schema, and identity Validator. All benchmark templates now use a 40-turn limit. The early
diagnostic runs were removed. New runs need fresh execution IDs and must record their
definition and cache policy. B-0001 and B-0002 retain their three-answer profiles.

The default is **3 iterations per subject and model**, set by `default_iterations: 3` in
`config/benchmarks.yaml`. Use this count for new-game planning and launches unless the user
specifies another count. Earlier five-repeat diagnostics do not change this default.

## Concise evidence/knowledge policy

New B-0003 definitions select `adjudication_policy: concise_knowledge_v1`. The Oracle,
Reviewer, and Judge share a shorter factual policy. All three return `basis: evidence` when
quoted sources and direct deductions suffice, or `basis: other` otherwise. `other` includes
remembered facts, combined support, and unresolved answers. The required
`supporting_statement` identifies the decisive fact and material limitation in at most 600
characters, and explicitly identifies remembered facts. These are model-reported audit claims,
not verified accounts of internal reasoning. Full reasoning transcripts are not requested.

Research searches first, then may use concrete, well-established knowledge. Memory cannot
override material source conflict. Mere plausibility and failed searches cannot establish a
negative answer. Current/disputed facts and claims of absence/completeness need adequate
source coverage. Meaning, scope, negation, and the distinction between origin, material, form,
and identity remain shared rules. The five answer meanings and independent exact-token
adjudication are unchanged.

The claim-scope revision distinguishes the named object from its constituent material and
keeps `is`, `is made of`, `is made by`, and `is part of` separate. It evaluates each OR branch
independently and inclusively, and requires both AND branches. It preserves possibility,
frequency, and generic claims without adding conditions such as rigidity or intactness.
It separates physical state from porosity, flexibility, and fragility. If unresolved ordinary
interpretations reverse the answer, it uses UNKNOWN. These are
shared rules for every subject; no subject-specific answers are embedded in the prompts.

Research has one semantic attempt. `oracle_configuration.research_query_target` defaults to 3
and controls the query count requested in the Oracle prompt. The API ceiling is calculated
as that target plus two bonus calls: target 3 allows at most 5, and target 5 allows at most 7.
The prompt asks only for the target, without offering the bonus allowance. The Parallel server
tool's `max_uses`, top-level `max_tool_calls`, local usage guard, and query-report schema all
use the derived ceiling. Query reports retain actual submissions, including any bonus use.
The target accepts 1-28, leaving room for the bonus within OpenRouter's 30-call API maximum.
The SDK adapter restores the tool controls after serialization.

Completed valid answers within the ceiling continue through normal independent review,
including when reported searches exceed the prompt target. Actual search counts and costs
remain in existing metrics and audits; the extra allowance is not a new answer-reuse policy.
There is no second diversified research attempt. A schema retry receives only the remaining
allowance from recorded search usage, so the two bonus calls are shared across attempts.
Exhausted budgets stop retries. OpenRouter's server loop is expected to stop searching and
request a final answer using the context already collected when its tool budget is reached.
Uncertain transport failures and unusable provider results are not blindly replayed under this
budget; explicit rate-limit rejections remain retryable. The provider must report search use,
and exceeding the derived hard ceiling remains an infrastructure error. This allowance does
not add a client-side no-search recovery request or bypass Reviewer/Judge failures. A remote
service's unreported work after a connection failure cannot be certified by local accounting.

Directional `evidence` decisions require source excerpts/supporting indices. An `other`
Oracle answer can have no source excerpts and still receives blind review. Reviewer and Judge
receive only subject, current question, and numbered source excerpts, possibly empty. Each
may use its own knowledge under the shared policy; neither receives earlier answers, basis,
supporting statements, search history, or traces. Oracle UNKNOWN uses `other` and may retain
relevant source context in the private result, while still bypassing review. It is recorded as
`bounded_unknown` and does not seed either ASK answer cache.

Evidence keeps its existing 2,000-character allowance per item, with no extra word limit.
An item may be an exact `kind: quotation` or a `kind: source_summary` containing only facts
retrieved from its source URL, faithfully expressed in the Oracle's own words. Summaries are
preferred for longer context; quotations remain supported when exact wording matters. Both
must preserve material qualifications, scope, dates, quantities, negation and counterevidence.
Summaries do not contain the Oracle's decision, reasoning or remembered knowledge. Omitted
kind means quotation, preserving historical evidence. Reviewer/Judge receive the source-summary
label with the numbered evidence, and never treat it as proof of the source's exact wording.
The supporting statement remains private and does not replace source context. These forms are
model-reported evidence, not independently verified source extractions.

Reviewer/Judge UNKNOWN may retain valid indices of excerpts explaining ambiguity, conflict,
or missing coverage, with `basis: evidence` or `basis: other` and the required private
supporting statement. The references explain uncertainty, not a directional verdict. No
answer, basis, statement, or index is rewritten. Reviewer UNKNOWN still invokes the blind
Judge; Judge UNKNOWN is final and play continues. Invalid or out-of-range indices, missing
required fields, and unsupported values still undergo bounded recovery and fail if exhausted.
Older policies retain the no-indices rule for UNKNOWN. This avoids losing a game merely
because a valid uncertainty decision included its relevant context.

The Oracle's basis/statement are retained in standalone results and summaries and in the
benchmark's `audit.calls[].research.attempts[]`. Reviewer/Judge basis/statements remain in
`turns[].adjudication.oracle_quality`. Only the final answer token enters Guesser history.
Private decision support is never copied into the public dataset or used as later model input.
Historical compatible answer reuse retains the original support as audit data only.

Versions are `live-web-oracle-v17-labelled-source-context`,
`oracle-reviewer-v12-labelled-source-context`, and `oracle-judge-v15-labelled-source-context`.
The research prompt lists the allowed research-outcome labels from the same enum as the
response schema, including `ambiguous_question`; invented alternative labels remain invalid.
Earlier policies retain their prompt text, wire schemas, and absent-field serialization.
The new configuration, schemas, and versions separate factual-answer and prompt caches;
use fresh execution IDs. Models, routes, and three repetitions are unchanged. Prompt changes
do not automatically update publication eligibility. The separate 8 September 2026 release
decision accepts the recorded new results and their explicit contract revisions; see
`source/publication/README.md`.
The factual contract explicitly hashes both the requested query target and the derived
ceiling. Earlier strict-three executions and answer-cache inventories remain separate.

## Why add qualified answers?

Edition 1.0 offers YES, NO, and UNKNOWN for factual questions. When relevant evidence favors
one direction but leaves a material gap, UNKNOWN loses that direction and a firm YES or NO
can overstate the support. Edition 1.1 adds RATHER_YES and RATHER_NO to express the supported
direction while keeping the uncertainty visible.

The intended benefit is more useful partial information for the Guesser without treating it
as certainty. The Guesser must keep alternatives possible and check key assumptions before
narrowing heavily. UNKNOWN remains necessary when there is no reliable direction or when
unresolved ambiguity or conflicting evidence changes the answer. Qualified answers are not
numerical probabilities, and a failed search alone cannot justify a negative answer.

This is a design rationale, not a demonstrated accuracy improvement. The editions also differ
in subjects, trial counts, question limits, and prompts, so their scores cannot isolate the
effect of the two additional answers. Blind review and exact-token disagreement routing still
apply; identity validation keeps YES, NO, and UNKNOWN.

## Answer meanings

| Token | Meaning |
| --- | --- |
| YES | Reliable evidence establishes the claim under its ordinary meaning. |
| RATHER_YES | Relevant evidence favors the claim, with a material gap preventing YES. |
| RATHER_NO | Relevant evidence favors rejecting the claim, with a material gap preventing NO. |
| NO | Reliable counterevidence rules out the claim under the same meaning. |
| UNKNOWN | No reliable direction, or unresolved ambiguity or conflict changes the answer. |

Direct factual deductions are allowed. Firm answers do not require absolute certainty.
Qualified answers express uncertainty about the exact claim, not how often or how strongly a
property applies. A well-supported answer to "sometimes" can be YES even when the answer to
"always" is NO. A failed web search alone supports neither NO nor RATHER_NO. A verified complete
record can establish absence;
substantial relevant coverage that would normally record the claim can support RATHER_NO.
A short description's omission is not enough.

The prompts use one shared factual policy for every subject category. They preserve the
question's meaning and scope: "can", "sometimes", "usually", "always", and "mainly" make
different claims. One example does not establish a general rule, and a fact about one member
or version does not automatically apply to a whole group. Doing, having, or being used for
something does not by itself establish what the subject is defined by or known for.
There are no category-specific branches or examples naming benchmark subjects.

The Guesser treats qualified answers as clues and keeps opposite candidates possible. It
checks a key assumption with a different property before narrowing heavily and reconsiders
earlier assumptions after rejected guesses. The initial category remains its only subject
metadata. The catalog still contains its existing subjects; this prompt revision adds none.

All Guesser profiles now share the same fixed guide to the category labels. It explains that
`thing` spans natural and human-made entities, living organisms, body parts, phenomena, and
concepts, and may identify a general kind or a particular instance. The entire guide appears
for every category; no branch selects hints from a subject or names catalog entries.

## Adjudication and isolation

Oracle UNKNOWN remains final. Every other Oracle token requires blind review. Exact-token
agreement is final. Any difference, including YES versus RATHER_YES, invokes the blind Judge.
The Judge's exact token is final. Reviewer and Judge receive only the trusted subject, current
question, and numbered evidence excerpts, with no prior decisions, history, or web access.

All four directional research answers require 1-3 evidence items. The Reviewer uses only
supplied evidence and identifies at least one supporting index for a directional answer.
Evidence-based Judge answers follow the same rule.

New B-0003 definitions explicitly select
`oracle_configuration.adjudication_policy: judge_stable_knowledge_v1`. The Judge first assesses
whether the supplied excerpts support any directional answer, including a qualified answer.
Only insufficient factual coverage that would otherwise force UNKNOWN permits the bounded
knowledge fallback. It requires stable, widely established facts about a specific closed
relation with a unique answer, such as sole authorship, birthplace, or creator. It cannot
override material contradictory evidence, settle ambiguity, or upgrade an evidence-supported
qualified answer merely from memory. Current, disputed, subjective, open-world, and exhaustive
claims remain outside the exception. A knowledge decision records `basis="model_knowledge"`
and no evidence indices; the Reviewer cannot use this basis.

Knowledge-based decisions may use YES, RATHER_YES, RATHER_NO, or NO. Firm answers require known
facts that establish the claim or its rejection. Qualified answers require concrete known
facts that favor the chosen direction, with a material gap preventing a firm answer. A vague
recollection or mere likelihood is insufficient. UNKNOWN always uses `basis="evidence"` and
no indices; qualified tokens do not authorize overriding contradictions with memory.

Missing `adjudication_policy` means `profile_default`, omitted from serialized configuration.
For qualified_v1 this retains the historical evidence-only Reviewer and Judge and their
original prompts and schemas. Standard and concise profiles retain their existing exceptions.
The new policy is valid only with qualified_v1. Schema generation and local validation use the
role and policy together; publication independently validates the same distinction and checks
that episode policy matches the execution manifest. Required-role or schema failure remains an
infrastructure failure with no provisional-answer fallback. Research usually uses 1-4 queries
and must keep the existing hard 1-8 query-list contract. Nothing truncates or repairs that list.

Only the final token enters Guesser history. Qualified tokens are allowed only on ASK.
Identity validation remains YES/NO/UNKNOWN and locally rejects qualified answers. Guesser and
Oracle five-answer profiles must be selected together, and official mode rejects them before
startup calls. The canonical FORMAT_ERROR and all other isolation rules remain unchanged.

## Versions and persistence

- Guesser: `stateful-category-guesser-v16-five-answer-category-guide`.
- Oracle: `live-web-oracle-v12-evidence-context`.
- Recovery: `live-web-oracle-recovery-v5-evidence-context`.
- Reviewer: `oracle-evidence-reviewer-v7-generic-five-answers`.
- Judge with `profile_default`: `oracle-evidence-judge-v8-generic-five-answers`.
- Judge with `judge_stable_knowledge_v1`: `oracle-evidence-judge-v10-stable-knowledge`.

The evidence-context revision asks primary and recovery research to retain enough surrounding
source text for an independent reader to assess the exact question and its scope, including
relevant qualifications and counterevidence. The existing limits remain 1-3 excerpts of at
most 2,000 characters each. Longer excerpts are not presumed sufficient: missing coverage must
still affect the selected answer. No subject-specific examples, schema fields, search calls,
or feedback channels are added. Reviewer, Judge, Guesser and Validator prompts are unchanged.
The changed research prefixes and versions change the factual-contract hash automatically,
excluding earlier evidence packages from historical ASK reuse. Use fresh execution IDs.
Publication's existing release pins retain the earlier research versions until separately
updated; this revision does not change a published cohort.

The Judge policy revision changes only the Judge's fixed prompt and permitted decision basis.
It adds no calls: Oracle UNKNOWN and exact-token agreement still bypass the Judge. The
configuration field changes the immutable benchmark definition hash, and the new Judge prompt
version separates its prefix-cache key. Use fresh execution IDs. Never resume old positions
under the new policy or pool results from the two policies. Publication must compare only matching
configurations and prompt versions. New-policy runs remain outside an existing cohort until an
explicit publication-definition change.

Code enforces role permissions, answer vocabulary, and the relationship between decision basis
and evidence indices. Whether coverage is insufficient and remembered knowledge is reliable
remains model judgment and requires factual auditing; a valid schema is not proof of accuracy.

The local Judge policy audit from 6 September 2026 retains eight
historical-prompt checks, eight checks of the first fallback prompt, and eight final-prompt
checks. The final prompt matched all eight expected answers and decision bases after clarifying
contradiction, eligibility, and partial-coverage rules. This is a small controlled regression
check, not an independent accuracy estimate. All four knowledge-based directional tokens are
also covered by local validation and publication tests.
Its supporting artifacts are private review material; this public summary does not require
access to them.

These versions replace the earlier people-focused five-answer prompts. Historical runs retain
their recorded prompt versions and hashes. New runs need fresh IDs; results from the two
prompt revisions must be distinguished when comparing gameplay.

The shared category guide changes only the Guesser from its earlier v13 revision. Oracle,
recovery, Reviewer, Judge, and Validator prompts keep their existing versions. Standard and
concise Guesser profiles also receive the guide under their own new versions.

Schema-v9 execution artifacts can retain the new tokens. Additional qualified final-answer
and Judge counters are optional and omitted when zero. Standard provider schemas,
configuration snapshots, and serialized zero counters retain their original representation.
The publication fully validates these artifacts and admits only release-qualified runs to
benchmark edition 1.1. Its v10 dataset supports the five-token question transcripts. The
maintained v9 compatibility dataset represents edition 1 only. The GUI defaults to 1.1 and
keeps edition 1 selectable. See `source/publication/README.md` for the qualification contract.
Earlier one-subject, 50-question diagnostics do not satisfy the 1.1 release cohort.

Prompt-prefix caching was re-evaluated: versions separate the changed prefixes and schemas;
Guesser, research, recovery, Reviewer, and Judge namespaces stay isolated. Existing exact routes
and provider cache policies remain in force. The benchmark's separately versioned
[ASK reuse policies](oracle-history-cache.md) apply when enabled; they are not a change to
these prompts. Provider response caching remains disabled, with no padding or assumed saving.
Read actual billed costs, cache tokens, and latency from this run. Shorter/changed prefixes may
change cache eligibility. Fresh route preflight and startup canaries precede the experiment.

## New trials

The current factual contract is `oracle-factual-answer-v2-inconclusive-unknown`. The application
no longer scans question keywords to decide whether missing evidence is an infrastructure
failure. Valid research that remains inconclusive after recovery returns UNKNOWN and play
continues; actual technical failures retain their infrastructure classification. New execution
definition and factual-cache hashes separate this behavior from earlier runs. Prompts and
the five-token ASK vocabulary are unchanged, and historical results are not reclassified.

Use active subjects, fresh execution IDs, the current paired profiles, and three iterations
per subject and model unless another count is requested. For long runs, use detached screen,
nohup, and caffeinate on macOS. Verify processes, manifest, canaries, and the first turn as
described in the [benchmark control-plane guide](../source/execution/benchmark/README.md).

Report all scheduled positions, infrastructure outcomes, qualified-token frequency, UNKNOWN
frequency, question counts, and recorded cost. A selected-subject diagnostic cannot establish
a general model ranking or isolate the effect of changes to both prompts and the answer protocol.
