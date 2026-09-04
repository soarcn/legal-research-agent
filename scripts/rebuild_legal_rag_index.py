"""Rebuild only the named, derived LegalPassageV1 Weaviate collection."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from weaviate.client import WeaviateAsyncClient

from legal_research.adapters.embedding import BgeM3EmbeddingProvider
from legal_research.adapters.weaviate.readiness import connection_params_from_url
from legal_research.adapters.weaviate.source_index import WeaviateSourcePassageIndex
from legal_research.application.index_rebuild import (
    REBUILD_CONFIRMATION,
    DerivedIndexRebuildService,
)
from legal_research.application.legal_rag_bench_loader import LegalRagBenchSourceLoader
from legal_research.application.source_passage_embedding import SourcePassageEmbedder
from legal_research.config import get_settings


async def main() -> int:
    settings = get_settings()
    confirmation = os.environ.get("CONFIRM_REBUILD_INDEX", "")
    report = await DerivedIndexRebuildService(
        loader=LegalRagBenchSourceLoader.from_manifest(
            Path("data/manifests/legal-rag-bench-v1.json")
        ),
        embedder=SourcePassageEmbedder(
            BgeM3EmbeddingProvider(settings.embedding), settings.embedding
        ),
        index=WeaviateSourcePassageIndex(
            lambda: WeaviateAsyncClient(
                connection_params=connection_params_from_url(
                    settings.weaviate_url, grpc_port=settings.weaviate_grpc_port
                )
            )
        ),
    ).rebuild(raw_root=Path("data/raw"), confirmation=confirmation)
    print(
        json.dumps(
            {
                "source_snapshot_id": report.source_snapshot_id,
                "expected_passage_count": report.expected_passage_count,
                "indexed_passage_count": report.indexed_passage_count,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    if os.environ.get("CONFIRM_REBUILD_INDEX") != REBUILD_CONFIRMATION:
        raise SystemExit(
            "Set CONFIRM_REBUILD_INDEX=legal-passage-v1 to rebuild only LegalPassageV1."
        )
    raise SystemExit(asyncio.run(main()))
