"""Selected-role canaries share execution adapters, capability checks, and spending guards."""

import uuid
from typing import Literal

from deep20_backends.models import BackendObservation, FrozenModel, Role
from deep20_game.config import ModelConfig
from deep20_game.models import (
    ActionType,
    GameProviderRequest,
    GuesserAction,
    GuessValidationResult,
    guesser_action_output_schema,
    parse_guesser_action_output,
)
from deep20_game.prompt import initial_guesser_messages, validator_messages
from deep20_game.service_util import validate_game_trace
from deep20_oracle.config import ModelRouteConfig
from deep20_oracle.models import (
    EvidenceReviewResult,
    OracleAnswer,
    OracleRequest,
    OracleResearchAttemptResult,
    OracleRole,
)
from deep20_oracle.prompt import render_messages
from deep20_oracle.protocol import answer_output_schema, validate_protocol_result
from deep20_oracle.provider import ProviderRequest
from deep20_oracle.service import validate_oracle_provider_trace

from .backend_adapters import GameBackendAdapter, OracleBackendAdapter
from .backend_config import RuntimeSnapshot
from .backend_factory import BackendFactory
from .backend_resolution import validate_mock_replies
from .canary import _STRUCTURED_CANARY_REVIEW, _evidence_review_canary_request
from .models import BenchmarkDefinitionSnapshot, BenchmarkModelSnapshot


class BackendPreflightResult(FrozenModel):
    role: Role
    status: Literal["validated_mock", "waiting_for_operator", "metadata_checked", "canary_passed"]
    observation: BackendObservation | None = None


class BackendPreflightReport(FrozenModel):
    schema_version: Literal[1] = 1
    runtime_fingerprint: str
    roles: tuple[BackendPreflightResult, ...]


def run_backend_preflight(runtime: RuntimeSnapshot, definition: BenchmarkDefinitionSnapshot,
                          model: BenchmarkModelSnapshot, factory: BackendFactory, *, canary: bool) -> BackendPreflightReport:
    validate_mock_replies(runtime, definition.oracle_configuration)
    results: list[BackendPreflightResult] = []
    invocation = uuid.uuid4().hex
    oracle = definition.oracle_configuration
    for role in Role:
        binding = runtime.roles.binding(role)
        if binding.implementation in {"mock", "interactive"}:
            results.append(BackendPreflightResult(role=role,
                status="validated_mock" if binding.implementation == "mock" else "waiting_for_operator"))
            continue
        configurations: dict[Role, ModelConfig | ModelRouteConfig] = {Role.GUESSER: model.configuration, Role.ORACLE: oracle,
            Role.REVIEWER: oracle.reviewer, Role.JUDGE: oracle.judge,
            Role.VALIDATOR: definition.validator_configuration}
        backend = factory.create(role, configurations[role])
        try:
            if not canary:
                results.append(BackendPreflightResult(role=role, status="metadata_checked"))
                continue
            session = f"deep20-draft-canary-{role.value}-{invocation}"
            cache = runtime.role_cache_key(role, "draft-canary-v1")
            if role in {Role.GUESSER, Role.VALIDATOR}:
                game_config = model.configuration if role is Role.GUESSER else definition.validator_configuration
                messages = (initial_guesser_messages(definition.game_policy.max_questions, "synthetic_entity", "Q7MV2KZA",
                                                     definition.game_policy.prompt_profile) if role is Role.GUESSER else
                            validator_messages(_STRUCTURED_CANARY_REVIEW.subject,
                                               GuesserAction(action=ActionType.GUESS, question=None, name="Ada Lovelace",
                                                             description="The mathematician identified by Wikidata Q7259.")))
                game_exchange = GameBackendAdapter(backend, role, game_config).complete(GameProviderRequest(
                    messages=messages, output_schema=guesser_action_output_schema() if role is Role.GUESSER else
                    answer_output_schema(GuessValidationResult), schema_name=f"{role.value}_canary",
                    session_id=session, prompt_cache_key=cache))
                trace = game_exchange.trace
                validate_game_trace(trace, game_config)
                if role is Role.GUESSER:
                    parse_guesser_action_output(game_exchange.raw_output)
                elif GuessValidationResult.model_validate_json(game_exchange.raw_output).answer is not OracleAnswer.YES:
                    raise ValueError("Validator canary rejected the matching identity")
            else:
                oracle_config: ModelRouteConfig
                if role is Role.ORACLE:
                    request = ProviderRequest(
                        messages=render_messages(OracleRequest(run_id="draft-canary",
                            subject=_STRUCTURED_CANARY_REVIEW.subject, question=_STRUCTURED_CANARY_REVIEW.question),
                            profile=oracle.prompt_profile, policy=oracle.adjudication_policy,
                            research_query_target=oracle.research_query_target),
                        output_schema=answer_output_schema(OracleResearchAttemptResult, oracle.prompt_profile,
                            role=OracleRole.ORACLE, policy=oracle.adjudication_policy,
                            research_query_target=oracle.research_query_target),
                        response_schema_name="oracle_canary", max_web_search_requests=oracle.research_search_limit,
                        session_id=session, prompt_cache_key=cache)
                    oracle_config = oracle
                else:
                    request = _evidence_review_canary_request(invocation, role=OracleRole(role.value),
                        profile=oracle.prompt_profile, policy=oracle.adjudication_policy).model_copy(update={
                            "session_id": session, "prompt_cache_key": cache})
                    oracle_config = oracle.reviewer if role is Role.REVIEWER else oracle.judge
                exchange = OracleBackendAdapter(backend, role, oracle_config).complete(request)
                trace = exchange.trace
                validate_oracle_provider_trace(trace, config=oracle_config, role=OracleRole(role.value))
                decision = (OracleResearchAttemptResult.model_validate_json(exchange.raw_output) if role is Role.ORACLE else
                            EvidenceReviewResult.model_validate_json(exchange.raw_output).validate_evidence_count(1))
                validate_protocol_result(decision, oracle.prompt_profile, role=OracleRole(role.value),
                                         policy=oracle.adjudication_policy, research_query_target=oracle.research_query_target)
            if trace.finish_reason != "stop":
                raise ValueError("role canary did not finish with stop")
            results.append(BackendPreflightResult(role=role, status="canary_passed", observation=trace.backend))
        finally:
            backend.close()
    return BackendPreflightReport(runtime_fingerprint=runtime.fingerprint, roles=tuple(results))
