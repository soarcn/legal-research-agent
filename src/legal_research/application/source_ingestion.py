"""Idempotent ingestion orchestration for one verified immutable source snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol
from uuid import UUID

from legal_research.application.legal_rag_bench_loader import (
    LegalRagBenchSourceLoader,
    LoadedLegalRagBench,
)
from legal_research.application.source_passage_embedding import EmbeddedSourcePassage
from legal_research.domain import IngestionJob, SourcePassage, SourceSnapshot


class IngestionFailureCategory(StrEnum):
    """Safe, operational failure categories without source text or vectors."""

    PERSISTENCE = "persistence"
    EMBEDDING = "embedding"
    INDEX = "index"


class SourceIngestionRepository(Protocol):
    """Authoritative persistence operations used by the ingestion workflow."""

    async def start_job(self, snapshot: SourceSnapshot) -> IngestionJob:
        """Create a running, observable ingestion job."""

        ...

    async def persist_source_facts(self, source: LoadedLegalRagBench) -> None:
        """Idempotently persist immutable source facts."""

        ...

    async def succeed_job(self, ingestion_job_id: UUID) -> None:
        """Mark an ingestion job successful."""

        ...

    async def fail_job(self, ingestion_job_id: UUID, category: IngestionFailureCategory) -> None:
        """Persist the safe category for a failed ingestion job."""

        ...


class SourcePassageEmbeddingService(Protocol):
    """The derived-vector operation required by source ingestion."""

    async def embed(self, passages: tuple[SourcePassage, ...]) -> tuple[EmbeddedSourcePassage, ...]:
        """Return one derived vector for each supplied source passage."""

        ...


class DerivedPassageIndex(Protocol):
    """Rebuildable vector-index operations; never a source of legal truth."""

    async def ensure_collection(self) -> None:
        """Create or validate the explicit derived collection contract."""

        ...

    async def upsert(
        self,
        *,
        snapshot: SourceSnapshot,
        passages: tuple[EmbeddedSourcePassage, ...],
        source_passages: LoadedLegalRagBench,
    ) -> None:
        """Idempotently write source-native passages and their derived vectors."""

        ...


@dataclass(frozen=True, slots=True)
class IngestionReport:
    """Safe ingestion outcome suitable for a CLI, logs, and audit records."""

    ingestion_job_id: UUID
    source_snapshot_id: str
    source_passage_count: int
    benchmark_question_count: int
    indexed_passage_count: int


class SourceIngestionService:
    """Keep source loading, persistence, embedding and indexing explicitly ordered."""

    def __init__(
        self,
        *,
        loader: LegalRagBenchSourceLoader,
        repository: SourceIngestionRepository,
        embedder: SourcePassageEmbeddingService,
        index: DerivedPassageIndex,
    ) -> None:
        self._loader = loader
        self._repository = repository
        self._embedder = embedder
        self._index = index

    async def ingest(self, raw_root: Path) -> IngestionReport:
        """Load verified bytes once, then persist and index them with bounded failure state."""
        source = self._loader.load(raw_root)
        job = await self._repository.start_job(source.snapshot)
        phase = IngestionFailureCategory.PERSISTENCE
        try:
            await self._repository.persist_source_facts(source)
            phase = IngestionFailureCategory.EMBEDDING
            embedded = await self._embedder.embed(source.passages)
            phase = IngestionFailureCategory.INDEX
            await self._index.ensure_collection()
            await self._index.upsert(
                snapshot=source.snapshot,
                passages=embedded,
                source_passages=source,
            )
            await self._repository.succeed_job(job.ingestion_job_id)
        except Exception:
            await self._repository.fail_job(job.ingestion_job_id, phase)
            raise

        return IngestionReport(
            ingestion_job_id=job.ingestion_job_id,
            source_snapshot_id=source.snapshot.source_snapshot_id,
            source_passage_count=len(source.passages),
            benchmark_question_count=len(source.questions),
            indexed_passage_count=len(embedded),
        )
