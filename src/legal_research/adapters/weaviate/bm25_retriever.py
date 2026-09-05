"""Snapshot-scoped Weaviate BM25 retrieval for unchanged v1 source passages."""

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
from legal_research.domain import SourceSnapshot


class WeaviateBm25Client(Protocol):
    @property
    def collections(self) -> object: ...
    async def connect(self) -> None: ...
    async def close(self) -> None: ...


WeaviateBm25ClientFactory = Callable[[], WeaviateBm25Client]


@dataclass(frozen=True, slots=True)
class Bm25RetrievalConfiguration:
    top_k: int = 10
    mode: str = "bm25"

    def __post_init__(self) -> None:
        if self.top_k <= 0:
            raise ValueError("top_k must be positive")


@dataclass(frozen=True, slots=True)
class RetrievedSourcePassage:
    passage_id: str
    score: float


@dataclass(frozen=True, slots=True)
class Bm25RetrievalResult:
    source_snapshot_id: str
    jurisdiction: str
    configuration: Bm25RetrievalConfiguration
    passages: tuple[RetrievedSourcePassage, ...]
    latency_ms: float


class WeaviateBm25SourcePassageRetriever:
    """Read only the requested corpus snapshot and jurisdiction before BM25 ranking."""

    def __init__(self, client_factory: WeaviateBm25ClientFactory) -> None:
        self._client_factory = client_factory

    @classmethod
    def from_url(
        cls, weaviate_url: str, *, grpc_port: int = 50051
    ) -> WeaviateBm25SourcePassageRetriever:
        """Build the local v4 client without exposing its SDK at application boundaries."""
        connection_params = connection_params_from_url(weaviate_url, grpc_port=grpc_port)
        return cls(client_factory=lambda: WeaviateAsyncClient(connection_params=connection_params))

    async def retrieve(
        self,
        *,
        query: str,
        snapshot: SourceSnapshot,
        jurisdiction: str,
        configuration: Bm25RetrievalConfiguration | None = None,
        effective_at: date | None = None,
    ) -> Bm25RetrievalResult:
        if not query.strip():
            raise ValueError("query must not be empty")
        if effective_at is not None:
            raise ValueError("v1 does not support legal effective-date filtering")
        if jurisdiction != snapshot.jurisdiction:
            raise ValueError("jurisdiction must match the requested source snapshot")
        resolved_configuration = configuration or Bm25RetrievalConfiguration()
        client = self._client_factory()
        started = perf_counter()
        try:
            await client.connect()
            collection = client.collections.get(LEGAL_PASSAGE_V1_SCHEMA.collection_name)  # type: ignore[attr-defined]
            response = await collection.query.bm25(  # type: ignore[attr-defined]
                query=query,
                filters=Filter.all_of(
                    [
                        Filter.by_property("sourceSnapshotId").equal(snapshot.source_snapshot_id),
                        Filter.by_property("jurisdiction").equal(jurisdiction),
                    ]
                ),
                limit=resolved_configuration.top_k,
                return_properties=["passageId"],
                return_metadata=MetadataQuery(score=True),
            )
            passages = tuple(
                RetrievedSourcePassage(
                    passage_id=str(item.properties["passageId"]), score=float(item.metadata.score)
                )
                for item in response.objects
            )
            return Bm25RetrievalResult(
                source_snapshot_id=snapshot.source_snapshot_id,
                jurisdiction=jurisdiction,
                configuration=resolved_configuration,
                passages=passages,
                latency_ms=(perf_counter() - started) * 1000,
            )
        finally:
            with suppress(Exception):
                await client.close()
