"""Async PostgreSQL connectivity and operational readiness adapter."""

from typing import Protocol

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from legal_research.ports.readiness import CapabilityStatus, ProbeResult


class PostgresConnectivity(Protocol):
    """The minimal database operation required by the readiness boundary."""

    async def ping(self) -> None:
        """Confirm that PostgreSQL accepts a simple read-only query."""

        ...


class AsyncPostgresDatabase:
    """Own an async SQLAlchemy engine for ordinary application adapters.

    P1 establishes connectivity only. It does not define repositories or legal
    domain tables; those contracts belong to later phases.
    """

    def __init__(self, database_url: str) -> None:
        self._engine = create_async_engine(database_url, pool_pre_ping=True)

    @property
    def engine(self) -> AsyncEngine:
        """Expose the typed engine for infrastructure adapters and integration tests."""

        return self._engine

    async def ping(self) -> None:
        """Verify an async connection with a read-only query."""

        async with self._engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

    async def dispose(self) -> None:
        """Release the connection pool during application shutdown or tests."""

        await self._engine.dispose()


class PostgresReadinessProbe:
    """Map PostgreSQL reachability to the shared safe readiness contract."""

    name = "postgres"

    def __init__(self, database: PostgresConnectivity) -> None:
        self._database = database

    async def probe(self) -> ProbeResult:
        """Return a status only; ReadinessService owns HTTP diagnostics."""

        try:
            await self._database.ping()
        except Exception:
            return ProbeResult(name=self.name, status=CapabilityStatus.FAILED)

        return ProbeResult.ready(name=self.name)
