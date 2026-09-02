import asyncio

from legal_research.application.readiness import ReadinessService
from legal_research.ports.readiness import (
    CapabilityStatus,
    ProbeResult,
    ReadinessStatus,
)


class ReadyProbe:
    name = "postgres"

    async def probe(self) -> ProbeResult:
        return ProbeResult.ready()


class ResultProbe:
    def __init__(self, name: str, result: ProbeResult) -> None:
        self.name = name
        self._result = result

    async def probe(self) -> ProbeResult:
        return self._result


class SlowProbe:
    name = "weaviate"

    async def probe(self) -> ProbeResult:
        await asyncio.sleep(0.05)
        return ProbeResult.ready()


class ExplodingProbe:
    name = "ollama"

    async def probe(self) -> ProbeResult:
        raise RuntimeError("postgresql://legal_agent:secret@localhost:5432/legal_agent")


async def test_readiness_is_ready_when_every_capability_probe_is_ready() -> None:
    report = await ReadinessService(probes=[ReadyProbe()]).check()

    assert report.is_ready is True
    assert report.status is ReadinessStatus.READY
    assert report.capabilities == (ProbeResult.ready(name="postgres"),)


async def test_readiness_reports_failed_disabled_timeout_and_exception_safely() -> None:
    report = await ReadinessService(
        probes=[
            ResultProbe(
                "postgres",
                ProbeResult(
                    status=CapabilityStatus.FAILED,
                    diagnostic="x" * 300,
                ),
            ),
            ResultProbe(
                "reranker",
                ProbeResult(status=CapabilityStatus.DISABLED),
            ),
            SlowProbe(),
            ExplodingProbe(),
        ],
        timeout_seconds=0.001,
    ).check()

    assert report.status is ReadinessStatus.NOT_READY
    assert [capability.status for capability in report.capabilities] == [
        CapabilityStatus.FAILED,
        CapabilityStatus.DISABLED,
        CapabilityStatus.TIMED_OUT,
        CapabilityStatus.ERROR,
    ]
    assert report.capabilities[0].name == "postgres"
    assert report.capabilities[0].diagnostic == "Capability is unavailable."
    assert "x" not in (report.capabilities[0].diagnostic or "")
    assert report.capabilities[1].diagnostic == "Capability is disabled by configuration."
    assert report.capabilities[2].diagnostic == "Capability probe timed out."
    assert report.capabilities[3].diagnostic == "Capability probe failed."
    assert "secret" not in str(report.capabilities[3])
