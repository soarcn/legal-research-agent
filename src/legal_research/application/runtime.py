"""Application composition for host-runtime capabilities.

The API transport receives a ``ReadinessService`` rather than constructing
database or search clients itself. This keeps the HTTP boundary thin while
giving the process one place to own lifecycle-managed infrastructure.
"""

from dataclasses import dataclass

from legal_research.adapters.postgres import AsyncPostgresDatabase, PostgresReadinessProbe
from legal_research.adapters.weaviate import WeaviateReadinessProbe
from legal_research.application.generation_readiness import GenerationReadinessProbe
from legal_research.application.readiness import ReadinessService
from legal_research.config import Settings
from legal_research.ports.generation import GenerationReadinessProvider


@dataclass(slots=True)
class ReadinessRuntime:
    """The configured readiness service and resources it owns."""

    service: ReadinessService
    _postgres_database: AsyncPostgresDatabase

    async def close(self) -> None:
        """Release host-process resources during application shutdown."""

        await self._postgres_database.dispose()


def build_readiness_runtime(
    settings: Settings,
    *,
    generation_provider: GenerationReadinessProvider | None = None,
) -> ReadinessRuntime:
    """Compose P1 capabilities; register generation only when an adapter is supplied."""

    postgres_database = AsyncPostgresDatabase(settings.database_url)
    probes = [
        PostgresReadinessProbe(postgres_database),
        WeaviateReadinessProbe.from_url(
            settings.weaviate_url,
            grpc_port=settings.weaviate_grpc_port,
        ),
    ]
    if generation_provider is not None:
        probes.append(
            GenerationReadinessProbe(
                provider_config=settings.generation_provider_config,
                provider=generation_provider,
            )
        )
    service = ReadinessService(probes=probes)
    return ReadinessRuntime(service=service, _postgres_database=postgres_database)
