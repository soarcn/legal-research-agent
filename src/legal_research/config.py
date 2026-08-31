from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and `.env`."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://legal_agent:legal_agent@localhost:5432/legal_agent"
    weaviate_url: str = "http://localhost:8080"
    ollama_base_url: str = "http://localhost:11434"
    corpus_source_snapshot_id: str = "legal-rag-bench@db0b31dc6d195ce9916897e1ac5e4e6209736c8a"


@lru_cache
def get_settings() -> Settings:
    return Settings()
