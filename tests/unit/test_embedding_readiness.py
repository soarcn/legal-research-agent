"""Embedding readiness remains provider-neutral and safely classified."""

from dataclasses import dataclass

import pytest

from legal_research.application.embedding_readiness import EmbeddingReadinessProbe
from legal_research.ports.embedding import (
    EmbeddingError,
    EmbeddingFailureKind,
    EmbeddingRequest,
    EmbeddingResponse,
)
from legal_research.ports.readiness import CapabilityStatus


@dataclass
class FakeEmbeddingProvider:
    failure: EmbeddingError | None = None

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        if self.failure is not None:
            raise self.failure
        return EmbeddingResponse(vectors=((0.1,),), model_id="fake", revision="a" * 40, dimension=1)


async def test_readiness_reports_ready_after_one_valid_embedding() -> None:
    result = await EmbeddingReadinessProbe(FakeEmbeddingProvider()).probe()

    assert result.status is CapabilityStatus.READY


@pytest.mark.parametrize(
    ("failure", "expected_status"),
    [
        (EmbeddingFailureKind.UNAVAILABLE, CapabilityStatus.FAILED),
        (EmbeddingFailureKind.TIMEOUT, CapabilityStatus.TIMED_OUT),
        (EmbeddingFailureKind.LOAD_FAILURE, CapabilityStatus.ERROR),
        (EmbeddingFailureKind.INVALID_OUTPUT, CapabilityStatus.ERROR),
    ],
)
async def test_readiness_maps_embedding_failures_safely(
    failure: EmbeddingFailureKind, expected_status: CapabilityStatus
) -> None:
    result = await EmbeddingReadinessProbe(FakeEmbeddingProvider(EmbeddingError(failure))).probe()

    assert result.status is expected_status
