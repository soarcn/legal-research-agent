"""P3.5 keeps ingestion observable, ordered, and safe to retry."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from legal_research.application.legal_rag_bench_loader import LoadedLegalRagBench
from legal_research.application.source_ingestion import (
    IngestionFailureCategory,
    SourceIngestionService,
)
from legal_research.application.source_passage_embedding import (
    EmbeddedSourcePassage,
    EmbeddingProvenance,
)
from legal_research.domain import (
    BenchmarkQuestion,
    IngestionJob,
    IngestionJobStatus,
    SourcePassage,
    SourceSnapshot,
)


class FakeLoader:
    def __init__(self, source: LoadedLegalRagBench) -> None:
        self.source = source

    def load(self, raw_root: Path) -> LoadedLegalRagBench:
        assert raw_root == Path("data/raw/legal-rag-bench")
        return self.source


class FakeRepository:
    def __init__(self) -> None:
        self.persisted = 0
        self.succeeded: list[object] = []
        self.failed: list[tuple[object, IngestionFailureCategory]] = []

    async def start_job(self, snapshot: SourceSnapshot) -> IngestionJob:
        return IngestionJob(
            ingestion_job_id=uuid4(),
            source_snapshot_id=snapshot.source_snapshot_id,
            status=IngestionJobStatus.RUNNING,
            started_at=datetime.now(UTC),
        )

    async def persist_source_facts(self, source: LoadedLegalRagBench) -> None:
        self.persisted += 1

    async def succeed_job(self, ingestion_job_id: object) -> None:
        self.succeeded.append(ingestion_job_id)

    async def fail_job(self, ingestion_job_id: object, category: IngestionFailureCategory) -> None:
        self.failed.append((ingestion_job_id, category))


class FakeEmbedder:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    async def embed(self, passages: tuple[SourcePassage, ...]) -> tuple[EmbeddedSourcePassage, ...]:
        if self.fail:
            raise RuntimeError("embedding unavailable")
        return tuple(
            EmbeddedSourcePassage(
                source_snapshot_id=passage.source_snapshot_id,
                passage_id=passage.passage_id,
                content_sha256=passage.content_sha256,
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
            for passage in passages
        )


class FakeIndex:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.ensured = 0
        self.upserts = 0

    async def ensure_collection(self) -> None:
        self.ensured += 1

    async def upsert(
        self,
        *,
        snapshot: SourceSnapshot,
        passages: tuple[EmbeddedSourcePassage, ...],
        source_passages: LoadedLegalRagBench,
    ) -> None:
        self.upserts += 1
        if self.fail:
            raise RuntimeError("index unavailable")


def _source() -> LoadedLegalRagBench:
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
    question = BenchmarkQuestion(
        source_snapshot_id="snapshot",
        question_id=1,
        question="Question",
        answer="Answer",
        relevant_passage_id="source-1",
    )
    return LoadedLegalRagBench(snapshot=snapshot, passages=(passage,), questions=(question,))


async def test_ingestion_retries_source_facts_and_index_without_changing_report() -> None:
    repository = FakeRepository()
    index = FakeIndex()
    service = SourceIngestionService(
        loader=FakeLoader(_source()), repository=repository, embedder=FakeEmbedder(), index=index
    )

    first = await service.ingest(Path("data/raw/legal-rag-bench"))
    second = await service.ingest(Path("data/raw/legal-rag-bench"))

    assert first.source_snapshot_id == second.source_snapshot_id == "snapshot"
    assert first.indexed_passage_count == second.indexed_passage_count == 1
    assert repository.persisted == 2
    assert len(repository.succeeded) == 2
    assert index.ensured == index.upserts == 2


async def test_ingestion_records_safe_embedding_failure() -> None:
    repository = FakeRepository()
    service = SourceIngestionService(
        loader=FakeLoader(_source()),
        repository=repository,
        embedder=FakeEmbedder(fail=True),
        index=FakeIndex(),
    )

    with pytest.raises(RuntimeError, match="embedding unavailable"):
        await service.ingest(Path("data/raw/legal-rag-bench"))

    assert repository.failed[0][1] is IngestionFailureCategory.EMBEDDING


async def test_ingestion_records_safe_index_failure() -> None:
    repository = FakeRepository()
    service = SourceIngestionService(
        loader=FakeLoader(_source()),
        repository=repository,
        embedder=FakeEmbedder(),
        index=FakeIndex(fail=True),
    )

    with pytest.raises(RuntimeError, match="index unavailable"):
        await service.ingest(Path("data/raw/legal-rag-bench"))

    assert repository.failed[0][1] is IngestionFailureCategory.INDEX
