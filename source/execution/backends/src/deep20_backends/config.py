"""Portable backend settings. Role-specific mock replies are validated by role services."""

from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import Field, model_validator

from .models import FrozenModel, JsonObject


class OllamaSettings(FrozenModel):
    implementation: Literal["ollama"] = "ollama"
    model: str = Field(min_length=1, max_length=300)
    model_digest: str | None = Field(default=None, pattern=r"^(sha256:)?[0-9a-f]{64}$")
    base_url: str = "http://127.0.0.1:11434"
    max_output_tokens: int = Field(default=4096, ge=128, le=65536)
    timeout_seconds: int = Field(default=120, ge=1, le=600)
    context_tokens: int = Field(default=32768, ge=1024)
    think: bool | Literal["low", "medium", "high"] = False
    temperature: float = Field(default=0, ge=0, le=2)
    research: Literal["parallel"] | None = None

    @model_validator(mode="after")
    def local_endpoint(self) -> OllamaSettings:
        url = urlsplit(self.base_url)
        if (
            url.scheme not in {"http", "https"}
            or url.hostname not in {"localhost", "127.0.0.1", "::1"}
            or url.username is not None
            or url.password is not None
            or url.query
            or url.fragment
            or url.path not in {"", "/"}
        ):
            raise ValueError("Ollama requires a local HTTP endpoint without credentials or a path")
        return self


class InteractiveSettings(FrozenModel):
    implementation: Literal["interactive"] = "interactive"
    operator: str = Field(min_length=1, max_length=80)
    model: str = Field(default="operator", min_length=1, max_length=300)
    research: Literal["parallel"] | None = None
    isolated_context: bool = False
    wait_timeout_seconds: int | None = Field(default=None, ge=1)


class FixedMockSettings(FrozenModel):
    implementation: Literal["mock"] = "mock"
    behavior: Literal["fixed"] = "fixed"
    response: JsonObject


class ScriptedMockSettings(FrozenModel):
    implementation: Literal["mock"] = "mock"
    behavior: Literal["script"] = "script"
    responses: tuple[JsonObject, ...] = Field(min_length=1)


class ApprovePrimarySettings(FrozenModel):
    implementation: Literal["mock"] = "mock"
    behavior: Literal["approve_primary"] = "approve_primary"


type MockSettings = Annotated[
    FixedMockSettings | ScriptedMockSettings | ApprovePrimarySettings,
    Field(discriminator="behavior"),
]
