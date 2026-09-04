"""Deterministic identities for source facts and a separate future-source path."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from uuid import UUID, uuid5

_IDENTITY_NAMESPACE = UUID("7ec2f6ce-ea8e-4d82-8a31-0b10e983bd99")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class SourcePassageIdentity:
    """A v1 source-native passage ID scoped by its immutable source snapshot."""

    source_snapshot_id: str
    source_passage_id: str

    def __post_init__(self) -> None:
        if not self.source_snapshot_id.strip() or not self.source_passage_id.strip():
            raise ValueError("Source passage identity requires non-blank snapshot and passage IDs.")

    @property
    def key(self) -> str:
        """Return a collision-safe persistence key without altering the source-native ID."""
        return _stable_uuid("source-passage", self.source_snapshot_id, self.source_passage_id)


def future_document_id(*, source_authority: str, canonical_citation: str) -> str:
    """Identify a future source-recognized legal document from authoritative metadata."""
    return _stable_uuid("future-document", source_authority, canonical_citation)


def future_document_version_id(*, document_id: str, source_content_sha256: str) -> str:
    """Identify an immutable future document representation by its source content hash."""
    _require_sha256(source_content_sha256)
    return _stable_uuid("future-document-version", document_id, source_content_sha256)


def future_section_id(*, document_version_id: str, section_path: tuple[str, ...]) -> str:
    """Identify a section within one immutable future document representation."""
    if not section_path or any(not item.strip() for item in section_path):
        raise ValueError("Section identity requires a non-empty, non-blank hierarchy.")
    return _stable_uuid("future-section", document_version_id, *section_path)


def future_derived_passage_id(
    *, section_id: str, start_char: int, end_char: int, content_sha256: str
) -> str:
    """Identify a derived future-source passage without changing its parent section."""
    if start_char < 0 or end_char <= start_char:
        raise ValueError("Derived passage offsets must be non-negative and increasing.")
    _require_sha256(content_sha256)
    return _stable_uuid(
        "future-derived-passage", section_id, str(start_char), str(end_char), content_sha256
    )


def _stable_uuid(kind: str, *components: str) -> str:
    if not kind.strip() or any(not component.strip() for component in components):
        raise ValueError("Stable identity components must be non-blank strings.")
    payload = json.dumps([kind, *components], ensure_ascii=True, separators=(",", ":"))
    return str(uuid5(_IDENTITY_NAMESPACE, payload))


def _require_sha256(value: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError("Content hashes must be lowercase SHA-256 values.")
