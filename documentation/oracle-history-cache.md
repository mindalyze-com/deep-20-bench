# Historical Oracle answers

`concise_knowledge_v1` uses separate prompt/schema/configuration contracts. It permits an
`other` answer with empty evidence after independent review. Historical candidates reconstruct
that original result with its recorded research basis and supporting statement, validate the
selected policy, and preserve the support as audit data. No support enters model requests.
`bounded_unknown` is excluded from all ASK cache policies. Earlier policies remain readable;
results from the new policy cannot seed an earlier-policy execution or vice versa.


New benchmark executions use the versioned `historical_ask_v1` policy by default. The benchmark
may reuse an earlier, fully adjudicated ASK answer. It copies the original Oracle evidence and
quality decisions and clearly identifies the source. This is the user-authorized exception to
the previous application-response-cache prohibition. Standalone Oracle/game commands, Guesser
responses, GUESS validation, and provider response caching remain outside this policy.

## Matching and eligibility

Startup reads original manifests in `runs/`, `archive/`, and
`benchmark-logs/superseded-runs/`. It filters by benchmark ID, game protocol version and prompt
profile, the effective Oracle configuration (including Reviewer, Judge, recovery, routing,
search settings and parameters), and the current factual-answer contract. That contract hashes
the versioned primary/recovery/review/Judge prompts and their output schemas, together with a
version for service behavior. Bump the factual contract version when adjudication or failure
behavior changes without changing those prompts or schemas. Cache matching/reuse rules have
their own policy versions.

`oracle-factual-answer-v2-inconclusive-unknown` removes keyword-based research failure
decisions. Valid inconclusive research returns UNKNOWN after recovery. This changes the
contract hash without changing provider prompts or the `historical_ask_v1` /
`same_episode_ask_v1` matching rules. Earlier hashes cannot seed or resume a new-contract
execution. Benchmark definition hashes also include the factual contract, including when
caching is disabled. Use fresh execution IDs and retain historical outcomes unchanged.

`oracle-factual-answer-v3-question-id` retains that behavior and adds the `question-id-v1`
metadata contract for Oracle and Reviewer generations. The fixed metadata instruction, schema,
roles, and policy version enter the deterministic contract hash. Individual random IDs do not.
Logical prompt hashes still cover the factual input without metadata; actual provider requests
retain their IDs privately. Earlier contract hashes cannot seed or resume revised executions.

New manifests record `oracle_contract_hash`. Older manifests without this complete contract
proof are skipped rather than assumed compatible. Their separate per-call prompt labels cannot
prove the schemas or the versions of roles that did not run. Existing history does not need to
be migrated or rewritten; compatible new completed trials seed later executions.

When a subject is loaded, only that subject's original leaf trial YAML files are read.
The full trusted subject snapshot, including aliases, description and reference URL, must match;
target ID is only a file-selection shortcut. The question key applies Unicode `casefold()` and
collapses runs of ordinary ASCII spaces. It does not remove punctuation, strip surrounding
whitespace, normalize tabs/newlines, stem words, or use semantic similarity. Original wording
is retained. Existing action/request validation still applies before lookup.

Each source must be a completed, scoring-eligible trial with verified integrity and locally
validated typed data. Recorded role prompt versions and rendered prompt hashes must match the
current question, subject and original evidence. Required review/Judge decisions must exist,
use the selected answer vocabulary and permitted evidence basis, and reference valid evidence
indices. Incomplete research, missing audits, failed retrieval, and already-reused answers do
not seed the cache. Conflicting final tokens for one compatible question disable that key.
When several matching records agree, use the latest answer timestamp, then original call ID
for deterministic tie-breaking.

Answers are historical observations, with their original timestamps. There is no automatic
claim of freshness or time-based expiry in v1. Use `--no-oracle-cache` on a new execution when
fresh research is required. Review historical reuse when evaluating time-sensitive questions.

## Process and snapshot behavior

Each benchmark process has a private memory cache. There is no shared answer database or
writer. Trial YAML is saved atomically after each game, subject aggregates after their trials,
and the full benchmark result at the end. Cache readers use original trial files. They do not
wait for the source benchmark to finish and never consume a partially completed game.

New direct benchmark executions without `--oracle-history-before` record
`discovery_policy: per_subject_history_v1` alongside `historical_ask_v1`. Startup records the
initial inventory and policy in the signed manifest. Before each subject's first game, the
benchmark scans the three history roots again for compatible manifests and that subject's
completed trial files, using a new cutoff. This includes games saved by other processes since
this execution started, including executions that started later.

