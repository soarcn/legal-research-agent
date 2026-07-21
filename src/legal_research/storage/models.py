from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Document(Base):
    """Authoritative identity and provenance record for a source document."""

    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_url: Mapped[str] = mapped_column(Text)
    source_authority: Mapped[str | None] = mapped_column(String(255))
    licence: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DocumentVersion(Base):
    """Immutable, time-bounded source version; Weaviate indexes this record's passages."""

    __tablename__ = "document_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AgentRun(Base):
    """Observable workflow record; never stores model chain-of-thought."""

    __tablename__ = "agent_runs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    question: Mapped[str] = mapped_column(Text)
    jurisdiction: Mapped[str | None] = mapped_column(String(32))
    effective_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="started")
    prompt_version: Mapped[str | None] = mapped_column(String(64))
    model_name: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
