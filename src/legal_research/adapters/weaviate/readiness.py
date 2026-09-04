"""Asynchronous, collection-free Weaviate runtime capability checks."""

from collections.abc import Callable
from contextlib import suppress
from typing import Protocol
from urllib.parse import urlparse

from weaviate.client import WeaviateAsyncClient
from weaviate.connect.base import ConnectionParams, ProtocolParams

from legal_research.ports.readiness import CapabilityStatus, ProbeResult


class WeaviateReadinessClient(Protocol):
    """Only the read-only lifecycle operations required by this capability."""

    async def connect(self) -> None:
        """Connect to the configured Weaviate endpoint."""

        ...

    async def close(self) -> None:
        """Release client resources after a bounded readiness check."""

        ...


WeaviateReadinessClientFactory = Callable[[], WeaviateReadinessClient]


class WeaviateReadinessProbe:
    """Check configured Weaviate connectivity without reading or changing data."""

    name = "weaviate"

    def __init__(self, *, client_factory: WeaviateReadinessClientFactory) -> None:
        self._client_factory = client_factory

    @classmethod
    def from_url(
        cls,
        weaviate_url: str,
        *,
        grpc_port: int = 50051,
    ) -> "WeaviateReadinessProbe":
        """Build a probe for an HTTP(S) endpoint and its configured gRPC port."""
        connection_params = connection_params_from_url(weaviate_url, grpc_port=grpc_port)

        def create_client() -> WeaviateAsyncClient:
            return WeaviateAsyncClient(connection_params=connection_params)

        return cls(client_factory=create_client)

    async def probe(self) -> ProbeResult:
        """Return a provider-neutral result and never forward SDK errors."""
        client = self._client_factory()
        try:
            # The v4 client's connect() performs its initialization readiness
            # checks. Calling is_ready() afterwards can print raw SDK errors.
            await client.connect()
        except Exception:
            return ProbeResult(name=self.name, status=CapabilityStatus.FAILED)
        finally:
            with suppress(Exception):
                await client.close()

        return ProbeResult.ready(name=self.name)


def connection_params_from_url(weaviate_url: str, *, grpc_port: int) -> ConnectionParams:
    """Translate a configured HTTP(S) URL to the v4 client's explicit endpoints."""
    parsed = urlparse(weaviate_url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname is None:
        message = "WEAVIATE_URL must be an absolute HTTP(S) URL."
        raise ValueError(message)

    secure = parsed.scheme == "https"
    http_port = parsed.port or (443 if secure else 80)
    return ConnectionParams(
        http=ProtocolParams(host=parsed.hostname, port=http_port, secure=secure),
        grpc=ProtocolParams(host=parsed.hostname, port=grpc_port, secure=secure),
    )
