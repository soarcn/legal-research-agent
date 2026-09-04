"""The v1 Weaviate schema is explicit, source-bounded, and versioned."""

import pytest

from legal_research.adapters.weaviate.schema import (
    LEGAL_PASSAGE_V1_COLLECTION,
    LEGAL_PASSAGE_V1_INDEX_VERSION,
    legal_passage_v1_schema,
)


def test_v1_schema_uses_flat_external_vectors_and_bm25_text_fields() -> None:
    schema = legal_passage_v1_schema(embedding_dimension=1024)

    assert schema.collection_name == LEGAL_PASSAGE_V1_COLLECTION
    assert schema.index_version == LEGAL_PASSAGE_V1_INDEX_VERSION
    assert schema.vectorizer == "none"
    assert schema.vector_index_type == "flat"
    assert schema.searchable_property_names == ("title", "text", "footnotes")


def test_v1_schema_filters_only_supported_source_metadata() -> None:
    schema = legal_passage_v1_schema(embedding_dimension=1024)

    assert schema.filterable_property_names == (
        "sourceSnapshotId",
        "passageId",
        "contentSha256",
        "jurisdiction",
        "language",
    )
    all_names = {property_.name for property_ in schema.properties}
    assert "effectiveAt" not in all_names
    assert "documentVersionId" not in all_names


def test_v1_schema_rejects_an_embedding_dimension_change() -> None:
    with pytest.raises(ValueError, match="1024-dimensional"):
        legal_passage_v1_schema(embedding_dimension=768)
