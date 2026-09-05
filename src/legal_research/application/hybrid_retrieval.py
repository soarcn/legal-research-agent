"""Deterministic weighted rank fusion over the P4 BM25 and dense retrieval baselines."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from typing import Protocol

from legal_research.adapters.weaviate.bm25_retriever import (
    Bm25RetrievalConfiguration,
    Bm25RetrievalResult,
)
from legal_research.adapters.weaviate.dense_retriever import (
    DenseRetrievalConfiguration,
    DenseRetrievalResult,
)
from legal_research.domain import SourceSnapshot


class Bm25Retriever(Protocol):
    async def retrieve(
        self,
        *,
        query: str,
        snapshot: SourceSnapshot,
        jurisdiction: str,
        configuration: Bm25RetrievalConfiguration | None = None,
        effective_at: date | None = None,
    ) -> Bm25RetrievalResult: ...


class DenseRetriever(Protocol):
    async def retrieve(
        self,
        *,
        query: str,
        snapshot: SourceSnapshot,
        jurisdiction: str,
        configuration: DenseRetrievalConfiguration | None = None,
        effective_at: date | None = None,
    ) -> DenseRetrievalResult: ...


@dataclass(frozen=True, slots=True)
class HybridRetrievalConfiguration:
    alpha: float = 0.5
    candidate_k: int = 30
    final_k: int = 10
    rank_constant: int = 60
    mode: str = "hybrid_weighted_rrf"

    def __post_init__(self) -> None:
        if not 0 <= self.alpha <= 1:
            raise ValueError("alpha must be between zero and one")
        if self.candidate_k <= 0 or self.final_k <= 0 or self.final_k > self.candidate_k:
            raise ValueError("candidate_k and final_k must be positive with final_k <= candidate_k")
        if self.rank_constant <= 0:
            raise ValueError("rank_constant must be positive")


@dataclass(frozen=True, slots=True)
class HybridRetrievedPassage:
    passage_id: str
    fused_score: float
    bm25_rank: int | None
    dense_rank: int | None


@dataclass(frozen=True, slots=True)
class HybridRetrievalResult:
    source_snapshot_id: str
    jurisdiction: str
    configuration: HybridRetrievalConfiguration
    passages: tuple[HybridRetrievedPassage, ...]
    bm25_latency_ms: float
    dense_latency_ms: float

    @property
    def latency_ms(self) -> float:
        return self.bm25_latency_ms + self.dense_latency_ms


class HybridSourcePassageRetriever:
    """Fuse independently filtered P4 candidates while retaining their rank provenance."""

    def __init__(
        self,
        bm25: Bm25Retriever,
        dense: DenseRetriever,
        dense_configuration: DenseRetrievalConfiguration,
    ) -> None:
        self._bm25 = bm25
        self._dense = dense
        self._dense_configuration = dense_configuration

    async def retrieve(
        self,
        *,
        query: str,
        snapshot: SourceSnapshot,
        jurisdiction: str,
        configuration: HybridRetrievalConfiguration | None = None,
        effective_at: date | None = None,
    ) -> HybridRetrievalResult:
        resolved = configuration or HybridRetrievalConfiguration()
        bm25 = await self._bm25.retrieve(
            query=query,
            snapshot=snapshot,
            jurisdiction=jurisdiction,
            configuration=Bm25RetrievalConfiguration(top_k=resolved.candidate_k),
            effective_at=effective_at,
        )
        dense = await self._dense.retrieve(
            query=query,
            snapshot=snapshot,
            jurisdiction=jurisdiction,
            configuration=replace(self._dense_configuration, top_k=resolved.candidate_k),
            effective_at=effective_at,
        )
        if (
            bm25.source_snapshot_id != dense.source_snapshot_id
            or bm25.jurisdiction != dense.jurisdiction
        ):
            raise ValueError("hybrid candidates must share one source snapshot and jurisdiction")
        fused = _fuse(bm25, dense, resolved)
        return HybridRetrievalResult(
            source_snapshot_id=bm25.source_snapshot_id,
            jurisdiction=bm25.jurisdiction,
            configuration=resolved,
            passages=fused[: resolved.final_k],
            bm25_latency_ms=bm25.latency_ms,
            dense_latency_ms=dense.latency_ms,
        )


def _fuse(
    bm25: Bm25RetrievalResult,
    dense: DenseRetrievalResult,
    configuration: HybridRetrievalConfiguration,
) -> tuple[HybridRetrievedPassage, ...]:
    bm25_ranks = {item.passage_id: index for index, item in enumerate(bm25.passages, start=1)}
    dense_ranks = {item.passage_id: index for index, item in enumerate(dense.passages, start=1)}
    passages = []
    for passage_id in bm25_ranks.keys() | dense_ranks.keys():
        bm25_rank, dense_rank = bm25_ranks.get(passage_id), dense_ranks.get(passage_id)
        fused_score = (
            (1 - configuration.alpha) / (configuration.rank_constant + bm25_rank)
            if bm25_rank is not None
            else 0.0
        ) + (
            configuration.alpha / (configuration.rank_constant + dense_rank)
            if dense_rank is not None
            else 0.0
        )
        passages.append(HybridRetrievedPassage(passage_id, fused_score, bm25_rank, dense_rank))
    return tuple(sorted(passages, key=lambda item: (-item.fused_score, item.passage_id)))
