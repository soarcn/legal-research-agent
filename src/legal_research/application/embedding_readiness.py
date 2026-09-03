"""Safe readiness mapping for configured embedding capability."""

from legal_research.ports.embedding import (
    EmbeddingError,
    EmbeddingFailureKind,
    EmbeddingProvider,
    EmbeddingRequest,
)
from legal_research.ports.readiness import CapabilityProbe, CapabilityStatus, ProbeResult


class EmbeddingReadinessProbe(CapabilityProbe):
    """Prove the configured embedding adapter can produce one dense vector."""

    name = "embedding"

    def __init__(self, provider: EmbeddingProvider) -> None:
        self._provider = provider

    async def probe(self) -> ProbeResult:
        try:
            await self._provider.embed(EmbeddingRequest(texts=("embedding capability probe",)))
        except EmbeddingError as error:
            return ProbeResult(status=_capability_status(error.kind))
        return ProbeResult.ready()


def _capability_status(failure: EmbeddingFailureKind) -> CapabilityStatus:
    """Map internal embedding failures onto the public capability vocabulary."""
    statuses = {
        EmbeddingFailureKind.UNAVAILABLE: CapabilityStatus.FAILED,
        EmbeddingFailureKind.TIMEOUT: CapabilityStatus.TIMED_OUT,
        EmbeddingFailureKind.LOAD_FAILURE: CapabilityStatus.ERROR,
        EmbeddingFailureKind.INVALID_OUTPUT: CapabilityStatus.ERROR,
        EmbeddingFailureKind.TRANSPORT_ERROR: CapabilityStatus.ERROR,
    }
    return statuses[failure]
