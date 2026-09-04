"""Pinned Legal RAG Bench acquisition and integrity verification."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Protocol
from urllib.request import urlopen


class DatasetSnapshotError(Exception):
    """A safe dataset acquisition or verification failure."""


class DatasetDownloadError(DatasetSnapshotError):
    """The pinned source could not be downloaded."""


class DatasetIntegrityError(DatasetSnapshotError):
    """Downloaded files differ from the committed snapshot contract."""


class DatasetLicenceError(DatasetSnapshotError):
    """The source card does not advertise the required restrictive policy."""


class DatasetDownloader(Protocol):
    """Read-only byte downloader that can be replaced in deterministic tests."""

    def download(self, url: str) -> bytes:
        """Return the complete response body or raise a safe download error."""

        ...


class UrllibDatasetDownloader:
    """Small stdlib downloader for the public, immutable dataset files."""

    def download(self, url: str) -> bytes:
        try:
            with urlopen(url, timeout=60) as response:
                body = response.read()
                if isinstance(body, bytes):
                    return body
                raise DatasetDownloadError(
                    "The pinned dataset source returned an invalid response."
                )
        except OSError as error:
            raise DatasetDownloadError(
                "The pinned dataset source could not be downloaded."
            ) from error


@dataclass(frozen=True, slots=True)
class SnapshotFile:
    """One committed raw-file integrity contract."""

    path: str
    count: int
    sha256: str


@dataclass(frozen=True, slots=True)
class DatasetSnapshotManifest:
    """The committed, source-independent contract for one frozen snapshot."""

    dataset: str
    revision: str
    source_snapshot_id: str
    licence_policy: str
    corpus: SnapshotFile
    qa: SnapshotFile

    @classmethod
    def load(cls, path: Path) -> DatasetSnapshotManifest:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            corpus = payload["corpus"]
            qa = payload["qa"]
            return cls(
                dataset=_non_empty_string(payload["dataset"], "dataset"),
                revision=_commit_sha(payload["dataset_revision"]),
                source_snapshot_id=_non_empty_string(
                    payload["source_snapshot_id"], "source_snapshot_id"
                ),
                licence_policy=_non_empty_string(payload["licence_policy"], "licence_policy"),
                corpus=_snapshot_file(corpus, "corpus"),
                qa=_snapshot_file(qa, "qa"),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise DatasetIntegrityError("The committed dataset manifest is invalid.") from error


@dataclass(frozen=True, slots=True)
class DatasetVerification:
    """Non-sensitive outcome suitable for CLI output and audit records."""

    corpus_count: int
    qa_count: int
    source_snapshot_id: str
    licence_policy: str


class LegalRagBenchSnapshotFetcher:
    """Fetch and validate only the immutable v1 source files before replacement."""

    _base_url = "https://huggingface.co/datasets/{dataset}/resolve/{revision}/{filename}"
    _required_licence = "cc-by-nc-sa-4.0"

    def __init__(
        self,
        manifest: DatasetSnapshotManifest,
        downloader: DatasetDownloader | None = None,
    ) -> None:
        self._manifest = manifest
        self._downloader = downloader or UrllibDatasetDownloader()

    def fetch(self, raw_root: Path) -> DatasetVerification:
        """Download, validate, then atomically replace the two ignored raw files."""
        corpus_bytes = self._download("corpus.jsonl")
        qa_bytes = self._download("qa.jsonl")
        card_bytes = self._download("README.md")

        _validate_licence(card_bytes, self._required_licence)
        corpus_ids = _validate_corpus(corpus_bytes, self._manifest.corpus)
        _validate_qa(qa_bytes, self._manifest.qa, corpus_ids)

        _atomic_write(raw_root / Path(self._manifest.corpus.path).name, corpus_bytes)
        _atomic_write(raw_root / Path(self._manifest.qa.path).name, qa_bytes)
        return DatasetVerification(
            corpus_count=self._manifest.corpus.count,
            qa_count=self._manifest.qa.count,
            source_snapshot_id=self._manifest.source_snapshot_id,
            licence_policy=self._manifest.licence_policy,
        )

    def verify_existing(self, raw_root: Path) -> DatasetVerification:
        """Verify an existing raw snapshot without any network access."""
        try:
            corpus_bytes = (raw_root / Path(self._manifest.corpus.path).name).read_bytes()
            qa_bytes = (raw_root / Path(self._manifest.qa.path).name).read_bytes()
        except OSError as error:
            raise DatasetIntegrityError("The local raw dataset snapshot is unavailable.") from error
        corpus_ids = _validate_corpus(corpus_bytes, self._manifest.corpus)
        _validate_qa(qa_bytes, self._manifest.qa, corpus_ids)
        return DatasetVerification(
            corpus_count=self._manifest.corpus.count,
            qa_count=self._manifest.qa.count,
            source_snapshot_id=self._manifest.source_snapshot_id,
            licence_policy=self._manifest.licence_policy,
        )

    def _download(self, filename: str) -> bytes:
        url = self._base_url.format(
            dataset=self._manifest.dataset,
            revision=self._manifest.revision,
            filename=filename,
        )
        return self._downloader.download(url)


def _validate_licence(card: bytes, required_licence: str) -> None:
    try:
        text = card.decode("utf-8")
    except UnicodeDecodeError as error:
        raise DatasetLicenceError("The dataset card could not be read as UTF-8.") from error
    metadata = re.search(r"^license:\s*([^\s]+)\s*$", text, flags=re.MULTILINE)
    if metadata is None or metadata.group(1).casefold() != required_licence:
        raise DatasetLicenceError("The source card does not advertise the required licence policy.")


def _validate_corpus(content: bytes, expected: SnapshotFile) -> set[str]:
    _validate_hash(content, expected)
    records = _jsonl_records(content, expected)
    identifiers: set[str] = set()
    try:
        for record in records:
            identifier = _non_empty_string(record.get("id"), "corpus id")
            _non_empty_string(record.get("title"), "corpus title")
            _non_empty_string(record.get("text"), "corpus text")
            _optional_string(record.get("footnotes"), "corpus footnotes")
            if identifier in identifiers:
                raise DatasetIntegrityError("The corpus contains duplicate source-passage IDs.")
            identifiers.add(identifier)
    except ValueError as error:
        raise DatasetIntegrityError(
            "The corpus contains an invalid source-passage record."
        ) from error
    return identifiers


def _validate_qa(content: bytes, expected: SnapshotFile, corpus_ids: set[str]) -> None:
    _validate_hash(content, expected)
    records = _jsonl_records(content, expected)
    identifiers: set[int] = set()
    try:
        for record in records:
            identifier = record.get("id")
            if not isinstance(identifier, int) or isinstance(identifier, bool):
                raise DatasetIntegrityError("The QA file contains a non-integer question ID.")
            _non_empty_string(record.get("question"), "question")
            _non_empty_string(record.get("answer"), "answer")
            passage_id = _non_empty_string(record.get("relevant_passage_id"), "relevant_passage_id")
            if identifier in identifiers:
                raise DatasetIntegrityError("The QA file contains duplicate question IDs.")
            if passage_id not in corpus_ids:
                raise DatasetIntegrityError("A QA gold reference does not exist in the corpus.")
            identifiers.add(identifier)
    except ValueError as error:
        raise DatasetIntegrityError("The QA file contains an invalid benchmark record.") from error


def _validate_hash(content: bytes, expected: SnapshotFile) -> None:
    if hashlib.sha256(content).hexdigest() != expected.sha256:
        raise DatasetIntegrityError("A downloaded dataset file does not match its pinned SHA-256.")


def _jsonl_records(content: bytes, expected: SnapshotFile) -> list[dict[str, object]]:
    try:
        lines = content.decode("utf-8").splitlines()
        records = [json.loads(line) for line in lines]
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DatasetIntegrityError("A dataset file is not valid UTF-8 JSONL.") from error
    if len(records) != expected.count or any(not isinstance(record, dict) for record in records):
        raise DatasetIntegrityError(
            "A dataset file does not have the expected record count or shape."
        )
    return records


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
        temporary.write(content)
        temporary_path = Path(temporary.name)
    try:
        temporary_path.replace(path)
    except OSError as error:
        temporary_path.unlink(missing_ok=True)
        raise DatasetIntegrityError(
            "The verified dataset file could not be stored locally."
        ) from error


def _snapshot_file(value: object, name: str) -> SnapshotFile:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    count = value.get("count")
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        raise ValueError(f"{name} count must be positive")
    return SnapshotFile(
        path=_non_empty_string(value.get("path"), f"{name} path"),
        count=count,
        sha256=_sha256(value.get("sha256"), f"{name} SHA-256"),
    )


def _non_empty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _optional_string(value: object, name: str) -> str | None:
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{name} must be a string or null")
    return value


def _commit_sha(value: object) -> str:
    return _sha256(value, "dataset revision")


def _sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value):
        raise ValueError(f"{name} must be a lowercase SHA")
    return value
