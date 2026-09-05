"""P5.3 reranking is bounded, provenance-preserving, and model-contract checked."""

from legal_research.application.hybrid_retrieval import (
    HybridRetrievalConfiguration,
    HybridRetrievalResult,
    HybridRetrievedPassage,
)
from legal_research.application.reranked_retrieval import RerankConfiguration, SourcePassageReranker
from legal_research.domain import SourcePassage
from legal_research.ports.reranking import RerankResponse


class FakeProvider:
    async def rerank(self, request):
        assert request.passages == ("text a", "text b")
        return RerankResponse(
            scores=(0.1, 0.9),
            model_id="BAAI/bge-reranker-v2-m3",
            revision="953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e",
        )


def _source(passage_id: str, text: str) -> SourcePassage:
    return SourcePassage(
        source_snapshot_id="snapshot",
        passage_id=passage_id,
        title="title",
        text=text,
        footnotes=None,
        content_sha256="a" * 64,
    )


async def test_reranker_orders_bounded_hybrid_candidates_by_cross_encoder_score() -> None:
    hybrid = HybridRetrievalResult(
        "snapshot",
        "VIC",
        HybridRetrievalConfiguration(candidate_k=2, final_k=2),
        (HybridRetrievedPassage("a", 0.2, 1, None), HybridRetrievedPassage("b", 0.1, None, 1)),
        1,
        2,
    )
    result = await SourcePassageReranker(FakeProvider()).rerank(
        query="query",
        hybrid=hybrid,
        source_passages=(_source("a", "text a"), _source("b", "text b")),
        configuration=RerankConfiguration(candidate_k=2, final_k=1),
    )
    assert result.passages[0].passage_id == "b"
    assert result.passages[0].hybrid_rank == 2
