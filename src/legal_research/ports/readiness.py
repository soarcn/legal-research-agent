"""Provider-neutral contracts for operational capability checks."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

SAFE_DIAGNOSTIC_MAX_LENGTH = 200


class CapabilityStatus(StrEnum):
    """The observable state of a required runtime capability."""

    READY = "ready"
    FAILED = "failed"
    DISABLED = "disabled"
    TIMED_OUT = "timed_out"
    ERROR = "error"


class ReadinessStatus(StrEnum):
    """The aggregate readiness state of the configured application."""

    READY = "ready"
    NOT_READY = "not_ready"


@dataclass(frozen=True, slots=True)
class ProbeResult:
    """A probe outcome whose diagnostic is filtered before operational exposure."""

    status: CapabilityStatus
    name: str = ""
    diagnostic: str | None = None

    @classmethod
    def ready(cls, *, name: str = "") -> "ProbeResult":
        return cls(status=CapabilityStatus.READY, name=name)


class CapabilityProbe(Protocol):
    """A narrow async boundary for checking one external capability."""

    name: str

    async def probe(self) -> ProbeResult:
        """Return a provider-neutral status; callers own diagnostic exposure."""

        ...