The benchmark atomically saves that subject inventory, including an empty inventory, to
`subjects/<target-id>/oracle-history-<parent-snapshot-hash>.json` before using it. This is an
execution-owned checkpoint of file references, not a shared answer database. Hits record the
subject inventory's hash and original answer provenance. The final result includes these
inventories in `run.oracle_cache_loads[].snapshot`. A subject loads once per process: further
external games for that subject are not discovered between its repetitions or questions.
Later subjects each receive their own scan. Concurrent misses can still make independent
paid calls; there is no wait for another process's in-flight answer.

File fingerprints include size, inode and modification/change times. Opened-file fingerprints
are checked before and after reading. Changed, deleted, corrupt, or partially written source
files are skipped and counted. Duplicate JSON/YAML keys are rejected. Full result integrity is
checked before use. Diagnostic output, public JSON, GUI state, and prepared review indexes
never supply answers. Signed execution events are used only to exclude source runs with Oracle
contract revisions; they never supply answers. The existing execution lock protects inventory
checkpoints; no new lock or shared writer is added.

Resume restores each visited subject's saved inventory, including empty inventories. It fails
if a started subject's checkpoint is missing or corrupt. Subjects not yet visited can discover
new history when they start. Eligible live answers from this execution's completed games are
still added under `same_execution_ask_v1`. An explicitly authorized Oracle contract repair
clears external history and disables further subject discovery for that execution, retaining
the earlier empty-inventory repair behavior.

With an explicit `--oracle-history-before`, startup freezes the inventory for the entire
execution. Older manifests without `discovery_policy` retain that frozen behavior. Resume
cannot enable caching for an older execution or change its recorded discovery policy or cutoff.
A changed factual contract or routing exclusion requires a new execution ID unless using the
explicit contract-repair exception.

For a model comparison batch, pass the same timezone-aware, past ISO timestamp with
`--oracle-history-before` to every new execution. Keep the source artifacts immutable for the
batch. Without this option, new direct and batch executions discover history per subject, so available
answers can depend on process timing. The manifest and subject checkpoints record the
inventories and their hashes.

