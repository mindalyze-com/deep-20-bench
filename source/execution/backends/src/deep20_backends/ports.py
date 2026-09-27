from typing import Protocol

from .models import BackendCapabilities, ModelRequest, ModelResponse


class ModelBackend(Protocol):
    @property
    def capabilities(self) -> BackendCapabilities: ...

    def complete(self, request: ModelRequest) -> ModelResponse: ...

    def close(self) -> None: ...
