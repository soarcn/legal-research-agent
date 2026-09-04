"""Domain models preserve frozen-source semantics without legal inferences."""

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from legal_research.domain import (
    BenchmarkQuestion,
    EvidenceState,
    ResearchRun,
    SourcePassage,
    SourceSnapshot,
)


def source_snapshot(**overrides: object) -> SourceSnapshot:
    values: dict[str, object] = {
        "source_snapshot_id": "legal-rag-bench@" + "a" * 40,
        "dataset": "isaacus/legal-rag-bench",
        "dataset_revision": "a" * 40,
        "source_url": "https://huggingface.co/datasets/isaacus/legal-rag-bench",
        "retrieved_at": datetime(2026, 9, 4, tzinfo=UTC),
        "corpus_sha256": "b" * 64,
        "corpus_count": 4876,
        "qa_sha256": "c" * 64,
        "qa_count": 100,
        "licence_policy": "Treat as CC BY-NC-SA 4.0 pending publisher clarification",
        "jurisdiction": "VIC",
        "language": "en-AU",
        "corpus_snapshot_date": None,
        "corpus_snapshot_date_status": "not_published_by_dataset",
    }
    values.update(overrides)
    return SourceSnapshot(**values)


def test_source_snapshot_preserves_provenance_without_effective_date_inference() -> None:
    snapshot = source_snapshot()

    assert snapshot.legal_effective_at is None
    assert snapshot.corpus_snapshot_date is None
    assert snapshot.corpus_snapshot_date_status == "not_published_by_dataset"


def test_source_snapshot_rejects_non_utc_retrieval_time() -> None:
    with pytest.raises(ValidationError):
        source_snapshot(retrieved_at=datetime(2026, 9, 4, tzinfo=UTC).replace(tzinfo=None))


def test_source_snapshot_requires_status_consistent_with_published_date() -> None:
    with pytest.raises(ValidationError):
        source_snapshot(corpus_snapshot_date=date(2026, 1, 1))


def test_source_passage_preserves_native_id_and_allows_null_footnotes() -> None:
    passage = SourcePassage(
        source_snapshot_id="snapshot-1",
        passage_id="1.2-c2-s2",
        title="Jury excusal",
        text="Source text remains unchanged.",
        footnotes=None,
        content_sha256="d" * 64,
    )

    assert passage.passage_id == "1.2-c2-s2"
    assert passage.footnotes is None


def test_benchmark_question_preserves_exact_gold_passage_reference() -> None:
    question = BenchmarkQuestion(
        source_snapshot_id="snapshot-1",
        question_id=1,
        question="Question",
        answer="Answer",
        relevant_passage_id="1.2-c2-s2",
    )

    assert question.relevant_passage_id == "1.2-c2-s2"


def test_research_run_uses_evidence_state_not_numeric_confidence() -> None:
    run = ResearchRun(
        source_snapshot_id="snapshot-1",
        question="Question",
        jurisdiction="VIC",
        evidence_state=EvidenceState.UNSUPPORTED,
        created_at=datetime(2026, 9, 4, tzinfo=UTC),
    )

    assert run.evidence_state is EvidenceState.UNSUPPORTED
    assert "confidence" not in ResearchRun.model_fields
