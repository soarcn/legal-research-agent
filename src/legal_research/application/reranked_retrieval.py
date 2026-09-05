"""Bounded BGE reranking of already retrieved source-passage evidence."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from legal_research.application.hybrid_retrieval import HybridRetrievalResult
from legal_research.domain import SourcePassage
from legal_research.ports.reranking import RerankerProvider, RerankRequest


@dataclass(frozen=True, slots=True)
class RerankConfiguration:
    candidate_k: int = 20
    final_k: int = 5
    model_id: str = "BAAI/bge-reranker-v2-m3"
    revision: str = "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"

    def __post_init__(self) -> None:
        if self.candidate_k <= 0 or self.final_k <= 0 or self.final_k > self.candidate_k:
            raise ValueError("candidate_k and final_k must be positive with final_k <= candidate_k")


@dataclass(frozen=True, slots=True)
class RerankedPassage:
    passage_id: str
    reranker_score: float
    hybrid_rank: int


@dataclass(frozen=True, slots=True)
class RerankedRetrievalResult:
    passages: tuple[RerankedPassage, ...]
    configuration: RerankConfiguration
    latency_ms: float


class SourcePassageReranker:
    """Score only bounded hybrid candidates and preserve their pre-rerank rank."""

    def __init__(self, provider: RerankerProvider) -> None:
        self._provider = provider

    async def rerank(
        self,
        *,
        query: str,
        hybrid: HybridRetrievalResult,
        source_passages: tuple[SourcePassage, ...],
        configuration: RerankConfiguration | None = None,
    ) -> RerankedRetrievalResult:
        resolved = configuration or RerankConfiguration()
        candidates = hybrid.passages[: resolved.candidate_k]
        source_by_id = {passage.passage_id: passage for passage in source_passages}
        if len(candidates) < resolved.final_k:
            raise ValueError("hybrid retrieval returned fewer candidates than requested final_k")
        try:
            texts = tuple(source_by_id[item.passage_id].text for item in candidates)
        except KeyError as error:
            raise ValueError(
                "all rerank candidates must belong to the supplied source snapshot"
            ) from error
        started = perf_counter()
        response = await self._provider.rerank(RerankRequest(query=query, passages=texts))
        if response.model_id != resolved.model_id or response.revision != resolved.revision:
            raise ValueError("reranker response does not match the configured model contract")
        ranked = tuple(
            sorted(
                (
                    RerankedPassage(item.passage_id, score, index)
                    for index, (item, score) in enumerate(
                        zip(candidates, response.scores, strict=True), start=1
                    )
                ),
                key=lambda item: (-item.reranker_score, item.passage_id),
            )
        )
        return RerankedRetrievalResult(
            ranked[: resolved.final_k], resolved, (perf_counter() - started) * 1000
        )
