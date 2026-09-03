"""Application composition for host-runtime capabilities."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from legal_research.adapters.embedding import BgeM3EmbeddingProvider
from legal_research.adapters.generation import create_generation_provider
from legal_research.adapters.postgres import AsyncPostgresDatabase, PostgresReadinessProbe
from legal_research.adapters.reranking import BgeM3RerankerProvider
from legal_research.adapters.weaviate import WeaviateReadinessProbe
from legal_research.application.embedding_readiness import EmbeddingReadinessProbe
from legal_research.application.generation_readiness import GenerationReadinessProbe
from legal_research.application.readiness import ReadinessService
from legal_research.application.reranker_readiness import RerankerReadinessProbe
from legal_research.config import Settings
from legal_research.ports.generation import GenerationReadinessProvider


@dataclass(slots=True)
class ReadinessRuntime:
    """The configured readiness service and resources it owns."""

    service: ReadinessService
    _postgres_database: AsyncPostgresDatabase
    _generation_close: Callable[[], Awaitable[None]] | None = None

    async def close(self) -> None:
        """Release host-process resources during application shutdown."""
        if self._generation_close is not None:
            await self._generation_close()
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
    created_generation_provider = None
    if generation_provider is None:
        created_generation_provider = create_generation_provider(
            settings.generation_provider_config
        )
        configured_generation_provider = created_generation_provider
    else:
        configured_generation_provider = generation_provider
    probes.append(
        GenerationReadinessProbe(
            provider_config=settings.generation_provider_config,
            provider=configured_generation_provider,
        )
    )
    if settings.embedding_enabled:
        probes.append(EmbeddingReadinessProbe(BgeM3EmbeddingProvider(settings.embedding)))
    if settings.reranker_enabled:
        probes.append(RerankerReadinessProbe(BgeM3RerankerProvider(settings.reranker)))
    service = ReadinessService(probes=probes, timeout_seconds=settings.readiness_timeout_seconds)
    close_generation = (
        created_generation_provider.aclose if created_generation_provider is not None else None
    )
    return ReadinessRuntime(
        service=service,
        _postgres_database=postgres_database,
        _generation_close=close_generation,
    )
