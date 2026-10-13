# Contributing

Deep20Bench software is source-available under a dual-license model. See
[LICENSE.md](LICENSE.md) for the terms. Contributions must be compatible with the applicable
project license.

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

Integration tests need credentials and make paid provider calls. They are excluded from the
normal test run; do not add them to it.

## Guesser isolation

The Guesser is the model under test. It may see only the history the protocol allows. Any
change to prompts, message history, provider requests, sessions, caches, tools, retries,
artifacts, reports, or component wiring must check this boundary and add or update tests that
prove the Guesser still sees only permitted data.

Do not commit credentials, files under `private/`, or owner-only `error-outputs.jsonl`
diagnostics. Before publishing a finished run that has Guesser format errors (contract
violations), run `deep20-publication capture-guesser-outputs` and review the public snapshot it
creates. Build the publication only from finished benchmark runs.
