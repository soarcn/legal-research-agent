import pytest

from legal_research.adapters.postgres.connection import PostgresReadinessProbe
from legal_research.ports.readiness import CapabilityStatus


class ReachableDatabase:
    async def ping(self) -> None:
        return None


class UnreachableDatabase:
    async def ping(self) -> None:
        raise ConnectionError("postgresql://legal_agent:secret@localhost/legal_agent")


@pytest.mark.asyncio
async def test_postgres_probe_reports_ready_when_connection_succeeds() -> None:
    result = await PostgresReadinessProbe(ReachableDatabase()).probe()

    assert result.name == "postgres"
    assert result.status is CapabilityStatus.READY


@pytest.mark.asyncio
async def test_postgres_probe_reports_failed_without_exposing_connection_detail() -> None:
    result = await PostgresReadinessProbe(UnreachableDatabase()).probe()

    assert result.name == "postgres"
    assert result.status is CapabilityStatus.FAILED
    assert result.diagnostic is None
