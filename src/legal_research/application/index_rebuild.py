"""An explicit, confirmation-gated rebuild of the derived source index only."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from legal_research.application.legal_rag_bench_loader import (
    LegalRagBenchSourceLoader,
    LoadedLegalRagBench,
)
from legal_research.application.source_passage_embedding import (
    EmbeddedSourcePassage,
    SourcePassageEmbedder,
)
from legal_research.domain import SourceSnapshot

REBUILD_CONFIRMATION = "legal-passage-v1"


class RebuildableDerivedIndex(Protocol):
    """The deliberately small destructive surface needed for a rebuild."""

    async def delete_collection(self) -> None: ...

    async def ensure_collection(self) -> None: ...

    async def upsert(
        self,
        *,
        snapshot: SourceSnapshot,
        passages: tuple[EmbeddedSourcePassage, ...],
        source_passages: LoadedLegalRagBench,
    ) -> None: ...

    async def count(self) -> int: ...


@dataclass(frozen=True, slots=True)
class IndexRebuildReport:
    source_snapshot_id: str
    expected_passage_count: int
    indexed_passage_count: int


class DerivedIndexRebuildService:
    """Never write PostgreSQL or raw files while rebuilding a derived index."""

    def __init__(
        self,
        *,
        loader: LegalRagBenchSourceLoader,
        embedder: SourcePassageEmbedder,
        index: RebuildableDerivedIndex,
    ) -> None:
        self._loader = loader
        self._embedder = embedder
        self._index = index

    async def rebuild(self, *, raw_root: Path, confirmation: str) -> IndexRebuildReport:
        if confirmation != REBUILD_CONFIRMATION:
            raise ValueError("Rebuild requires the explicit LegalPassageV1 confirmation value.")
        source = self._loader.load(raw_root)
        embedded = await self._embedder.embed(source.passages)
        if len(embedded) != len(source.passages):
            raise ValueError(
                "The embedding result is incomplete; the existing derived index was preserved."
            )
        await self._index.delete_collection()
        await self._index.ensure_collection()
        await self._index.upsert(
            snapshot=source.snapshot, passages=embedded, source_passages=source
        )
        count = await self._index.count()
        if count != len(source.passages):
            raise RuntimeError(
                "The rebuilt derived index count does not match the verified source count."
            )
        return IndexRebuildReport(
            source_snapshot_id=source.snapshot.source_snapshot_id,
            expected_passage_count=len(source.passages),
            indexed_passage_count=count,
        )
