"""Contract tests for the synthetic P2 provenance fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from legal_research.domain import future_document_id, future_document_version_id, future_section_id

FIXTURE_PATH = Path(__file__).parents[2] / "evals" / "golden_documents" / "v1.json"


def _fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_golden_fixture_is_synthetic_and_has_required_shape() -> None:
    fixture = _fixture()
    documents = fixture["documents"]

    assert fixture["fixture_version"] == "golden-documents-v1"
    assert fixture["source_snapshot"]["legal_effective_at"] is None
    assert len(documents) == 10

    sections = [
        section
        for document in documents
        for version in document["versions"]
        for section in version["sections"]
    ]
    assert 30 <= len(sections) <= 50
    assert any(len(section["path"]) == 3 for section in sections)
    assert "Legal RAG Bench" not in FIXTURE_PATH.read_text(encoding="utf-8")


def test_golden_fixture_keeps_duplicate_text_at_distinct_source_locations() -> None:
    fixture = _fixture()
    locations_by_text: dict[str, list[tuple[str, tuple[str, ...]]]] = {}

    for document in fixture["documents"]:
        for version in document["versions"]:
            document_id = future_document_id(
                source_authority=document["source_authority"],
                canonical_citation=document["canonical_citation"],
            )
            version_id = future_document_version_id(
                document_id=document_id,
                source_content_sha256=version["source_content_sha256"],
            )
            for section in version["sections"]:
                path = tuple(section["path"])
                section_id = future_section_id(document_version_id=version_id, section_path=path)
                locations_by_text.setdefault(section["text"], []).append((section_id, path))

    duplicates = [locations for locations in locations_by_text.values() if len(locations) > 1]
    assert duplicates
    for locations in duplicates:
        assert len({section_id for section_id, _ in locations}) == len(locations)


def test_golden_fixture_versions_have_one_document_identity_and_distinct_version_identities() -> (
    None
):
    fixture = _fixture()
    versioned_document = next(
        document for document in fixture["documents"] if len(document["versions"]) == 2
    )
    document_id = future_document_id(
        source_authority=versioned_document["source_authority"],
        canonical_citation=versioned_document["canonical_citation"],
    )
    version_ids = {
        future_document_version_id(
            document_id=document_id,
            source_content_sha256=version["source_content_sha256"],
        )
        for version in versioned_document["versions"]
    }

    assert len(version_ids) == 2
    assert version_ids == {
        future_document_version_id(
            document_id=document_id,
            source_content_sha256=version["source_content_sha256"],
        )
        for version in versioned_document["versions"]
    }
    assert versioned_document["versions"][0]["effective_to"] == "2011-12-31"
    assert versioned_document["versions"][1]["effective_from"] == "2012-01-01"
