"""Deterministic retrieval metrics and schema-versioned local artifacts."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from legal_research.application.retrieval_benchmark import RetrievalBenchmarkCase

SCHEMA_VERSION = "1"


class RetrievalEvaluationError(ValueError):
    """Raised when rankings cannot be evaluated against a frozen benchmark split."""


@dataclass(frozen=True, slots=True)
class RetrievalExperimentIdentity:
    """Immutable identities required to compare a retrieval experiment safely."""

    experiment_id: str
    corpus_id: str
    corpus_sha256: str
    code_revision: str
    retrieval_configuration: Mapping[str, object]

    def __post_init__(self) -> None:
        if not all((self.experiment_id, self.corpus_id, self.code_revision)):
            raise RetrievalEvaluationError("experiment, corpus, and code identities are required")
        if len(self.corpus_sha256) != 64 or any(
            character not in "0123456789abcdef" for character in self.corpus_sha256
        ):
            raise RetrievalEvaluationError("corpus_sha256 must be a lowercase SHA-256 hex digest")
        if len(self.code_revision) != 40 or any(
            character not in "0123456789abcdef" for character in self.code_revision
        ):
            raise RetrievalEvaluationError("code_revision must be a lowercase Git SHA")
        try:
            json.dumps(self.retrieval_configuration, sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError) as error:
            raise RetrievalEvaluationError(
                "retrieval_configuration must be JSON serializable"
            ) from error

    @property
    def retrieval_configuration_sha256(self) -> str:
        canonical = json.dumps(
            self.retrieval_configuration, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True, slots=True)
class RankedRetrievalResult:
    """One retriever's ranked result for one benchmark question."""

    question_id: int
    passage_ids: tuple[str, ...]
    latency_ms: float

    def __post_init__(self) -> None:
        if self.question_id <= 0:
            raise RetrievalEvaluationError("question_id must be positive")
        if self.latency_ms < 0:
            raise RetrievalEvaluationError("latency_ms must be non-negative")
        if len(set(self.passage_ids)) != len(self.passage_ids):
            raise RetrievalEvaluationError("ranked passage_ids must not contain duplicates")


@dataclass(frozen=True, slots=True)
class RetrievalCaseResult:
    """Deterministic metrics and evidence for one exact gold-passage lookup."""

    question_id: int
    relevant_passage_id: str
    exact_passage_rank: int | None
    recall_at_1: float
    recall_at_5: float
    recall_at_10: float
    reciprocal_rank: float
    ndcg_at_10: float
    latency_ms: float


@dataclass(frozen=True, slots=True)
class RetrievalAggregateMetrics:
    """Unweighted means and latency percentiles over the complete selected split."""

    case_count: int
    recall_at_1: float
    recall_at_5: float
    recall_at_10: float
    mrr: float
    ndcg_at_10: float
    latency_p50_ms: float
    latency_p95_ms: float


@dataclass(frozen=True, slots=True)
class RetrievalEvaluation:
    """A complete reproducible evaluation for one non-holdout split."""

    identity: RetrievalExperimentIdentity
    benchmark_id: str
    split: str
    source_snapshot_id: str
    aggregate: RetrievalAggregateMetrics
    cases: tuple[RetrievalCaseResult, ...]


