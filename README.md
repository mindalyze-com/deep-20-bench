# Deep20Bench

Deep20Bench evaluates how well an LLM identifies a hidden subject through adaptive yes/no
questions.

## Browse the results

Official model comparisons, run details, subject results, episode transcripts, and public data
are available in the static publication:

**[Browse Deep20Bench results →](https://mindalyze-com.github.io/deep-20-bench/)**

## Motivation

Fixed-question benchmarks measure responses to prompts chosen in advance. Deep20Bench instead
measures world knowledge, question planning, and state tracking while the model decides what to
ask next.

The benchmark grew from applying Twenty Questions to broad, real-world subjects. Its
[story and relation to prior work](documentation/homepage-creation.md) are documented
separately.

## Method

The Guesser is the model under test. A live-web Oracle researches each factual question, a
blind no-web Reviewer checks every initial `YES` or `NO`, and a blind no-web Judge resolves
disagreements. A separate Guess Validator evaluates proposed identities.

The Guesser receives only the broad category, its own valid actions, adjudicated `YES`, `NO`,
or `UNKNOWN` tokens, and the fixed format-recovery event after its own invalid output. It never
receives subject details, evidence, adjudicator state, provider traces, or private artifacts.
See the [architecture](documentation/architecture.md) and
[output-contract specification](documentation/guesser-output-contract.md).

The Question Score uses averages. Lower is better. A successful trial contributes its
counted questions. A model failure contributes 51, one above the 50-question limit. For each
subject, the publication averages its five trial values. It then averages the seven subject
averages. Because every subject has five trials, this is also the average of all 35 penalized
trial values. Every model failure therefore affects the score.

## Quick start

Python 3.14.6 and [uv](https://docs.astral.sh/uv/) are required.

```bash
uv sync
```

Place an OpenRouter key in the ignored file `private/openrouter.yml`:

```yaml
api:
  api_key: your-openrouter-key
```

Run one experimental trial:

```bash
uv run deep20 benchmark run B-0001 \
  --model M-0001 \
  --benchmark-mode experimental \
  --targets T-0001 \
  --iterations 1 \
  --run-id BX-local-example
```

Benchmark runs make paid provider calls. `OPENROUTER_API_KEY` can be used as a temporary
credential override.

## Documentation

The [static publication](https://mindalyze-com.github.io/deep-20-bench/) is the main interface
for browsing results and transcripts. Its source lives in this
[repository](https://github.com/mindalyze-com/deep-20-bench), and the publication package
generates the committed site into [`docs/`](docs/).

- [Benchmark control plane](benchmark/README.md)
- [Architecture](documentation/architecture.md)
- [Game engine](game/README.md)
- [Oracle, Reviewer, and Judge](oracle/Usage.md)
- [Publication package](publication/README.md)
- [Documentation index](documentation/README.md)

## Authors, citation, and license

Deep20Bench was created by Patrick Heusser and Markus Tuor. Patrick designed and implemented
the benchmark. See [CITATION.cff](CITATION.cff) for citation metadata.

Project code is source-available under the
[PolyForm Noncommercial License 1.0.0](LICENSES/PolyForm-Noncommercial-1.0.0.txt).
Project-authored documentation and result data use
[Creative Commons Attribution 4.0](LICENSES/CC-BY-4.0.txt). See [LICENSE.md](LICENSE.md) for
the exact scope and third-party exclusions.
