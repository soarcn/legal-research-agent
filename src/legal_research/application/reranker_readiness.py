"""Safe readiness mapping for configured reranker capability."""

from legal_research.ports.readiness import CapabilityProbe, CapabilityStatus, ProbeResult
from legal_research.ports.reranking import (
    RerankerError,
    RerankerFailureKind,
    RerankerProvider,
    RerankRequest,
)


class RerankerReadinessProbe(CapabilityProbe):
    """Prove the configured cross-encoder can score a bounded non-legal pair."""

    name = "reranker"

    def __init__(self, provider: RerankerProvider) -> None:
        self._provider = provider

    async def probe(self) -> ProbeResult:
        try:
            await self._provider.rerank(
                RerankRequest(
                    query="Which passage discusses marine mammals?",
                    passages=(
                        "A whale is a marine mammal.",
                        "A triangle has three sides.",
                    ),
                )
            )
        except RerankerError as error:
            return ProbeResult(status=_capability_status(error.kind))
        return ProbeResult.ready()


def _capability_status(failure: RerankerFailureKind) -> CapabilityStatus:
    """Map internal reranker failures onto the public capability vocabulary."""
    statuses = {
        RerankerFailureKind.UNAVAILABLE: CapabilityStatus.FAILED,
        RerankerFailureKind.TIMEOUT: CapabilityStatus.TIMED_OUT,
        RerankerFailureKind.LOAD_FAILURE: CapabilityStatus.ERROR,
        RerankerFailureKind.INVALID_OUTPUT: CapabilityStatus.ERROR,
        RerankerFailureKind.TRANSPORT_ERROR: CapabilityStatus.ERROR,
    }
    return statuses[failure]
