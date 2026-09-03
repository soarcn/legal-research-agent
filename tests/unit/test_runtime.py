"""Tests for application-level runtime composition without live services."""

from legal_research.application.fake_generation import FakeGenerationProvider
from legal_research.application.runtime import build_readiness_runtime
from legal_research.config import Settings


async def test_runtime_registers_default_capabilities_without_connecting() -> None:
    runtime = build_readiness_runtime(Settings())

    try:
        assert runtime.service.capability_names == ("postgres", "weaviate", "generation")
    finally:
        await runtime.close()


async def test_runtime_registers_embedding_only_when_explicitly_enabled() -> None:
    runtime = build_readiness_runtime(Settings(embedding_enabled=True))

    try:
        assert runtime.service.capability_names == (
            "postgres",
            "weaviate",
            "generation",
            "embedding",
        )
    finally:
        await runtime.close()


async def test_runtime_registers_reranker_only_when_explicitly_enabled() -> None:
    runtime = build_readiness_runtime(Settings(reranker_enabled=True))

    try:
        assert runtime.service.capability_names == (
            "postgres",
            "weaviate",
            "generation",
            "reranker",
        )
    finally:
        await runtime.close()


async def test_runtime_registers_all_explicit_model_capabilities() -> None:
    runtime = build_readiness_runtime(Settings(embedding_enabled=True, reranker_enabled=True))

    try:
        assert runtime.service.capability_names == (
            "postgres",
            "weaviate",
            "generation",
            "embedding",
            "reranker",
        )
    finally:
        await runtime.close()


async def test_runtime_registers_only_the_supplied_active_generation_provider() -> None:
    runtime = build_readiness_runtime(
        Settings(),
        generation_provider=FakeGenerationProvider(),
    )

    try:
        assert runtime.service.capability_names == ("postgres", "weaviate", "generation")
    finally:
        await runtime.close()
