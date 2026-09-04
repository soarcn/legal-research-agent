"""Stable identities preserve source-native IDs and separate future derived IDs."""

import pytest

from legal_research.domain import (
    SourcePassageIdentity,
    future_derived_passage_id,
    future_document_id,
    future_document_version_id,
    future_section_id,
)

HASH_A = "a" * 64
HASH_B = "b" * 64


def test_source_passage_identity_keeps_native_id_but_scopes_its_key() -> None:
    first = SourcePassageIdentity("snapshot-a", "1.2-c2-s2")
    second = SourcePassageIdentity("snapshot-b", "1.2-c2-s2")

    assert first.source_passage_id == "1.2-c2-s2"
    assert first.key != second.key


def test_future_document_identity_is_repeatable_and_uses_authority() -> None:
    first = future_document_id(source_authority="VIC", canonical_citation="Crimes Act 1958")
    second = future_document_id(source_authority="VIC", canonical_citation="Crimes Act 1958")
    changed_authority = future_document_id(
        source_authority="Commonwealth", canonical_citation="Crimes Act 1958"
    )

    assert first == second
    assert first != changed_authority


def test_future_version_identity_changes_only_when_source_content_changes() -> None:
    document_id = future_document_id(source_authority="VIC", canonical_citation="Example Act")

    assert future_document_version_id(
        document_id=document_id, source_content_sha256=HASH_A
    ) != future_document_version_id(document_id=document_id, source_content_sha256=HASH_B)


def test_nested_sections_and_duplicate_text_have_distinct_derived_identities() -> None:
    version_id = future_document_version_id(document_id="document", source_content_sha256=HASH_A)
    parent = future_section_id(document_version_id=version_id, section_path=("Part 1", "Section 1"))
    sibling = future_section_id(
        document_version_id=version_id, section_path=("Part 1", "Section 2")
    )

    assert parent != sibling
    assert future_derived_passage_id(
        section_id=parent, start_char=0, end_char=12, content_sha256=HASH_A
    ) != future_derived_passage_id(
        section_id=sibling, start_char=0, end_char=12, content_sha256=HASH_A
    )


@pytest.mark.parametrize(
    "factory",
    [
        lambda: SourcePassageIdentity("", "passage"),
        lambda: future_document_version_id(document_id="document", source_content_sha256="invalid"),
        lambda: future_section_id(document_version_id="version", section_path=()),
        lambda: future_derived_passage_id(
            section_id="section", start_char=3, end_char=3, content_sha256=HASH_A
        ),
    ],
)
def test_invalid_identity_inputs_are_rejected(factory: object) -> None:
    with pytest.raises(ValueError):
        factory()  # type: ignore[operator]
