"""Role ports preserve factual projections independently of the inference transport."""

from collections.abc import Callable
from typing import Literal, Protocol

from .models import (
    EvidenceReviewRequest,
    EvidenceReviewResult,
    OracleCall,
    OracleRequest,
    OracleResearchAttemptResult,
    ProviderTrace,
    StrictModel,
)
from .provider import ProviderRequest


class OracleClient(Protocol):
    def ask(self, request: OracleRequest) -> OracleCall: ...


class ResearchRoleRequest(StrictModel):
    factual: OracleRequest
    inference: ProviderRequest


class ResearchRoleCall(StrictModel):
    result: OracleResearchAttemptResult
    trace: ProviderTrace


class ResearchClient(Protocol):
    def research(self, request: ResearchRoleRequest) -> ResearchRoleCall: ...


class EvidenceRoleRequest(StrictModel):
    factual: EvidenceReviewRequest
    inference: ProviderRequest


class EvidenceRoleCall(StrictModel):
    result: EvidenceReviewResult
    trace: ProviderTrace


class ApprovePrimary(StrictModel):
    kind: Literal["approve_primary"] = "approve_primary"


class ReviewerClient(Protocol):
    def review(self, request: EvidenceRoleRequest) -> EvidenceRoleCall | ApprovePrimary: ...


class JudgeClient(Protocol):
    def judge(self, request: EvidenceRoleRequest) -> EvidenceRoleCall: ...


class ConfiguredResearchClient:
    def __init__(self, complete: Callable[[ResearchRoleRequest], ResearchRoleCall]):
        self._complete = complete

    def research(self, request: ResearchRoleRequest) -> ResearchRoleCall:
        return self._complete(request)


class ConfiguredReviewerClient:
    def __init__(self, complete: Callable[[EvidenceRoleRequest], EvidenceRoleCall]):
        self._complete = complete

    def review(self, request: EvidenceRoleRequest) -> EvidenceRoleCall:
        return self._complete(request)


class ConfiguredJudgeClient:
    def __init__(self, complete: Callable[[EvidenceRoleRequest], EvidenceRoleCall]):
        self._complete = complete

    def judge(self, request: EvidenceRoleRequest) -> EvidenceRoleCall:
        return self._complete(request)


class ApprovePrimaryReviewer:
    """A synthetic review policy, not a prediction of the hidden primary answer."""

    def review(self, request: EvidenceRoleRequest) -> ApprovePrimary:
        return ApprovePrimary()
