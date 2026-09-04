"""A deterministic, section-preserving chunker for future legal sources."""

from __future__ import annotations

import hashlib

from legal_research.domain import (
    DerivedPassage,
    FutureSourceSection,
    future_derived_passage_id,
    future_section_id,
)


class SectionAwareChunker:
    """Split one section at a time; v1 Legal RAG Bench passages never enter here."""

    def __init__(self, *, max_chars: int) -> None:
        if max_chars < 1:
            raise ValueError("max_chars must be at least one")
        self._max_chars = max_chars

    def chunk(self, sections: tuple[FutureSourceSection, ...]) -> tuple[DerivedPassage, ...]:
        """Create non-overlapping passages with offsets into their own source section."""
        passages: list[DerivedPassage] = []
        for section in sections:
            section_id = future_section_id(
                document_version_id=section.document_version_id,
                section_path=section.section_path,
            )
            passages.extend(self._chunk_section(section, section_id))
        return tuple(passages)

    def _chunk_section(
        self, section: FutureSourceSection, section_id: str
    ) -> tuple[DerivedPassage, ...]:
        passages: list[DerivedPassage] = []
        start = 0
        while start < len(section.text):
            end = _chunk_end(section.text, start, self._max_chars)
            text = section.text[start:end]
            content_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
            passages.append(
                DerivedPassage(
                    source_snapshot_id=section.source_snapshot_id,
                    passage_id=future_derived_passage_id(
                        section_id=section_id,
                        start_char=start,
                        end_char=end,
                        content_sha256=content_sha256,
                    ),
                    parent_section_id=section_id,
                    section_path=section.section_path,
                    text=text,
                    start_char=start,
                    end_char=end,
                    content_sha256=content_sha256,
                )
            )
            start = end
        return tuple(passages)


def _chunk_end(text: str, start: int, max_chars: int) -> int:
    """Prefer a whitespace boundary but retain every character and always progress."""
    hard_end = min(start + max_chars, len(text))
    if hard_end == len(text) or text[hard_end - 1].isspace():
        return hard_end
    boundary = text.rfind(" ", start + 1, hard_end)
    return boundary + 1 if boundary >= start + 1 else hard_end