class FastRetrievalEvaluator:
    """Score exact gold source-passage retrieval without generation or Agent behaviour."""

    def evaluate(
        self,
        cases: Sequence[RetrievalBenchmarkCase],
        rankings: Sequence[RankedRetrievalResult],
        identity: RetrievalExperimentIdentity,
    ) -> RetrievalEvaluation:
        """Return deterministic metrics, rejecting incomplete or mixed result sets."""
        if not cases:
            raise RetrievalEvaluationError("at least one benchmark case is required")
        self._validate_cases(cases)
        rankings_by_question = self._index_rankings(rankings)
        expected_ids = {case.question_id for case in cases}
        actual_ids = set(rankings_by_question)
        if actual_ids != expected_ids:
            raise RetrievalEvaluationError(
                "rankings must contain exactly the selected benchmark cases"
            )

        case_results = tuple(
            self._score_case(case, rankings_by_question[case.question_id]) for case in cases
        )
        return RetrievalEvaluation(
            identity=identity,
            benchmark_id=cases[0].benchmark_id,
            split=cases[0].split.value,
            source_snapshot_id=cases[0].source_snapshot_id,
            aggregate=_aggregate(case_results),
            cases=case_results,
        )

    @staticmethod
    def _validate_cases(cases: Sequence[RetrievalBenchmarkCase]) -> None:
        first = cases[0]
        if first.split.value == "holdout":
            raise RetrievalEvaluationError("the v1 holdout is unavailable to the fast evaluator")
        if len({case.question_id for case in cases}) != len(cases):
            raise RetrievalEvaluationError(
                "benchmark cases must not contain duplicate question IDs"
            )
        if any(
            case.benchmark_id != first.benchmark_id
            or case.split != first.split
            or case.source_snapshot_id != first.source_snapshot_id
            for case in cases
        ):
            raise RetrievalEvaluationError("benchmark cases must share one frozen split identity")

    @staticmethod
    def _index_rankings(
        rankings: Sequence[RankedRetrievalResult],
    ) -> dict[int, RankedRetrievalResult]:
        indexed = {ranking.question_id: ranking for ranking in rankings}
        if len(indexed) != len(rankings):
            raise RetrievalEvaluationError("rankings must not contain duplicate question IDs")
        return indexed

    @staticmethod
    def _score_case(
        case: RetrievalBenchmarkCase, ranking: RankedRetrievalResult
    ) -> RetrievalCaseResult:
        try:
            rank = ranking.passage_ids.index(case.relevant_passage_id) + 1
        except ValueError:
            rank = None
        reciprocal_rank = 0.0 if rank is None else 1.0 / rank
        ndcg_at_10 = 0.0 if rank is None or rank > 10 else 1.0 / math.log2(rank + 1)
        return RetrievalCaseResult(
            question_id=case.question_id,
            relevant_passage_id=case.relevant_passage_id,
            exact_passage_rank=rank,
            recall_at_1=float(rank is not None and rank <= 1),
            recall_at_5=float(rank is not None and rank <= 5),
            recall_at_10=float(rank is not None and rank <= 10),
            reciprocal_rank=reciprocal_rank,
            ndcg_at_10=ndcg_at_10,
            latency_ms=ranking.latency_ms,
        )


def write_evaluation_artifacts(evaluation: RetrievalEvaluation, directory: Path) -> None:
    """Write distinct schema-versioned JSON artifacts without overwriting a formal run."""
    if directory.exists():
        raise RetrievalEvaluationError("evaluation artifact directory already exists")
    directory.mkdir(parents=True)
    identity = {
        **asdict(evaluation.identity),
        "retrieval_configuration_sha256": evaluation.identity.retrieval_configuration_sha256,
    }
    common = {
        "schema_version": SCHEMA_VERSION,
        "identity": identity,
        "benchmark_id": evaluation.benchmark_id,
        "split": evaluation.split,
        "source_snapshot_id": evaluation.source_snapshot_id,
    }
    (directory / "aggregate.json").write_text(
        json.dumps({**common, "metrics": asdict(evaluation.aggregate)}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (directory / "per-case.json").write_text(
        json.dumps(
            {**common, "cases": [asdict(case) for case in evaluation.cases]},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _aggregate(cases: Sequence[RetrievalCaseResult]) -> RetrievalAggregateMetrics:
    count = len(cases)
    return RetrievalAggregateMetrics(
        case_count=count,
        recall_at_1=sum(case.recall_at_1 for case in cases) / count,
        recall_at_5=sum(case.recall_at_5 for case in cases) / count,
        recall_at_10=sum(case.recall_at_10 for case in cases) / count,
        mrr=sum(case.reciprocal_rank for case in cases) / count,
        ndcg_at_10=sum(case.ndcg_at_10 for case in cases) / count,
        latency_p50_ms=_nearest_rank_percentile([case.latency_ms for case in cases], 50),
        latency_p95_ms=_nearest_rank_percentile([case.latency_ms for case in cases], 95),
    )


def _nearest_rank_percentile(values: Sequence[float], percentile: int) -> float:
    """Return the nearest-rank percentile, avoiding interpolation ambiguity in small suites."""
    ordered = sorted(values)
    index = math.ceil(percentile / 100 * len(ordered)) - 1
    return ordered[index]
