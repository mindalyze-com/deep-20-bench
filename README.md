<p align="center">
  <a href="https://deep20bench.com/">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="docs/og.webp">
      <source media="(prefers-color-scheme: light)" srcset="docs/og-light.webp">
      <img
        src="docs/og-light.webp"
        width="1200"
        alt="Deep20Bench - Can an LLM ask its way to the answer?"
      >
    </picture>
  </a>
</p>

<h1 align="center">Deep20Bench</h1>

<p align="center">A public prototype for testing how AI models play Twenty Questions.</p>

<h2 align="center">
  <a href="https://deep20bench.com/">Open the homepage and results →</a>
</h2>

<p align="center">
  <a href="https://deep20bench.com/results/">Results</a> ·
  <a href="https://deep20bench.com/methodology/">Method</a> ·
  <a href="https://deep20bench.com/data/">Data</a> ·
  <a href="https://github.com/mindalyze-com/deep-20-bench/discussions">Discussions</a>
</p>

Deep20Bench measures how many questions an AI model needs to identify a hidden subject: a
person, a character, a kind of thing, or a specific thing. Each question builds on the earlier
answers. Fewer questions give a better (lower) score.

The current edition, 1.1, allows 40 questions. Questions are answered with Yes, Rather yes,
Rather no, No, or Unknown; guesses get Yes, No, or Unknown. Edition 1.0 used only Yes, No, and
Unknown with a 50-question limit, and its published results keep their original scores.

Within an edition, every model plays the same subjects with the same question limit and
scoring rules. Edition 1.1 accepts a few reviewed versions of the answer-checking prompts and
subject descriptions; each run records which one it used. The subject set is small, so the
results support only limited conclusions. All
[results](https://deep20bench.com/results/), transcripts, and scoring data are public.

## Run one round locally

Python 3.14.6 and [uv](https://docs.astral.sh/uv/) are required.

```bash
uv sync
```

Place an OpenRouter key in the ignored file `private/openrouter.yml`:

```yaml
api:
  api_key: your-openrouter-key
```

Run one experimental round. This makes paid OpenRouter calls:

```bash
uv run deep20 benchmark run B-0001 \
  --model M-0001 \
  --benchmark-mode experimental \
  --targets T-0001 \
  --iterations 1 \
  --run-id BX-local-example
```

You can also set the key in `OPENROUTER_API_KEY` instead of using the file.

## Project documentation

- [Source layout](source/README.md)
- [Architecture](documentation/architecture.md)
- [Running benchmarks](source/execution/benchmark/README.md)
- [Game engine](source/execution/game/README.md)
- [Oracle, Reviewer, and Judge](source/execution/oracle/Usage.md)
- [Publication package](source/publication/README.md)
- [Documentation index](documentation/README.md)

## Citation and license

Deep20Bench was created by Patrick Heusser and Markus Tuor. See [CITATION.cff](CITATION.cff) for
citation details.

The software is source-available under a dual-license model:
[PolyForm Noncommercial 1.0.0](LICENSES/PolyForm-Noncommercial-1.0.0.txt) for noncommercial use,
with separate commercial licenses available. Project-authored documentation and result data use
[Creative Commons Attribution 4.0](LICENSES/CC-BY-4.0.txt). See [LICENSE.md](LICENSE.md) for the
exact scope and third-party exclusions.
