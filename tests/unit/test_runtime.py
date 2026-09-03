"""Tests for application-level runtime composition without live services."""

from legal_research.application.runtime import build_readiness_runtime
from legal_research.config import Settings


async def test_runtime_registers_default_capabilities_without_connecting() -> None:
    runtime = build_readiness_runtime(Settings())

    try:
        assert runtime.service.capability_names == ("postgres", "weaviate")
    finally:
        await runtime.close()


async def test_runtime_registers_embedding_only_when_explicitly_enabled() -> None:
    runtime = build_readiness_runtime(Settings(embedding_enabled=True))

    try:
        assert runtime.service.capability_names == ("postgres", "weaviate", "embedding")
    finally:
        await runtime.close()
