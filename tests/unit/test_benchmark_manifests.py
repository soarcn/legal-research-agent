import json
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[2]
EXPECTED_REVISION = "db0b31dc6d195ce9916897e1ac5e4e6209736c8a"


def load_json(relative_path: str) -> dict[str, object]:
    path = REPOSITORY_ROOT / relative_path
    return json.loads(path.read_text(encoding="utf-8"))


def test_corpus_manifest_is_versioned_metadata() -> None:
    manifest = load_json("data/manifests/legal-rag-bench-v1.json")

    assert manifest["dataset_revision"] == EXPECTED_REVISION
    assert manifest["source_snapshot_id"] == f"legal-rag-bench@{EXPECTED_REVISION}"
    assert manifest["corpus_snapshot_date"] is None
    assert manifest["legal_effective_at"] is None
    assert manifest["corpus"]["count"] == 4876  # type: ignore[index]
    assert manifest["qa"]["count"] == 100  # type: ignore[index]


def test_benchmark_splits_cover_each_question_once() -> None:
    expected_counts = {"development": 60, "validation": 20, "holdout": 20}
    all_ids: list[int] = []

    for split, expected_count in expected_counts.items():
        manifest = load_json(f"evals/splits/{split}.json")
        ids = manifest["question_ids"]

        assert manifest["benchmark"] == "legal-rag-benchmark-v1"
        assert manifest["dataset_revision"] == EXPECTED_REVISION
        assert manifest["seed"] == 20260721
        assert manifest["split"] == split
        assert manifest["count"] == expected_count
        assert isinstance(ids, list)
        assert len(ids) == expected_count
        assert all(isinstance(question_id, int) for question_id in ids)
        all_ids.extend(ids)

    assert len(all_ids) == len(set(all_ids)) == 100
    assert set(all_ids) == set(range(1, 101))
