"""Tests for application-level runtime composition without live services."""

from legal_research.application.runtime import build_readiness_runtime
from legal_research.config import Settings


async def test_runtime_registers_postgres_and_weaviate_without_connecting() -> None:
    runtime = build_readiness_runtime(Settings())

    try:
        assert runtime.service.capability_names == ("postgres", "weaviate")
    finally:
        await runtime.close()
