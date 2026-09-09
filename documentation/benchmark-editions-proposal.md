# Benchmark edition design record

Status: implemented locally on 6 September 2026. This file preserves the original proposal,
including its pre-implementation repository snapshot and planned work. It is a historical
design record, not the current implementation guide. Present and future tense below refer
to that proposal's date.

The current contract is in [publication README](../source/publication/README.md#edition-contracts).
Both editions, qualification checks, scoped data, compatible v9 export, selector, comparison,
and empty states are implemented. Release prompt/configuration pins remain separate from
later execution defaults, including the newer Judge and Validator policies. The public
Methodology now includes the [qualified-answer rationale](five-answer-experiment.md#why-add-qualified-answers).

## Historical proposal - 6 September 2026

## Recommendation

Present **Deep20Bench 1.1** as the current edition and **Deep20Bench 1** as the previous edition. Both use the same application, result views, scoring implementation, and transcript components. Each edition owns its comparison cohort, selected runs, rankings, methodology, and downloads.

Use a persistent **Benchmark edition** selector with `v.1.1 · Current` first and `v.1.0 · Previous` second. Fresh visits open 1.1. Explicit links to edition 1 always open edition 1. An edition is part of the benchmark's public identity, including page titles and citations.

The four directional answer classes are `YES`, `RATHER_YES`, `RATHER_NO`, and `NO`; only the two qualified classes are new. `UNKNOWN` remains a fifth possible ASK token. Describe this as **four directional answers plus Unknown**. Guess validation still accepts only `YES`, `NO`, and `UNKNOWN`. These labels must not imply that qualified answers represent numeric probabilities.

Edition numbers are strings, not floating-point numbers or software semantic-version promises. Use machine IDs `1.0` and `1.1`, with display labels `1` and `1.1`. Keep these separate from game protocol 9, public dataset schema 9/10, prompt versions, benchmark IDs, and frontend package versions.

## Repository snapshot before implementation

| Area | Current state | Consequence |
| --- | --- | --- |
| Historical publication | `core-v2`, B-0001, 7 subjects, 5 repeats, 50-question limit | This is the initial edition 1 cohort. |
| New-game template | B-0003, paired `qualified_v1`, 3 repeats, 40-question limit | Define a separate edition 1.1 cohort. |
| Subject scheduling | 10 active subjects; Stephen King and Mario remain registered but inactive | Freeze explicit publication subjects instead of following future active-status changes. |
| Publication configuration | A tuple of cohorts, exactly one `active` | Extend the existing registry rather than create a second catalog. |
| Run discovery | Validates qualified manifests, then excludes their summaries and episodes | Add full typed support before admitting these runs. |
| Qualification | Rejects every nonstandard prompt profile; does not enforce cohort benchmark ID | Add explicit edition membership checks. |
| Frontend | Shared Vue views; global manifest and leaderboard URLs | Make edition identity an explicit loader and route parameter. |
| Existing qualified diagnostics | Discovered B-0003 manifests use 50 questions and one subject | None matches the proposed 40-question, ten-subject release cohort. |

At proposal time, the public manifest contained 18 evaluated model configurations. This was a snapshot, not a fixed GUI count. The qualification work proposed here was subsequently implemented; its current checks are documented in the publication README.

Relevant sources: [publication configuration](../config/publication.yml), [benchmark definitions](../config/benchmarks.yaml), [subject catalog](../config/subjects.yaml), [five-answer specification](five-answer-experiment.md), [publication package](../source/publication/README.md), and [homepage specification](homepage-creation.md).

## User experience

### Selection and visual treatment

Keep the current paper background, dark typography, serif headings, and blue result accent. When space permits, place the edition selector in the dark header row before Source, with an outlined group and lime highlight for the selected version. Keep the name available on hover and to assistive technology, and align all header controls vertically. Below 960 pixels, keep a slim row directly below the main navigation. Both placements stay outside the result metric tabs and distinguish **which benchmark** from **which result measure**.

Use a two-option segmented control at comfortable widths and a labeled native select on narrow screens. Selected state uses dark fill and explicit text; the previous edition remains fully legible. Do not introduce edition-specific color themes that compete with the existing score, stability, cost, time, and efficiency colors.

Below the page heading, show a compact definition strip derived from the selected cohort:

- Edition 1.1: `10 subjects · 3 rounds per subject · 40-question limit`.
- Edition 1: `7 subjects · 5 rounds per subject · 50-question limit`.

The 1.1 values are the proposed release settings based on today's configuration. Freeze them before admitting results. Show the answer vocabulary nearby, with a short **What changed** disclosure. An edition 1 page carries the neutral text `Previous edition`; avoid warning styling.

Keep selected edition visible in run, subject, and episode views, chart headings or accessible descriptions, data exports, and document metadata. Transcript labels show `Rather yes` and `Rather no` in full. Technical details retain exact wire tokens. Qualified answers use distinct text and softer visual emphasis; meaning never depends on color alone.

### Navigation rules

1. Fresh `/` and unversioned general result URLs open edition 1.1. Browser storage does not override an explicit URL or make the fresh default unpredictable.
2. Use stable edition URLs: `/editions/1.0/` and `/editions/1.1/`, with `/results/`, `/results/cost/`, `/results/time/`, `/results/reliability/`, `/results/efficiency/`, `/methodology/`, and `/data/` beneath each prefix.
3. Switching editions preserves the current result measure and compatible display choices. Back/Forward restores the edition because the selection changes the URL.
4. Existing `/runs/<execution>/subjects/<target>/episodes/<trial>/` URLs retain their recorded run identity. The publisher supplies edition membership; the page derives its selected edition from that identity.
5. From a run or subject page, switch to the destination edition's selected run for the same immutable model ID, retaining the subject only when present. If no counterpart exists, open that edition's results with a brief explanation. Do not match models by display name.
6. From an episode, switch at most to the matching destination subject page. Trial numbers across these changed experiments do not identify equivalent episodes.
7. Unknown edition IDs show a clear unavailable page and links to valid editions. Never silently substitute the default under an explicit unknown edition URL.

Unversioned overview/result/method/data URLs are documented current-edition aliases; they cannot identify historical comparison settings. Prerender their current content and give aliases a canonical link to the stable edition destination. Keep self-referencing canonicals and sitemap entries for stable edition pages. About remains site-wide. Existing exact run links remain stable. Generate alias HTML locally because GitHub Pages cannot depend on server routing rules or a JavaScript redirect for initial content.

### What changed and comparison limits

Show both definitions in a short table on the methodology page. Include answers, subject set, repeats, question budget, failure penalty, and the changed Guesser/adjudication prompt policy. The new review policy is evidence-only and every exact-token disagreement requires the Judge; this is more than a label change.

Keep score, confidence intervals, cost, timing, Pareto flags, and efficiency normalization within the selected cohort. Edition 1 has a failure penalty of 51; proposed edition 1.1 has 41. The average-within-subject, then average-across-subjects rule stays shared.

Do not pool scores, rank the editions together, carry over missing model scores, or label a difference as model improvement. Different subjects, budgets, prompts, and repetition counts prevent that interpretation. A later comparison page could show two clearly separated columns, but it is outside the first delivery.

### Empty and partial coverage

Edition 1.1 can be the default before it has qualified data. Show `No complete 1.1 results yet`, its full benchmark definition, and an ordinary action to view edition 1. Hide the winner and ranking chart in that state.

After the first full model run qualifies, show only qualifying model configurations and the evaluated count. Do not require every registered model to finish before displaying results. Describe a sole result as one evaluated model rather than a competitive winner.

Missing or infrastructure-failed trials do not qualify. Completed model failures still count and receive the edition's penalty. A model absent from 1.1 is unmeasured there, not worse. Loading or fetch failure uses an error state, not an empty-results claim. Never display a previous edition's rows beneath the newly selected edition heading while loading.

## Implementation design

### One registry and one compilation path

Extend `CohortConfig` in the existing publication configuration with edition metadata and explicit eligibility settings. Advance `PublicationConfig` to version 2. Replace the per-cohort `active` flag with one `default_edition_id: "1.1"`. Initially enforce one published cohort per edition. Retain historical `cohort_id: core-v2` instead of renaming its identity.

Suggested new fields are `edition_id`, `edition_label`, `edition_status` (`current` or `previous`), and `eligibility`. Reuse existing fields for benchmark ID, target IDs, seed, iterations, budget, and model IDs. Derive labels, answer descriptions, counts, and penalties from typed edition/cohort data; do not duplicate them in Vue. Validate unique IDs, exactly one current edition, and agreement between current status and default ID.

Use a small discriminated eligibility type with two explicit policies: historical standard and qualified release. Avoid a generic rule language. Both require the declared benchmark identity and paired answer profiles. Historical edition 1 preserves its existing valid selection and documented allowances for historical seeds, prompt versions, and model settings; audit the effect of adding benchmark-ID enforcement before enabling it.

The qualified release policy additionally pins the selected subject identities, base seed, 40-question budget, three completed repetitions per subject, and approved prompt/adjudication revision. Validate recorded resolved versions in every retained episode, including repaired trials, so runs made before and after a prompt change cannot slip into one edition through the same `qualified_v1` name. Validate the recorded support-role configuration against the release policy; use immutable Guesser model IDs and their signed snapshots for model identity.

Freeze edition 1.1's proposed targets as `T-0001`, `T-0002`, `T-0004`, `T-0005`, `T-0006`, `T-0008`, `T-0009`, `T-0010`, `T-0011`, and `T-0012`. The current expected Guesser revision is `stateful-category-guesser-v16-five-answer-category-guide`, which includes the fixed guide to category meanings; the corresponding Oracle/recovery/Reviewer/Judge versions are specified in the five-answer document. Do not assume that a matching benchmark ID alone establishes this revision. New default catalog values must never alter either edition retrospectively.

Extract `compile_cohort(runs, cohort, ...)` from `compile_publication`. Compile each cohort independently from validated inputs. Select the newest qualifying completion per `(edition_id, model_id)`, retain exact ties, and fail on latest-timestamp ambiguity within that key. Reuse existing Decimal scoring and confidence-interval functions. Make model metadata edition-local: the current global map must not overwrite historical signed metadata when an ID occurs in both editions.

### Qualified source and public contracts

Replace the discovery skip with full validation of supported qualified summaries, states, and episodes. Keep original signed representations intact. Extend typed readers for the actual qualified counters, adjudication data, and answer variants before projecting anything. Valid diagnostics can be classified as outside a published cohort; malformed or tampered supported artifacts still fail the build.

Use separate factual and identity answer types. A factual ASK answer can contain five tokens in the qualified profile; a GUESS answer can contain only three. Preserve cross-field checks, not just a broader string union. Exposing `RATHER_YES` in the public schema must not accidentally make it valid for guess validation or a standard transcript.

Advance the primary public dataset to schema 10. Add a small edition index at `data/editions.json` with available editions, default ID, and typed document references. Publish edition manifests, leaderboards, repeat averages, and downloads under `data/editions/<edition-id>/`. Keep globally unique run/subject/episode document paths where practical and add validated edition ownership. Bump each changed split-document contract explicitly. Use one internal typed projection with deliberate serializers for supported public formats.

Keep `data/deep20bench-v9.json` and its companion v9 schema as a maintained edition 1 compatibility projection. Regenerate them on every build from all current qualifying data representable by that contract. Preserve their existing score and cohort meaning. Never squash qualified answers to YES/NO or insert edition 1.1 rows into edition 1. The v9 contract cannot represent both cohorts and five-token transcripts losslessly; document the excluded edition 1.1 results and link to schema 10 on the Data page. Existing versioned and unversioned data endpoints require an explicit compatibility inventory before changing their meaning.

### Shared frontend

Add one `EditionSwitcher.vue` and a small `useEditionContext` composable derived from route identity and the edition index. Existing views receive the selected edition's manifest and result documents. Avoid duplicate `HomeV1`/`HomeV11` or result pages. Central route helpers supply edition-aware destinations.

Update API, preloaded page-state, and view-cache keys to include edition identity and the referenced document path/build identity. Scope model selection, sort state, and repeat averages appropriately. Reuse `useKeyedPublicationLoad` to reject responses for a previous edition, and clear or gate previous data until the destination documents agree on edition identity. Validate fetched and embedded documents consistently, including schema and edition identity.

Review `KeepAlive` keys and page initialization: reusing the same Vue component across editions must reload its data and context. Static rendering and hydration must resolve the same edition from the route. Keep the current small split-document loading model; switching editions must not download both complete datasets.

Make homepage examples, methodology, answer legends, scoring copy, result counts, downloads, and citation text edition-aware. Site-wide About content stays shared. No new framework, database, backend, state-management dependency, or deployment service is needed.

### Main code locations

| Change | Existing source |
| --- | --- |
| Edition/cohort registry | [config/publication.yml](../config/publication.yml) |
| Strict config, source, and output contracts | [models.py](../source/publication/compiler/src/deep20_publication/models.py) |
| Discovery and qualified readers | [cli.py](../source/publication/compiler/src/deep20_publication/cli.py), [loader.py](../source/publication/compiler/src/deep20_publication/loader.py) |
| Per-edition qualification and aggregation | [compiler.py](../source/publication/compiler/src/deep20_publication/compiler.py) |
| Split documents and generated routes | [split.py](../source/publication/compiler/src/deep20_publication/split.py) and the site prerender script |
| Selector placement | [SiteHeader.vue](../source/publication/site/src/components/SiteHeader.vue); add `EditionSwitcher.vue` |
| Typed document loading and initial state | [api.ts](../source/publication/site/src/lib/api.ts), [types.ts](../source/publication/site/src/lib/types.ts), [page-state.ts](../source/publication/site/src/lib/page-state.ts) |
| Routes, helpers, and cached views | [router.ts](../source/publication/site/src/router.ts), [route-location.ts](../source/publication/site/src/lib/route-location.ts), [App.vue](../source/publication/site/src/App.vue) |
| Reactive request identity | [use-keyed-publication-load.ts](../source/publication/site/src/lib/use-keyed-publication-load.ts); add `use-edition-context.ts` |
| Copy and answer rendering | Existing Home, Results, Methodology, Data, and Episode views |

### Execution and isolation

This change consumes completed results. It does not add edition labels to Guesser history, requests, variation tokens, provider metadata, sessions, or prompt caches. It does not rewrite signed runs or change game protocol 9 merely to display edition 1.1.

The current execution configuration rejects `qualified_v1` in `official` mode. Publishing a validated completed run under a declared edition is separate from changing execution-mode rules. Preserve the recorded experimental mode in provenance; qualification follows the explicit release policy. Decide any future official-mode support in a separate execution change, with its own required specifications and isolation tests. Do not silently change modes or claim diagnostics were official executions.

Provider prompt caching is not applicable to this publication feature: no LLM call is added. Browser caching stores only generated public reports, isolated from execution. Keep the publication dependency and public-field allowlist tests. No prompt-policy, scoring, or runtime retry changes are part of this proposal.

## Delivery plan

| Step | Concrete work | Completion evidence |
| --- | --- | --- |
| 1. Freeze definitions and audit compatibility | Record edition 1's current selected runs and metrics; finalize 1.1's explicit cohort/revision; inventory old URLs and source shapes | A fixture proves old selections and numeric results remain unchanged; every discovered new run has a qualification reason |
| 2. Support both editions in the compiler | Extend config/read models, validate qualified artifacts, compile per edition, emit schema 10 and maintained v9 | Integrity, profile separation, exact ranking, counter, and export tests pass for both editions |
| 3. Connect routing and data | Add edition index/context, selector, stable paths, scoped loading and page state | Direct reload, edition switching, Back/Forward, counterpart fallback, and delayed-response tests pass |
| 4. Complete visual and editorial work | Update overview, all five result views, method, data, citations, transcripts, metadata, and responsive empty states | Desktop/mobile and keyboard checks pass; initial HTML and hydrated content show the same edition |
| 5. Generate and verify locally | Regenerate the entire `docs/` tree; run deterministic check and old-link checks | Both editions work on a local static HTTP host; v9 remains valid and current; no source run changed |

Steps 2-4 can be reviewed as separate local changes with a two-edition fixture. Each fixture should contain a shared model, a model missing from 1.1, qualified ASK answers, ordinary GUESS answers, and both completed model failure and infrastructure failure. Actual paid runs are independent of GUI delivery and need their own authorized launch scope. Use three iterations per subject and model when that work is requested.

Required focused checks:

- Edition 1 membership, selected execution IDs, scores, ties, uncertainty, and retained-attempt cost remain unchanged for identical source inputs.
- Standard and qualified profiles cannot mix; B-0002, old qualified prompt revisions, 50-question qualified diagnostics, wrong subjects/seeds, and incomplete coverage cannot qualify for 1.1.
- Tampered manifests, summaries, state, and trial files fail; relaxed answer parsing cannot relax other validation.
- `RATHER_YES`/`RATHER_NO` render correctly for qualified ASK and are rejected for GUESS and standard ASK.
- Winners, Pareto flags, efficiency bounds, and confidence intervals use only their own edition.
- An empty 1.1 never borrows edition 1 data; a delayed 1.0 response cannot overwrite 1.1 after rapid switching.
- Explicit old edition and existing exact run links survive; subject/episode switching never invents counterparts.
- Downloads, metadata, JSON-LD citations, sitemap, prerendered page state, and hydrated views identify the same edition.
- Strict Python/Vue/TypeScript checks and publication boundary tests pass. Verify layouts at 360px, tablet, and desktop widths with keyboard operation and no horizontal clipping.
- Full local publication build and `build --check` pass; the v9 compatibility dataset still validates against its unchanged companion schema.

Expected scope: a moderate publication feature spanning configuration, the compiler, and shared frontend data/routing. The main risk is an incorrect edition-to-run mapping, followed by stale frontend data and incomplete legacy URL handling. A visible selector alone would not resolve those issues.

The original proposal did not itself change application source or generated output. Its later implementation and subsequent publication-source changes require complete local `docs/` regeneration. Do not commit, push, open a PR, or publish externally without an explicit request; do not create a Codex Sites project for this repository.
