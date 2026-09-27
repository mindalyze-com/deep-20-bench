# GPT OSS: direct Codex Oracle experiment

Prepared on 10 September 2026. The live run has not started. No paid calls or games have
been executed for this experiment. Automatic approval review rejected the detached launch
because it required more explicit authorization of the 30-game scope and spending limit.

## Prepared method

- Guesser: existing `M-0002`, gpt-oss-120B (high), `openai/gpt-oss-120b` pinned to Cerebras.
- Schedule: all 10 active subjects, three consecutive games per subject, in catalog order.
- Policy: experimental B-0003, paired `qualified_v1` profiles, 40 counted questions and
  one final guess-only opportunity, with the current `concise_knowledge_v1` support policy.
- Support: this Codex conversation supplies fresh Oracle, Reviewer, any required Judge,
  and guess-validation decisions through the existing typed bridge.
- Research: fresh web evidence for each ASK; no saved ASK answer reuse.
- Isolation: the Guesser receives only the ordinary fixed instructions, category, paired
  variation token, its own actions, final answer tokens, and canonical format corrections.
- Startup: exact-route metadata check and one paid Guesser canary before the games.
- Persistence: regular benchmark artifacts in a separate ignored private directory.

The support roles share this conversation and are not independent blind reviewers.
Codex support token usage and cost are not measured by the bridge. This follows the
[Gemini experiment](results.md) and is a descriptive comparison, not a causal evaluation
of independent Oracle quality.

## Reference and reporting

The regular comparison is `BX-20260908-B-0003-experimental-M0002-001`. It completed all
30 games with 20 successes and 71 Guesser format violations. Its retained games averaged
$0.0682 in Guesser cost, about $2.05 across 30 games. This historical cost is not a
spending limit or a forecast; retries, failures and different question paths can change cost.

The comparison will report per-subject and per-iteration scores, success counts, incorrect
guesses, format violations, infrastructure outcomes, qualified/UNKNOWN answer frequency,
Guesser cost including the startup check, and configuration differences. Successful games
score their counted questions; model failures score 41; infrastructure failures are excluded
from the score. Actual results remain pending.

## Prompt caching

Retain the existing Guesser's automatic best-effort exact-prefix caching configuration.
Its fixed instructions and append-only visible transcript remain unchanged. No padding or
response caching is added. Record actual cache reads, writes, billed costs and latency;
no savings are assumed. The local support bridge does not measure Codex prompt caching.

## Prepared artifacts and checks

| Item | Value |
| --- | --- |
| Experiment selector | `DEEP20_CODEX_EXPERIMENT=gptoss` |
| Direct execution | `BX-20260910-B-0003-codex-direct-M0002-001` |
| Private directory | `private/reviews/gptoss-direct-20260910/` |
| Preview | 30 games, 10 active subjects, zero paid calls |
| Offline bridge tests | 2 passed, including disagreement routing and Guesser isolation |
| Strict bridge type check | Passed |
| Live route check and canary | Not run |
| Completed direct games | 0 / 30 |

The private directory contains the prepared request, experimental support catalog, and
detached launch script. It is not included in the public documentation.

Run the offline bridge checks from the repository root with:

```sh
DEEP20_CODEX_EXPERIMENT=gptoss .venv/bin/python -m pytest \
  documentation/analysis/codex-as-oracle/src/test_bridge.py -q
```

After a live launch, select `gptoss` for every pending, submit, progress and comparison
command. The default selector still reads the Gemini experiment. Results will be recorded
here after the authorized run completes.
