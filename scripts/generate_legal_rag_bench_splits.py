"""Generate deterministic Legal RAG Bench v1 question-ID splits."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260721)
    return parser.parse_args()


def load_ids(path: Path) -> list[int]:
    ids: list[int] = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            record = json.loads(line)
            question_id = record.get("id")
            if not isinstance(question_id, int):
                raise ValueError(f"Line {line_number} has a non-integer question ID")
            ids.append(question_id)

    if len(ids) != 100 or len(set(ids)) != 100:
        raise ValueError("Expected exactly 100 unique Legal RAG Bench question IDs")
    return ids


def write_manifest(path: Path, split: str, ids: list[int], seed: int) -> None:
    payload = {
        "benchmark": "legal-rag-benchmark-v1",
        "dataset": "isaacus/legal-rag-bench",
        "dataset_revision": "db0b31dc6d195ce9916897e1ac5e4e6209736c8a",
        "qa_sha256": "e3b869a4e293d081ec5f5b39c2058c8d27b36f611aa9f8275eb1877a7c8b38b0",
        "split": split,
        "seed": seed,
        "count": len(ids),
        "question_ids": ids,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    ids = load_ids(args.qa)
    random.Random(args.seed).shuffle(ids)

    args.output.mkdir(parents=True, exist_ok=True)
    write_manifest(args.output / "development.json", "development", ids[:60], args.seed)
    write_manifest(args.output / "validation.json", "validation", ids[60:80], args.seed)
    write_manifest(args.output / "holdout.json", "holdout", ids[80:], args.seed)


if __name__ == "__main__":
    main()
