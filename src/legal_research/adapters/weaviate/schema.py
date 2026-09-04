"""Immutable contract for the rebuildable Legal RAG Bench v1 collection."""

from dataclasses import dataclass

LEGAL_PASSAGE_V1_COLLECTION = "LegalPassageV1"
LEGAL_PASSAGE_V1_INDEX_VERSION = "legal-passage-v1"
LEGAL_PASSAGE_V1_VECTOR_DIMENSION = 1024


@dataclass(frozen=True, slots=True)
class WeaviatePropertySchema:
    """One future Weaviate property and the index features it must expose."""

    name: str
    data_type: str
    filterable: bool = False
    searchable: bool = False


@dataclass(frozen=True, slots=True)
class WeaviateCollectionSchema:
    """A provider-independent schema description that P3.5 will create and validate."""

    collection_name: str
    index_version: str
    vector_dimension: int
    vectorizer: str
    vector_index_type: str
    properties: tuple[WeaviatePropertySchema, ...]

    @property
    def searchable_property_names(self) -> tuple[str, ...]:
        return tuple(property_.name for property_ in self.properties if property_.searchable)

    @property
    def filterable_property_names(self) -> tuple[str, ...]:
        return tuple(property_.name for property_ in self.properties if property_.filterable)


LEGAL_PASSAGE_V1_SCHEMA = WeaviateCollectionSchema(
    collection_name=LEGAL_PASSAGE_V1_COLLECTION,
    index_version=LEGAL_PASSAGE_V1_INDEX_VERSION,
    vector_dimension=LEGAL_PASSAGE_V1_VECTOR_DIMENSION,
    vectorizer="none",
    vector_index_type="flat",
    properties=(
        WeaviatePropertySchema("sourceSnapshotId", "text", filterable=True),
        WeaviatePropertySchema("passageId", "text", filterable=True),
        WeaviatePropertySchema("contentSha256", "text", filterable=True),
        WeaviatePropertySchema("jurisdiction", "text", filterable=True),
        WeaviatePropertySchema("language", "text", filterable=True),
        WeaviatePropertySchema("title", "text", searchable=True),
        WeaviatePropertySchema("text", "text", searchable=True),
        WeaviatePropertySchema("footnotes", "text", searchable=True),
    ),
)


def legal_passage_v1_schema(*, embedding_dimension: int) -> WeaviateCollectionSchema:
    """Reject a changed vector space instead of silently reusing the v1 index name."""
    if embedding_dimension != LEGAL_PASSAGE_V1_VECTOR_DIMENSION:
        raise ValueError(
            "LegalPassageV1 requires the accepted 1024-dimensional BGE-M3 vector contract."
        )
    return LEGAL_PASSAGE_V1_SCHEMA
