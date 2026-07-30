# Contributing

Deep20Bench is source-available under the licenses in [LICENSE.md](LICENSE.md). Contributions
must be compatible with the applicable project license.

## Local checks

Install the locked development environment:

```bash
uv sync
uv sync --project source/publication/compiler --group dev
npm ci --prefix source/publication/site
```

Run the checks used in CI:

```bash
uv run ruff check source/execution scripts
uv run mypy
uv run pytest -q -m "not integration"

uv run --project source/publication/compiler ruff check source/publication/compiler
uv run --project source/publication/compiler mypy source/publication/compiler/src source/publication/compiler/tests
uv run --project source/publication/compiler pytest -q source/publication/compiler/tests
npm run --prefix source/publication/site check
uv run --project source/publication/compiler deep20-publication build --check
uv run python scripts/check-markdown-links.py
```

Integration tests require credentials and make paid provider calls. Do not run them as part of
the normal test suite.

## Guesser isolation

The Guesser is the model under test. It may receive only the protocol-defined visible history.
Any change to prompts, message history, provider requests, sessions, caches, tools, retries,
artifacts, reports, or component wiring must review this boundary and add or update tests that
prove the Guesser-visible projection remains limited to permitted data.

Do not commit credentials, files under `private/`, or owner-only `error-outputs.jsonl`
diagnostics. Before publishing a new terminal run with contract violations, run
`deep20-publication capture-guesser-outputs` and review the typed public snapshot. Build the
generated publication only from terminal benchmark runs.
