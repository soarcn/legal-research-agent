"""Pinned snapshot acquisition is deterministic and safe without network access."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pytest

from legal_research.application.dataset_snapshot import (
    DatasetDownloadError,
    DatasetIntegrityError,
    DatasetLicenceError,
    DatasetSnapshotManifest,
    LegalRagBenchSnapshotFetcher,
    SnapshotFile,
)

CORPUS = b'{"id":"passage-1","title":"Title","text":"Text","footnotes":"Notes"}\n'
QA = b'{"id":1,"question":"Question","answer":"Answer","relevant_passage_id":"passage-1"}\n'
CARD = b"---\nlicense: cc-by-nc-sa-4.0\n---\n# Dataset\n"


@dataclass
class FakeDownloader:
    responses: dict[str, bytes]
    failure: Exception | None = None

    def download(self, url: str) -> bytes:
        if self.failure is not None:
            raise self.failure
        return self.responses[url.rsplit("/", maxsplit=1)[-1]]


def manifest() -> DatasetSnapshotManifest:
    return DatasetSnapshotManifest(
        dataset="owner/dataset",
        revision="a" * 40,
        source_snapshot_id="dataset@" + "a" * 40,
        licence_policy="Treat as CC BY-NC-SA 4.0 pending publisher clarification",
        corpus=SnapshotFile("data/raw/corpus.jsonl", 1, hashlib.sha256(CORPUS).hexdigest()),
        qa=SnapshotFile("data/raw/qa.jsonl", 1, hashlib.sha256(QA).hexdigest()),
    )


def fetcher(
    *, card: bytes = CARD, failure: Exception | None = None
) -> LegalRagBenchSnapshotFetcher:
    return LegalRagBenchSnapshotFetcher(
        manifest(),
        FakeDownloader({"corpus.jsonl": CORPUS, "qa.jsonl": QA, "README.md": card}, failure),
    )


def test_fetch_validates_then_writes_ignored_snapshot_files(tmp_path: Path) -> None:
    result = fetcher().fetch(tmp_path)

    assert result.corpus_count == 1
    assert result.qa_count == 1
    assert (tmp_path / "corpus.jsonl").read_bytes() == CORPUS
    assert (tmp_path / "qa.jsonl").read_bytes() == QA


def test_fetch_does_not_replace_existing_files_when_integrity_fails(tmp_path: Path) -> None:
    existing = tmp_path / "corpus.jsonl"
    existing.write_bytes(b"known-good-local-snapshot")
    invalid_corpus = CORPUS.replace(b"Text", b"Changed")
    invalid_fetcher = LegalRagBenchSnapshotFetcher(
        manifest(),
        FakeDownloader({"corpus.jsonl": invalid_corpus, "qa.jsonl": QA, "README.md": CARD}),
    )

    with pytest.raises(DatasetIntegrityError):
        invalid_fetcher.fetch(tmp_path)

    assert existing.read_bytes() == b"known-good-local-snapshot"


def test_fetch_rejects_missing_restrictive_licence(tmp_path: Path) -> None:
    with pytest.raises(DatasetLicenceError):
        fetcher(card=b"---\nlicense: cc-by-nc-4.0\n---\n").fetch(tmp_path)


def test_fetch_propagates_safe_download_failure(tmp_path: Path) -> None:
    with pytest.raises(DatasetDownloadError):
        fetcher(
            failure=DatasetDownloadError("The pinned dataset source could not be downloaded.")
        ).fetch(tmp_path)


def test_verify_existing_checks_hash_and_cross_references_without_network(tmp_path: Path) -> None:
    (tmp_path / "corpus.jsonl").write_bytes(CORPUS)
    (tmp_path / "qa.jsonl").write_bytes(QA)

    result = fetcher().verify_existing(tmp_path)

    assert result.source_snapshot_id == "dataset@" + "a" * 40


def test_verify_allows_empty_source_footnotes_when_the_hash_contract_matches(
    tmp_path: Path,
) -> None:
    corpus = CORPUS.replace(b"Notes", b"")
    adjusted_manifest = DatasetSnapshotManifest(
        dataset="owner/dataset",
        revision="a" * 40,
        source_snapshot_id="dataset@" + "a" * 40,
        licence_policy="Treat as CC BY-NC-SA 4.0 pending publisher clarification",
        corpus=SnapshotFile("data/raw/corpus.jsonl", 1, hashlib.sha256(corpus).hexdigest()),
        qa=SnapshotFile("data/raw/qa.jsonl", 1, hashlib.sha256(QA).hexdigest()),
    )
    (tmp_path / "corpus.jsonl").write_bytes(corpus)
    (tmp_path / "qa.jsonl").write_bytes(QA)

    LegalRagBenchSnapshotFetcher(adjusted_manifest).verify_existing(tmp_path)


def test_verify_allows_null_source_footnotes_when_the_hash_contract_matches(
    tmp_path: Path,
) -> None:
    corpus = CORPUS.replace(b'"Notes"', b"null")
    adjusted_manifest = DatasetSnapshotManifest(
        dataset="owner/dataset",
        revision="a" * 40,
        source_snapshot_id="dataset@" + "a" * 40,
        licence_policy="Treat as CC BY-NC-SA 4.0 pending publisher clarification",
        corpus=SnapshotFile("data/raw/corpus.jsonl", 1, hashlib.sha256(corpus).hexdigest()),
        qa=SnapshotFile("data/raw/qa.jsonl", 1, hashlib.sha256(QA).hexdigest()),
    )
    (tmp_path / "corpus.jsonl").write_bytes(corpus)
    (tmp_path / "qa.jsonl").write_bytes(QA)

    LegalRagBenchSnapshotFetcher(adjusted_manifest).verify_existing(tmp_path)


def test_manifest_rejects_invalid_committed_metadata(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text("{}", encoding="utf-8")

    with pytest.raises(DatasetIntegrityError):
        DatasetSnapshotManifest.load(path)
