"""Translate resolved role bindings into existing domain configuration contracts."""

from decimal import Decimal

from deep20_backends.config import (
    ApprovePrimarySettings,
    FixedMockSettings,
    InteractiveSettings,
    OllamaSettings,
    ScriptedMockSettings,
)
from deep20_backends.models import JsonObject, Role
from deep20_game.config import ModelConfig, PromptCacheConfig, SeedCapability
from deep20_game.models import GuessValidationResult, parse_guesser_action_output
from deep20_oracle.config import (
    EvidenceReviewConfig,
    ModelRouteConfig,
    OracleConfig,
    RecoveryPolicy,
)
from deep20_oracle.models import EvidenceReviewResult, OracleResearchAttemptResult, OracleRole
from deep20_oracle.protocol import validate_protocol_result
from deep20_oracle.util import canonical_json, sha256_text

from .backend_config import OpenRouterSettings, RoleBinding, RuntimeSnapshot
from .models import BenchmarkDefinitionSnapshot, BenchmarkModelSnapshot


def _route(binding: RoleBinding, role: Role) -> JsonObject:
    if isinstance(binding, OpenRouterSettings):
        return {key: value for key, value in binding.model_dump(mode="json").items()
                if key in ModelRouteConfig.model_fields}
    if isinstance(binding, OllamaSettings):
        return {
            "gateway": "ollama", "model": binding.model, "provider": "ollama",
            "reasoning_effort": str(binding.think).lower(),
            "max_output_tokens": binding.max_output_tokens,
            "timeout_seconds": binding.timeout_seconds,
            "allow_fallbacks": False,
        }
    model = binding.model if isinstance(binding, InteractiveSettings) else f"mock/{role.value}"
    return {
        "gateway": binding.implementation, "model": model, "provider": binding.implementation,
        "reasoning_effort": "none", "allow_fallbacks": False,
        "recovery": RecoveryPolicy(
            max_elapsed_seconds=0, max_request_attempts=1,
            no_result_retries=0, invalid_output_retries=0,
            rate_limit_max_elapsed_seconds=0, rate_limit_max_request_attempts=1,
        ).model_dump(mode="json"),
    }


def _namespace(runtime: RuntimeSnapshot, role: Role) -> str:
    return sha256_text(canonical_json({
        "edition": runtime.edition.edition_id,
        "role": role.value,
        "binding": runtime.roles.binding(role).model_dump(mode="json"),
        "workflow": "runtime-v1",
        **({"research": runtime.research.model_dump(mode="json")} if role is Role.ORACLE else {}),
    }))


def game_configuration(base: ModelConfig, runtime: RuntimeSnapshot, role: Role) -> ModelConfig:
    binding = runtime.roles.binding(role)
    updates = _route(binding, role)
    values = {**base.model_dump(mode="json"), **updates,
              "cache_namespace": _namespace(runtime, role)}
    if isinstance(binding, OpenRouterSettings):
        if binding.prompt_cache is None and (binding.model, binding.provider) != (base.model, base.provider):
            raise ValueError("a changed OpenRouter game model requires its own prompt_cache pricing")
        values.update(
            reasoning_control=binding.reasoning_control.value,
            structured_output_mode=binding.structured_output_mode.value,
            seed_capability=binding.seed_capability.value,
            prompt_cache=(binding.prompt_cache or base.prompt_cache).model_dump(mode="json"),
        )
    else:
        values.update(
            reasoning_control="effort", structured_output_mode="strict_json_schema",
            seed_capability=(SeedCapability.SUPPORTED.value if isinstance(binding, OllamaSettings)
                             else SeedCapability.UNSUPPORTED.value),
            prompt_cache=PromptCacheConfig(
                input_usd_per_million=Decimal(0), cached_input_usd_per_million=Decimal(0),
            ).model_dump(mode="json"),
        )
    return ModelConfig.model_validate({key: value for key, value in values.items()
                                       if key in ModelConfig.model_fields})


def oracle_configuration(base: OracleConfig, runtime: RuntimeSnapshot) -> OracleConfig:
    def evidence(base_role: EvidenceReviewConfig, role: Role) -> EvidenceReviewConfig:
        return EvidenceReviewConfig.model_validate({
            **base_role.model_dump(mode="json"),
            # Reset provider routing when replacing an automatic route with another backend.
            "provider_routing": "exact", "allow_fallbacks": False,
            **_route(runtime.roles.binding(role), role),
            "cache_namespace": _namespace(runtime, role),
        })

    values = {
        **base.model_dump(mode="json"),
        "provider_routing": "exact", "allow_fallbacks": False,
        **_route(runtime.roles.oracle, Role.ORACLE),
        "cache_namespace": _namespace(runtime, Role.ORACLE),
        "reviewer": evidence(base.reviewer, Role.REVIEWER).model_dump(mode="json"),
        "judge": evidence(base.judge, Role.JUDGE).model_dump(mode="json"),
    }
    return OracleConfig.model_validate(values)


def validate_mock_replies(runtime: RuntimeSnapshot, oracle: OracleConfig) -> None:
    """Catch bad simulation inputs before any selected real role can spend money."""
    for role in Role:
        binding = runtime.roles.binding(role)
        replies: tuple[JsonObject, ...]
        if isinstance(binding, ApprovePrimarySettings):
            continue
        if isinstance(binding, FixedMockSettings):
            replies = (binding.response,)
        elif isinstance(binding, ScriptedMockSettings):
            replies = binding.responses
        else:
            continue
        for reply in replies:
            raw = canonical_json(reply)
            if role is Role.GUESSER:
                parse_guesser_action_output(raw)
            elif role is Role.VALIDATOR:
                GuessValidationResult.model_validate_json(raw)
            else:
                decision = (OracleResearchAttemptResult.model_validate_json(raw)
                            if role is Role.ORACLE else EvidenceReviewResult.model_validate_json(raw))
                validate_protocol_result(
                    decision, oracle.prompt_profile, role=OracleRole(role.value),
                    policy=oracle.adjudication_policy, research_query_target=oracle.research_query_target,
                )


def resolved_model(model: BenchmarkModelSnapshot, runtime: RuntimeSnapshot) -> BenchmarkModelSnapshot:
    configuration = game_configuration(model.configuration, runtime, Role.GUESSER)
    return model.model_copy(update={
        "configuration": configuration,
        "configuration_hash": sha256_text(canonical_json(configuration.model_dump(mode="json"))),
    })


def resolved_definition(
    definition: BenchmarkDefinitionSnapshot, runtime: RuntimeSnapshot,
) -> BenchmarkDefinitionSnapshot:
    oracle = oracle_configuration(definition.oracle_configuration, runtime)
    validator = game_configuration(definition.validator_configuration, runtime, Role.VALIDATOR)
    validate_mock_replies(runtime, oracle)
    return definition.model_copy(update={
        "oracle_configuration": oracle,
        "validator_configuration": validator,
        "definition_hash": sha256_text(canonical_json({
            "base_definition_hash": definition.definition_hash,
            "runtime": runtime.model_dump(mode="json"),
            "oracle": oracle.model_dump(mode="json"),
            "validator": validator.model_dump(mode="json"),
        })),
    })
