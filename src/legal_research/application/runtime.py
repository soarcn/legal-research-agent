"""Application composition for host-runtime capabilities."""

from dataclasses import dataclass

from legal_research.adapters.embedding import BgeM3EmbeddingProvider
from legal_research.adapters.postgres import AsyncPostgresDatabase, PostgresReadinessProbe
from legal_research.adapters.weaviate import WeaviateReadinessProbe
from legal_research.application.embedding_readiness import EmbeddingReadinessProbe
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
    """Compose accepted P1 probes without loading optional models until checked."""
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
    if settings.embedding_enabled:
        probes.append(EmbeddingReadinessProbe(BgeM3EmbeddingProvider(settings.embedding)))
    service = ReadinessService(probes=probes, timeout_seconds=settings.readiness_timeout_seconds)
    return ReadinessRuntime(service=service, _postgres_database=postgres_database)
