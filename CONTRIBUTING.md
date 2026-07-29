# Contributing

Deep20Bench is source-available under the licenses in [LICENSE.md](LICENSE.md). Contributions
must be compatible with the applicable project license.

## Local checks

Install the locked development environment:

```bash
uv sync
uv sync --project publication --group dev
npm ci --prefix publication/site
```

Run the checks used in CI:

```bash
uv run ruff check benchmark game oracle scripts
uv run mypy
uv run pytest -q -m "not integration"

uv run --project publication ruff check publication
uv run --project publication mypy publication/src publication/tests
uv run --project publication pytest -q publication/tests
npm run --prefix publication/site check
uv run --project publication deep20-publication build --check
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
diagnostics. Build the generated publication only from terminal benchmark runs.
