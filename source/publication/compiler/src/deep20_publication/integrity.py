from __future__ import annotations

import hashlib
import json

import yaml
from pydantic import JsonValue, TypeAdapter
from yaml.constructor import ConstructorError

try:
    # libyaml's C parser is several times faster on the large signed run artifacts.
    from yaml import CSafeLoader as _SafeLoader
except ImportError:  # PyYAML built without libyaml: same results, slower parsing.
    from yaml import SafeLoader as _SafeLoader  # type: ignore[assignment]

_JSON_OBJECT = TypeAdapter(dict[str, JsonValue])


class PublicationInputError(RuntimeError):
    """Raised when a publication source cannot be trusted or validated."""


class _UniqueKeyLoader(_SafeLoader):
    """Safe YAML loading with the duplicate-key check below.

    With libyaml only scanning and parsing run in C; construction keeps PyYAML's safe
    constructor.
    """


def _construct_unique_mapping(
    loader: _UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[object, object]:
    mapping: dict[object, object] = {}
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
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def canonical_json(value: JsonValue) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_yaml_object(text: str, label: str) -> dict[str, JsonValue]:
    try:
        raw = yaml.load(text, Loader=_UniqueKeyLoader)
        return _JSON_OBJECT.validate_python(raw)
    except (ValueError, yaml.YAMLError) as error:
        raise PublicationInputError(f"cannot parse {label}: {error}") from error


def _unique_json_pairs(pairs: list[tuple[str, JsonValue]]) -> dict[str, JsonValue]:
    result: dict[str, JsonValue] = {}
    for key, value in pairs:
        if key in result:
            raise PublicationInputError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def parse_json_object(text: str, label: str) -> dict[str, JsonValue]:
    try:
        raw = json.loads(
            text,
            object_pairs_hook=_unique_json_pairs,
        )
        return _JSON_OBJECT.validate_python(raw)
    except ValueError as error:
        raise PublicationInputError(f"cannot parse {label}: {error}") from error


def verify_signed_object(value: dict[str, JsonValue], label: str) -> None:
    unsigned = dict(value)
    stored = unsigned.pop("integrity_hash", None)
    expected = sha256_text(canonical_json(_JSON_OBJECT.validate_python(unsigned)))
    if stored != expected:
        raise PublicationInputError(f"{label} integrity hash mismatch")
