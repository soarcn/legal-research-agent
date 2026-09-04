from datetime import datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative metadata registry.

    PostgreSQL is authoritative for provenance and observable run records.
    """

    pass


class SourceSnapshotRecord(Base):
    __tablename__ = "source_snapshots"

    source_snapshot_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    dataset: Mapped[str] = mapped_column(String(256))
    dataset_revision: Mapped[str] = mapped_column(String(40))
    source_url: Mapped[str] = mapped_column(Text)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    corpus_sha256: Mapped[str] = mapped_column(String(64))
    corpus_count: Mapped[int] = mapped_column(Integer)
    qa_sha256: Mapped[str] = mapped_column(String(64))
    qa_count: Mapped[int] = mapped_column(Integer)
    licence_policy: Mapped[str] = mapped_column(Text)
    jurisdiction: Mapped[str] = mapped_column(String(32))
    language: Mapped[str] = mapped_column(String(32))
    corpus_snapshot_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    corpus_snapshot_date_status: Mapped[str] = mapped_column(String(64))


class SourcePassageRecord(Base):
    __tablename__ = "source_passages"

    source_snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("source_snapshots.source_snapshot_id"), primary_key=True
    )
    source_passage_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    footnotes: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_sha256: Mapped[str] = mapped_column(String(64))


class BenchmarkQuestionRecord(Base):
    __tablename__ = "benchmark_questions"

    source_snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("source_snapshots.source_snapshot_id"), primary_key=True
    )
    question_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    relevant_passage_id: Mapped[str] = mapped_column(String(256))


class IngestionJobRecord(Base):
    __tablename__ = "ingestion_jobs"

    ingestion_job_id: Mapped[UUID] = mapped_column(primary_key=True)
    source_snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("source_snapshots.source_snapshot_id")
    )
    status: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_category: Mapped[str | None] = mapped_column(String(128), nullable=True)


class ResearchRunRecord(Base):
    __tablename__ = "research_runs"

    run_id: Mapped[UUID] = mapped_column(primary_key=True)
    source_snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("source_snapshots.source_snapshot_id")
    )
    question: Mapped[str] = mapped_column(Text)
    jurisdiction: Mapped[str] = mapped_column(String(32))
    requested_effective_at: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    evidence_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
