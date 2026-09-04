"""Pure loading of an already verified Legal RAG Bench v1 snapshot."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

from legal_research.application.dataset_snapshot import (
    DatasetIntegrityError,
    DatasetSnapshotManifest,
    LegalRagBenchSnapshotFetcher,
)
from legal_research.domain import BenchmarkQuestion, SourcePassage, SourceSnapshot


class LegalRagBenchLoadError(Exception):
    """The verified local snapshot could not be represented as source facts."""


@dataclass(frozen=True, slots=True)
class LoadedLegalRagBench:
    """Immutable source facts for later ingestion; no index representation."""

    snapshot: SourceSnapshot
    passages: tuple[SourcePassage, ...]
    questions: tuple[BenchmarkQuestion, ...]


class LegalRagBenchSourceLoader:
    """Map the P2-pinned local source files to unchanged domain objects."""

    def __init__(self, manifest: DatasetSnapshotManifest, snapshot: SourceSnapshot) -> None:
        if manifest.source_snapshot_id != snapshot.source_snapshot_id:
            raise ValueError(
                "The dataset manifest and source snapshot must identify the same source."
            )
        self._manifest = manifest
        self._snapshot = snapshot

    @classmethod
    def from_manifest(cls, path: Path) -> LegalRagBenchSourceLoader:
        """Create a loader from the committed P2 dataset manifest only."""
        manifest = DatasetSnapshotManifest.load(path)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            snapshot = SourceSnapshot(
                source_snapshot_id=manifest.source_snapshot_id,
                dataset=manifest.dataset,
                dataset_revision=manifest.revision,
                source_url=payload["source"],
                retrieved_at=datetime.fromisoformat(payload["retrieved_at"].replace("Z", "+00:00")),
                corpus_sha256=manifest.corpus.sha256,
                corpus_count=manifest.corpus.count,
                qa_sha256=manifest.qa.sha256,
                qa_count=manifest.qa.count,
                licence_policy=manifest.licence_policy,
                jurisdiction=payload["jurisdiction"],
                language=payload["language"],
                corpus_snapshot_date=payload["corpus_snapshot_date"],
                corpus_snapshot_date_status=payload["corpus_snapshot_date_status"],
            )
        except (KeyError, TypeError, ValueError, ValidationError, json.JSONDecodeError) as error:
            raise LegalRagBenchLoadError("The committed source metadata is invalid.") from error
        return cls(manifest, snapshot)

    def load(self, raw_root: Path) -> LoadedLegalRagBench:
        """Verify local bytes, then return immutable source objects without side effects."""
        try:
            LegalRagBenchSnapshotFetcher(self._manifest).verify_existing(raw_root)
            corpus = _read_jsonl(raw_root / Path(self._manifest.corpus.path).name)
            qa = _read_jsonl(raw_root / Path(self._manifest.qa.path).name)
            passages = tuple(
                SourcePassage(
                    source_snapshot_id=self._snapshot.source_snapshot_id,
                    passage_id=_required_string(record.get("id"), "corpus id"),
                    title=_required_string(record.get("title"), "corpus title"),
                    text=_required_string(record.get("text"), "corpus text"),
                    footnotes=_optional_string(record.get("footnotes"), "corpus footnotes"),
                    content_sha256=_source_record_sha256(record),
                )
                for record in corpus
            )
            questions = tuple(
                BenchmarkQuestion(
                    source_snapshot_id=self._snapshot.source_snapshot_id,
                    question_id=_question_id(record.get("id")),
                    question=_required_string(record.get("question"), "question"),
                    answer=_required_string(record.get("answer"), "answer"),
                    relevant_passage_id=_required_string(
                        record.get("relevant_passage_id"), "relevant_passage_id"
                    ),
                )
                for record in qa
            )
        except (
            DatasetIntegrityError,
            KeyError,
            TypeError,
            ValueError,
            ValidationError,
            UnicodeDecodeError,
        ) as error:
            raise LegalRagBenchLoadError(
                "The local Legal RAG Bench snapshot could not be loaded safely."
            ) from error

        return LoadedLegalRagBench(
            snapshot=self._snapshot,
            passages=passages,
            questions=questions,
        )


def _read_jsonl(path: Path) -> tuple[dict[str, object], ...]:
    try:
        records = tuple(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())
    except (OSError, json.JSONDecodeError) as error:
        raise LegalRagBenchLoadError("The verified local source file could not be read.") from error
    if any(not isinstance(record, dict) for record in records):
        raise LegalRagBenchLoadError("The verified local source file has an invalid record.")
    return records


def _source_record_sha256(record: dict[str, object]) -> str:
    """Hash all source-visible fields while ignoring JSONL formatting differences."""
    canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _required_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _optional_string(value: object, name: str) -> str | None:
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{name} must be a string or null")
    return value


def _question_id(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError("question ID must be a positive integer")
    return value
