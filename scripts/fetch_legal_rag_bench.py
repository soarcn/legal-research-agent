"""Fetch or locally verify the pinned Legal RAG Bench v1 snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from legal_research.application.dataset_snapshot import (
    DatasetSnapshotError,
    DatasetSnapshotManifest,
    LegalRagBenchSnapshotFetcher,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest", type=Path, default=Path("data/manifests/legal-rag-bench-v1.json")
    )
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--verify-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        fetcher = LegalRagBenchSnapshotFetcher(DatasetSnapshotManifest.load(args.manifest))
        result = (
            fetcher.verify_existing(args.raw_root)
            if args.verify_only
            else fetcher.fetch(args.raw_root)
        )
    except DatasetSnapshotError as error:
        print(json.dumps({"result": "failed", "error": str(error)}))
        return 1
    print(
        json.dumps(
            {
                "result": "verified",
                "source_snapshot_id": result.source_snapshot_id,
                "corpus_count": result.corpus_count,
                "qa_count": result.qa_count,
                "licence_policy": result.licence_policy,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
