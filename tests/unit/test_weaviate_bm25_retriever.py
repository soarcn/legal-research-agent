"""P4.3 BM25 retrieval stays snapshot-scoped and deterministic at its adapter seam."""

from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest

from legal_research.adapters.weaviate.bm25_retriever import (
    Bm25RetrievalConfiguration,
    WeaviateBm25SourcePassageRetriever,
)
from legal_research.domain import SourceSnapshot


class FakeQuery:
    def __init__(self) -> None:
        self.arguments: dict[str, object] | None = None

    async def bm25(self, **kwargs: object) -> object:
        self.arguments = kwargs
        return SimpleNamespace(
            objects=(
                SimpleNamespace(
                    properties={"passageId": "passage-2"}, metadata=SimpleNamespace(score=0.9)
                ),
            )
        )


class FakeClient:
    def __init__(self) -> None:
        self.query = FakeQuery()
        self.collections = SimpleNamespace(get=lambda _: SimpleNamespace(query=self.query))
        self.closed = 0

    async def connect(self) -> None: ...

    async def close(self) -> None:
        self.closed += 1


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


async def test_bm25_filters_snapshot_and_jurisdiction_before_search() -> None:
    client = FakeClient()

    result = await WeaviateBm25SourcePassageRetriever(lambda: client).retrieve(
        query="self defence",
        snapshot=_snapshot(),
        jurisdiction="VIC",
        configuration=Bm25RetrievalConfiguration(top_k=5),
    )

    assert result.passages[0].passage_id == "passage-2"
    assert result.passages[0].score == 0.9
    assert client.query.arguments is not None
    assert client.query.arguments["limit"] == 5
    assert client.closed == 1


@pytest.mark.parametrize("effective_at", [date(2020, 1, 1), date(2026, 1, 1)])
async def test_bm25_rejects_unsupported_effective_date_before_connection(
    effective_at: date,
) -> None:
    client = FakeClient()
    retriever = WeaviateBm25SourcePassageRetriever(lambda: client)

    with pytest.raises(ValueError, match="effective-date"):
        await retriever.retrieve(
            query="self defence",
            snapshot=_snapshot(),
            jurisdiction="VIC",
            effective_at=effective_at,
        )

    assert client.closed == 0


async def test_bm25_rejects_a_jurisdiction_outside_the_source_snapshot() -> None:
    with pytest.raises(ValueError, match="jurisdiction"):
        await WeaviateBm25SourcePassageRetriever(lambda: FakeClient()).retrieve(
            query="self defence", snapshot=_snapshot(), jurisdiction="NSW"
        )
