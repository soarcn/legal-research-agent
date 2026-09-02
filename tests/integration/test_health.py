import asyncio

from fastapi.testclient import TestClient

from apps.api.main import app, create_app
from legal_research.adapters.postgres import AsyncPostgresDatabase
from legal_research.application.readiness import ReadinessService
from legal_research.application.runtime import ReadinessRuntime
from legal_research.config import Settings
from legal_research.ports.readiness import CapabilityStatus, ProbeResult


class FakeProbe:
    def __init__(self, name: str, result: ProbeResult) -> None:
        self.name = name
        self._result = result
        self.calls = 0

    async def probe(self) -> ProbeResult:
        self.calls += 1
        return self._result


class RaisingProbe:
    name = "postgres"

    async def probe(self) -> ProbeResult:
        raise RuntimeError("postgresql://username:password@private-host")


class WaitingProbe:
    name = "weaviate"

    async def probe(self) -> ProbeResult:
        await asyncio.Event().wait()
        raise AssertionError("unreachable")


def test_health_is_available() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_does_not_invoke_readiness_probes() -> None:
    probe = FakeProbe("postgres", ProbeResult.ready(name="postgres"))
    api = create_app(readiness_service=ReadinessService([probe]))

    response = TestClient(api).get("/health")

    assert response.status_code == 200
    assert probe.calls == 0


def test_default_runtime_composition_exposes_registered_capabilities_through_ready(
    monkeypatch,
) -> None:
    runtime = ReadinessRuntime(
        service=ReadinessService(
            [
                FakeProbe("postgres", ProbeResult.ready(name="postgres")),
                FakeProbe("weaviate", ProbeResult(status=CapabilityStatus.FAILED)),
            ]
        ),
        _postgres_database=AsyncPostgresDatabase(Settings().database_url),
    )
    monkeypatch.setattr("apps.api.main.build_readiness_runtime", lambda _: runtime)

    with TestClient(create_app()) as client:
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "capabilities": [
            {"name": "postgres", "status": "ready"},
            {
                "name": "weaviate",
                "status": "failed",
                "diagnostic": "Capability is unavailable.",
            },
        ],
    }


def test_ready_returns_only_safe_provider_neutral_fields_when_all_probes_are_ready() -> None:
    api = create_app(
        readiness_service=ReadinessService(
            [
                FakeProbe("postgres", ProbeResult.ready(name="postgres")),
                FakeProbe("weaviate", ProbeResult.ready(name="weaviate")),
            ]
        )
    )

    response = TestClient(api).get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "capabilities": [
            {"name": "postgres", "status": "ready"},
            {"name": "weaviate", "status": "ready"},
        ],
    }


def test_ready_returns_service_unavailable_when_a_capability_is_not_ready() -> None:
    api = create_app(
        readiness_service=ReadinessService(
            [
                FakeProbe(
                    "weaviate",
                    ProbeResult(name="weaviate", status=CapabilityStatus.DISABLED),
                )
            ]
        )
    )

    response = TestClient(api).get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "capabilities": [
            {
                "name": "weaviate",
                "status": "disabled",
                "diagnostic": "Capability is disabled by configuration.",
            }
        ],
    }


def test_ready_exposes_a_bounded_safe_diagnostic_without_probe_details() -> None:
    api = create_app(
        readiness_service=ReadinessService(
            [
                FakeProbe(
                    "postgres",
                    ProbeResult(
                        status=CapabilityStatus.FAILED,
                        diagnostic="postgresql://legal_agent:password@private-host?token=secret",
                    ),
                )
            ]
        )
    )

    response = TestClient(api).get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "capabilities": [
            {
                "name": "postgres",
                "status": "failed",
                "diagnostic": "Capability is unavailable.",
            }
        ],
    }


def test_ready_returns_service_unavailable_when_a_capability_probe_fails() -> None:
    api = create_app(
        readiness_service=ReadinessService(
            [
                FakeProbe(
                    "postgres",
                    ProbeResult(name="postgres", status=CapabilityStatus.FAILED),
                )
            ]
        )
    )

    response = TestClient(api).get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "capabilities": [
            {
                "name": "postgres",
                "status": "failed",
                "diagnostic": "Capability is unavailable.",
            }
        ],
    }


def test_ready_returns_service_unavailable_when_a_capability_probe_times_out() -> None:
    api = create_app(
        readiness_service=ReadinessService(probes=[WaitingProbe()], timeout_seconds=0.01)
    )

    response = TestClient(api).get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "capabilities": [
            {
                "name": "weaviate",
                "status": "timed_out",
                "diagnostic": "Capability probe timed out.",
            }
        ],
    }


def test_ready_does_not_expose_exception_details() -> None:
    api = create_app(readiness_service=ReadinessService(probes=[RaisingProbe()]))

    response = TestClient(api).get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "capabilities": [
            {
                "name": "postgres",
                "status": "error",
                "diagnostic": "Capability probe failed.",
            }
        ],
    }
