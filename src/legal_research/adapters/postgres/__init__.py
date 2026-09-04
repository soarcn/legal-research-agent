"""PostgreSQL adapter — connectivity, SQLAlchemy models, and repositories."""

from legal_research.adapters.postgres.connection import (
    AsyncPostgresDatabase,
    PostgresReadinessProbe,
)

__all__ = ["AsyncPostgresDatabase", "PostgresReadinessProbe"]
from legal_research.adapters.postgres.source_ingestion import PostgresSourceIngestionRepository

__all__ = ["PostgresSourceIngestionRepository"]
