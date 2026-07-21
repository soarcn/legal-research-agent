from fastapi import FastAPI

from legal_research.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Australian Legal Research Agent",
    version="0.1.0",
    description="Local, evidence-grounded legal research assistance. Not legal advice.",
)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Liveness endpoint; dependency checks belong to a future readiness endpoint."""
    return {"status": "ok", "environment": settings.app_env}
