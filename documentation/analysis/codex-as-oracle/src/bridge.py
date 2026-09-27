"""On-demand live Guesser experiment with decisions entered by this Codex thread."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Annotated, Literal, Protocol

from deep20_benchmark.artifacts import ArtifactStore, BenchmarkTrialSink
from deep20_benchmark.catalog import (
    BenchmarkCatalog,
    BenchmarkCatalogEntry,
    load_benchmark_catalog,
    load_model_catalog,
)
from deep20_benchmark.models import (
    BenchmarkExecutionId,
    BenchmarkId,
    BenchmarkModelId,
    BenchmarkRequest,
    InfrastructureCircuitBreaker,
)
from deep20_benchmark.runner import BenchmarkRunner
from deep20_benchmark.runtime import TrialExecutionContext
from deep20_game.config import BenchmarkMode, ModelConfig
from deep20_game.engine import GameEngine
from deep20_game.guesser import Guesser
from deep20_game.models import (
    EpisodeResult,
    GameProviderExchange,
    GameProviderRequest,
    GameRequest,
    GuesserSamplingContext,
    GuessValidationResult,
)
from deep20_game.openrouter_provider import OpenRouterGameProvider
from deep20_game.sinks import ExecutionObserver
from deep20_game.validator import GuessValidator
from deep20_oracle import load_openrouter_api_key, load_subject_catalog
from deep20_oracle.config import ModelRouteConfig, OracleConfig, PromptProfile
from deep20_oracle.models import (
    EvidenceReviewResult,
    OracleAnswer,
    OracleResearchAttemptResult,
    ProviderTrace,
    ProviderUsage,
    StrictModel,
)
from deep20_oracle.protocol import validate_protocol_result
from deep20_oracle.provider import ProviderExchange, ProviderRequest
from deep20_oracle.service import Oracle
from deep20_oracle.util import sha256_text, timestamp
from pydantic import Field, TypeAdapter, model_validator

REPOSITORY = Path(__file__).resolve().parents[4]
EXPERIMENT = os.environ.get("DEEP20_CODEX_EXPERIMENT", "gemini38")
if EXPERIMENT == "gemini38":
    ROOT = REPOSITORY / "private/reviews/gemini38-direct-20260910"
    EXECUTION = "BX-20260910-B-0003-codex-direct-M0021-001"
    MODEL = BenchmarkModelId("M-0021")
    BASELINE = BenchmarkExecutionId("BX-20260908-B-0003-experimental-M0021-001")
elif EXPERIMENT == "opus5":
    ROOT = REPOSITORY / "private/reviews/opus5-direct-20260910"
    EXECUTION = "BX-20260910-B-0003-codex-direct-M0006-001"
    MODEL = BenchmarkModelId("M-0006")
    BASELINE = BenchmarkExecutionId("BX-20260907-B-0003-experimental-M0006-002")
elif EXPERIMENT == "grok46":
    ROOT = REPOSITORY / "private/reviews/grok46-direct-20260910"
    EXECUTION = "BX-20260910-B-0003-codex-direct-M0015-001"
    MODEL = BenchmarkModelId("M-0015")
    BASELINE = BenchmarkExecutionId("BX-20260908-B-0003-experimental-M0015-001")
elif EXPERIMENT == "gptoss":
    ROOT = REPOSITORY / "private/reviews/gptoss-direct-20260910"
    EXECUTION = "BX-20260910-B-0003-codex-direct-M0002-001"
    MODEL = BenchmarkModelId("M-0002")
    BASELINE = BenchmarkExecutionId("BX-20260908-B-0003-experimental-M0002-001")
elif EXPERIMENT == "luna":
    ROOT = REPOSITORY / "private/reviews/luna-direct-20260910-004"
    EXECUTION = "BX-20260910-B-0003-codex-direct-M0001-004"
    MODEL = BenchmarkModelId("M-0001")
    BASELINE = BenchmarkExecutionId("BX-20260908-B-0003-experimental-M0001-001")
else:
    raise ValueError("DEEP20_CODEX_EXPERIMENT must be gemini38, opus5, grok46, gptoss or luna")
BENCHMARK = BenchmarkId("B-0003")


class WorkContext(StrictModel):
    target_id: str
    trial_number: int


class OracleWork(StrictModel):
    kind: Literal["oracle"] = "oracle"
    sequence: int
    context: WorkContext
    request_hash: str
    request: ProviderRequest


class ValidatorWork(StrictModel):
    kind: Literal["validator"] = "validator"
    sequence: int
    context: WorkContext
    request_hash: str
    request: GameProviderRequest


Work = Annotated[OracleWork | ValidatorWork, Field(discriminator="kind")]
WORK: TypeAdapter[Work] = TypeAdapter(Work)


class OracleDecision(StrictModel):
    kind: Literal["oracle"] = "oracle"
    sequence: int
    request_hash: str
    oracle: OracleResearchAttemptResult
    reviewer: EvidenceReviewResult | None
    judge: EvidenceReviewResult | None = None
    search_count: int = Field(ge=1, le=5)

    @model_validator(mode="after")
    def routing(self) -> OracleDecision:
        if self.oracle.answer is OracleAnswer.UNKNOWN:
            if self.reviewer is not None or self.judge is not None:
                raise ValueError("UNKNOWN must bypass further decisions")
        else:
            if self.reviewer is None:
                raise ValueError("directional answer requires a review decision")
            self.reviewer.validate_evidence_count(len(self.oracle.evidence))
            disagreement = self.oracle.answer != self.reviewer.answer
            if disagreement != (self.judge is not None):
                raise ValueError("Judge is required exactly when answers differ")
            if self.judge is not None:
                self.judge.validate_evidence_count(len(self.oracle.evidence))
        return self


class ValidatorDecision(StrictModel):
    kind: Literal["validator"] = "validator"
    sequence: int
    request_hash: str
    result: GuessValidationResult


Decision = Annotated[OracleDecision | ValidatorDecision, Field(discriminator="kind")]
DECISION: TypeAdapter[Decision] = TypeAdapter(Decision)


def write_model(path: Path, value: StrictModel) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value.model_dump_json(indent=2) + "\n")
    temporary.chmod(0o600)
    temporary.replace(path)


class Broker:
    def __init__(self, work_root: Path):
        self.root = work_root
        self.root.mkdir(parents=True, exist_ok=True)
        self.sequence = 0
        self.context: WorkContext | None = None
        self.bundle: OracleDecision | None = None

    def wait(self, request: ProviderRequest | GameProviderRequest) -> Decision:
        assert self.context is not None
        self.sequence += 1
        request_hash = sha256_text(request.model_dump_json())
        if isinstance(request, ProviderRequest):
            work: Work = OracleWork(
                sequence=self.sequence,
                context=self.context,
                request_hash=request_hash,
                request=request,
            )
        else:
            work = ValidatorWork(
                sequence=self.sequence,
                context=self.context,
                request_hash=request_hash,
                request=request,
            )
        pending = self.root / "pending.json"
        response = self.root / f"response-{self.sequence:04d}.json"
        write_model(pending, work)
        started = time.monotonic()
        while not response.exists():
            if (self.root / "STOP").exists():
                raise RuntimeError("interactive_experiment_stopped")
            if time.monotonic() - started > 1200:
                raise RuntimeError("interactive_decision_timeout")
            time.sleep(0.2)
        decision = DECISION.validate_json(response.read_text())
        if (
            decision.kind != work.kind
            or decision.sequence != work.sequence
            or decision.request_hash != work.request_hash
        ):
            raise ValueError("interactive decision does not match pending request")
        # Durable public-format results are owned by BenchmarkRunner, not this mailbox.
        response.unlink()
        pending.unlink()
        return decision


def local_trace(
    config: ModelRouteConfig | ModelConfig,
    request: ProviderRequest | GameProviderRequest,
    raw: str,
    started: str,
    elapsed: int,
    searches: int = 0,
) -> ProviderTrace:
    return ProviderTrace(
        requested_at=started,
        completed_at=timestamp(),
        latency_ms=elapsed,
        requested_model=config.model,
        resolved_model=config.model,
        requested_provider=config.provider,
        resolved_provider=config.provider,
        request=request.model_dump(mode="json"),
        raw_output=raw,
        usage=ProviderUsage(search_count=searches, cost_usd=None),
    )


class LocalOracleProvider:
    def __init__(
        self, broker: Broker, role: Literal["oracle", "reviewer", "judge"], config: ModelRouteConfig
    ):
        self.broker, self.role, self.config = broker, role, config

    def complete(self, request: ProviderRequest) -> ProviderExchange:
        started, timer = timestamp(), time.monotonic()
        searches = 0
        if self.role == "oracle":
            decision = self.broker.wait(request)
            if not isinstance(decision, OracleDecision):
                raise ValueError("Oracle requires an Oracle decision")
            self.broker.bundle = decision
            result: OracleResearchAttemptResult | EvidenceReviewResult = decision.oracle
            searches = decision.search_count
        else:
            bundle = self.broker.bundle
            if bundle is None:
                raise ValueError("no current adjudication bundle")
            review = bundle.reviewer if self.role == "reviewer" else bundle.judge
            if review is None:
                raise ValueError("missing required direct role decision")
            result = review
        raw = result.model_dump_json()
        trace = local_trace(
            self.config, request, raw, started, round((time.monotonic() - timer) * 1000), searches
        )
        return ProviderExchange(raw_output=raw, trace=trace)


class LocalValidatorProvider:
    def __init__(self, broker: Broker, config: ModelConfig):
        self.broker, self.config = broker, config

    def complete(self, request: GameProviderRequest) -> GameProviderExchange:
        started, timer = timestamp(), time.monotonic()
        decision = self.broker.wait(request)
        if not isinstance(decision, ValidatorDecision):
            raise TypeError("Validator requires an identity decision")
        raw = decision.result.model_dump_json()
        return GameProviderExchange(
            raw_output=raw,
            trace=local_trace(
                self.config, request, raw, started, round((time.monotonic() - timer) * 1000)
            ),
        )


class GuesserProvider(Protocol):
    def complete(self, request: GameProviderRequest) -> GameProviderExchange: ...

    def close(self) -> None: ...


class ProviderFactory(Protocol):
    def __call__(
        self, api_key: str, config: ModelConfig, *, title: str
    ) -> GuesserProvider: ...


class DirectExecutor:
    def __init__(
        self, api_key: str, broker: Broker, provider_factory: ProviderFactory | None = None
    ):
        self.api_key, self.broker = api_key, broker
        self.provider_factory = provider_factory

    def execute(
        self, context: TrialExecutionContext, sink: BenchmarkTrialSink, observer: ExecutionObserver
    ) -> EpisodeResult:
        self.broker.context = WorkContext(
            target_id=context.subject.target_id, trial_number=context.identity.trial_number
        )
        definition = context.definition
        config = definition.oracle_configuration
        factory = self.provider_factory or OpenRouterGameProvider
        provider = factory(
            self.api_key,
            context.model.configuration,
            title="Deep20Bench Direct Codex Experiment Guesser",
        )
        try:
            engine = GameEngine(
                guesser=Guesser(
                    provider, sink, context.model.configuration, definition.game_policy
                ),
                oracle=Oracle(
                    LocalOracleProvider(self.broker, "oracle", config),
                    LocalOracleProvider(self.broker, "reviewer", config.reviewer),
                    LocalOracleProvider(self.broker, "judge", config.judge),
                    sink,
                    config,
                ),
                validator=GuessValidator(
                    LocalValidatorProvider(self.broker, definition.validator_configuration),
                    sink,
                    definition.validator_configuration,
                ),
                audit_writer=sink,
                policy=definition.game_policy,
                guesser_config=context.model.configuration,
                oracle_config=config,
                validator_config=definition.validator_configuration,
                observer=observer,
                reuse_episode_answers=False,
            )
            return engine.play(
                GameRequest(
                    run_id=str(context.identity.episode_run_id),
                    subject=context.subject,
                    guesser_sampling=GuesserSamplingContext(
                        base_seed=context.base_seed, trial_number=context.identity.trial_number
                    ),
                )
            )
        finally:
            provider.close()


def experimental_catalog() -> BenchmarkCatalog:
    base = load_benchmark_catalog(REPOSITORY / "config/benchmarks.yaml").entry(BENCHMARK)
    route = {
        "gateway": "codex_interactive",
        "model": "codex/current-thread",
        "provider": "codex-local",
        "reasoning_effort": "current-thread",
        "allow_fallbacks": False,
        "provider_routing": "exact",
    }
    oracle = OracleConfig.model_validate(
        {
            **base.oracle_configuration.model_dump(),
            **route,
            "reviewer": {**base.oracle_configuration.reviewer.model_dump(), **route},
            "judge": {**base.oracle_configuration.judge.model_dump(), **route},
        }
    )
    validator_route = {key: value for key, value in route.items() if key != "provider_routing"}
    validator = ModelConfig.model_validate(
        {
            **base.validator_configuration.model_dump(),
            **validator_route,
            "configuration_id": "codex-direct-validator",
            "prompt_cache": {"input_usd_per_million": "0", "cached_input_usd_per_million": "0"},
        }
    )
    entry = BenchmarkCatalogEntry.model_validate(
        {
            **base.model_dump(),
            "display_name": "Five-answer experiment with direct Codex adjudication",
            "oracle_configuration": oracle,
            "validator_configuration": validator,
        }
    )
    return BenchmarkCatalog(benchmarks={str(BENCHMARK): entry})


def preview(prepared_request: BenchmarkRequest | None = None) -> None:
    catalog = experimental_catalog()
    subjects = load_subject_catalog(REPOSITORY / "config/subjects.yaml")
    request = prepared_request or BenchmarkRequest(
        benchmark_id=BENCHMARK,
        execution_id=BenchmarkExecutionId(EXECUTION),
        model_id=MODEL,
        benchmark_mode=BenchmarkMode.EXPERIMENTAL,
        iterations_override=3,
    )
    ROOT.mkdir(parents=True, exist_ok=True)
    if (ROOT / "runs").exists():
        raise ValueError("preview requires a fresh experiment directory")
    write_model(ROOT / "request.json", request)
    write_model(ROOT / "benchmark-catalog.json", catalog)
    print(
        json.dumps(
            {
                "status": "preview",
                "active_subjects": len(subjects.active_subjects()),
                "games": (len(request.target_ids) or len(subjects.active_subjects()))
                * (request.iterations_override or 3),
                "model": str(MODEL),
                "paid_calls": 0,
                "execution": EXECUTION,
            }
        )
    )


def run(provider_factory: ProviderFactory | None = None) -> None:
    # No support role is constructed with an OpenRouter adapter.
    key = load_openrouter_api_key(REPOSITORY)
    models = load_model_catalog(REPOSITORY / "config/models.yaml")
    subjects = load_subject_catalog(REPOSITORY / "config/subjects.yaml")
    catalog = experimental_catalog()
    request = BenchmarkRequest.model_validate_json((ROOT / "request.json").read_text())
    store = ArtifactStore(REPOSITORY)
    store.runs_root = ROOT / "runs"
    broker = Broker(ROOT / "work")
    runner = BenchmarkRunner(
        store=store,
        model_catalog=models,
        benchmark_catalog=catalog,
        subject_catalog=subjects,
        executor=DirectExecutor(key, broker, provider_factory),
    )
    result = runner.run(
        request,
        circuit_breaker=InfrastructureCircuitBreaker(max_consecutive_infrastructure_failures=1),
    )
    print(
        json.dumps(
            {"status": "completed", "execution": EXECUTION, "result_hash": result.integrity_hash}
        )
    )


def pending() -> None:
    path = ROOT / "work/pending.json"
    if not path.exists():
        print(json.dumps({"status": "no_pending_decision"}))
        return
    item = WORK.validate_json(path.read_text())
    print(
        json.dumps(
            {
                "sequence": item.sequence,
                "kind": item.kind,
                "request_hash": item.request_hash,
                "context": item.context.model_dump(),
                "input": item.request.messages[1]["content"],
            },
            ensure_ascii=False,
        )
    )


def submit(path: Path, *, require_identity: bool = False) -> None:
    item = WORK.validate_json((ROOT / "work/pending.json").read_text())
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise TypeError("decision must be a JSON object")
    expected = {"kind": item.kind, "sequence": item.sequence, "request_hash": item.request_hash}
    for field, value in expected.items():
        if (require_identity or field in raw) and raw.get(field) != value:
            raise ValueError("decision identity does not match the pending request")
    raw.update(kind=item.kind, sequence=item.sequence, request_hash=item.request_hash)
    decision = DECISION.validate_python(raw)
    if isinstance(decision, OracleDecision):
        from deep20_oracle.models import OracleRole

        config = experimental_catalog().entry(BENCHMARK).oracle_configuration
        validate_protocol_result(
            decision.oracle,
            PromptProfile.QUALIFIED_V1,
            role=OracleRole.ORACLE,
            policy=config.adjudication_policy,
        )
        for role, review in (
            (OracleRole.REVIEWER, decision.reviewer),
            (OracleRole.JUDGE, decision.judge),
        ):
            if review is not None:
                validate_protocol_result(
                    review, PromptProfile.QUALIFIED_V1, role=role, policy=config.adjudication_policy
                )
    write_model(ROOT / f"work/response-{item.sequence:04d}.json", decision)
    print(json.dumps({"submitted": item.sequence, "kind": item.kind}))


if __name__ == "__main__":
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preview", "run", "pending", "submit"))
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--input", type=Path)
    args = parser.parse_args()
    if args.command == "run":
        if not args.live:
            parser.error("paid Guesser execution requires --live")
        run()
    elif args.command == "preview":
        preview()
    elif args.command == "pending":
        pending()
    else:
        if args.input is None:
            parser.error("submit requires --input")
        submit(args.input)
