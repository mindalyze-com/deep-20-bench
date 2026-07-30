from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import JsonValue
from yaml.constructor import ConstructorError


def timestamp() -> str:
    return datetime.now(UTC).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def openrouter_provider_identity(value: str) -> str:
    """Normalize OpenRouter route slugs and resolved provider display names."""

    canonical = "".join(
        character for character in value.casefold() if character.isalnum()
    )
    return {
        "google": "googlevertex",
    }.get(canonical, canonical)


def openrouter_provider_matches(requested: str, resolved: str) -> bool:
    return openrouter_provider_identity(requested) == openrouter_provider_identity(
        resolved
    )


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def safe_json_value(value: object) -> JsonValue:
    """Project exception/provider diagnostics onto bounded JSON-compatible data."""
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, dict):
        return {str(key): safe_json_value(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [safe_json_value(item) for item in value]
    if isinstance(value, BaseException):
        return {"type": type(value).__name__, "message": str(value)[:500]}
    return {"unserializable_type": type(value).__name__}


def repository_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() and (candidate / "pyproject.toml").is_file():
            return candidate
    raise FileNotFoundError("Deep20Bench repository root not found")


class _UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


def load_yaml_unique(path: Path) -> Any:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
