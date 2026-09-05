"""Run one reproducible non-holdout retrieval experiment."""

from __future__ import annotations

import argparse
import asyncio
import subprocess
from dataclasses import asdict
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
from legal_research.application.retrieval_benchmark import BenchmarkSplit, SplitAwareBenchmarkLoader
from legal_research.application.retrieval_evaluation import (
    FastRetrievalEvaluator,
    RankedRetrievalResult,
    RetrievalExperimentIdentity,
    write_evaluation_artifacts,
)
from legal_research.config import get_settings


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=("bm25", "dense", "hybrid", "hybrid-rerank"), required=True
    )
    parser.add_argument("--split", choices=("development", "validation"), default="development")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--candidate-k", type=int)
    parser.add_argument("--experiment-id", required=True)
    arguments = parser.parse_args()
    settings = get_settings()
    source_loader = LegalRagBenchSourceLoader.from_manifest(
        Path("data/manifests/legal-rag-bench-v1.json")
    )
    source = source_loader.load(Path("data/raw"))
    cases = SplitAwareBenchmarkLoader(source_loader).load(
        Path("data/raw"), split=BenchmarkSplit(arguments.split)
    )
    if arguments.mode == "bm25":
        configuration = Bm25RetrievalConfiguration(top_k=arguments.top_k)
        retriever = WeaviateBm25SourcePassageRetriever.from_url(
            settings.weaviate_url, grpc_port=settings.weaviate_grpc_port
        )
        results = [
            await retriever.retrieve(
                query=case.question,
                snapshot=source.snapshot,
                jurisdiction=source.snapshot.jurisdiction,
                configuration=configuration,
            )
            for case in cases
        ]
        rankings = [
            RankedRetrievalResult(
                question_id=case.question_id,
                passage_ids=tuple(item.passage_id for item in result.passages),
                latency_ms=result.latency_ms,
            )
            for case, result in zip(cases, results, strict=True)
        ]
        configuration_identity = asdict(configuration)
    elif arguments.mode == "dense":
        configuration = DenseRetrievalConfiguration.from_embedding_config(
            settings.embedding, top_k=arguments.top_k
        )
        retriever = WeaviateDenseSourcePassageRetriever.from_url(
            settings.weaviate_url,
            grpc_port=settings.weaviate_grpc_port,
            embedding_provider=BgeM3EmbeddingProvider(settings.embedding),
            embedding_config=settings.embedding,
        )
        results = [
            await retriever.retrieve(
                query=case.question,
                snapshot=source.snapshot,
                jurisdiction=source.snapshot.jurisdiction,
                configuration=configuration,
            )
            for case in cases
        ]
        rankings = [
            RankedRetrievalResult(
                question_id=case.question_id,
                passage_ids=tuple(item.passage_id for item in result.passages),
                latency_ms=result.latency_ms,
            )
            for case, result in zip(cases, results, strict=True)
        ]
        configuration_identity = asdict(configuration)
    else:
        candidate_k = arguments.candidate_k or (30 if arguments.mode == "hybrid" else 20)
        final_k = arguments.top_k if arguments.mode == "hybrid" else candidate_k
        hybrid_configuration = HybridRetrievalConfiguration(
            alpha=arguments.alpha,
            candidate_k=candidate_k,
            final_k=final_k,
        )
        dense_configuration = DenseRetrievalConfiguration.from_embedding_config(
            settings.embedding, top_k=candidate_k
        )
        hybrid_retriever = HybridSourcePassageRetriever(
            WeaviateBm25SourcePassageRetriever.from_url(
                settings.weaviate_url, grpc_port=settings.weaviate_grpc_port
            ),
            WeaviateDenseSourcePassageRetriever.from_url(
                settings.weaviate_url,
                grpc_port=settings.weaviate_grpc_port,
                embedding_provider=BgeM3EmbeddingProvider(settings.embedding),
                embedding_config=settings.embedding,
            ),
            dense_configuration,
        )
        hybrid_results = [
            await hybrid_retriever.retrieve(
                query=case.question,
                snapshot=source.snapshot,
                jurisdiction=source.snapshot.jurisdiction,
                configuration=hybrid_configuration,
            )
            for case in cases
        ]
        if arguments.mode == "hybrid":
            rankings = [
                RankedRetrievalResult(
                    question_id=case.question_id,
                    passage_ids=tuple(
                        item.passage_id for item in result.passages[: arguments.top_k]
                    ),
                    latency_ms=result.latency_ms,
                )
                for case, result in zip(cases, hybrid_results, strict=True)
            ]
            configuration_identity = {"hybrid": asdict(hybrid_configuration)}
        else:
            rerank_configuration = RerankConfiguration(
                candidate_k=candidate_k, final_k=arguments.top_k
            )
            reranker = SourcePassageReranker(BgeM3RerankerProvider(settings.reranker))
            reranked_results = [
                await reranker.rerank(
                    query=case.question,
                    hybrid=hybrid_result,
                    source_passages=source.passages,
                    configuration=rerank_configuration,
                )
                for case, hybrid_result in zip(cases, hybrid_results, strict=True)
            ]
            rankings = [
                RankedRetrievalResult(
                    question_id=case.question_id,
                    passage_ids=tuple(item.passage_id for item in result.passages),
                    latency_ms=hybrid_result.latency_ms + result.latency_ms,
                )
                for case, hybrid_result, result in zip(
                    cases, hybrid_results, reranked_results, strict=True
                )
            ]
            configuration_identity = {
                "hybrid": asdict(hybrid_configuration),
                "reranker": asdict(rerank_configuration),
            }
        configuration_identity["embedding_runtime"] = settings.embedding.model_dump(mode="json")
        if arguments.mode == "hybrid-rerank":
            configuration_identity["reranker_runtime"] = settings.reranker.model_dump(mode="json")
    code_revision = (
        await asyncio.to_thread(subprocess.check_output, ["git", "rev-parse", "HEAD"], text=True)
    ).strip()
    evaluation = FastRetrievalEvaluator().evaluate(
        cases,
        rankings,
        RetrievalExperimentIdentity(
            experiment_id=arguments.experiment_id,
            corpus_id=source.snapshot.source_snapshot_id,
            corpus_sha256=source.snapshot.corpus_sha256,
            code_revision=code_revision,
            retrieval_configuration=configuration_identity,
        ),
    )
    write_evaluation_artifacts(evaluation, Path("artifacts") / arguments.experiment_id)
    print(evaluation.aggregate)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
