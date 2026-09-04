"""P3.6 prevents an accidental destructive derived-index rebuild."""

from pathlib import Path

import pytest

from legal_research.application.index_rebuild import DerivedIndexRebuildService


class ShouldNotRun:
    def __getattr__(self, name: str) -> object:
        raise AssertionError(f"{name} must not run without confirmation")


async def test_rebuild_rejects_missing_confirmation_before_loading_or_deleting() -> None:
    service = DerivedIndexRebuildService(
        loader=ShouldNotRun(),  # type: ignore[arg-type]
        embedder=ShouldNotRun(),  # type: ignore[arg-type]
        index=ShouldNotRun(),  # type: ignore[arg-type]
    )

    with pytest.raises(ValueError, match="explicit LegalPassageV1 confirmation"):
        await service.rebuild(raw_root=Path("data/raw"), confirmation="")
