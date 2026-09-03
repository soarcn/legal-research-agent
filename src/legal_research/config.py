"""Typed runtime configuration.

Generation configuration deliberately describes one active provider. Provider
selection is never inferred from an endpoint: switching between Ollama and an
OpenAI-compatible runtime is an explicit configuration change.
"""

from enum import StrEnum
from functools import lru_cache
from typing import Annotated
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GenerationProvider(StrEnum):
    """Supported generation-provider protocol families."""

    OLLAMA = "ollama"
    OPENAI_COMPATIBLE = "openai_compatible"


class GenerationCapabilities(BaseModel):
    """Features explicitly advertised by the configured provider/runtime."""

    model_config = ConfigDict(frozen=True)

    text_generation: bool = True
    structured_output: bool = False
    tool_calling: bool = False
    streaming: bool = False


class GenerationProviderConfig(BaseModel):
    """Validated configuration for the one generation provider used at runtime."""

    model_config = ConfigDict(frozen=True)

    provider: GenerationProvider
    model: str
    base_url: str
    api_key: SecretStr | None
    timeout_seconds: Annotated[float, Field(gt=0, le=300)]
    capabilities: GenerationCapabilities

    @field_validator("model")
    @classmethod
    def model_must_not_be_blank(cls, value: str) -> str:
        """Reject an ambiguous model before an adapter can issue a request."""
        stripped_value = value.strip()
        if not stripped_value:
            msg = "generation model must not be blank"
            raise ValueError(msg)
        return stripped_value

    @field_validator("base_url")
    @classmethod
    def base_url_must_be_safe_http_endpoint(cls, value: str) -> str:
        """Accept only absolute HTTP(S) endpoints without embedded secrets."""
        stripped_value = value.strip()
        parsed = urlsplit(stripped_value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            msg = "generation base URL must be an absolute HTTP(S) endpoint"
            raise ValueError(msg)
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            msg = "generation base URL must not contain credentials, query parameters, or fragments"
            raise ValueError(msg)
        try:
            _ = parsed.port
        except ValueError as error:
            msg = "generation base URL contains an invalid port"
            raise ValueError(msg) from error
        return stripped_value.rstrip("/")

    @field_validator("api_key", mode="before")
    @classmethod
    def api_key_must_not_be_blank(cls, value: object) -> object:
        """Allow absent keys while rejecting accidentally configured blank keys."""
        if isinstance(value, str):
            if not value.strip():
                msg = "generation API key must not be blank when configured"
                raise ValueError(msg)
            return value.strip()
        if isinstance(value, SecretStr) and not value.get_secret_value().strip():
            msg = "generation API key must not be blank when configured"
            raise ValueError(msg)
        return value


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and `.env`."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://legal_agent:legal_agent@localhost:5432/legal_agent"
    weaviate_url: str = "http://localhost:8080"
    weaviate_grpc_port: int = 50051
    corpus_source_snapshot_id: str = "legal-rag-bench@db0b31dc6d195ce9916897e1ac5e4e6209736c8a"

    generation_provider: GenerationProvider = GenerationProvider.OLLAMA
    generation_model: str = "qwen3:8b"
    generation_base_url: str = "http://localhost:11434"
    generation_api_key: SecretStr | None = None
    generation_timeout_seconds: Annotated[float, Field(gt=0, le=300)] = 60
    generation_supports_text_generation: bool = True
    generation_supports_structured_output: bool = False
    generation_supports_tool_calling: bool = False
    generation_supports_streaming: bool = False

    @model_validator(mode="after")
    def active_generation_config_must_be_valid(self) -> "Settings":
        """Fail at settings construction instead of during a provider call."""
        _ = self.generation_provider_config
        return self

    @property
    def generation_provider_config(self) -> GenerationProviderConfig:
        """Build the only active, validated generation-provider configuration."""
        return GenerationProviderConfig(
            provider=self.generation_provider,
            model=self.generation_model,
            base_url=self.generation_base_url,
            api_key=self.generation_api_key,
            timeout_seconds=self.generation_timeout_seconds,
            capabilities=GenerationCapabilities(
                text_generation=self.generation_supports_text_generation,
                structured_output=self.generation_supports_structured_output,
                tool_calling=self.generation_supports_tool_calling,
                streaming=self.generation_supports_streaming,
            ),
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
