"""Future-source chunking is deterministic, section-local, and offset-safe."""

from __future__ import annotations

import pytest

from legal_research.application.section_chunker import SectionAwareChunker
from legal_research.domain import FutureSourceSection


def _section(*, path: tuple[str, ...], text: str) -> FutureSourceSection:
    return FutureSourceSection(
        source_snapshot_id="synthetic-golden-fixtures-v1",
        document_version_id="document-version-1",
        section_path=path,
        text=text,
    )


def test_chunker_preserves_nested_path_and_round_trips_section_text() -> None:
    section = _section(
        path=("Part 1", "2 Definitions", "2(1) Register"),
        text="One two three four five six.",
    )

    passages = SectionAwareChunker(max_chars=10).chunk((section,))

    assert all(passage.section_path == section.section_path for passage in passages)
    assert all(passage.parent_section_id == passages[0].parent_section_id for passage in passages)
    assert "".join(passage.text for passage in passages) == section.text
    assert [(passage.start_char, passage.end_char) for passage in passages] == [
        (0, 8),
        (8, 14),
        (14, 24),
        (24, len(section.text)),
    ]
    assert all(len(passage.text) <= 10 for passage in passages)
    assert all(
        section.text[passage.start_char : passage.end_char] == passage.text for passage in passages
    )


def test_chunker_never_combines_sections_with_duplicate_text() -> None:
    text = "Repeated source wording."
    left = _section(path=("Part 1", "1 Left"), text=text)
    right = _section(path=("Part 1", "2 Right"), text=text)

    passages = SectionAwareChunker(max_chars=100).chunk((left, right))

    assert len(passages) == 2
    assert passages[0].text == passages[1].text
    assert passages[0].parent_section_id != passages[1].parent_section_id
    assert passages[0].passage_id != passages[1].passage_id


def test_chunker_handles_long_unbroken_text_without_losing_offsets() -> None:
    section = _section(path=("Part 1", "1 Token"), text="abcdefghij")

    passages = SectionAwareChunker(max_chars=4).chunk((section,))

    assert [passage.text for passage in passages] == ["abcd", "efgh", "ij"]
    assert [(passage.start_char, passage.end_char) for passage in passages] == [
        (0, 4),
        (4, 8),
        (8, 10),
    ]


@pytest.mark.parametrize("max_chars", [0, -1])
def test_chunker_rejects_non_positive_size(max_chars: int) -> None:
    with pytest.raises(ValueError, match="at least one"):
        SectionAwareChunker(max_chars=max_chars)
