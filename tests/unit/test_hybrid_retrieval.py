"""P5.1 weighted rank fusion is deterministic and preserves candidate provenance."""

from __future__ import annotations

from datetime import UTC, datetime

from legal_research.adapters.weaviate.bm25_retriever import (
    Bm25RetrievalResult,
    RetrievedSourcePassage,
)
from legal_research.adapters.weaviate.dense_retriever import (
    DenseRetrievalConfiguration,
    DenseRetrievalResult,
    DenseRetrievedSourcePassage,
)
from legal_research.application.hybrid_retrieval import (
    HybridRetrievalConfiguration,
    HybridSourcePassageRetriever,
)
from legal_research.domain import SourceSnapshot


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


class FakeBm25:
    async def retrieve(self, **_: object) -> Bm25RetrievalResult:
        from legal_research.adapters.weaviate.bm25_retriever import Bm25RetrievalConfiguration

        return Bm25RetrievalResult(
            "snapshot",
            "VIC",
            Bm25RetrievalConfiguration(3),
            (RetrievedSourcePassage("a", 1), RetrievedSourcePassage("b", 0.5)),
            10,
        )


class FakeDense:
    async def retrieve(self, **_: object) -> DenseRetrievalResult:
        config = DenseRetrievalConfiguration("model", "d" * 40, 2, True, 3)
        return DenseRetrievalResult(
            "snapshot",
            "VIC",
            config,
            (DenseRetrievedSourcePassage("b", 0.1), DenseRetrievedSourcePassage("c", 0.2)),
            20,
        )


async def test_weighted_rank_fusion_preserves_each_source_rank() -> None:
    config = DenseRetrievalConfiguration("model", "d" * 40, 2, True)
    result = await HybridSourcePassageRetriever(FakeBm25(), FakeDense(), config).retrieve(
        query="self defence",
        snapshot=_snapshot(),
        jurisdiction="VIC",
        configuration=HybridRetrievalConfiguration(alpha=0.5, candidate_k=3, final_k=3),
    )
    assert [item.passage_id for item in result.passages] == ["b", "a", "c"]
    assert result.passages[0].bm25_rank == 2
    assert result.passages[0].dense_rank == 1
    assert result.latency_ms == 30
