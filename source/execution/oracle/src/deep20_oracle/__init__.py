"""Typed, live-web factual oracle for Deep20Bench."""

from .artifacts import RunArtifactPolicy
from .audit import RunAuditWriter
from .catalog import SubjectCatalog, load_subject_catalog
from .config import EvidenceReviewConfig, OracleConfig, RecoveryPolicy, load_oracle_config
from .credentials import CredentialLoadError, load_openrouter_api_key
from .errors import (
    AuditWriteError,
    OracleConfigurationError,
    OracleError,
    OracleProtocolError,
    OracleProviderError,
)
from .models import (
    Evidence,
    EvidenceDecisionBasis,
    EvidenceReviewResult,
    OracleAdjudication,
    OracleAnswer,
    OracleCall,
    OracleMetrics,
    OracleQuestionType,
    OracleRequest,
    OracleResult,
    OracleRoleMetrics,
    Subject,
)
from .service import Oracle

__all__ = [
    "AuditWriteError",
    "CredentialLoadError",
    "Evidence",
    "EvidenceDecisionBasis",
    "EvidenceReviewConfig",
    "EvidenceReviewResult",
    "Oracle",
    "OracleAdjudication",
    "OracleAnswer",
    "OracleCall",
    "OracleConfig",
    "OracleConfigurationError",
    "OracleError",
    "OracleMetrics",
    "OracleProtocolError",
    "OracleProviderError",
    "OracleQuestionType",
    "OracleRequest",
    "OracleResult",
    "OracleRoleMetrics",
    "RecoveryPolicy",
    "RunArtifactPolicy",
    "RunAuditWriter",
    "Subject",
    "SubjectCatalog",
    "load_openrouter_api_key",
    "load_oracle_config",
    "load_subject_catalog",
]
