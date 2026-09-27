# Codex as Oracle

The [subject results and model-ranking comparison](comparison.md) brings together eight
direct-Codex experiments and their regular-Oracle references. It includes the dated results
by subject, each model's changes, and rankings on matching completed games. See also the
related [Akinator question-count comparison](../akinator/README.md).

New experiments can use the main benchmark's explicit [edition 1.2 DRAFT](../../edition-1.2-draft.md).
It supports OpenRouter, Ollama, interactive workers and mocks through role interfaces, with
one scheduler and a durable work queue. It remains local and inactive. Models are selected
with `--model`; role overrides are configuration, so new models need no Python wrapper.

The instructions below describe the earlier generic experiment helper and its existing runs.
Keep those entry points for their saved executions; they do not have the new draft's blind
worker and managed research contracts.

Use [experiment.py](src/experiment.py) for the earlier experiment format. Select the Guesser with
`--model`; no model-specific Python wrapper or environment selector is needed. Model IDs
load their registered route, reasoning, output limit and prompt-cache configuration.

From the repository root:

```sh
HELPERS=documentation/analysis/codex-as-oracle/src
.venv/bin/python "$HELPERS/experiment.py" models
.venv/bin/python "$HELPERS/experiment.py" preview \
  --model M-0001 --execution BX-codex-oracle-example \
  --budget-usd 5 --baseline BX-20260908-B-0003-experimental-M0001-001
.venv/bin/python "$HELPERS/experiment.py" progress --execution BX-codex-oracle-example
```

These commands are offline. The example $5 cap is a preparation parameter, not permission
to spend. Preview defaults to three games per active subject and seed 0; `--iterations`
and `--seed` can override those values. `--baseline` is optional and enables comparison.
Preview saves the selected model, subject selection, configuration and spending limit under
`private/reviews/codex-oracle/<execution>/`. Later commands need only `--execution`; an
optional `--model` must match the saved selection. Preview cannot overwrite an execution.

After explicit live authorization, launch the following command using the detached
`screen` and `caffeinate` procedure in the
[benchmark instructions](../../../source/execution/benchmark/README.md):

```sh
.venv/bin/python "$HELPERS/experiment.py" run --execution BX-codex-oracle-example --live
```

The shared launcher rejects changes since preview, checks route capabilities and pricing,
runs one startup canary, then uses the same budget guard for every game and HTTP retry.
It derives conservative reservations from the selected route's advertised input, cache-write,
output, request and tier prices, with a 10% margin. It changes no model parameters. Reported
billing replaces each reservation; missing billing stays reserved. Unknown canary cost is
reported as `null`. A launch is claimed once, including failed startups. A new execution is
a separate experiment and budget; further paid attempts require authorization that accounts
for earlier spending. Existing failed artifacts must be retained.

An active Codex operator still researches and supplies every support decision:

```sh
.venv/bin/python "$HELPERS/experiment.py" pending --execution BX-codex-oracle-example
.venv/bin/python "$HELPERS/experiment.py" next --execution BX-codex-oracle-example --after 1
.venv/bin/python "$HELPERS/experiment.py" submit --execution BX-codex-oracle-example --input decision.json
.venv/bin/python "$HELPERS/experiment.py" comparison --execution BX-codex-oracle-example
.venv/bin/python -m pytest "$HELPERS" -q
```

Copy the pending work's `kind`, `sequence` and `request_hash` into the decision JSON along
with the fields defined in [bridge.py](src/bridge.py). Submission rejects missing or stale
request identity. All inspection, submission and test commands are offline. The helper does
not start a Codex conversation or schedule progress notifications.

Prompt-caching assessment: retain the registered automatic or explicit prefix-cache policy,
fixed instructions, append-only visible history and existing role namespaces. Add no padding
or response caching; all ASK decisions remain fresh. Record actual provider cache usage and
billing, without assuming savings. The shared CLI changes only selection, launch accounting
and reporting. Support usage and caching within the Codex conversation remain unmetered.

The model-specific commands below are compatibility helpers for existing experiments.
Their saved IDs, artifacts and historical limitations remain separate from the generic CLI.

The [Grok 4.6 experiment](grok46-results.md) completed all 30 games with the
existing high-reasoning registration, `M-0015`: 29 successes and a mean score of
16.40. Recorded Grok cost, including startup, was $3.946766; Codex support cost is
unmeasured. Select its private run with `DEEP20_CODEX_EXPERIMENT=grok46`. It used
a private helper snapshot to preserve the experiment during concurrent edits.

The [Claude Fable 5.1 experiment](fable51-results.md) uses the existing high-reasoning
registration, `M-0020`. Its [helper](src/fable51.py) selects a separate 30-game run.
The run stopped under its $11 spending guard at $7.53240350, with 27 games complete,
one interrupted and two unstarted. Its report includes the partial comparison and accounting.

