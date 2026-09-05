"""Deterministic metric and artifact regression coverage for P4.2."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from legal_research.application.retrieval_benchmark import BenchmarkSplit, RetrievalBenchmarkCase
from legal_research.application.retrieval_evaluation import (
    FastRetrievalEvaluator,
    RankedRetrievalResult,
    RetrievalEvaluationError,
    RetrievalExperimentIdentity,
    write_evaluation_artifacts,
)


def _case(question_id: int, gold: str) -> RetrievalBenchmarkCase:
    return RetrievalBenchmarkCase(
        benchmark_id="legal-rag-benchmark-v1",
        split=BenchmarkSplit.DEVELOPMENT,
        source_snapshot_id="snapshot",
        question_id=question_id,
        question=f"Question {question_id}",
        relevant_passage_id=gold,
    )


def _identity() -> RetrievalExperimentIdentity:
    return RetrievalExperimentIdentity(
        experiment_id="test-retrieval-001",
        corpus_id="legal-rag-bench-v1",
        corpus_sha256="a" * 64,
        code_revision="b" * 40,
        retrieval_configuration={"mode": "fake", "top_k": 10},
    )


def test_metrics_cover_hits_misses_ranks_and_nearest_rank_latency() -> None:
    evaluation = FastRetrievalEvaluator().evaluate(
        [_case(1, "gold-1"), _case(2, "gold-2"), _case(3, "gold-3")],
        [
            RankedRetrievalResult(1, ("gold-1",), 10),
            RankedRetrievalResult(2, ("other", "gold-2"), 20),
            RankedRetrievalResult(3, ("other",), 30),
        ],
        _identity(),
    )

    assert [case.exact_passage_rank for case in evaluation.cases] == [1, 2, None]
    assert evaluation.aggregate.recall_at_1 == pytest.approx(1 / 3)
    assert evaluation.aggregate.recall_at_5 == pytest.approx(2 / 3)
    assert evaluation.aggregate.mrr == pytest.approx(0.5)
    assert evaluation.aggregate.ndcg_at_10 == pytest.approx((1 + 1 / math.log2(3)) / 3)
    assert evaluation.aggregate.latency_p50_ms == 20
    assert evaluation.aggregate.latency_p95_ms == 30


def test_evaluator_rejects_missing_or_duplicate_rankings() -> None:
    evaluator = FastRetrievalEvaluator()
    cases = [_case(1, "gold-1")]

    with pytest.raises(RetrievalEvaluationError, match="exactly"):
        evaluator.evaluate(cases, [], _identity())
    with pytest.raises(RetrievalEvaluationError, match="duplicate"):
        evaluator.evaluate(
            cases,
            [RankedRetrievalResult(1, (), 1), RankedRetrievalResult(1, ("gold-1",), 1)],
            _identity(),
        )


def test_identity_requires_reproducible_json_configuration() -> None:
    with pytest.raises(RetrievalEvaluationError, match="JSON"):
        RetrievalExperimentIdentity(
            experiment_id="test",
            corpus_id="corpus",
            corpus_sha256="a" * 64,
            code_revision="b" * 40,
            retrieval_configuration={"invalid": object()},
        )


def test_evaluator_rejects_holdout_cases() -> None:
    holdout = RetrievalBenchmarkCase(
        benchmark_id="legal-rag-benchmark-v1",
        split=BenchmarkSplit.HOLDOUT,
        source_snapshot_id="snapshot",
        question_id=1,
        question="Reserved",
        relevant_passage_id="gold-1",
    )

    with pytest.raises(RetrievalEvaluationError, match="holdout"):
        FastRetrievalEvaluator().evaluate([holdout], [RankedRetrievalResult(1, (), 1)], _identity())


def test_artifacts_are_versioned_and_non_overwriting(tmp_path: Path) -> None:
    evaluation = FastRetrievalEvaluator().evaluate(
        [_case(1, "gold-1")], [RankedRetrievalResult(1, ("gold-1",), 1)], _identity()
    )
    target = tmp_path / "run"

    write_evaluation_artifacts(evaluation, target)

    aggregate = json.loads((target / "aggregate.json").read_text(encoding="utf-8"))
    assert aggregate["schema_version"] == "1"
    assert aggregate["identity"]["retrieval_configuration_sha256"]
    with pytest.raises(RetrievalEvaluationError, match="already exists"):
        write_evaluation_artifacts(evaluation, target)
