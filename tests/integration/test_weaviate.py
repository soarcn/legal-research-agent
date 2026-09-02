"""Weaviate readiness tests.

The deterministic cases exercise the adapter seam without Docker. The final
case is intentionally opt-in because the normal quality gate must not require
local infrastructure: run it with ``RUN_REAL_INTEGRATION=1`` after starting
the project Weaviate service.
"""

import pytest

from legal_research.application.readiness import ReadinessService
from legal_research.ports.readiness import CapabilityStatus


class FakeWeaviateClient:
    """Small async client double for the adapter contract."""

    def __init__(self, *, connect_error: Exception | None = None) -> None:
        self._connect_error = connect_error
        self.connect_calls = 0
        self.close_calls = 0

    async def connect(self) -> None:
        self.connect_calls += 1
        if self._connect_error is not None:
            raise self._connect_error

    async def close(self) -> None:
        self.close_calls += 1


async def test_weaviate_probe_reports_ready_after_async_connection() -> None:
    from legal_research.adapters.weaviate.readiness import WeaviateReadinessProbe

    client = FakeWeaviateClient()
    probe = WeaviateReadinessProbe(client_factory=lambda: client)

    result = await probe.probe()

    assert result.name == "weaviate"
    assert result.status is CapabilityStatus.READY
    assert client.connect_calls == 1
    assert client.close_calls == 1


async def test_weaviate_probe_reports_failed_without_leaking_connection_details() -> None:
    from legal_research.adapters.weaviate.readiness import WeaviateReadinessProbe

    client = FakeWeaviateClient(
        connect_error=RuntimeError("http://weaviate:secret-token@private-host:8080")
    )
    report = await ReadinessService(
        probes=[WeaviateReadinessProbe(client_factory=lambda: client)]
    ).check()

    result = report.capabilities[0]
    assert result.name == "weaviate"
    assert result.status is CapabilityStatus.FAILED
    assert result.diagnostic == "Capability is unavailable."
    assert "secret-token" not in str(result)
    assert client.close_calls == 1


async def test_weaviate_probe_reports_failed_when_connection_rejects_client() -> None:
    from legal_research.adapters.weaviate.readiness import WeaviateReadinessProbe

    client = FakeWeaviateClient(connect_error=ConnectionError("service is unavailable"))

    result = await WeaviateReadinessProbe(client_factory=lambda: client).probe()

    assert result.name == "weaviate"
    assert result.status is CapabilityStatus.FAILED
    assert client.close_calls == 1


@pytest.mark.real_service
async def test_default_probe_connects_to_local_weaviate_service() -> None:
    from legal_research.adapters.weaviate.readiness import WeaviateReadinessProbe
    from legal_research.config import Settings

    settings = Settings()
    result = await WeaviateReadinessProbe.from_url(
        settings.weaviate_url,
        grpc_port=settings.weaviate_grpc_port,
    ).probe()

    assert result.status is CapabilityStatus.READY
