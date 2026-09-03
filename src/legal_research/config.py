from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, field_validator
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


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and `.env`."""

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://legal_agent:legal_agent@localhost:5432/legal_agent"
    weaviate_url: str = "http://localhost:8080"
    weaviate_grpc_port: int = 50051
    ollama_base_url: str = "http://localhost:11434"
    corpus_source_snapshot_id: str = "legal-rag-bench@db0b31dc6d195ce9916897e1ac5e4e6209736c8a"
    embedding: EmbeddingModelConfig = EmbeddingModelConfig()
    embedding_enabled: bool = False
    readiness_timeout_seconds: float = Field(default=60.0, gt=0, le=300)


@lru_cache
def get_settings() -> Settings:
    return Settings()
