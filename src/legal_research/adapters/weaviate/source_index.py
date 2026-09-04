"""Explicit Weaviate v1 derived-index adapter for source-native passages."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from typing import Protocol

from weaviate.classes.config import Configure, DataType, Property

from legal_research.application.legal_rag_bench_loader import LoadedLegalRagBench
from legal_research.application.source_passage_embedding import EmbeddedSourcePassage
from legal_research.domain import SourcePassageIdentity, SourceSnapshot

from .schema import LEGAL_PASSAGE_V1_SCHEMA, WeaviatePropertySchema


class WeaviateCollectionManager(Protocol):
    """The narrow async client surface required by this adapter."""

    @property
    def collections(self) -> object:
        """Expose the SDK collection manager."""

        ...

    async def connect(self) -> None:
        """Open the client connection."""

        ...

    async def close(self) -> None:
        """Close the client connection."""

        ...


WeaviateClientFactory = Callable[[], WeaviateCollectionManager]


class WeaviateSourcePassageIndex:
    """Own derived vector writes while preserving source passage IDs as properties."""

    def __init__(self, client_factory: WeaviateClientFactory) -> None:
        self._client_factory = client_factory

    async def ensure_collection(self) -> None:
        client = self._client_factory()
        try:
            await client.connect()
            collections = client.collections
            if await collections.exists(LEGAL_PASSAGE_V1_SCHEMA.collection_name):  # type: ignore[attr-defined]
                collection = collections.get(LEGAL_PASSAGE_V1_SCHEMA.collection_name)  # type: ignore[attr-defined]
                configuration = await collection.config.get()  # type: ignore[attr-defined]
                vectorizer = getattr(configuration.vectorizer, "value", configuration.vectorizer)
                if (
                    vectorizer != LEGAL_PASSAGE_V1_SCHEMA.vectorizer
                    or configuration.vector_index_config.vector_index_type()
                    != LEGAL_PASSAGE_V1_SCHEMA.vector_index_type
                ):
                    raise ValueError(
                        "The existing LegalPassageV1 collection has a different contract."
                    )
                return
            await collections.create(  # type: ignore[attr-defined]
                LEGAL_PASSAGE_V1_SCHEMA.collection_name,
                properties=[_sdk_property(item) for item in LEGAL_PASSAGE_V1_SCHEMA.properties],
                vectorizer_config=Configure.Vectorizer.none(),
                vector_index_config=Configure.VectorIndex.flat(),
            )
        finally:
            with suppress(Exception):
                await client.close()

    async def delete_collection(self) -> None:
        """Delete only the named derived collection; callers own confirmation policy."""
        client = self._client_factory()
        try:
            await client.connect()
            collections = client.collections
            if await collections.exists(LEGAL_PASSAGE_V1_SCHEMA.collection_name):  # type: ignore[attr-defined]
                await collections.delete(LEGAL_PASSAGE_V1_SCHEMA.collection_name)  # type: ignore[attr-defined]
        finally:
            with suppress(Exception):
                await client.close()

    async def count(self) -> int:
        """Return only the derived collection object count for rebuild verification."""
        client = self._client_factory()
        try:
            await client.connect()
            collections = client.collections
            if not await collections.exists(LEGAL_PASSAGE_V1_SCHEMA.collection_name):  # type: ignore[attr-defined]
                return 0
            collection = collections.get(LEGAL_PASSAGE_V1_SCHEMA.collection_name)  # type: ignore[attr-defined]
            result = await collection.aggregate.over_all(total_count=True)  # type: ignore[attr-defined]
            return int(result.total_count)
        finally:
            with suppress(Exception):
                await client.close()

    async def upsert(
        self,
        *,
        snapshot: SourceSnapshot,
        passages: tuple[EmbeddedSourcePassage, ...],
        source_passages: LoadedLegalRagBench,
    ) -> None:
        source_by_id = {passage.passage_id: passage for passage in source_passages.passages}
        if len({passage.passage_id for passage in passages}) != len(passages):
            raise ValueError("An index write cannot contain duplicate source passage IDs.")
        client = self._client_factory()
        try:
            await client.connect()
            collection = client.collections.get(LEGAL_PASSAGE_V1_SCHEMA.collection_name)  # type: ignore[attr-defined]
            for embedded in passages:
                source = source_by_id.get(embedded.passage_id)
                if source is None or embedded.source_snapshot_id != snapshot.source_snapshot_id:
                    raise ValueError(
                        "The derived vector does not belong to the requested source snapshot."
                    )
                stable_id = SourcePassageIdentity(
                    source_snapshot_id=snapshot.source_snapshot_id,
                    source_passage_id=source.passage_id,
                ).key
                properties = {
                    "sourceSnapshotId": snapshot.source_snapshot_id,
                    "passageId": source.passage_id,
                    "contentSha256": source.content_sha256,
                    "jurisdiction": snapshot.jurisdiction,
                    "language": snapshot.language,
                    "title": source.title,
                    "text": source.text,
                    "footnotes": source.footnotes or "",
                }
                try:
                    await collection.data.insert(  # type: ignore[attr-defined]
                        properties=properties,
                        uuid=stable_id,
                        vector=list(embedded.vector),
                    )
                except Exception as error:
                    if not _is_already_exists(error):
                        raise
                    await collection.data.update(  # type: ignore[attr-defined]
                        uuid=stable_id,
                        properties=properties,
                        vector=list(embedded.vector),
                    )
        finally:
            with suppress(Exception):
                await client.close()


def _sdk_property(schema: WeaviatePropertySchema) -> Property:
    return Property(
        name=schema.name,
        data_type=DataType.TEXT,
        index_filterable=schema.filterable,
        index_searchable=schema.searchable,
        skip_vectorization=True,
    )


def _is_already_exists(error: Exception) -> bool:
    """Avoid depending on a version-specific Weaviate exception hierarchy."""
    return "already exists" in str(error).lower()
