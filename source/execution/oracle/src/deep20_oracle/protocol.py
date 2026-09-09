"""Profile-specific wire schemas and local validation for factual answer tokens."""

from pydantic import TypeAdapter

from .config import AdjudicationPolicy, PromptProfile
from .knowledge_prompts import MAX_SUPPORT_CHARACTERS, REVIEW_UNKNOWN_CONTEXT_RULE
from .models import (
    EvidenceDecisionBasis,
    EvidenceKind,
    EvidenceReviewResult,
    JsonObject,
    OracleAnswer,
    OracleResearchAttemptResult,
    OracleResult,
    OracleRole,
    StrictModel,
)
from .search_budget import (
    DEFAULT_RESEARCH_QUERY_TARGET,
    STANDARD_MAX_RESEARCH_QUERIES,
    research_search_limit,
)

STANDARD_ANSWERS = (OracleAnswer.YES, OracleAnswer.NO, OracleAnswer.UNKNOWN)
_JSON_OBJECT: TypeAdapter[JsonObject] = TypeAdapter(JsonObject)


def validate_answer(answer: OracleAnswer, profile: PromptProfile) -> None:
    if profile is not PromptProfile.QUALIFIED_V1 and answer not in STANDARD_ANSWERS:
        raise ValueError("qualified answers require the five-answer experimental profile")


def permits_judge_knowledge(
    profile: PromptProfile,
    role: OracleRole | None,
    policy: AdjudicationPolicy,
) -> bool:
    return (
        profile is PromptProfile.QUALIFIED_V1
        and role is OracleRole.JUDGE
        and policy is AdjudicationPolicy.JUDGE_STABLE_KNOWLEDGE_V1
    )


def validate_protocol_result(
    result: StrictModel,
    profile: PromptProfile,
    *,
    role: OracleRole | None = None,
    policy: AdjudicationPolicy = AdjudicationPolicy.PROFILE_DEFAULT,
    research_query_target: int = DEFAULT_RESEARCH_QUERY_TARGET,
) -> None:
    if isinstance(result, (OracleResult, EvidenceReviewResult)):
        validate_answer(result.answer, profile)
        concise = policy is AdjudicationPolicy.CONCISE_KNOWLEDGE_V1
        if concise:
            if profile is not PromptProfile.QUALIFIED_V1:
                raise ValueError("concise knowledge requires qualified_v1")
            if result.basis is None or result.supporting_statement is None:
                raise ValueError("concise knowledge decisions require basis and supporting_statement")
            if result.basis not in {EvidenceDecisionBasis.EVIDENCE, EvidenceDecisionBasis.OTHER}:
                raise ValueError("concise knowledge basis must be evidence or other")
            if (
                isinstance(result, OracleResult)
                and result.answer is OracleAnswer.UNKNOWN
                and result.basis is not EvidenceDecisionBasis.OTHER
            ):
                raise ValueError("UNKNOWN uses other basis")
            if (isinstance(result, OracleResearchAttemptResult)
                and len(result.attempted_queries) > research_search_limit(research_query_target)):
                raise ValueError("concise knowledge research exceeded the query allowance")
            return
        if isinstance(result, OracleResult) and any(
            item.kind is not EvidenceKind.QUOTATION for item in result.evidence
        ):
            raise ValueError("source summaries require concise_knowledge_v1")
        if (isinstance(result, OracleResearchAttemptResult)
            and len(result.attempted_queries) > STANDARD_MAX_RESEARCH_QUERIES):
            raise ValueError("standard research exceeded the query allowance")
        if result.supporting_statement is not None or (
            isinstance(result, OracleResult) and result.basis is not None
        ):
            raise ValueError("decision support requires concise_knowledge_v1")
        if isinstance(result, EvidenceReviewResult) and result.basis is EvidenceDecisionBasis.OTHER:
            raise ValueError("expanded decision bases require concise_knowledge_v1")
    if (
        profile is PromptProfile.QUALIFIED_V1
        and isinstance(result, EvidenceReviewResult)
        and result.basis is not EvidenceDecisionBasis.EVIDENCE
        and not permits_judge_knowledge(profile, role, policy)
    ):
        raise ValueError("five-answer review decisions must use the supplied evidence")


def answer_output_schema(
    model: type[StrictModel], profile: PromptProfile = PromptProfile.STANDARD,
    *,
    role: OracleRole | None = None,
    policy: AdjudicationPolicy = AdjudicationPolicy.PROFILE_DEFAULT,
    research_query_target: int = DEFAULT_RESEARCH_QUERY_TARGET,
) -> JsonObject:
    schema = _JSON_OBJECT.validate_python(model.model_json_schema())
    definitions = schema.get("$defs")
    if not isinstance(definitions, dict):
        raise TypeError("answer schema has no definitions")
    answer = definitions.get("OracleAnswer")
    if not isinstance(answer, dict):
        raise TypeError("answer schema has no OracleAnswer definition")
    choices = tuple(OracleAnswer) if profile is PromptProfile.QUALIFIED_V1 else STANDARD_ANSWERS
    answer["enum"] = [choice.value for choice in choices]
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        raise TypeError("answer schema has no properties")
    required = schema.get("required")
    if not isinstance(required, list):
        raise TypeError("answer schema has no required fields")
    basis = definitions.get("EvidenceDecisionBasis")
    if policy is AdjudicationPolicy.CONCISE_KNOWLEDGE_V1:
        if profile is not PromptProfile.QUALIFIED_V1:
            raise ValueError("concise knowledge requires qualified_v1")
        if not isinstance(basis, dict):
            raise TypeError("decision schema has no basis definition")
        basis["enum"] = [EvidenceDecisionBasis.EVIDENCE.value, EvidenceDecisionBasis.OTHER.value]
        properties["basis"] = {"$ref": "#/$defs/EvidenceDecisionBasis"}
        properties["supporting_statement"] = {
            "type": "string", "minLength": 1, "maxLength": MAX_SUPPORT_CHARACTERS,
            "title": "Supporting Statement",
        }
        for field in ("basis", "supporting_statement"):
            if field not in required:
                required.append(field)
        queries = properties.get("attempted_queries")
        if isinstance(queries, dict):
            queries["maxItems"] = research_search_limit(research_query_target)
        indices = properties.get("evidence_indices")
        if isinstance(indices, dict):
            indices["description"] = REVIEW_UNKNOWN_CONTEXT_RULE
    else:
        # Earlier live policies keep the exact three-field evidence wire contract.
        evidence = definitions.get("Evidence")
        evidence_properties = evidence.get("properties") if isinstance(evidence, dict) else None
        if isinstance(evidence_properties, dict):
            evidence_properties.pop("kind", None)
        definitions.pop("EvidenceKind", None)
        queries = properties.get("attempted_queries")
        if isinstance(queries, dict):
            queries["maxItems"] = STANDARD_MAX_RESEARCH_QUERIES
        properties.pop("supporting_statement", None)
        if issubclass(model, OracleResult):
            properties.pop("basis", None)
            definitions.pop("EvidenceDecisionBasis", None)
        elif isinstance(basis, dict):
            basis["enum"] = [EvidenceDecisionBasis.EVIDENCE.value]
            if profile is not PromptProfile.QUALIFIED_V1 or permits_judge_knowledge(
                profile, role, policy
            ):
                basis["enum"] = [EvidenceDecisionBasis.EVIDENCE.value, EvidenceDecisionBasis.MODEL_KNOWLEDGE.value]
    return schema