The [Muse Spark experiment](muse-results.md) completed all 30 games using the existing
Muse Spark 1.3 Contributor (high) registration, `M-0026`: 30 successes and a mean
score of 19.33, compared with 18.37 in the regular reference. Reported Guesser cost,
including startup, was $0.200705416. Charges plus a reserve for one retry with missing
billing are $0.323257736, below the $9 cap; Codex support cost is unmeasured. Its
[helper](src/muse.py) selects the separate private run. The report documents shared
support context and uneven operator interpretations.

This experiment measures how Gemini 3.8 Flash's question count changes when a Codex
conversation supplies the Oracle, Reviewer, Judge and guess-validation decisions. It runs
three consecutive games per subject, collects fresh answers without the question cache,
and saves the regular benchmark artifact format.

The support roles share one Codex conversation; they are not independent blind reviewers.
See [results.md](results.md) for the completed 30-game comparison and its limitations.

The [GPT OSS experiment](gptoss-results.md) uses the existing gpt-oss-120B (high)
registration. Its 30-game setup is prepared; live execution is awaiting explicit scope
and spending-limit authorization. Set `DEEP20_CODEX_EXPERIMENT=gptoss` for its helper commands.

The [GPT-5.6 Luna experiment](luna-results.md) uses the existing Luna (high) registration,
`M-0001`. All 30 games completed, with 25 successes and a mean score of 22.67.
Reported OpenRouter charges were $0.23703388; charges plus the reserve for unmetered
startup failures were $2.44760268, within the authorized $5 cap.
Set `DEEP20_CODEX_EXPERIMENT=luna` for its helper commands.
The later [five-case Luna replay](luna-repair-results.md) produced three successes and two
further failures. Original scores remain unchanged; cumulative charges plus the retained
reserve were $2.51142306 under the same $5 cap.

The same experiment with Claude Opus 5 (high) is documented in
[opus5-results.md](opus5-results.md): all 30 games completed, with 29 successes
and a mean score of 18.00. Select its private run with
`DEEP20_CODEX_EXPERIMENT=opus5` before using any helper; the default remains
the historical Gemini run. Both selections schedule three games per active subject.

All helper code is in [src/](src/):

The Astra run solved 27 games before its spending guard stopped further play.
Results, the paired comparison and accounting are in [astra6-results.md](astra6-results.md).
Use [src/astra6.py](src/astra6.py) for its commands and separate private run.

| Helper | Purpose |
| --- | --- |
| [experiment.py](src/experiment.py) | Select any registered Guesser and prepare, launch or inspect its experiment. |
| [spend_guard.py](src/spend_guard.py) | Shared route-price validation and per-attempt budget accounting. |
| [bridge.py](src/bridge.py) | Prepare a run, show pending work and accept typed Codex decisions. |
| [live_entry.py](src/live_entry.py) | Shared route check, startup canary and game launch used by the entry points. |
| [next.py](src/next.py) | Wait briefly for the next question or guess. |
| [progress.py](src/progress.py) | Read saved scores, subject averages, schedule and Guesser cost. |
| [comparison.py](src/comparison.py) | Write per-subject and per-iteration comparisons with the regular Oracle run. |
| [test_bridge.py](src/test_bridge.py) | Offline checks for persistence, routing and Guesser isolation. |

From the repository root, using the project's virtual environment:

```sh
HELPERS=documentation/analysis/codex-as-oracle/src
.venv/bin/python "$HELPERS/progress.py"
.venv/bin/python "$HELPERS/comparison.py"
.venv/bin/python -m pytest "$HELPERS/test_bridge.py" -q
```

These commands make no model calls. They use the existing private run data under
`private/reviews/gemini38-direct-20260910/`; that data is not included here.

For a new experiment, use the generic `experiment.py` commands above. The compatibility
helpers use current repository catalogs and do not pin the historical configuration;
the generic launcher validates its saved preview before any paid call.

An active Codex operator must collect fresh evidence and supply each decision: use
`bridge.py pending` or `next.py --after N`, then `bridge.py submit --input <decision.json>`.
The decision schemas are in `bridge.py`. The helpers do not invoke Codex themselves or
schedule the six-minute reports; those were supplied by the conversation during the run.

The [GPT-5.6 Sol experiment](sol-results.md) uses Sol (high), `M-0010`, as the Guesser
with this same direct-Codex method. Its [Sol helper](src/sol.py) selects separate private
artifacts without changing the Gemini run. It completed 19 games successfully before its
spending guard stopped play. The report includes the partial comparison and cost accounting.
