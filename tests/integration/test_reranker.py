"""Opt-in local BGE reranker coverage using the pinned runtime contract."""

from pathlib import Path

import pytest


@pytest.mark.real_service
async def test_local_bge_reranker_scores_source_passage_candidates() -> None:
    from legal_research.adapters.reranking import BgeM3RerankerProvider
    from legal_research.application.hybrid_retrieval import (
        HybridRetrievalConfiguration,
        HybridRetrievalResult,
        HybridRetrievedPassage,
    )
    from legal_research.application.legal_rag_bench_loader import LegalRagBenchSourceLoader
    from legal_research.application.reranked_retrieval import (
        RerankConfiguration,
        SourcePassageReranker,
    )
    from legal_research.config import Settings

    settings = Settings()
    source = LegalRagBenchSourceLoader.from_manifest(
        Path("data/manifests/legal-rag-bench-v1.json")
    ).load(Path("data/raw"))
    result = await SourcePassageReranker(BgeM3RerankerProvider(settings.reranker)).rerank(
        query=source.questions[0].question,
        hybrid=HybridRetrievalResult(
            source.snapshot.source_snapshot_id,
            "VIC",
            HybridRetrievalConfiguration(candidate_k=2, final_k=2),
            tuple(
                HybridRetrievedPassage(passage.passage_id, 1.0 / index, index, None)
                for index, passage in enumerate(source.passages[:2], start=1)
            ),
            0,
            0,
        ),
        source_passages=source.passages,
        configuration=RerankConfiguration(candidate_k=2, final_k=1),
    )
    assert len(result.passages) == 1
