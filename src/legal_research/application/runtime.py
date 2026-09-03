"""Application composition for host-runtime capabilities.

The API transport receives a ``ReadinessService`` rather than constructing
database or search clients itself. This keeps the HTTP boundary thin while
giving the process one place to own lifecycle-managed infrastructure.
"""

from dataclasses import dataclass

from legal_research.adapters.embedding import BgeM3EmbeddingProvider
from legal_research.adapters.postgres import AsyncPostgresDatabase, PostgresReadinessProbe
from legal_research.adapters.weaviate import WeaviateReadinessProbe
from legal_research.application.embedding_readiness import EmbeddingReadinessProbe
from legal_research.application.readiness import ReadinessService
from legal_research.config import Settings


@dataclass(slots=True)
class ReadinessRuntime:
    """The configured readiness service and resources it owns."""

    service: ReadinessService
    _postgres_database: AsyncPostgresDatabase

    async def close(self) -> None:
        """Release host-process resources during application shutdown."""

        await self._postgres_database.dispose()


def build_readiness_runtime(settings: Settings) -> ReadinessRuntime:
    """Compose the currently implemented P1 capabilities without loading models yet."""

    postgres_database = AsyncPostgresDatabase(settings.database_url)
    probes = [
        PostgresReadinessProbe(postgres_database),
        WeaviateReadinessProbe.from_url(
            settings.weaviate_url,
            grpc_port=settings.weaviate_grpc_port,
        ),
    ]
    if settings.embedding_enabled:
        probes.append(EmbeddingReadinessProbe(BgeM3EmbeddingProvider(settings.embedding)))
    service = ReadinessService(
        probes=probes,
        timeout_seconds=settings.readiness_timeout_seconds,
    )
    return ReadinessRuntime(service=service, _postgres_database=postgres_database)
