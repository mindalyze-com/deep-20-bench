"""Resolve role overrides once, before constructing any active backend."""

from __future__ import annotations

from typing import Annotated, Literal

from deep20_backends.config import (
    ApprovePrimarySettings,
    FixedMockSettings,
    InteractiveSettings,
    MockSettings,
    OllamaSettings,
    ScriptedMockSettings,
)
from deep20_backends.editions import Edition
from deep20_backends.models import FrozenModel, Role
from deep20_backends.research import ResearchPolicy
from deep20_game.config import (
    ModelConfig,
    PromptCacheConfig,
    ReasoningControl,
    SeedCapability,
    StructuredOutputMode,
)
from deep20_oracle.config import ModelRouteConfig, OracleConfig
from deep20_oracle.util import canonical_json, sha256_text
from pydantic import Field, model_validator


class OpenRouterSettings(ModelRouteConfig):
    implementation: Literal["openrouter"] = "openrouter"
    reasoning_control: ReasoningControl = ReasoningControl.EFFORT
    structured_output_mode: StructuredOutputMode = StructuredOutputMode.STRICT_JSON_SCHEMA
    seed_capability: SeedCapability = SeedCapability.UNSUPPORTED
    prompt_cache: PromptCacheConfig | None = None

    @model_validator(mode="after")
    def requires_openrouter(self) -> OpenRouterSettings:
        if self.gateway != "openrouter":
            raise ValueError("OpenRouter settings require the openrouter gateway")
        return self


type RoleBinding = Annotated[
    OpenRouterSettings | OllamaSettings | InteractiveSettings | MockSettings,
    Field(discriminator="implementation"),
]


class RoleOverrides(FrozenModel):
    guesser: RoleBinding | None = None
    oracle: RoleBinding | None = None
    reviewer: RoleBinding | None = None
    judge: RoleBinding | None = None
    validator: RoleBinding | None = None

    def binding(self, role: Role) -> RoleBinding | None:
        return {
            Role.GUESSER: self.guesser,
            Role.ORACLE: self.oracle,
            Role.REVIEWER: self.reviewer,
            Role.JUDGE: self.judge,
            Role.VALIDATOR: self.validator,
        }[role]


class RoleBindings(FrozenModel):
    guesser: RoleBinding
    oracle: RoleBinding
    reviewer: RoleBinding
    judge: RoleBinding
    validator: RoleBinding

    def binding(self, role: Role) -> RoleBinding:
        return {
            Role.GUESSER: self.guesser,
            Role.ORACLE: self.oracle,
            Role.REVIEWER: self.reviewer,
            Role.JUDGE: self.judge,
            Role.VALIDATOR: self.validator,
        }[role]

    @model_validator(mode="after")
    def role_capabilities(self) -> RoleBindings:
        for role in Role:
            binding = self.binding(role)
            if isinstance(binding, ApprovePrimarySettings) and role is not Role.REVIEWER:
                raise ValueError("approve_primary is available only for Reviewer")
            if isinstance(binding, (InteractiveSettings, OllamaSettings)):
                if role is Role.ORACLE and binding.research != "parallel":
                    raise ValueError("active non-OpenRouter Oracles require Parallel research")
                if role is not Role.ORACLE and binding.research is not None:
                    raise ValueError("research is available only to Oracle")
            if (
                role is Role.GUESSER
                and isinstance(binding, InteractiveSettings)
                and not binding.isolated_context
            ):
                raise ValueError("an interactive Guesser requires an isolated worker context")
        if isinstance(self.guesser, InteractiveSettings) and any(
            isinstance(binding := self.binding(role), InteractiveSettings) and binding.operator == self.guesser.operator
            for role in (Role.ORACLE, Role.REVIEWER, Role.JUDGE, Role.VALIDATOR)
        ):
            raise ValueError("interactive Guesser and privileged roles require different operator contexts")
        return self

    @property
    def synthetic(self) -> bool:
        return any(self.binding(role).implementation == "mock" for role in Role)

    @property
    def interactive(self) -> bool:
        return any(self.binding(role).implementation == "interactive" for role in Role)

    @property
    def factual_cache_eligible(self) -> bool:
        return not (self.synthetic or self.interactive) and all(
            not isinstance(binding := self.binding(role), OllamaSettings) or binding.model_digest is not None
            for role in Role
        )


class RuntimeConfig(FrozenModel):
    version: Literal[1] = 1
    roles: RoleOverrides = Field(default_factory=RoleOverrides)
    research: ResearchPolicy = Field(default_factory=ResearchPolicy)


class RuntimeSnapshot(FrozenModel):
    version: Literal[1] = 1
    edition: Edition
    roles: RoleBindings
    research: ResearchPolicy = Field(default_factory=ResearchPolicy)

    @property
    def fingerprint(self) -> str:
        return sha256_text(canonical_json(self.model_dump(mode="json")))

    def role_cache_key(self, role: Role, original: str) -> str:
        """A Guesser namespace never incorporates the other four role bindings."""
        return "d20-" + sha256_text(canonical_json({
            "edition": self.edition.edition_id,
            "role": role.value,
            "binding": self.roles.binding(role).model_dump(mode="json"),
            "original": original,
        }))[:48]

    def factual_contract(self, original: str) -> str:
        return sha256_text(canonical_json({
            "version": "edition-factual-contract-v1",
            "edition": self.edition.edition_id,
            "oracle": self.roles.oracle.model_dump(mode="json"),
            "reviewer": self.roles.reviewer.model_dump(mode="json"),
            "judge": self.roles.judge.model_dump(mode="json"),
            "research": self.research.model_dump(mode="json"),
            "original": original,
        }))


def openrouter_settings(config: ModelConfig | ModelRouteConfig) -> OpenRouterSettings:
    payload = config.model_dump(mode="json")
    return OpenRouterSettings.model_validate({
        key: value for key, value in payload.items() if key in OpenRouterSettings.model_fields
    })


def resolve_runtime(
    edition: Edition,
    overrides: RuntimeConfig,
    *,
    guesser: ModelConfig,
    oracle: OracleConfig,
    validator: ModelConfig,
) -> RuntimeSnapshot:
    if not edition.runtime_overrides:
        raise ValueError("runtime overrides require the explicitly selected draft edition")
    if overrides.roles.guesser is not None:
        binding = overrides.roles.guesser
        # Keep --model identity tied to the registered backend/model, including mocks.
        expected_gateway = binding.implementation
        expected_model = (
            f"mock/{Role.GUESSER.value}"
            if isinstance(binding, (FixedMockSettings, ScriptedMockSettings, ApprovePrimarySettings))
            else binding.model
        )
        if guesser.gateway != expected_gateway or guesser.model != expected_model:
            raise ValueError("Guesser override must match its registered --model backend and model")
    elif guesser.gateway != "openrouter":
        raise ValueError("non-OpenRouter Guesser registrations require an explicit role binding")
    roles = RoleBindings(
        guesser=overrides.roles.guesser or openrouter_settings(guesser),
        oracle=overrides.roles.oracle or openrouter_settings(oracle),
        reviewer=overrides.roles.reviewer or openrouter_settings(oracle.reviewer),
        judge=overrides.roles.judge or openrouter_settings(oracle.judge),
        validator=overrides.roles.validator or openrouter_settings(validator),
    )
    return RuntimeSnapshot(edition=edition, roles=roles, research=overrides.research)
