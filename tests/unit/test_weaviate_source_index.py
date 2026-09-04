"""P3.5 uses an explicit, stable-ID Weaviate derived index."""

from __future__ import annotations

from datetime import UTC, datetime

from legal_research.adapters.weaviate.schema import LEGAL_PASSAGE_V1_COLLECTION
from legal_research.adapters.weaviate.source_index import WeaviateSourcePassageIndex
from legal_research.application.legal_rag_bench_loader import LoadedLegalRagBench
from legal_research.application.source_passage_embedding import (
    EmbeddedSourcePassage,
    EmbeddingProvenance,
)
from legal_research.domain import SourcePassage, SourcePassageIdentity, SourceSnapshot


class FakeData:
    def __init__(self) -> None:
        self.inserted: list[dict[str, object]] = []
        self.updated: list[dict[str, object]] = []
        self.fail_duplicate = False

    async def insert(self, **kwargs: object) -> str:
        if self.fail_duplicate:
            raise RuntimeError("object already exists")
        self.inserted.append(kwargs)
        return "unused"

    async def update(self, **kwargs: object) -> None:
        self.updated.append(kwargs)


class FakeCollection:
    def __init__(self) -> None:
        self.data = FakeData()
        self.config = FakeConfig()


class FakeVectorIndexConfig:
    @staticmethod
    def vector_index_type() -> str:
        return "flat"


class FakeConfig:
    vectorizer = "none"
    vector_index_config = FakeVectorIndexConfig()

    async def get(self) -> FakeConfig:
        return self


class FakeCollections:
    def __init__(self) -> None:
        self.exists_value = False
        self.created: list[tuple[str, dict[str, object]]] = []
        self.collection = FakeCollection()

    async def exists(self, name: str) -> bool:
        assert name == LEGAL_PASSAGE_V1_COLLECTION
        return self.exists_value

    async def create(self, name: str, **kwargs: object) -> None:
        self.created.append((name, kwargs))
        self.exists_value = True

    def get(self, name: str) -> FakeCollection:
        assert name == LEGAL_PASSAGE_V1_COLLECTION
        return self.collection


class FakeClient:
    def __init__(self, collections: FakeCollections) -> None:
        self.collections = collections
        self.connected = 0
        self.closed = 0

    async def connect(self) -> None:
        self.connected += 1

    async def close(self) -> None:
        self.closed += 1


def _source() -> tuple[SourceSnapshot, LoadedLegalRagBench, tuple[EmbeddedSourcePassage, ...]]:
    snapshot = SourceSnapshot(
        source_snapshot_id="snapshot",
        dataset="dataset",
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
    passage = SourcePassage(
        source_snapshot_id="snapshot",
        passage_id="source-1",
        title="Title",
        text="Text",
        footnotes=None,
        content_sha256="d" * 64,
    )
    embedded = EmbeddedSourcePassage(
        source_snapshot_id="snapshot",
        passage_id="source-1",
        content_sha256="d" * 64,
        vector=(1.0, 2.0),
        provenance=EmbeddingProvenance(
            model_id="test",
            revision="a" * 40,
            dimension=2,
            device="cpu",
            batch_size=1,
            normalized=True,
        ),
    )
    return snapshot, LoadedLegalRagBench(snapshot, (passage,), ()), (embedded,)


async def test_index_creates_the_external_vector_flat_collection() -> None:
    collections = FakeCollections()
    client = FakeClient(collections)

    await WeaviateSourcePassageIndex(lambda: client).ensure_collection()

    name, kwargs = collections.created[0]
    assert name == LEGAL_PASSAGE_V1_COLLECTION
    assert len(kwargs["properties"]) == 8
    assert client.connected == client.closed == 1


async def test_index_uses_stable_source_identity_and_updates_a_retry() -> None:
    collections = FakeCollections()
    collections.exists_value = True
    client = FakeClient(collections)
    snapshot, source, embedded = _source()
    index = WeaviateSourcePassageIndex(lambda: client)

    await index.upsert(snapshot=snapshot, passages=embedded, source_passages=source)
    collections.collection.data.fail_duplicate = True
    await index.upsert(snapshot=snapshot, passages=embedded, source_passages=source)

    stable_id = SourcePassageIdentity(
        source_snapshot_id="snapshot", source_passage_id="source-1"
    ).key
    assert collections.collection.data.inserted[0]["uuid"] == stable_id
    assert collections.collection.data.updated[0]["uuid"] == stable_id
    assert collections.collection.data.inserted[0]["vector"] == [1.0, 2.0]
    assert collections.collection.data.inserted[0]["properties"] == {
        "sourceSnapshotId": "snapshot",
        "passageId": "source-1",
        "contentSha256": "d" * 64,
        "jurisdiction": "VIC",
        "language": "en",
        "title": "Title",
        "text": "Text",
        "footnotes": "",
    }
