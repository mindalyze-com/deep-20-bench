"""Filesystem and credential ownership for a draft execution's shared infrastructure."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import ExitStack
from decimal import Decimal
from pathlib import Path

from deep20_backends.config import InteractiveSettings, OllamaSettings
from deep20_backends.models import (
    BackendError,
    BackendObservation,
    BackendUsage,
    ModelRequest,
    Role,
)
from deep20_backends.parallel import ParallelResearchTools
from deep20_backends.ports import ModelBackend
from deep20_backends.research import ResearchScope
from deep20_backends.research_backend import ResearchBackend
from deep20_game.config import ModelConfig
from deep20_oracle.config import ModelRouteConfig
from pydantic import TypeAdapter

from .artifacts import ArtifactStore
from .backend_config import RuntimeSnapshot
from .backend_factory import BackendFactory
from .backend_preflight import run_backend_preflight
from .interactive_backend import InteractiveBackend
from .models import BenchmarkDefinitionSnapshot, BenchmarkModelSnapshot
from .openrouter_spending import OpenRouterPriceBound, OpenRouterSpendingGuard, fetch_price_bound
from .research_journal import SqliteResearchJournal
from .runtime import TrialExecutionContext
from .spending import SqliteSpendingLedger
from .work_models import WorkIdentity, WorkRequest
from .work_queue import SqliteWorkQueue


def private_database(path: Path, resources: ExitStack) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    os.close(descriptor)
    path.chmod(0o600)
    connection = sqlite3.connect(path, timeout=30)
    resources.callback(connection.close)
    connection.execute("PRAGMA journal_mode=WAL")
    return connection


class RuntimeServices:
    def __init__(
        self, run_root: Path, runtime: RuntimeSnapshot, resources: ExitStack,
        *, api_key: str | None, budget_usd: Decimal | None,
        parallel_api_key: str | None = None,
        judge_ignored_providers: tuple[str, ...] = (),
    ):
        self.runtime = runtime
        self.run_root = run_root
        self.prices: dict[Role, OpenRouterPriceBound] = {}
        self.local_models: dict[Role, BackendObservation] = {}
        model_path = run_root / "local-models.json"
        if model_path.exists():
            self.local_models = TypeAdapter(dict[Role, BackendObservation]).validate_json(model_path.read_text(encoding="utf-8"))
        self.api_key = api_key
        self.parallel_api_key = parallel_api_key
        self.judge_ignored_providers = judge_ignored_providers
        self.queue = SqliteWorkQueue(private_database(run_root / "work.sqlite", resources))
        self.research_journal = SqliteResearchJournal(self.queue.connection)
        self.ledger = (SqliteSpendingLedger(
            private_database(run_root / "spending.sqlite", resources), budget_usd,
        ) if budget_usd is not None else None)
        snapshot_path = run_root / "backend-runtime.json"
        if snapshot_path.exists():
            saved = RuntimeSnapshot.model_validate_json(snapshot_path.read_text(encoding="utf-8"))
            if saved != runtime:
                raise BackendError("runtime_snapshot_changed", "draft runtime differs from its saved snapshot")
        else:
            ArtifactStore._atomic_write(snapshot_path, runtime.model_dump_json(indent=2) + "\n")
            snapshot_path.chmod(0o600)
        resources.callback(self.persist_spending)

    def persist_spending(self) -> None:
        if self.ledger is not None:
            ArtifactStore._atomic_write(self.run_root / "spending-summary.json", self.ledger.snapshot().model_dump_json(indent=2) + "\n")

    def observe_local_model(self, role: Role, observation: BackendObservation) -> None:
        saved = self.local_models.get(role)
        if saved is not None and (saved.model_digest, saved.resolved_model) != (observation.model_digest, observation.resolved_model):
            raise BackendError("local_model_changed", "installed model differs from the model saved for this execution")
        self.local_models[role] = observation
        ArtifactStore._atomic_write(self.run_root / "local-models.json", json.dumps({
            role.value: model.model_dump(mode="json") for role, model in self.local_models.items()
        }, indent=2) + "\n")

    def wrap_research(self, backend: ModelBackend, settings: OllamaSettings) -> ModelBackend:
        return ResearchBackend(backend, self.runtime.research, self.research_tools)

    def preflight(self, definition: BenchmarkDefinitionSnapshot, model: BenchmarkModelSnapshot, *, canary: bool) -> None:
        factory = BackendFactory(api_key=self.api_key, runtime=self.runtime,
                                 judge_ignored_providers=self.judge_ignored_providers,
                                 research=self.wrap_research, http_guard=self.http_guard,
                                 on_local_model=self.observe_local_model)
        report = run_backend_preflight(self.runtime, definition, model, factory, canary=canary)
        ArtifactStore._atomic_write(self.run_root / "backend-preflight.json", report.model_dump_json(indent=2) + "\n")

    def http_guard(self, role: Role, config: ModelConfig | ModelRouteConfig) -> OpenRouterSpendingGuard:
        if self.ledger is None:
            raise BackendError("spending_limit_missing", "paid inference requires a durable spending allowance")
        if role not in self.prices:
            self.prices[role] = fetch_price_bound(config)
            ArtifactStore._atomic_write(self.run_root / "backend-pricing.json", json.dumps({
                "runtime_fingerprint": self.runtime.fingerprint,
                "bounds": {role.value: value.model_dump(mode="json") for role, value in self.prices.items()},
            }, indent=2) + "\n")
        return OpenRouterSpendingGuard(self.ledger, self.prices[role])

    def factory(self, context: TrialExecutionContext) -> BackendFactory:
        def identity(role: Role) -> WorkIdentity:
            trial = context.identity
            return WorkIdentity(
                execution_id=trial.execution_id, model_id=trial.model_id,
                target_id=trial.target_id, trial_id=trial.trial_id,
                attempt_number=context.attempt_number, role=role,
            )
        self.queue.invalidate_prior_attempts(identity(Role.GUESSER))

        def interactive(role: Role, settings: InteractiveSettings) -> ModelBackend:
            return InteractiveBackend(settings, identity(role), self.queue,
                                      research_usage=self.research_usage if settings.research else None)

        return BackendFactory(
            api_key=self.api_key, runtime=self.runtime,
            judge_ignored_providers=self.judge_ignored_providers,
            interactive=interactive,
            research=self.wrap_research,
            on_episode_committed=lambda: self.queue.finish_attempt(identity(Role.GUESSER)),
            http_guard=self.http_guard,
            on_local_model=self.observe_local_model,
        )

    def research_usage(self, work: WorkRequest) -> BackendUsage:
        return self.research_journal.usage(work.request_id)

    def research_tools(self, request: ModelRequest) -> ParallelResearchTools:
        if self.ledger is None or self.parallel_api_key is None:
            raise BackendError("research_configuration_missing", "research requires separate credentials and a spending allowance")
        if request.role is not Role.ORACLE or request.max_search_requests is None:
            raise BackendError("research_role_required", "only Oracle requests may use research")
        scope = ResearchScope(scope_id=f"RR-{uuid.uuid4().hex}",
                              search_limit=request.max_search_requests, policy=self.runtime.research)
        return ParallelResearchTools(self.parallel_api_key, scope, self.ledger, self.research_journal)
