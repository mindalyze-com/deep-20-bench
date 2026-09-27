"""Deterministic inference replacement with no provider or research activity."""

import json
from datetime import UTC, datetime
from decimal import Decimal

from .config import FixedMockSettings, ScriptedMockSettings
from .models import (
    BackendCapabilities,
    BackendError,
    BackendKind,
    BackendObservation,
    BackendUsage,
    ModelRequest,
    ModelResponse,
)


class MockBackend:
    capabilities = BackendCapabilities(structured_output=True)

    def __init__(self, settings: FixedMockSettings | ScriptedMockSettings):
        self.settings = settings
        self._next = 0

    def complete(self, request: ModelRequest) -> ModelResponse:
        if isinstance(self.settings, FixedMockSettings):
            response = self.settings.response
        else:
            if self._next >= len(self.settings.responses):
                raise BackendError("mock_script_exhausted", "the configured mock script is exhausted")
            response = self.settings.responses[self._next]
            self._next += 1
        now = datetime.now(UTC).isoformat()
        return ModelResponse(
            content=json.dumps(response, ensure_ascii=False, separators=(",", ":")),
            finish_reason="stop",
            requested_at=now,
            completed_at=now,
            latency_ms=0,
            observation=BackendObservation(
                kind=BackendKind.MOCK,
                model=f"mock/{request.role.value}",
                inference_requests=0,
                usage=BackendUsage(
                    input_tokens=0,
                    output_tokens=0,
                    cached_input_tokens=0,
                    cache_write_tokens=0,
                    reasoning_tokens=0,
                    cost_usd=Decimal(0),
                ),
            ),
        )

    def close(self) -> None:
        pass
