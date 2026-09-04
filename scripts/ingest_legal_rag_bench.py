"""Ingest the verified Legal RAG Bench v1 snapshot into local services."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from weaviate.client import WeaviateAsyncClient

from legal_research.adapters.embedding import BgeM3EmbeddingProvider
from legal_research.adapters.postgres.connection import AsyncPostgresDatabase
from legal_research.adapters.postgres.source_ingestion import PostgresSourceIngestionRepository
from legal_research.adapters.weaviate.readiness import connection_params_from_url
from legal_research.adapters.weaviate.source_index import WeaviateSourcePassageIndex
from legal_research.application.legal_rag_bench_loader import LegalRagBenchSourceLoader
from legal_research.application.source_ingestion import SourceIngestionService
from legal_research.application.source_passage_embedding import SourcePassageEmbedder
from legal_research.config import get_settings

MANIFEST_PATH = Path("data/manifests/legal-rag-bench-v1.json")
RAW_ROOT = Path("data/raw")


async def main() -> int:
    """Run one bounded, observable ingestion attempt without printing source text or vectors."""
    settings = get_settings()
    database = AsyncPostgresDatabase(settings.database_url)
    try:
        report = await SourceIngestionService(
            loader=LegalRagBenchSourceLoader.from_manifest(MANIFEST_PATH),
            repository=PostgresSourceIngestionRepository(database.engine),
            embedder=SourcePassageEmbedder(
                BgeM3EmbeddingProvider(settings.embedding), settings.embedding
            ),
            index=WeaviateSourcePassageIndex(
                lambda: WeaviateAsyncClient(
                    connection_params=connection_params_from_url(
                        settings.weaviate_url,
                        grpc_port=settings.weaviate_grpc_port,
                    )
                )
            ),
        ).ingest(RAW_ROOT)
    finally:
        await database.dispose()

    print(
        json.dumps(
            {
                "ingestion_job_id": str(report.ingestion_job_id),
                "source_snapshot_id": report.source_snapshot_id,
                "source_passage_count": report.source_passage_count,
                "benchmark_question_count": report.benchmark_question_count,
                "indexed_passage_count": report.indexed_passage_count,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
