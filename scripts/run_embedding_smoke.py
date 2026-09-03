"""Run an opt-in BGE-M3 capability check and write a redacted JSON report."""

import asyncio
import json
import platform
import resource
import subprocess
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

from legal_research.adapters.embedding import BgeM3EmbeddingProvider
from legal_research.config import get_settings
from legal_research.ports.embedding import EmbeddingError, EmbeddingRequest, EmbeddingResponse

REPORT_SCHEMA_VERSION = 1
FIXTURE_TEXT = "A short retrieval capability fixture."
REPORT_PATH = Path("artifacts/capability-reports/embedding-bge-m3.json")


async def main() -> int:
    """Perform first and cached inference without emitting vectors or source data."""
    settings = get_settings()
    config = settings.embedding
    provider = BgeM3EmbeddingProvider(config)
    started_at = datetime.now(UTC)
    peak_rss_before = _peak_rss_bytes()
    resources: dict[str, int | None] = {
        "peak_rss_bytes_before": peak_rss_before,
        "model_cache_bytes": _model_cache_size(config.model_id),
    }

    report: dict[str, object] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": started_at.isoformat(),
        "git_commit": _git_commit(),
        "result": "failed",
        "model": {
            "id": config.model_id,
            "revision": config.revision,
            "pooling": config.pooling,
            "normalize": config.normalize,
            "expected_dimension": config.expected_dimension,
            "max_sequence_length": config.max_sequence_length,
            "batch_size": config.batch_size,
            "device": config.device,
        },
        "runtime": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "sentence_transformers": _package_version("sentence-transformers"),
            "torch": _package_version("torch"),
        },
        "resources": resources,
    }

    try:
        first_latency_ms, first = await _timed_embed(provider)
        repeat_latency_ms, repeated = await _timed_embed(provider)
    except EmbeddingError as error:
        report["failure_kind"] = error.kind.value
        resources["peak_rss_bytes_after"] = _peak_rss_bytes()
        resources["model_cache_bytes"] = _model_cache_size(config.model_id)
        _write_report(report)
        return 1

    report.update(
        {
            "result": "passed",
            "observations": {
                "first_latency_ms": first_latency_ms,
                "repeat_latency_ms": repeat_latency_ms,
                "first_vector_count": len(first.vectors),
                "repeat_vector_count": len(repeated.vectors),
                "observed_dimension": first.dimension,
                "dimension_stable": first.dimension == repeated.dimension,
                "vectors_omitted": True,
            },
            "resources": resources,
        }
    )
    resources["peak_rss_bytes_after"] = _peak_rss_bytes()
    resources["model_cache_bytes"] = _model_cache_size(config.model_id)
    _write_report(report)
    return 0


async def _timed_embed(provider: BgeM3EmbeddingProvider) -> tuple[float, EmbeddingResponse]:
    started = perf_counter()
    response = await provider.embed(EmbeddingRequest(texts=(FIXTURE_TEXT,)))
    return round((perf_counter() - started) * 1000, 2), response


def _peak_rss_bytes() -> int:
    """Return the host-reported process peak RSS; macOS reports it in bytes."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


def _package_version(package_name: str) -> str:
    try:
        return version(package_name)
    except Exception:
        return "unavailable"


def _git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, check=False, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def _model_cache_size(model_id: str) -> int | None:
    cache_directory = (
        Path.home() / ".cache" / "huggingface" / "hub" / ("models--" + model_id.replace("/", "--"))
    )
    if not cache_directory.exists():
        return None
    return sum(path.stat().st_size for path in cache_directory.rglob("*") if path.is_file())


def _write_report(report: dict[str, object]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
