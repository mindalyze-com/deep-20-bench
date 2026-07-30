"""Check local links in the project's hand-written Markdown documentation."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit

REPOSITORY = Path(__file__).resolve().parents[1]
LINK_PATTERN = re.compile(r"!?\[[^\]]*]\(([^)]+)\)")
DOCUMENTATION_FILES = (
    Path("source/README.md"),
    Path("source/execution/benchmark/README.md"),
    Path("source/execution/game/README.md"),
    Path("source/execution/game/Concept.md"),
    Path("source/execution/game/Usage.md"),
    Path("source/execution/oracle/Usage.md"),
    Path("source/publication/README.md"),
)


def _timestamp() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _without_fenced_code(text: str) -> str:
    visible: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        stripped = line.lstrip()
        marker = stripped[:3]
        if marker in {"```", "~~~"}:
            fence = None if fence == marker else marker
            continue
        if fence is None:
            visible.append(line)
    return "\n".join(visible)


def _markdown_files() -> tuple[Path, ...]:
    paths = set(REPOSITORY.glob("*.md"))
    paths.update((REPOSITORY / "documentation").rglob("*.md"))
    paths.update(REPOSITORY / relative for relative in DOCUMENTATION_FILES)
    return tuple(sorted(path for path in paths if path.is_file()))


def _target_path(source: Path, raw_target: str) -> Path | None:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = re.split(r"""\s+["']""", target, maxsplit=1)[0]

    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or target.startswith("#"):
        return None
    if not parsed.path:
        return None
    return (source.parent / unquote(parsed.path)).resolve()


def main() -> int:
    checked_links = 0
    failures: list[dict[str, str]] = []
    for source in _markdown_files():
        text = _without_fenced_code(source.read_text(encoding="utf-8"))
        for match in LINK_PATTERN.finditer(text):
            target = _target_path(source, match.group(1))
            if target is None:
                continue
            checked_links += 1
            if not target.exists():
                failures.append(
                    {
                        "source": source.relative_to(REPOSITORY).as_posix(),
                        "target": target.as_posix(),
                    }
                )

    if failures:
        details = json.dumps(failures, ensure_ascii=True, separators=(",", ":"))
        print(
            f"{_timestamp()} ERROR markdown_links.failure "
            f"code=missing_target failures={len(failures)} details={details}",
            file=sys.stderr,
        )
        return 1

    print(
        f"{_timestamp()} INFO markdown_links.result "
        f"files={len(_markdown_files())} local_links={checked_links}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
