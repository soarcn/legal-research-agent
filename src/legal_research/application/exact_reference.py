"""Deterministic resolution of source-section references supported by the v1 corpus."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from legal_research.domain import SourcePassage


class ExactReferenceStatus(StrEnum):
    RESOLVED = "resolved"
    NOT_FOUND = "not_found"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class ExactReferenceResult:
    reference: str
    status: ExactReferenceStatus
    passage_ids: tuple[str, ...]


class ExactReferenceResolver:
    """Resolve only source-native dotted section IDs; statutes and cases remain unsupported in v1."""

    _SECTION = re.compile(r"^(?:section\s+)?(?P<section>\d+(?:\.\d+){0,3})$", re.IGNORECASE)

    def resolve(self, reference: str, passages: tuple[SourcePassage, ...]) -> ExactReferenceResult:
        normalized = reference.strip()
        match = self._SECTION.fullmatch(normalized)
        if match is None:
            return ExactReferenceResult(normalized, ExactReferenceStatus.UNSUPPORTED, ())
        section = match.group("section")
        matched = tuple(
            passage.passage_id
            for passage in passages
            if passage.passage_id == section or passage.passage_id.startswith(f"{section}-")
        )
        return ExactReferenceResult(
            normalized,
            ExactReferenceStatus.RESOLVED if matched else ExactReferenceStatus.NOT_FOUND,
            matched,
        )
