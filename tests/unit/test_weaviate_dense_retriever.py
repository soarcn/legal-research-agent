"""P4.5 dense retrieval enforces the accepted BGE-M3 index contract."""

from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest

from legal_research.adapters.weaviate.dense_retriever import WeaviateDenseSourcePassageRetriever
from legal_research.config import EmbeddingModelConfig
from legal_research.domain import SourceSnapshot
from legal_research.ports.embedding import EmbeddingRequest, EmbeddingResponse


class FakeEmbeddingProvider:
    def __init__(self, response: EmbeddingResponse) -> None:
        self.response = response
        self.requests: list[EmbeddingRequest] = []

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        self.requests.append(request)
        return self.response


class FakeClient:
    def __init__(self) -> None:
        self.closed = 0
        self.query = SimpleNamespace(near_vector=self._near_vector)
        self.collections = SimpleNamespace(get=lambda _: SimpleNamespace(query=self.query))
        self.arguments: dict[str, object] | None = None

    async def _near_vector(self, **kwargs: object) -> object:
        self.arguments = kwargs
        return SimpleNamespace(
            objects=(
                SimpleNamespace(
                    properties={"passageId": "p-1"}, metadata=SimpleNamespace(distance=0.1)
                ),
            )
        )

    async def connect(self) -> None: ...
    async def close(self) -> None:
        self.closed += 1


def _config() -> EmbeddingModelConfig:
    return EmbeddingModelConfig(expected_dimension=2, device="cpu")


def _snapshot() -> SourceSnapshot:
    return SourceSnapshot(
        source_snapshot_id="snapshot",
        dataset="test",
        dataset_revision="a" * 40,
        source_url="https://example.test",
        retrieved_at=datetime.now(UTC),
        corpus_sha256="b" * 64,
        corpus_count=1,
        qa_sha256="c" * 64,
        qa_count=1,
        licence_policy="test",
        jurisdiction="VIC",
        language="en",
        corpus_snapshot_date_status="not_published_by_dataset",
    )


async def test_dense_retrieves_with_a_matching_query_embedding() -> None:
    config = _config()
    provider = FakeEmbeddingProvider(
        EmbeddingResponse(
            vectors=((0.6, 0.8),), model_id=config.model_id, revision=config.revision, dimension=2
        )
    )
    client = FakeClient()
    result = await WeaviateDenseSourcePassageRetriever(lambda: client, provider, config).retrieve(
        query="self defence", snapshot=_snapshot(), jurisdiction="VIC"
    )
    assert result.passages[0].passage_id == "p-1"
    assert client.arguments is not None
    assert client.arguments["near_vector"] == [0.6, 0.8]


async def test_dense_rejects_wrong_embedding_contract_and_effective_date() -> None:
    config = _config()
    provider = FakeEmbeddingProvider(
        EmbeddingResponse(
            vectors=((1.0, 0.0),), model_id="wrong", revision=config.revision, dimension=2
        )
    )
    retriever = WeaviateDenseSourcePassageRetriever(lambda: FakeClient(), provider, config)
    with pytest.raises(ValueError, match="embedding"):
        await retriever.retrieve(query="self defence", snapshot=_snapshot(), jurisdiction="VIC")
    with pytest.raises(ValueError, match="effective-date"):
        await retriever.retrieve(
            query="self defence",
            snapshot=_snapshot(),
            jurisdiction="VIC",
            effective_at=date(2020, 1, 1),
        )
