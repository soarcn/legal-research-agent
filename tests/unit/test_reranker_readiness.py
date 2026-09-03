"""Reranker readiness remains provider-neutral and safely classified."""

from dataclasses import dataclass

import pytest

from legal_research.application.reranker_readiness import RerankerReadinessProbe
from legal_research.ports.readiness import CapabilityStatus
from legal_research.ports.reranking import (
    RerankerError,
    RerankerFailureKind,
    RerankRequest,
    RerankResponse,
)


@dataclass
class FakeRerankerProvider:
    failure: RerankerError | None = None

    async def rerank(self, request: RerankRequest) -> RerankResponse:
        if self.failure is not None:
            raise self.failure
        return RerankResponse(scores=(0.9, 0.1), model_id="fake", revision="a" * 40)


async def test_readiness_reports_ready_after_one_valid_rerank() -> None:
    result = await RerankerReadinessProbe(FakeRerankerProvider()).probe()

    assert result.status is CapabilityStatus.READY


@pytest.mark.parametrize(
    ("failure", "expected_status"),
    [
        (RerankerFailureKind.UNAVAILABLE, CapabilityStatus.FAILED),
        (RerankerFailureKind.TIMEOUT, CapabilityStatus.TIMED_OUT),
        (RerankerFailureKind.LOAD_FAILURE, CapabilityStatus.ERROR),
        (RerankerFailureKind.INVALID_OUTPUT, CapabilityStatus.ERROR),
    ],
)
async def test_readiness_maps_reranker_failures_safely(
    failure: RerankerFailureKind, expected_status: CapabilityStatus
) -> None:
    result = await RerankerReadinessProbe(FakeRerankerProvider(RerankerError(failure))).probe()

    assert result.status is expected_status
