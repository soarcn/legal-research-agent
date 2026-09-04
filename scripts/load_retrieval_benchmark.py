"""Safely inspect the permitted P4 retrieval benchmark selection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from legal_research.application.legal_rag_bench_loader import LegalRagBenchSourceLoader
from legal_research.application.retrieval_benchmark import BenchmarkSplit, SplitAwareBenchmarkLoader


def main() -> int:
    """Load one permitted split and report only its non-sensitive selection metadata."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--split",
        choices=(BenchmarkSplit.DEVELOPMENT.value, BenchmarkSplit.VALIDATION.value),
        default=BenchmarkSplit.DEVELOPMENT.value,
    )
    arguments = parser.parse_args()
    cases = SplitAwareBenchmarkLoader(
        LegalRagBenchSourceLoader.from_manifest(Path("data/manifests/legal-rag-bench-v1.json"))
    ).load(Path("data/raw"), split=arguments.split)
    print(
        json.dumps(
            {
                "benchmark_id": cases[0].benchmark_id,
                "split": cases[0].split.value,
                "source_snapshot_id": cases[0].source_snapshot_id,
                "case_count": len(cases),
                "question_ids": [case.question_id for case in cases],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
