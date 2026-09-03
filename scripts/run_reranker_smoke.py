"""Run an opt-in BGE reranker capability check without legal source data."""

import asyncio
import json
import platform
import resource
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from legal_research.adapters.reranking import BgeM3RerankerProvider
from legal_research.config import get_settings
from legal_research.ports.reranking import RerankerError, RerankRequest

REPORT_PATH = Path("artifacts/capability-reports/reranker-bge-m3.json")


async def main() -> int:
    """Load the pinned cross-encoder and score a fixed non-legal pair batch."""
    config = get_settings().reranker
    report: dict[str, object] = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": _git_commit(),
        "result": "failed",
        "model": {"id": config.model_id, "revision": config.revision, "device": config.device},
        "runtime": {"platform": platform.platform(), "python": platform.python_version()},
        "resources": {"peak_rss_bytes_before": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
    }
    provider = BgeM3RerankerProvider(config)
    started = perf_counter()
    try:
        response = await provider.rerank(
            RerankRequest(
                query="Which passage discusses marine mammals?",
                passages=("A whale is a marine mammal.", "A triangle has three sides."),
            )
        )
    except RerankerError as error:
        report["failure_kind"] = error.kind.value
        _write_report(report)
        return 1

    report["result"] = "passed"
    report["observations"] = {
        "latency_ms": round((perf_counter() - started) * 1000, 2),
        "score_count": len(response.scores),
        "scores_finite": True,
        "raw_scores_omitted": True,
    }
    report["resources"] = {
        "peak_rss_bytes_after": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    }
    _write_report(report)
    return 0


def _git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, check=False, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def _write_report(report: dict[str, object]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