The repository batch launcher defaults to per-subject discovery across concurrent model runs.
No option is needed; `--refresh-oracle-history` remains an explicit spelling of that default.
Use `--oracle-history-before` for a shared fixed cutoff or `--no-oracle-cache` to disable reuse.
These options are mutually exclusive. Saved batches retain their recorded settings on restart,
including older fixed cutoffs. See the
[benchmark guide](../source/execution/benchmark/README.md#catalogs-and-scheduling).
The batch plan is never a provider request or answer source; the benchmark builds and validates
its own inventories.

## Removing unwanted runs

Delete an unwanted execution's complete artifact directory and any copies under all three
history roots: `runs/`, `archive/`, and `benchmark-logs/superseded-runs/`. Moving a run into
an archive does not exclude it from answer reuse. Remove its matching launch logs and any
private artifact snapshots as part of the cleanup.

There is no separate persistent answer-cache database to clear. New processes cannot load
deleted source files. A running process may already hold answers in memory, so stop affected
benchmark processes before deletion and use fresh execution IDs afterward. Rebuild publication
output if it contains the removed executions. Git history and private review reports are not
cache inputs.

## Repeated questions within a game

New cached benchmark executions also record `episode_reuse_policy: same_episode_ask_v1` in
their signed inventory. The game engine keeps a private in-memory map for each `play` call.
After a successful live ASK finishes all required adjudication, the engine stores its final
answer, original evidence, quality decision and sanitized role audit. A later ASK with the same
normalized question reads that entry before consulting historical sources. It still consumes
one question and one Guesser turn, including at the question limit. GUESS is never cached.

The first live response is the source: `cache_source.policy` is `same_episode_ask_v1`, with the
original run, episode, subject, turn, Oracle call, question and answer timestamp. There is no
source file or file hash for this memory entry. The retained result validates the reference
against the earlier live turn and its role audit. Failed retrieval does not seed memory; a
semantic UNKNOWN does. Historical hits retain their historical provenance on repeated use.

This engine-local map is discarded at the end of the game, including failures. Reusing the same
engine object starts a new map; the benchmark's separate execution cache can supply answers
from completed games. There are no cache file writes or locks. `--no-oracle-cache` disables all ASK policies on new
executions. Resuming an older inventory without `episode_reuse_policy` preserves its original
historical-only behavior; an execution without caching remains uncached.

## Repeated questions across games in one execution

New cached executions record `execution_reuse_policy: same_execution_ask_v1` in the signed
inventory. After the benchmark atomically saves a completed, scoring-eligible trial, it reads
and integrity-validates that original artifact and adds its eligible live ASK answers to the
shared subject map. Later repetitions can reuse them even if the subject initially had no
historical matches. Each key still requires the complete trusted subject snapshot, normalized
question, and compatible Oracle configuration, factual contract, role prompts and routing.
Reused turns do not become new sources. Conflicting final tokens disable the key for the
execution; a later agreeing record does not re-enable it. Failed retrieval, `bounded_unknown`,
missing required role audits, and infrastructure-failed games never seed this cache.

The policy reuses the historical candidate validator, with the original game's completion time
as its answer-time limit instead of the external history cutoff. Each captured external inventory remains
frozen. Every hit records `cache_source.policy: same_execution_ask_v1`, the current execution,
original trial/episode/turn, original answer timestamp, and the source artifact's integrity hash.
Original evidence and adjudication are retained; the new turn incurs no adjudicator call or cost.

Resume rebuilds the execution map from verified completed trials in the signed schedule before
running another game, including repairs of earlier failed positions. An explicitly authorized
Oracle contract revision excludes every game started before the active revision. Other models
and concurrent executions cannot see this private map. Per-subject discovery can read the
original saved games through their trial files. No new persistent cache database or
shared writer is added. An older inventory without `execution_reuse_policy` keeps its recorded
behavior; its snapshot serialization and integrity hash do not change.

Every Guesser starts with its own fresh conversation. Only the final ASK token is reused; cache
provenance and evidence never enter its messages or another live adjudicator request. Fully
adjudicated answers can still be factually wrong: cache eligibility is not a truth guarantee,
and monitoring comments alone do not invalidate an entry. Use `--no-oracle-cache` when each
repetition must measure a fresh Oracle answer. Comparisons should disclose this reuse policy.

## Logs, accounting and results

The benchmark logs `benchmark.oracle_cache.loading` and `benchmark.oracle_cache.loaded` for
inventory discovery and each loaded subject. Completion lines include elapsed milliseconds,
file/byte counts, records found, eligible records, retained entries, conflicts and skipped files
where applicable. Ordinary turn logs include `answer_source=live`, `answer_source=historical`,
`answer_source=same_execution`, or `answer_source=same_episode`. Execution-cache updates log
eligible-answer, retained-entry and conflict counts after a game. Same-episode hits identify the original episode, turn and
answer time; historical turns identify the original execution, trial, turn and answer timestamp. Console
output never includes source evidence or call IDs.

Every reused turn and its marked retained role audit carry an identical `cache_source`.
Historical sources include original execution/model/benchmark/subject/trial/episode/Oracle-call IDs, turn number, question,
answer time, source file and integrity hash, snapshot hash, context hash and normalization
version. `summary.oracle_cache_hits` counts reuse separately from provider prompt-cache tokens.
Original provider telemetry remains in the marked audit as historical information. A hit adds
zero new provider calls, tokens, searches, retries, cost or provider latency; it does not count
as a new Reviewer/Judge invocation. The current episode duration includes actual cache work.

The final benchmark `result.yml` retains the startup and subject inventories, this process's subject-load
statistics, all per-turn provenance, original evidence and quality decisions. Trial and subject
YAML also retain the source-marked episode results. Existing records omit the optional fields.

The publication compiler exports an explicit source allowlist: execution, model, benchmark,
subject, trial, episode, turn, original question and answer time. Internal source paths, cache
context/snapshot hashes, and Oracle/provider call identifiers are not public. The Vue transcript
labels reused answers and offers an expandable source disclosure next to the copied evidence.
Same-episode sources use the explicit public `scope: same_episode` variant with subject,
episode, turn, question and answer time; the GUI links back to the original turn in that game.
The optional provenance field is representable in both the current v10 dataset and the
maintained standard-answer v9 compatibility download.
Cross-game sources within the current run use public `scope: same_execution`, with the same
allowlisted execution/trial attribution as historical sources. The transcript explicitly labels
them as answers from an earlier game in this benchmark run.

## Isolation and provider prompt caching

Only the final answer token enters Guesser history. Cache evidence, labels, IDs, versions,
telemetry, and source questions never enter Guesser/Validator requests or later fresh
Oracle/Reviewer/Judge requests. Cache misses use the existing blind live pipeline unchanged.
All requests still use their existing provider prompt-cache namespaces, controls and prices;
there is no prefix padding or provider response caching. Cache hits make no LLM request and
therefore have no new prompt-cache read/write tokens. Historical billing is not a measured
counterfactual saving. Required route canaries and prefix-cache assessments still apply before
paid launches.
