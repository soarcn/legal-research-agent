"""Immutable domain contracts for frozen sources and deterministic research work."""

from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EvidenceState(StrEnum):
    """Verifiable evidence states; never a model-generated numeric confidence."""

    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"
    CONFLICTING = "conflicting"


class IngestionJobStatus(StrEnum):
    """Observable lifecycle states for later ingestion orchestration."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class DomainModel(BaseModel):
    """Base model for stable, immutable domain boundaries."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class SourceSnapshot(DomainModel):
    """One immutable corpus acquisition, not a legal document version."""

    source_snapshot_id: str
    dataset: str
    dataset_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    source_url: str
    retrieved_at: datetime
    corpus_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    corpus_count: int = Field(gt=0)
    qa_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    qa_count: int = Field(gt=0)
    licence_policy: str
    jurisdiction: str
    language: str
    corpus_snapshot_date: date | None = None
    corpus_snapshot_date_status: str
    legal_effective_at: None = None

    @field_validator("retrieved_at")
    @classmethod
    def retrieved_at_must_be_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("retrieved_at must be a UTC timestamp")
        return value

    @model_validator(mode="after")
    def snapshot_date_status_must_match_value(self) -> SourceSnapshot:
        if (
            self.corpus_snapshot_date is None
            and self.corpus_snapshot_date_status != "not_published_by_dataset"
        ):
            raise ValueError("an unavailable corpus snapshot date must state its source status")
        if (
            self.corpus_snapshot_date is not None
            and self.corpus_snapshot_date_status != "published_by_dataset"
        ):
            raise ValueError("a published corpus snapshot date must state its source status")
        return self


class SourcePassage(DomainModel):
    """An unchanged source-native passage that is the v1 retrieval unit."""

    source_snapshot_id: str
    passage_id: str
    title: str
    text: str
    footnotes: str | None
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class BenchmarkQuestion(DomainModel):
    """A source-provided QA record and its exact gold source-passage reference."""

    source_snapshot_id: str
    question_id: int = Field(gt=0)
    question: str
    answer: str
    relevant_passage_id: str


class ResearchRun(DomainModel):
    """One observable deterministic workflow execution, independent of an Agent."""

    run_id: UUID = Field(default_factory=uuid4)
    source_snapshot_id: str
    question: str
    jurisdiction: str
    requested_effective_at: date | None = None
    evidence_state: EvidenceState | None = None
    created_at: datetime
    completed_at: datetime | None = None

    @field_validator("created_at", "completed_at")
    @classmethod
    def timestamps_must_be_utc(cls, value: datetime | None) -> datetime | None:
        if value is not None and (
            value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value)
        ):
            raise ValueError("timestamps must be UTC")
        return value


class IngestionJob(DomainModel):
    """An observable later ingestion attempt; no database persistence is implied yet."""

    ingestion_job_id: UUID = Field(default_factory=uuid4)
    source_snapshot_id: str
    status: IngestionJobStatus = IngestionJobStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_category: str | None = None

    @field_validator("started_at", "completed_at")
    @classmethod
    def timestamps_must_be_utc(cls, value: datetime | None) -> datetime | None:
        if value is not None and (
            value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value)
        ):
            raise ValueError("timestamps must be UTC")
        return value
