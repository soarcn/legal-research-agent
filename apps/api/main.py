from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from pydantic import BaseModel

from legal_research.application.readiness import ReadinessService
from legal_research.application.runtime import ReadinessRuntime, build_readiness_runtime
from legal_research.config import get_settings
from legal_research.ports.readiness import CapabilityStatus, ReadinessStatus


class ReadinessCapabilityResponse(BaseModel):
    """A provider-neutral capability state safe to expose operationally."""

    name: str
    status: CapabilityStatus
    diagnostic: str | None = None


class ReadinessResponse(BaseModel):
    """A safe aggregate readiness response with fixed, bounded diagnostics."""

    status: ReadinessStatus
    capabilities: list[ReadinessCapabilityResponse]


def create_app(*, readiness_service: ReadinessService | None = None) -> FastAPI:
    """Build the HTTP application with an optional readiness service for integration tests."""

    settings = get_settings()
    runtime: ReadinessRuntime | None = None
    if readiness_service is None:
        runtime = build_readiness_runtime(settings)
        resolved_readiness_service = runtime.service
    else:
        resolved_readiness_service = readiness_service

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        if runtime is not None:
            await runtime.close()

    api = FastAPI(
        title="Australian Legal Research Agent",
        version="0.1.0",
        description="Local, evidence-grounded legal research assistance. Not legal advice.",
        lifespan=lifespan,
    )

    @api.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        """Return liveness without probing external dependencies."""
        return {"status": "ok", "environment": settings.app_env}

    @api.get(
        "/ready",
        tags=["system"],
        response_model=ReadinessResponse,
        response_model_exclude_none=True,
    )
    async def ready(response: Response) -> ReadinessResponse:
        """Return provider-neutral readiness without exposing probe details."""
        report = await resolved_readiness_service.check()
        if not report.is_ready:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return ReadinessResponse(
            status=report.status,
            capabilities=[
                ReadinessCapabilityResponse(
                    name=result.name,
                    status=result.status,
                    diagnostic=result.diagnostic,
                )
                for result in report.capabilities
            ],
        )

    return api


app = create_app()
