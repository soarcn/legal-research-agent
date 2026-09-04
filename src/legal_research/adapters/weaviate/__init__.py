"""Weaviate adapter — runtime capability checks and later search components."""

from legal_research.adapters.weaviate.readiness import WeaviateReadinessProbe
from legal_research.adapters.weaviate.schema import LEGAL_PASSAGE_V1_SCHEMA, legal_passage_v1_schema

__all__ = ["LEGAL_PASSAGE_V1_SCHEMA", "WeaviateReadinessProbe", "legal_passage_v1_schema"]
