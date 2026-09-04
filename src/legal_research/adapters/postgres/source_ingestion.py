"""PostgreSQL persistence for immutable source facts and ingestion audit jobs."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine

from legal_research.application.legal_rag_bench_loader import LoadedLegalRagBench
from legal_research.application.source_ingestion import IngestionFailureCategory
from legal_research.domain import IngestionJob, IngestionJobStatus, SourceSnapshot

from .models import (
    BenchmarkQuestionRecord,
    IngestionJobRecord,
    SourcePassageRecord,
    SourceSnapshotRecord,
)


class PostgresSourceIngestionRepository:
    """Persist source facts once; later retries never alter immutable source rows."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def start_job(self, snapshot: SourceSnapshot) -> IngestionJob:
        """Record a running ingestion attempt before source writes begin."""
        job_id = uuid4()
        started_at = datetime.now(UTC)
        async with self._engine.begin() as connection:
            await connection.execute(
                insert(SourceSnapshotRecord)
                .values(_snapshot_values(snapshot))
                .on_conflict_do_nothing(index_elements=["source_snapshot_id"])
            )
            await connection.execute(
                insert(IngestionJobRecord).values(
                    ingestion_job_id=job_id,
                    source_snapshot_id=snapshot.source_snapshot_id,
                    status=IngestionJobStatus.RUNNING.value,
                    started_at=started_at,
                )
            )
        return IngestionJob(
            ingestion_job_id=job_id,
            source_snapshot_id=snapshot.source_snapshot_id,
            status=IngestionJobStatus.RUNNING,
            started_at=started_at,
        )

    async def persist_source_facts(self, source: LoadedLegalRagBench) -> None:
        """Use conflict-do-nothing writes because this source snapshot is immutable."""
        snapshot = source.snapshot
        async with self._engine.begin() as connection:
            await connection.execute(
                insert(SourceSnapshotRecord)
                .values(_snapshot_values(snapshot))
                .on_conflict_do_nothing(index_elements=["source_snapshot_id"])
            )
            await connection.execute(
                insert(SourcePassageRecord)
                .values(
                    [
                        {
                            "source_snapshot_id": passage.source_snapshot_id,
                            "source_passage_id": passage.passage_id,
                            "title": passage.title,
                            "text": passage.text,
                            "footnotes": passage.footnotes,
                            "content_sha256": passage.content_sha256,
                        }
                        for passage in source.passages
                    ]
                )
                .on_conflict_do_nothing(index_elements=["source_snapshot_id", "source_passage_id"])
            )
            await connection.execute(
                insert(BenchmarkQuestionRecord)
                .values(
                    [
                        {
                            "source_snapshot_id": question.source_snapshot_id,
                            "question_id": question.question_id,
                            "question": question.question,
                            "answer": question.answer,
                            "relevant_passage_id": question.relevant_passage_id,
                        }
                        for question in source.questions
                    ]
                )
                .on_conflict_do_nothing(index_elements=["source_snapshot_id", "question_id"])
            )

    async def succeed_job(self, ingestion_job_id: UUID) -> None:
        await self._finish_job(ingestion_job_id, IngestionJobStatus.SUCCEEDED)

    async def fail_job(self, ingestion_job_id: UUID, category: IngestionFailureCategory) -> None:
        await self._finish_job(ingestion_job_id, IngestionJobStatus.FAILED, category.value)

    async def _finish_job(
        self,
        ingestion_job_id: UUID,
        status: IngestionJobStatus,
        error_category: str | None = None,
    ) -> None:
        async with self._engine.begin() as connection:
            await connection.execute(
                update(IngestionJobRecord)
                .where(IngestionJobRecord.ingestion_job_id == ingestion_job_id)
                .values(
                    status=status.value,
                    completed_at=datetime.now(UTC),
                    error_category=error_category,
                )
            )


def _snapshot_values(snapshot: SourceSnapshot) -> dict[str, object]:
    return {
        "source_snapshot_id": snapshot.source_snapshot_id,
        "dataset": snapshot.dataset,
        "dataset_revision": snapshot.dataset_revision,
        "source_url": snapshot.source_url,
        "retrieved_at": snapshot.retrieved_at,
        "corpus_sha256": snapshot.corpus_sha256,
        "corpus_count": snapshot.corpus_count,
        "qa_sha256": snapshot.qa_sha256,
        "qa_count": snapshot.qa_count,
        "licence_policy": snapshot.licence_policy,
        "jurisdiction": snapshot.jurisdiction,
        "language": snapshot.language,
        "corpus_snapshot_date": snapshot.corpus_snapshot_date,
        "corpus_snapshot_date_status": snapshot.corpus_snapshot_date_status,
    }
