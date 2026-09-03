"""Run an explicit local text and JSON-schema generation capability check."""

import asyncio
import json
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Literal

from pydantic import BaseModel

from legal_research.adapters.generation import create_generation_provider
from legal_research.config import GenerationProviderConfig, get_settings
from legal_research.ports.generation import (
    GenerationFailure,
    GenerationProvider,
    PlainTextGenerationRequest,
    PlainTextGenerationResponse,
    StructuredGenerationRequest,
    StructuredGenerationResponse,
)
from legal_research.ports.readiness import CapabilityStatus

REPORT_SCHEMA_VERSION = 1
TEXT_PROMPT = "Reply with the word capability-ok and nothing else."
STRUCTURED_PROMPT = 'Return JSON with exactly one field: {"status": "ok"}.'


class StructuredSmokeResponse(BaseModel):
    """The stable, non-legal response schema used for this capability test."""

    status: Literal["ok"]


async def main() -> int:
    """Verify the configured local model without using legal source data."""
    settings = get_settings()
    config = settings.generation_provider_config
    provider = create_generation_provider(config)
    report = _initial_report(config)

    try:
        readiness = await provider.readiness_status()
        report["readiness_status"] = readiness.value
        if readiness is not CapabilityStatus.READY:
            _write_report(config, report)
            return 1

        text_latency_ms, text_result = await _timed_text(provider)
        if isinstance(text_result, GenerationFailure):
            report["text_generation_failure"] = text_result.kind.value
            _write_report(config, report)
            return 1

        structured_latency_ms, structured_result = await _timed_structured(provider)
        if isinstance(structured_result, GenerationFailure):
            report["structured_generation_failure"] = structured_result.kind.value
            _write_report(config, report)
            return 1

        report.update(
            {
                "result": "passed",
                "observations": {
                    "text_response_non_empty": bool(text_result.text.strip()),
                    "text_latency_ms": text_latency_ms,
                    "structured_output_validated": structured_result.output.status == "ok",
                    "structured_latency_ms": structured_latency_ms,
                    "raw_model_output_omitted": True,
                },
            }
        )
        _write_report(config, report)
        return 0
    finally:
        await provider.aclose()


def _initial_report(config: GenerationProviderConfig) -> dict[str, object]:
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": _git_commit(),
        "result": "failed",
        "provider": config.provider.value,
        "model": config.model,
        "base_url": config.base_url,
        "timeout_seconds": config.timeout_seconds,
        "advertised_capabilities": config.capabilities.model_dump(),
        "runtime": {"platform": platform.platform(), "python": platform.python_version()},
    }


async def _timed_text(
    provider: GenerationProvider,
) -> tuple[float, PlainTextGenerationResponse | GenerationFailure]:
    started = perf_counter()
    result = await provider.generate_text(PlainTextGenerationRequest(prompt=TEXT_PROMPT))
    return round((perf_counter() - started) * 1000, 2), result


async def _timed_structured(
    provider: GenerationProvider,
) -> tuple[float, StructuredGenerationResponse[StructuredSmokeResponse] | GenerationFailure]:
    started = perf_counter()
    result = await provider.generate_structured(
        StructuredGenerationRequest(
            prompt=STRUCTURED_PROMPT,
            response_model=StructuredSmokeResponse,
        )
    )
    return round((perf_counter() - started) * 1000, 2), result


def _git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, check=False, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def _write_report(config: GenerationProviderConfig, report: dict[str, object]) -> None:
    path = Path(f"artifacts/capability-reports/generation-{config.provider.value}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
