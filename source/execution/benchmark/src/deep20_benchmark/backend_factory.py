"""Composition-root registry for the selected inference implementations."""

from collections.abc import Callable

from deep20_backends.budget import HttpSpendingGuard
from deep20_backends.config import (
    ApprovePrimarySettings,
    FixedMockSettings,
    InteractiveSettings,
    OllamaSettings,
    ScriptedMockSettings,
)
from deep20_backends.mock import MockBackend
from deep20_backends.models import (
    BackendCapabilities,
    BackendError,
    BackendObservation,
    ModelRequest,
    ModelResponse,
    Role,
)
from deep20_backends.ollama import OllamaBackend
from deep20_backends.ports import ModelBackend
from deep20_game.config import ModelConfig
from deep20_game.openrouter_provider import OpenRouterGameProvider
from deep20_oracle.config import ModelRouteConfig
from deep20_oracle.openrouter_provider import OpenRouterProvider

from .backend_adapters import OpenRouterGameBackend, OpenRouterOracleBackend
from .backend_config import OpenRouterSettings, RuntimeSnapshot


class ApprovalPolicyBackend:
    """Reviewer control policies never produce an inference response."""

    capabilities = BackendCapabilities()

    def complete(self, request: ModelRequest) -> ModelResponse:
        raise BackendError("review_policy_not_inference", "approval policy must use the Reviewer port")

    def close(self) -> None:
        pass


class BackendFactory:
    def __init__(
        self,
        *,
        api_key: str | None,
        runtime: RuntimeSnapshot | None = None,
        judge_ignored_providers: tuple[str, ...] = (),
        interactive: Callable[[Role, InteractiveSettings], ModelBackend] | None = None,
        research: Callable[[ModelBackend, OllamaSettings], ModelBackend] | None = None,
        on_episode_committed: Callable[[], None] | None = None,
        http_guard: Callable[[Role, ModelConfig | ModelRouteConfig], HttpSpendingGuard] | None = None,
        on_local_model: Callable[[Role, BackendObservation], None] | None = None,
    ):
        self.api_key = api_key
        self.runtime = runtime
        self.judge_ignored_providers = judge_ignored_providers
        self.interactive = interactive
        self.research = research
        self.on_episode_committed = on_episode_committed
        self.http_guard = http_guard
        self.on_local_model = on_local_model

    def episode_committed(self) -> None:
        if self.on_episode_committed is not None:
            self.on_episode_committed()

    def create(self, role: Role, config: ModelConfig | ModelRouteConfig) -> ModelBackend:
        binding = self.runtime.roles.binding(role) if self.runtime is not None else None
        if binding is None or isinstance(binding, OpenRouterSettings):
            if self.runtime is not None and self.http_guard is None:
                raise BackendError("spending_guard_missing", "paid draft roles require a spending guard")
            guard = self.http_guard(role, config) if self.http_guard is not None else None
            if not self.api_key:
                raise BackendError("openrouter_credentials_missing", "OpenRouter credentials are required")
            if isinstance(config, ModelConfig):
                title = ("Deep20Bench Benchmark Guesser" if role is Role.GUESSER
                         else "Deep20Bench Benchmark Guess Validator")
                return OpenRouterGameBackend(OpenRouterGameProvider(self.api_key, config, title=title,
                                                                    http_guard=guard))
            title = {Role.ORACLE: "Deep20Bench Oracle", Role.REVIEWER: "Deep20Bench Oracle Reviewer",
                     Role.JUDGE: "Deep20Bench Oracle Judge"}[role]
            return OpenRouterOracleBackend(OpenRouterProvider(
                self.api_key, config, enable_web_search=role is Role.ORACLE, title=title,
                ignored_providers=self.judge_ignored_providers if role is Role.JUDGE else (),
                http_guard=guard,
            ))
        if isinstance(binding, (FixedMockSettings, ScriptedMockSettings)):
            return MockBackend(binding)
        if isinstance(binding, ApprovePrimarySettings):
            return ApprovalPolicyBackend()
        if isinstance(binding, InteractiveSettings):
            if self.interactive is None:
                raise BackendError("interactive_queue_missing", "an interactive work queue is required")
            return self.interactive(role, binding)
        backend = OllamaBackend(binding)
        try:
            observation = backend.preflight()
            if self.on_local_model is not None:
                self.on_local_model(role, observation)
            if role is Role.ORACLE:
                if self.research is None:
                    raise BackendError("research_tools_missing", "local Oracle requires research tools")
                if not backend.capabilities.tool_calls:
                    raise BackendError("ollama_tools_unsupported", "local Oracle requires a model with tool support")
                return self.research(backend, binding)
            return backend
        except BaseException:
            backend.close()
            raise
