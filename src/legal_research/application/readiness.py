"""Aggregate bounded operational readiness checks."""

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, replace

from legal_research.ports.readiness import (
    SAFE_DIAGNOSTIC_MAX_LENGTH,
    CapabilityProbe,
    CapabilityStatus,
    ProbeResult,
    ReadinessStatus,
)


@dataclass(frozen=True, slots=True)
class ReadinessReport:
    """A safe, aggregate view of configured runtime capabilities."""

    status: ReadinessStatus
    capabilities: tuple[ProbeResult, ...]

    @property
    def is_ready(self) -> bool:
        """Whether every configured capability reported ready."""

        return self.status is ReadinessStatus.READY


class ReadinessService:
    """Checks configured capabilities through provider-neutral probes."""

    def __init__(self, probes: Sequence[CapabilityProbe], timeout_seconds: float = 1.0) -> None:
        self._probes = tuple(probes)
        self._timeout_seconds = timeout_seconds

    @property
    def capability_names(self) -> tuple[str, ...]:
        """Return configured capability names without running their probes."""

        return tuple(probe.name for probe in self._probes)

    async def check(self) -> ReadinessReport:
        """Return readiness without exposing external implementation details."""

        results: list[ProbeResult] = []
        for probe in self._probes:
            results.append(await self._check_probe(probe))

        capabilities = tuple(results)
        status = (
            ReadinessStatus.READY
            if all(result.status is CapabilityStatus.READY for result in capabilities)
            else ReadinessStatus.NOT_READY
        )
        return ReadinessReport(status=status, capabilities=capabilities)

    async def _check_probe(self, probe: CapabilityProbe) -> ProbeResult:
        try:
            result = await asyncio.wait_for(probe.probe(), timeout=self._timeout_seconds)
        except TimeoutError:
            return ProbeResult(
                name=probe.name,
                status=CapabilityStatus.TIMED_OUT,
                diagnostic="Capability probe timed out.",
            )
        except Exception:
            return ProbeResult(
                name=probe.name,
                status=CapabilityStatus.ERROR,
                diagnostic="Capability probe failed.",
            )

        return replace(
            result,
            name=probe.name,
            diagnostic=_safe_diagnostic(result.status),
        )


def _safe_diagnostic(status: CapabilityStatus) -> str | None:
    """Return a bounded operator-facing reason without trusting probe detail."""
    diagnostics = {
        CapabilityStatus.READY: None,
        CapabilityStatus.FAILED: "Capability is unavailable.",
        CapabilityStatus.DISABLED: "Capability is disabled by configuration.",
        CapabilityStatus.TIMED_OUT: "Capability probe timed out.",
        CapabilityStatus.ERROR: "Capability probe failed.",
    }
    diagnostic = diagnostics[status]
    if diagnostic is None:
        return None

    return diagnostic[:SAFE_DIAGNOSTIC_MAX_LENGTH]
