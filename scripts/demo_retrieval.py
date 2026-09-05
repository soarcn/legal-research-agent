"""Show local retrieval evidence for one English legal research question."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from legal_research.adapters.embedding import BgeM3EmbeddingProvider
from legal_research.adapters.reranking import BgeM3RerankerProvider
from legal_research.adapters.weaviate.bm25_retriever import (
    Bm25RetrievalConfiguration,
    WeaviateBm25SourcePassageRetriever,
)
from legal_research.adapters.weaviate.dense_retriever import (
    DenseRetrievalConfiguration,
    WeaviateDenseSourcePassageRetriever,
)
from legal_research.application.hybrid_retrieval import (
    HybridRetrievalConfiguration,
    HybridSourcePassageRetriever,
)
from legal_research.application.legal_rag_bench_loader import LegalRagBenchSourceLoader
from legal_research.application.reranked_retrieval import (
    RerankConfiguration,
    SourcePassageReranker,
)
from legal_research.config import get_settings


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument(
        "--mode", choices=("bm25", "dense", "hybrid", "hybrid-rerank"), default="bm25"
    )
    parser.add_argument("--top-k", type=int, default=5)
    arguments = parser.parse_args()
    settings = get_settings()
    source = LegalRagBenchSourceLoader.from_manifest(
        Path("data/manifests/legal-rag-bench-v1.json")
    ).load(Path("data/raw"))
    passages = {passage.passage_id: passage for passage in source.passages}
    if arguments.mode == "bm25":
        result = await WeaviateBm25SourcePassageRetriever.from_url(
            settings.weaviate_url, grpc_port=settings.weaviate_grpc_port
        ).retrieve(
            query=arguments.question,
            snapshot=source.snapshot,
            jurisdiction="VIC",
            configuration=Bm25RetrievalConfiguration(top_k=arguments.top_k),
        )
        rows = [{"passage_id": item.passage_id, "score": item.score} for item in result.passages]
    elif arguments.mode == "dense":
        result = await WeaviateDenseSourcePassageRetriever.from_url(
            settings.weaviate_url,
            grpc_port=settings.weaviate_grpc_port,
            embedding_provider=BgeM3EmbeddingProvider(settings.embedding),
            embedding_config=settings.embedding,
        ).retrieve(
            query=arguments.question,
            snapshot=source.snapshot,
            jurisdiction="VIC",
            configuration=DenseRetrievalConfiguration.from_embedding_config(
                settings.embedding, top_k=arguments.top_k
            ),
        )
        rows = [
            {"passage_id": item.passage_id, "distance": item.distance} for item in result.passages
        ]
    else:
        candidate_k = 20 if arguments.mode == "hybrid-rerank" else max(30, arguments.top_k)
        hybrid = await HybridSourcePassageRetriever(
            WeaviateBm25SourcePassageRetriever.from_url(
                settings.weaviate_url, grpc_port=settings.weaviate_grpc_port
            ),
            WeaviateDenseSourcePassageRetriever.from_url(
                settings.weaviate_url,
                grpc_port=settings.weaviate_grpc_port,
                embedding_provider=BgeM3EmbeddingProvider(settings.embedding),
                embedding_config=settings.embedding,
            ),
            DenseRetrievalConfiguration.from_embedding_config(
                settings.embedding, top_k=candidate_k
            ),
        ).retrieve(
            query=arguments.question,
            snapshot=source.snapshot,
            jurisdiction="VIC",
            configuration=HybridRetrievalConfiguration(
                candidate_k=candidate_k, final_k=candidate_k
            ),
        )
        if arguments.mode == "hybrid":
            result = hybrid
            rows = [
                {
                    "passage_id": item.passage_id,
                    "fused_score": item.fused_score,
                    "bm25_rank": item.bm25_rank,
                    "dense_rank": item.dense_rank,
                }
                for item in hybrid.passages[: arguments.top_k]
            ]
        else:
            result = await SourcePassageReranker(BgeM3RerankerProvider(settings.reranker)).rerank(
                query=arguments.question,
                hybrid=hybrid,
                source_passages=source.passages,
                configuration=RerankConfiguration(candidate_k=candidate_k, final_k=arguments.top_k),
            )
            rows = [
                {
                    "passage_id": item.passage_id,
                    "reranker_score": item.reranker_score,
                    "hybrid_rank": item.hybrid_rank,
                }
                for item in result.passages
            ]
    for row in rows:
        passage = passages[row["passage_id"]]
        row["title"] = passage.title
        row["excerpt"] = passage.text[:240]
    print(
        json.dumps(
            {
                "question": arguments.question,
                "mode": arguments.mode,
                "source_snapshot_id": source.snapshot.source_snapshot_id,
                "latency_ms": result.latency_ms,
                "results": rows,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
