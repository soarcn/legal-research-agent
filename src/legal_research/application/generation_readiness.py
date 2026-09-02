"""Readiness adapter for the single configured generation provider."""

from legal_research.config import GenerationProviderConfig
from legal_research.ports.generation import GenerationReadinessProvider
from legal_research.ports.readiness import CapabilityStatus, ProbeResult


class GenerationReadinessProbe:
    """Expose one active generation provider through the shared probe contract."""

    name = "generation"

    def __init__(
        self,
        *,
        provider_config: GenerationProviderConfig,
        provider: GenerationReadinessProvider,
    ) -> None:
        self._provider_config = provider_config
        self._provider = provider

    @property
    def active_provider_name(self) -> str:
        """Return the selected provider family for safe local observability."""

        return self._provider_config.provider.value

    async def probe(self) -> ProbeResult:
        """Map a provider-neutral capability state without leaking exceptions."""

        try:
            capability_status = await self._provider.readiness_status()
        except Exception:
            return ProbeResult(name=self.name, status=CapabilityStatus.ERROR)

        if not isinstance(capability_status, CapabilityStatus):
            return ProbeResult(name=self.name, status=CapabilityStatus.ERROR)

        return ProbeResult(name=self.name, status=capability_status)
