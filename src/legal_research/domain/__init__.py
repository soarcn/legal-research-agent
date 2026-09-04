"""Legal research domain models, value objects, and protocols."""

from legal_research.domain.chunking import DerivedPassage, FutureSourceSection
from legal_research.domain.identifiers import (
    SourcePassageIdentity,
    future_derived_passage_id,
    future_document_id,
    future_document_version_id,
    future_section_id,
)
from legal_research.domain.models import (
    BenchmarkQuestion,
    EvidenceState,
    IngestionJob,
    IngestionJobStatus,
    ResearchRun,
    SourcePassage,
    SourceSnapshot,
)

__all__ = [
    "BenchmarkQuestion",
    "DerivedPassage",
    "EvidenceState",
    "FutureSourceSection",
    "IngestionJob",
    "IngestionJobStatus",
    "ResearchRun",
    "SourcePassage",
    "SourcePassageIdentity",
    "SourceSnapshot",
    "future_derived_passage_id",
    "future_document_id",
    "future_document_version_id",
    "future_section_id",
]
