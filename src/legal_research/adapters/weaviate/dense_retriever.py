"""BGE-M3 backed, snapshot-scoped vector retrieval for v1 source passages."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from datetime import date
from time import perf_counter
from typing import Protocol

from weaviate.classes.query import Filter, MetadataQuery
from weaviate.client import WeaviateAsyncClient

from legal_research.adapters.weaviate.readiness import connection_params_from_url
from legal_research.adapters.weaviate.schema import LEGAL_PASSAGE_V1_SCHEMA
from legal_research.config import EmbeddingModelConfig
from legal_research.domain import SourceSnapshot
from legal_research.ports.embedding import EmbeddingProvider, EmbeddingRequest


class WeaviateDenseClient(Protocol):
    @property
    def collections(self) -> object: ...

    async def connect(self) -> None: ...

    async def close(self) -> None: ...


WeaviateDenseClientFactory = Callable[[], WeaviateDenseClient]


@dataclass(frozen=True, slots=True)
class DenseRetrievalConfiguration:
    embedding_model_id: str
    embedding_revision: str
    embedding_dimension: int
    embedding_normalized: bool
    top_k: int = 10
    mode: str = "dense"

    @classmethod
    def from_embedding_config(
        cls, config: EmbeddingModelConfig, *, top_k: int = 10
    ) -> DenseRetrievalConfiguration:
        return cls(
            embedding_model_id=config.model_id,
            embedding_revision=config.revision,
            embedding_dimension=config.expected_dimension,
            embedding_normalized=config.normalize,
            top_k=top_k,
        )

    def __post_init__(self) -> None:
        if self.top_k <= 0 or self.embedding_dimension <= 0 or not self.embedding_normalized:
            raise ValueError(
                "dense retrieval requires a positive top_k and normalized embedding contract"
            )


@dataclass(frozen=True, slots=True)
class DenseRetrievedSourcePassage:
    passage_id: str
    distance: float


@dataclass(frozen=True, slots=True)
class DenseRetrievalResult:
    source_snapshot_id: str
    jurisdiction: str
    configuration: DenseRetrievalConfiguration
    passages: tuple[DenseRetrievedSourcePassage, ...]
    latency_ms: float


class WeaviateDenseSourcePassageRetriever:
    """Embed a query under the indexed BGE-M3 contract, then filter before vector ranking."""

    def __init__(
        self,
        client_factory: WeaviateDenseClientFactory,
        embedding_provider: EmbeddingProvider,
        embedding_config: EmbeddingModelConfig,
    ) -> None:
        self._client_factory = client_factory
        self._embedding_provider = embedding_provider
        self._embedding_config = embedding_config

    @classmethod
    def from_url(
        cls,
        weaviate_url: str,
        *,
        grpc_port: int,
        embedding_provider: EmbeddingProvider,
        embedding_config: EmbeddingModelConfig,
    ) -> WeaviateDenseSourcePassageRetriever:
        connection_params = connection_params_from_url(weaviate_url, grpc_port=grpc_port)
        return cls(
            client_factory=lambda: WeaviateAsyncClient(connection_params=connection_params),
            embedding_provider=embedding_provider,
            embedding_config=embedding_config,
        )

    async def retrieve(
        self,
        *,
        query: str,
        snapshot: SourceSnapshot,
        jurisdiction: str,
        configuration: DenseRetrievalConfiguration | None = None,
        effective_at: date | None = None,
    ) -> DenseRetrievalResult:
        if not query.strip():
            raise ValueError("query must not be empty")
        if effective_at is not None:
            raise ValueError("v1 does not support legal effective-date filtering")
        if jurisdiction != snapshot.jurisdiction:
            raise ValueError("jurisdiction must match the requested source snapshot")
        resolved = configuration or DenseRetrievalConfiguration.from_embedding_config(
            self._embedding_config
        )
        if resolved != DenseRetrievalConfiguration.from_embedding_config(
            self._embedding_config, top_k=resolved.top_k
        ):
            raise ValueError(
                "retrieval configuration must match the accepted indexed embedding contract"
            )
        started = perf_counter()
        embedding = await self._embedding_provider.embed(EmbeddingRequest(texts=(query,)))
        if (
            embedding.model_id != self._embedding_config.model_id
            or embedding.revision != self._embedding_config.revision
            or embedding.dimension != self._embedding_config.expected_dimension
            or len(embedding.vectors) != 1
        ):
            raise ValueError("query embedding does not match the accepted indexed corpus contract")
        client = self._client_factory()
        try:
            await client.connect()
            collection = client.collections.get(LEGAL_PASSAGE_V1_SCHEMA.collection_name)  # type: ignore[attr-defined]
            response = await collection.query.near_vector(  # type: ignore[attr-defined]
                near_vector=list(embedding.vectors[0]),
                filters=Filter.all_of(
                    [
                        Filter.by_property("sourceSnapshotId").equal(snapshot.source_snapshot_id),
                        Filter.by_property("jurisdiction").equal(jurisdiction),
                    ]
                ),
                limit=resolved.top_k,
                return_properties=["passageId"],
                return_metadata=MetadataQuery(distance=True),
            )
            passages = tuple(
                DenseRetrievedSourcePassage(
                    passage_id=str(item.properties["passageId"]),
                    distance=float(item.metadata.distance),
                )
                for item in response.objects
            )
            return DenseRetrievalResult(
                source_snapshot_id=snapshot.source_snapshot_id,
                jurisdiction=jurisdiction,
                configuration=resolved,
                passages=passages,
                latency_ms=(perf_counter() - started) * 1000,
            )
        finally:
            with suppress(Exception):
                await client.close()
