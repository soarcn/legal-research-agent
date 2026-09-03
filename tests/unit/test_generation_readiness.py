"""Deterministic readiness tests for the one configured generation provider."""

from legal_research.application.fake_generation import FakeGenerationProvider
from legal_research.application.generation_readiness import GenerationReadinessProbe
from legal_research.config import (
    GenerationCapabilities,
    GenerationProvider,
    GenerationProviderConfig,
)
from legal_research.ports.readiness import CapabilityStatus


def _provider_config() -> GenerationProviderConfig:
    return GenerationProviderConfig(
        provider=GenerationProvider.OLLAMA,
        model="qwen3:8b",
        base_url="http://localhost:11434",
        api_key=None,
        timeout_seconds=60,
        capabilities=GenerationCapabilities(structured_output=True),
    )


async def test_generation_readiness_probe_uses_only_the_active_provider() -> None:
    active_provider = FakeGenerationProvider(readiness=CapabilityStatus.READY)
    probe = GenerationReadinessProbe(
        provider_config=_provider_config(),
        provider=active_provider,
    )

    result = await probe.probe()

    assert result.name == "generation"
    assert result.status is CapabilityStatus.READY


async def test_generation_readiness_probe_preserves_a_safe_non_ready_state() -> None:
    probe = GenerationReadinessProbe(
        provider_config=_provider_config(),
        provider=FakeGenerationProvider(readiness=CapabilityStatus.DISABLED),
    )

    result = await probe.probe()

    assert result.name == "generation"
    assert result.status is CapabilityStatus.DISABLED
    assert result.diagnostic is None
