"""The P3.1 source loader keeps verified v1 source facts unchanged."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest

from legal_research.application.dataset_snapshot import DatasetSnapshotManifest, SnapshotFile
from legal_research.application.legal_rag_bench_loader import (
    LegalRagBenchLoadError,
    LegalRagBenchSourceLoader,
)
from legal_research.domain import SourceSnapshot

CORPUS = b'{"id":"passage-1","title":"Title","text":"Text","footnotes":null}\n'
QA = b'{"id":1,"question":"Question","answer":"Answer","relevant_passage_id":"passage-1"}\n'


def _manifest() -> DatasetSnapshotManifest:
    return DatasetSnapshotManifest(
        dataset="owner/dataset",
        revision="a" * 40,
        source_snapshot_id="dataset@" + "a" * 40,
        licence_policy="Strict project policy",
        corpus=SnapshotFile("data/raw/corpus.jsonl", 1, hashlib.sha256(CORPUS).hexdigest()),
        qa=SnapshotFile("data/raw/qa.jsonl", 1, hashlib.sha256(QA).hexdigest()),
    )


def _snapshot() -> SourceSnapshot:
    manifest = _manifest()
    return SourceSnapshot(
        source_snapshot_id=manifest.source_snapshot_id,
        dataset=manifest.dataset,
        dataset_revision=manifest.revision,
        source_url="https://example.test/dataset",
        retrieved_at=datetime(2026, 9, 4, tzinfo=UTC),
        corpus_sha256=manifest.corpus.sha256,
        corpus_count=manifest.corpus.count,
        qa_sha256=manifest.qa.sha256,
        qa_count=manifest.qa.count,
        licence_policy=manifest.licence_policy,
        jurisdiction="VIC",
        language="en-AU",
        corpus_snapshot_date=None,
        corpus_snapshot_date_status="not_published_by_dataset",
    )


def _write_verified_snapshot(raw_root: Path) -> None:
    raw_root.mkdir(exist_ok=True)
    (raw_root / "corpus.jsonl").write_bytes(CORPUS)
    (raw_root / "qa.jsonl").write_bytes(QA)


def test_loader_returns_unchanged_source_native_facts(tmp_path: Path) -> None:
    _write_verified_snapshot(tmp_path)

    loaded = LegalRagBenchSourceLoader(_manifest(), _snapshot()).load(tmp_path)

    assert loaded.snapshot == _snapshot()
    assert loaded.passages[0].passage_id == "passage-1"
    assert loaded.passages[0].title == "Title"
    assert loaded.passages[0].text == "Text"
    assert loaded.passages[0].footnotes is None
    assert loaded.questions[0].question_id == 1
    assert loaded.questions[0].relevant_passage_id == "passage-1"


def test_loader_is_repeatable_and_hashes_full_source_record(tmp_path: Path) -> None:
    _write_verified_snapshot(tmp_path)
    loader = LegalRagBenchSourceLoader(_manifest(), _snapshot())

    first = loader.load(tmp_path)
    second = loader.load(tmp_path)

    assert first == second
    assert (
        first.passages[0].content_sha256
        == hashlib.sha256(
            b'{"footnotes":null,"id":"passage-1","text":"Text","title":"Title"}'
        ).hexdigest()
    )


def test_loader_rejects_missing_or_unverified_local_data(tmp_path: Path) -> None:
    with pytest.raises(LegalRagBenchLoadError):
        LegalRagBenchSourceLoader(_manifest(), _snapshot()).load(tmp_path)


def test_loader_rejects_mismatched_snapshot_identity() -> None:
    mismatched = _snapshot().model_copy(update={"source_snapshot_id": "another-source"})

    with pytest.raises(ValueError, match="same source"):
        LegalRagBenchSourceLoader(_manifest(), mismatched)
