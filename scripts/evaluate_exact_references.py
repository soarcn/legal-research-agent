"""Run the frozen exact-reference suite against verified source passages."""

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from legal_research.application.exact_reference_evaluation import (
    ExactReferenceSuite,
    evaluate_exact_references,
)
from legal_research.application.legal_rag_bench_loader import LegalRagBenchSourceLoader


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output directory already exists; choose a new run directory")
    suite_bytes = Path("evals/exact_references/v1.json").read_bytes()
    suite = ExactReferenceSuite.model_validate_json(suite_bytes)
    source = LegalRagBenchSourceLoader.from_manifest(
        Path("data/manifests/legal-rag-bench-v1.json")
    ).load(Path("data/raw"))
    result = evaluate_exact_references(suite, source.passages)
    result.update(
        {
            "suite_sha256": hashlib.sha256(suite_bytes).hexdigest(),
            "corpus_sha256": source.snapshot.corpus_sha256,
            "code_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "created_at": datetime.now(UTC).isoformat(),
        }
    )
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}, indent=2))
    return 0 if result["supported_accuracy"] == 1 and result["boundary_accuracy"] == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
