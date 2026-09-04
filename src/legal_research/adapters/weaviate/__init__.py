"""Weaviate adapter — runtime capability checks and later search components."""

from legal_research.adapters.weaviate.readiness import WeaviateReadinessProbe
from legal_research.adapters.weaviate.schema import LEGAL_PASSAGE_V1_SCHEMA, legal_passage_v1_schema
from legal_research.adapters.weaviate.source_index import WeaviateSourcePassageIndex

__all__ = [
    "LEGAL_PASSAGE_V1_SCHEMA",
    "WeaviateReadinessProbe",
    "WeaviateSourcePassageIndex",
    "legal_passage_v1_schema",
]
