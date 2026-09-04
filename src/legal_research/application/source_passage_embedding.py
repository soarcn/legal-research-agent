"""Batch unchanged source passages through the configured dense embedding port."""

from __future__ import annotations

from dataclasses import dataclass

from legal_research.config import EmbeddingModelConfig
from legal_research.domain import SourcePassage
from legal_research.ports.embedding import EmbeddingProvider, EmbeddingRequest


@dataclass(frozen=True, slots=True)
class EmbeddingProvenance:
    """Configuration that makes an embedding result reproducible."""

    model_id: str
    revision: str
    dimension: int
    device: str
    batch_size: int
    normalized: bool


@dataclass(frozen=True, slots=True)
class EmbeddedSourcePassage:
    """One unchanged source passage paired with a derived dense vector."""

    source_snapshot_id: str
    passage_id: str
    content_sha256: str
    vector: tuple[float, ...]
    provenance: EmbeddingProvenance


class SourcePassageEmbedder:
    """Preserve source ordering while batching text-only v1 passage embeddings."""

    def __init__(self, provider: EmbeddingProvider, config: EmbeddingModelConfig) -> None:
        self._provider = provider
        self._config = config

    async def embed(self, passages: tuple[SourcePassage, ...]) -> tuple[EmbeddedSourcePassage, ...]:
        """Embed text exactly as supplied by the v1 source; no database or index write."""
        embedded: list[EmbeddedSourcePassage] = []
        for start in range(0, len(passages), self._config.batch_size):
            batch = passages[start : start + self._config.batch_size]
            if not batch:
                continue
            response = await self._provider.embed(
                EmbeddingRequest(tuple(item.text for item in batch))
            )
            if (
                response.model_id != self._config.model_id
                or response.revision != self._config.revision
                or response.dimension != self._config.expected_dimension
                or len(response.vectors) != len(batch)
            ):
                raise ValueError(
                    "The embedding provider response does not match the configured contract."
                )
            provenance = EmbeddingProvenance(
                model_id=response.model_id,
                revision=response.revision,
                dimension=response.dimension,
                device=self._config.device,
                batch_size=self._config.batch_size,
                normalized=self._config.normalize,
            )
            embedded.extend(
                EmbeddedSourcePassage(
                    source_snapshot_id=passage.source_snapshot_id,
                    passage_id=passage.passage_id,
                    content_sha256=passage.content_sha256,
                    vector=vector,
                    provenance=provenance,
                )
                for passage, vector in zip(batch, response.vectors, strict=True)
            )
        return tuple(embedded)
