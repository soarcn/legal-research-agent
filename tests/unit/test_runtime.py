"""Tests for application-level runtime composition without live services."""

from legal_research.application.fake_generation import FakeGenerationProvider
from legal_research.application.runtime import build_readiness_runtime
from legal_research.config import Settings


async def test_runtime_registers_postgres_and_weaviate_without_connecting() -> None:
    runtime = build_readiness_runtime(Settings())

    try:
        assert runtime.service.capability_names == ("postgres", "weaviate")
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
