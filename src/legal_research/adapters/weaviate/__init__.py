"""Weaviate adapter — runtime capability checks and later search components."""

from legal_research.adapters.weaviate.readiness import WeaviateReadinessProbe

__all__ = ["WeaviateReadinessProbe"]
