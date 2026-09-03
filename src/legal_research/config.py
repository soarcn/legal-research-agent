"""Typed runtime configuration."""

from enum import StrEnum
from functools import lru_cache
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbeddingModelConfig(BaseModel):
    """Fixed dense BGE-M3 settings that form the future vector-index contract."""

    model_id: str = "BAAI/bge-m3"
    revision: str = "3806044eb869c8756693584f7eb5dd04ab2bdd95"
    device: str = "mps"
    batch_size: int = Field(default=4, ge=1, le=64)
    normalize: bool = True
    expected_dimension: int = Field(default=1024, ge=1)
    pooling: Literal["dense"] = "dense"
    max_sequence_length: int = Field(default=8192, ge=1)
    local_files_only: bool = True

    @field_validator("revision")
    @classmethod
    def revision_must_be_a_commit_sha(cls, value: str) -> str:
        if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("Embedding revision must be a 40-character lowercase commit SHA.")
        return value


class RerankerModelConfig(BaseModel):
    """Fixed cross-encoder reranker settings for controlled P5 experiments."""

    model_id: str = "BAAI/bge-reranker-v2-m3"
    revision: str = "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"
    device: str = "mps"
    batch_size: int = Field(default=4, ge=1, le=64)
    max_sequence_length: int = Field(default=512, ge=1, le=4096)
    local_files_only: bool = True

    @field_validator("revision")
    @classmethod
    def revision_must_be_a_commit_sha(cls, value: str) -> str:
        if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("Reranker revision must be a 40-character lowercase commit SHA.")
        return value


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
        value = value.strip()
        if not value:
            raise ValueError("generation model must not be blank")
        return value

    @field_validator("base_url")
    @classmethod
    def base_url_must_be_safe_http_endpoint(cls, value: str) -> str:
        value = value.strip()
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("generation base URL must be an absolute HTTP(S) endpoint")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError(
                "generation base URL must not contain credentials, query parameters, or fragments"
            )
        try:
            _ = parsed.port
        except ValueError as error:
            raise ValueError("generation base URL contains an invalid port") from error
        return value.rstrip("/")

    @field_validator("api_key", mode="before")
    @classmethod
    def api_key_must_not_be_blank(cls, value: object) -> object:
        if isinstance(value, str):
            if not value.strip():
                raise ValueError("generation API key must not be blank when configured")
            return value.strip()
        if isinstance(value, SecretStr) and not value.get_secret_value().strip():
            raise ValueError("generation API key must not be blank when configured")
        return value


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and `.env`."""

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", extra="ignore")
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
    embedding: EmbeddingModelConfig = EmbeddingModelConfig()
    embedding_enabled: bool = False
    reranker: RerankerModelConfig = RerankerModelConfig()
    reranker_enabled: bool = False
    readiness_timeout_seconds: float = Field(default=60.0, gt=0, le=300)

    @model_validator(mode="after")
    def active_generation_config_must_be_valid(self) -> "Settings":
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
