"""P4.1 protects holdout questions while producing retrieval-only cases."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from legal_research.application.legal_rag_bench_loader import LoadedLegalRagBench
from legal_research.application.retrieval_benchmark import (
    BenchmarkSplit,
    BenchmarkSplitError,
    HoldoutAccessError,
    SplitAwareBenchmarkLoader,
    _load_split_manifest,
)
from legal_research.domain import BenchmarkQuestion, SourceSnapshot


class FakeSourceLoader:
    def __init__(self, source: LoadedLegalRagBench) -> None:
        self.source = source
        self.load_calls = 0

    def load(self, raw_root: Path) -> LoadedLegalRagBench:
        self.load_calls += 1
        return self.source


def _source(
    *, dataset_revision: str = "db0b31dc6d195ce9916897e1ac5e4e6209736c8a"
) -> LoadedLegalRagBench:
    snapshot = SourceSnapshot(
        source_snapshot_id="snapshot",
        dataset="isaacus/legal-rag-bench",
        dataset_revision=dataset_revision,
        source_url="https://example.test",
        retrieved_at=datetime.now(UTC),
        corpus_sha256="b" * 64,
        corpus_count=1,
        qa_sha256="e3b869a4e293d081ec5f5b39c2058c8d27b36f611aa9f8275eb1877a7c8b38b0",
        qa_count=100,
        licence_policy="test",
        jurisdiction="VIC",
        language="en",
        corpus_snapshot_date_status="not_published_by_dataset",
    )
    questions = tuple(
        BenchmarkQuestion(
            source_snapshot_id="snapshot",
            question_id=question_id,
            question=f"Question {question_id}",
            answer=f"Do not expose answer {question_id}",
            relevant_passage_id=f"passage-{question_id}",
        )
        for question_id in range(1, 101)
    )
    return LoadedLegalRagBench(snapshot=snapshot, passages=(), questions=questions)


def _write_split(directory: Path, name: str, question_ids: list[object]) -> Path:
    directory.mkdir(exist_ok=True)
    path = directory / f"{name}.json"
    path.write_text(
        json.dumps(
            {
                "benchmark": "legal-rag-benchmark-v1",
                "dataset_revision": "a" * 40,
                "qa_sha256": "c" * 64,
                "split": name,
                "count": len(question_ids),
                "question_ids": question_ids,
            }
        ),
        encoding="utf-8",
    )
    return path


def test_development_case_keeps_provenance_without_exposing_reference_answer() -> None:
    cases = SplitAwareBenchmarkLoader(FakeSourceLoader(_source())).load(Path("data/raw"))

    assert cases[0].benchmark_id == "legal-rag-benchmark-v1"
    assert cases[0].source_snapshot_id == "snapshot"
    assert cases[0].question == "Question 29"
    assert cases[0].relevant_passage_id == "passage-29"
    assert not hasattr(cases[0], "answer")


def test_validation_requires_explicit_selection() -> None:
    cases = SplitAwareBenchmarkLoader(FakeSourceLoader(_source())).load(
        Path("data/raw"), split=BenchmarkSplit.VALIDATION
    )

    assert [case.question_id for case in cases] == [
        4,
        33,
        19,
        92,
        43,
        25,
        76,
        54,
        96,
        21,
        11,
        22,
        35,
        86,
        67,
        2,
        63,
        37,
        48,
        72,
    ]


def test_holdout_is_rejected_before_source_questions_are_loaded() -> None:
    loader = FakeSourceLoader(_source())

    with pytest.raises(HoldoutAccessError, match="reserved"):
        SplitAwareBenchmarkLoader(loader).load(Path("data/raw"), split=BenchmarkSplit.HOLDOUT)

    assert loader.load_calls == 0


def test_string_holdout_is_rejected_before_source_questions_are_loaded() -> None:
    loader = FakeSourceLoader(_source())

    with pytest.raises(HoldoutAccessError, match="reserved"):
        SplitAwareBenchmarkLoader(loader).load(Path("data/raw"), split="holdout")

    assert loader.load_calls == 0


def test_split_that_does_not_match_source_snapshot_is_rejected() -> None:
    with pytest.raises(BenchmarkSplitError, match="does not match"):
        SplitAwareBenchmarkLoader(FakeSourceLoader(_source(dataset_revision="f" * 40))).load(
            Path("data/raw")
        )


@pytest.mark.parametrize("question_id", [True, 1.0, "1"])
def test_malformed_manifest_question_id_is_rejected(tmp_path: Path, question_id: object) -> None:
    path = _write_split(tmp_path, "development", [question_id])

    with pytest.raises(BenchmarkSplitError, match="invalid"):
        _load_split_manifest(path, BenchmarkSplit.DEVELOPMENT)
