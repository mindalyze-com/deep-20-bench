# Concise prompt experiment

`B-0002` tests concise Guesser and factual-adjudication instructions. It uses the existing
`YES`, `NO`, and `UNKNOWN` protocol, action schema, scoring rule, subject catalog, and model
routes. All benchmark templates now use a 40-question limit. `B-0001` retains its original
prompt profile. The early diagnostic runs were removed. New runs need fresh execution IDs
and must record their definition and cache policy.

Both `GamePolicy.prompt_profile` and `OracleConfig.prompt_profile` accept `standard`,
`concise_v1`, or `qualified_v1`; this experiment compares the first two. The default is
`standard`, omitted from serialization to preserve existing
manifest hashes. `B-0002` selects `concise_v1` for both. Revised prompts require experimental
mode. The CLI rejects an official launch before loading credentials or making startup calls;
the typed benchmark definition and game engine also enforce this boundary.

## Changes under test

The Guesser is told that an answer applies only to its question, activities can overlap, and
`UNKNOWN` gives no justified direction. When questioning stops helping, it should reconsider
its interpretation and assumptions and ask about another property. A brief fallibility note
does not permit dismissing an answer merely because it conflicts with a preferred candidate.
The instructions contain no real subjects or details from earlier games.

The concise Guesser now uses `stateful-category-guesser-v15-concise-category-guide`. It includes
the same fixed category guide as the standard and five-answer Guesser profiles, covering the
broad scope of `thing` as well as the character and person categories. This adds no selected
subject hints, catalog entries, or category-dependent branches. Use fresh execution IDs and
cache probes for the changed prefix; earlier results retain their recorded prompt versions.

The Oracle's shorter policy distinguishes direct factual deductions from missing evidence.
The same factual rules are included in primary research, independent recovery, Reviewer, and
Judge prompts. No research answer may rely on memory alone. Reviewer and Judge retain their
narrow labelled knowledge exception for stable, established relations with a unique answer.
It still excludes open-world, current, subjective, disputed, and completeness claims.

This is a combined intervention, including aligned Reviewer and Judge wording. Its results
cannot identify whether the Guesser or evidence-policy change caused an improvement.

## Isolation and persistence

All model-visible data projections are unchanged. The Guesser sees only its fixed system
instructions, category, subject-independent variation token, valid actions, final protocol
answers, and canonical `FORMAT_ERROR`. The profile adds no per-turn hint or private state.
Reviewer and Judge remain blind to earlier decisions and have no web access. Recovery sees
no prior queries, results, or history. Oracle `UNKNOWN` remains final; every Oracle `YES` or
`NO` requires review, disagreements require Judge, and required-role failure remains
infrastructure failure. Identity validation is unchanged.

Selected prompt versions enter call audits, result metadata, and prompt-cache namespaces.
Guesser calls reject a system prompt that does not match the selected profile before using
the provider. Standard and revised cache probes cannot certify one another. Provider prefix
caching remains available with measured usage. Benchmark ASK reuse follows the separate
[historical and same-game policies](oracle-history-cache.md); it is not a prompt-profile
feature. Provider response caching remains disabled, with no padding or assumed savings.
Shorter prompts may fall below route cache thresholds.

The publication reader accepts the new optional profile metadata. Revised profiles are
excluded from the standard leaderboard even if they cover every subject and trial. Existing
public results and the v9 compatibility URL remain available. No experimental GUI is added.

## New diagnostics

Select active subjects and a fresh execution ID, and record the intended definition and cache
policy. Use detached macOS `screen` jobs with `nohup` and `caffeinate`, following the
[benchmark launch rules](../source/execution/benchmark/README.md). Revised experimental runs
perform startup canaries by default. Each evidence canary uses the selected prompt profile
in a separate synthetic session.

Compare all scheduled trial outcomes, counted and penalized question totals, unknown answers,
contract violations, and recorded costs. A small selected-subject test cannot establish a
general improvement or model ranking. Keep failures and infrastructure outcomes visible.
