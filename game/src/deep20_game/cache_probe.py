from __future__ import annotations

import uuid
from pathlib import Path
from typing import Literal

from deep20_oracle.diagnostics import diagnose_exception
from deep20_oracle.models import FailureDiagnostics, ProviderTrace, StrictModel
from deep20_oracle.util import canonical_json, sha256_text, timestamp
from pydantic import Field, ValidationError

from .config import GamePolicy, ModelConfig
from .errors import GameConfigurationError, GameError
from .models import (
    GUESSER_ACTION_SCHEMA_NAME,
    ActionType,
    GameProviderRequest,
    GuesserAction,
    guesser_action_output_schema,
    parse_guesser_action_output,
)
from .prompt import (
    GUESSER_PROMPT_VERSION,
    append_visible_turn,
    initial_guesser_messages,
)
from .provider import GameModelProvider
from .sampling import derive_guesser_prompt_nonce
from .service_util import provider_trace_from_error, validate_game_trace


class CacheProbeArtifact(StrictModel):
    schema_version: Literal[1] = 1
    probe_id: str = Field(pattern=r"^CP-[0-9a-f]{32}$")
    success: bool
    failure_reason: str | None = None
    failure_diagnostics: FailureDiagnostics | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    configuration_id: str
    configuration_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    prompt_version: str
    output_schema_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    minimum_cacheable_tokens: int = Field(ge=1)
    ttl_seconds: int = Field(ge=1)
    pricing: dict[str, str]
    first_trace: ProviderTrace | None
    second_trace: ProviderTrace | None
    recorded_at: str
    integrity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    def summary(self) -> dict[str, object]:
        first_usage = self.first_trace.usage if self.first_trace else None
        second_usage = self.second_trace.usage if self.second_trace else None
        return {
            "probe_id": self.probe_id,
            "success": self.success,
            "configuration_id": self.configuration_id,
            "configuration_hash": self.configuration_hash,
            "prompt_version": self.prompt_version,
            "output_schema_hash": self.output_schema_hash,
            "minimum_cacheable_tokens": self.minimum_cacheable_tokens,
            "ttl_seconds": self.ttl_seconds,
            "first_cache_read_tokens": (first_usage.cached_input_tokens if first_usage else None),
            "first_cache_write_tokens": (first_usage.cache_write_tokens if first_usage else None),
            "second_cache_read_tokens": (
                second_usage.cached_input_tokens if second_usage else None
            ),
            "second_cache_write_tokens": (
                second_usage.cache_write_tokens if second_usage else None
            ),
            "integrity_hash": self.integrity_hash,
        }


def configuration_hash(config: ModelConfig) -> str:
    return sha256_text(canonical_json(config.model_dump(mode="json")))


def schema_hash() -> str:
    return sha256_text(canonical_json(guesser_action_output_schema()))


def run_cache_probe(
    provider: GameModelProvider,
    config: ModelConfig,
    policy: GamePolicy,
) -> CacheProbeArtifact:
    """Make two representative appended requests and prove a fresh prefix-cache read."""
    probe_id = f"CP-{uuid.uuid7().hex}"
    session_id = f"deep20-cache-probe-{probe_id}"
    output_schema = guesser_action_output_schema()
    cache_material = canonical_json(
        {
            "configuration_id": config.configuration_id,
            "prompt_version": GUESSER_PROMPT_VERSION,
            "schema_hash": sha256_text(canonical_json(output_schema)),
            "max_questions": policy.max_questions,
        }
    )
    cache_key = f"deep20-guesser-{sha256_text(cache_material)[:40]}"
    messages = initial_guesser_messages(
        policy.max_questions,
        "person",
        derive_guesser_prompt_nonce(base_seed=0, trial_number=1),
    )
    for index in range(policy.max_questions):
        synthetic = GuesserAction(
            action=ActionType.ASK,
            question=f"Is the hidden subject associated with characteristic number {index + 1}?",
            name=None,
            description=None,
        )
        messages = append_visible_turn(
            messages,
            synthetic,
            "YES" if index % 2 == 0 else "NO",
        )
    first_trace: ProviderTrace | None = None
    second_trace: ProviderTrace | None = None
    try:
        first = provider.complete(
            GameProviderRequest(
                messages=messages,
                output_schema=output_schema,
                schema_name=GUESSER_ACTION_SCHEMA_NAME,
                session_id=session_id,
                prompt_cache_key=cache_key,
            )
        )
        first_trace = first.trace
        validate_game_trace(first_trace, config)
        first_action = parse_guesser_action_output(first.raw_output)
    except (GameError, ValidationError) as error:
        first_trace = first_trace or provider_trace_from_error(error)
        return _artifact(
            probe_id,
            config,
            first_trace=first_trace,
            second_trace=None,
            failure_reason=(
                f"first probe request failed: {getattr(error, 'code', type(error).__name__)}"
            ),
            failure_diagnostics=diagnose_exception(error),
        )
    appended = append_visible_turn(messages, first_action, "UNKNOWN")
    try:
        second = provider.complete(
            GameProviderRequest(
                messages=appended,
                output_schema=output_schema,
                schema_name=GUESSER_ACTION_SCHEMA_NAME,
                session_id=session_id,
                prompt_cache_key=cache_key,
            )
        )
        second_trace = second.trace
        validate_game_trace(second_trace, config)
        parse_guesser_action_output(second.raw_output)
    except (GameError, ValidationError) as error:
        second_trace = second_trace or provider_trace_from_error(error)
        return _artifact(
            probe_id,
            config,
            first_trace=first_trace,
            second_trace=second_trace,
            failure_reason=(
                f"second probe request failed: {getattr(error, 'code', type(error).__name__)}"
            ),
            failure_diagnostics=diagnose_exception(error),
        )

    eligible = first_trace.usage.input_tokens >= config.prompt_cache.minimum_cacheable_tokens
    cache_created = (
        first_trace.usage.cache_write_tokens > 0
        or first_trace.usage.cached_input_tokens > 0
        or second_trace.usage.cached_input_tokens > 0
    )
    cache_read = second_trace.usage.cached_input_tokens > 0
    fresh = (
        second_trace.usage.output_tokens > 0
        and (second_trace.response_cache_status or "").casefold() != "hit"
    )
    checks = {
        "representative prompt did not reach the configured cache threshold": eligible,
        "first request reported neither a cache write nor a cache read": cache_created,
        "appended request reported no cached input tokens": cache_read,
        "appended request did not report a fresh generated response": fresh,
    }
    failure_reason = next((message for message, passed in checks.items() if not passed), None)
    return _artifact(
        probe_id,
        config,
        first_trace=first_trace,
        second_trace=second_trace,
        failure_reason=failure_reason,
    )


