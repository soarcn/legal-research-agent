"""P3.3 maps source passage batches to vectors without changing source facts."""

from __future__ import annotations

import pytest

from legal_research.application.source_passage_embedding import SourcePassageEmbedder
from legal_research.config import EmbeddingModelConfig
from legal_research.domain import SourcePassage
from legal_research.ports.embedding import EmbeddingRequest, EmbeddingResponse


class FakeEmbeddingProvider:
    def __init__(self, *, revision: str = "a" * 40) -> None:
        self.requests: list[EmbeddingRequest] = []
        self.revision = revision

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        self.requests.append(request)
        return EmbeddingResponse(
            vectors=tuple((float(index), 1.0) for index, _ in enumerate(request.texts)),
            model_id="BAAI/bge-m3",
            revision=self.revision,
            dimension=2,
        )


def _passage(identifier: str) -> SourcePassage:
    return SourcePassage(
        source_snapshot_id="snapshot",
        passage_id=identifier,
        title="Source title",
        text=f"Source text {identifier}",
        footnotes=None,
        content_sha256="a" * 64,
    )


def _config() -> EmbeddingModelConfig:
    return EmbeddingModelConfig(revision="a" * 40, expected_dimension=2, device="cpu", batch_size=2)


async def test_embedder_batches_in_source_order_and_preserves_source_ids() -> None:
    provider = FakeEmbeddingProvider()
    passages = (_passage("one"), _passage("two"), _passage("three"))

    result = await SourcePassageEmbedder(provider, _config()).embed(passages)

    assert [request.texts for request in provider.requests] == [
        ("Source text one", "Source text two"),
        ("Source text three",),
    ]
    assert [item.passage_id for item in result] == ["one", "two", "three"]
    assert all(item.source_snapshot_id == "snapshot" for item in result)
    assert result[0].provenance.device == "cpu"
    assert result[0].provenance.batch_size == 2


async def test_embedder_rejects_provider_identity_mismatch() -> None:
    provider = FakeEmbeddingProvider(revision="b" * 40)

    with pytest.raises(ValueError, match="configured contract"):
        await SourcePassageEmbedder(provider, _config()).embed((_passage("one"),))


async def test_embedder_allows_an_empty_source_batch_without_provider_call() -> None:
    provider = FakeEmbeddingProvider()

    assert await SourcePassageEmbedder(provider, _config()).embed(()) == ()
    assert provider.requests == []