def _artifact(
    probe_id: str,
    config: ModelConfig,
    *,
    first_trace: ProviderTrace | None,
    second_trace: ProviderTrace | None,
    failure_reason: str | None,
    failure_diagnostics: FailureDiagnostics | None = None,
) -> CacheProbeArtifact:
    base = {
        "schema_version": 1,
        "probe_id": probe_id,
        "success": failure_reason is None,
        "failure_reason": failure_reason,
        **(
            {"failure_diagnostics": failure_diagnostics.model_dump(mode="json")}
            if failure_diagnostics is not None
            else {}
        ),
        "configuration_id": config.configuration_id,
        "configuration_hash": configuration_hash(config),
        "prompt_version": GUESSER_PROMPT_VERSION,
        "output_schema_hash": schema_hash(),
        "minimum_cacheable_tokens": config.prompt_cache.minimum_cacheable_tokens,
        "ttl_seconds": config.prompt_cache.ttl_seconds,
        "pricing": {
            "input_usd_per_million": str(config.prompt_cache.input_usd_per_million),
            "cached_input_usd_per_million": str(config.prompt_cache.cached_input_usd_per_million),
            "cache_write_multiplier": str(config.prompt_cache.cache_write_multiplier),
        },
        "first_trace": first_trace.model_dump(mode="json") if first_trace else None,
        "second_trace": second_trace.model_dump(mode="json") if second_trace else None,
        "recorded_at": timestamp(),
    }
    return CacheProbeArtifact.model_validate(
        {**base, "integrity_hash": sha256_text(canonical_json(base))}
    )


def write_cache_probe(path: Path, artifact: CacheProbeArtifact) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(artifact.model_dump_json(indent=2) + "\n", encoding="utf-8")


def load_cache_probe(path: Path, config: ModelConfig) -> CacheProbeArtifact:
    artifact = CacheProbeArtifact.model_validate_json(path.read_text(encoding="utf-8"))
    unsigned = artifact.model_dump(mode="json")
    stored = unsigned.pop("integrity_hash")
    if stored != sha256_text(canonical_json(unsigned)):
        raise GameConfigurationError(
            "cache probe integrity hash mismatch",
            code="cache_probe_integrity_mismatch",
        )
    if artifact.configuration_hash != configuration_hash(config):
        raise GameConfigurationError(
            "cache probe does not match the exact Guesser configuration",
            code="cache_probe_configuration_mismatch",
        )
    if (
        artifact.prompt_version != GUESSER_PROMPT_VERSION
        or artifact.output_schema_hash != schema_hash()
    ):
        raise GameConfigurationError(
            "cache probe does not match the current Guesser prompt/schema",
            code="cache_probe_protocol_mismatch",
        )
    if not artifact.success:
        raise GameConfigurationError(
            f"cache probe failed: {artifact.failure_reason}",
            code="cache_probe_failed",
        )
    return artifact
