"""Split-aware retrieval benchmark cases that protect the v1 holdout."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from legal_research.application.legal_rag_bench_loader import LoadedLegalRagBench

BENCHMARK_ID = "legal-rag-benchmark-v1"
DEFAULT_SPLIT_DIRECTORY = Path("evals/splits")


class BenchmarkSplit(StrEnum):
    """The frozen project-defined v1 benchmark partitions."""

    DEVELOPMENT = "development"
    VALIDATION = "validation"
    HOLDOUT = "holdout"


class HoldoutAccessError(ValueError):
    """Raised before a P4 caller can load question or gold-label content."""


class BenchmarkSplitError(ValueError):
    """The committed split manifest cannot safely select source QA records."""


class BenchmarkSourceLoader(Protocol):
    """The narrow source boundary required by retrieval evaluation."""

    def load(self, raw_root: Path) -> LoadedLegalRagBench:
        """Return verified source facts."""

        ...


@dataclass(frozen=True, slots=True)
class RetrievalBenchmarkCase:
    """A retrieval-only case; source answers are deliberately not exposed."""

    benchmark_id: str
    split: BenchmarkSplit
    source_snapshot_id: str
    question_id: int
    question: str
    relevant_passage_id: str


class SplitAwareBenchmarkLoader:
    """Load only permitted retrieval cases from a verified frozen source snapshot."""

    def __init__(
        self,
        source_loader: BenchmarkSourceLoader,
    ) -> None:
        self._source_loader = source_loader

    def load(
        self,
        raw_root: Path,
        *,
        split: BenchmarkSplit | str = BenchmarkSplit.DEVELOPMENT,
    ) -> tuple[RetrievalBenchmarkCase, ...]:
        """Return development or validation cases, never v1 holdout content in P4."""
        try:
            resolved_split = BenchmarkSplit(split)
        except (TypeError, ValueError) as error:
            raise BenchmarkSplitError(
                "The requested retrieval benchmark split is invalid."
            ) from error
        if resolved_split is BenchmarkSplit.HOLDOUT:
            raise HoldoutAccessError(
                "The v1 holdout is reserved for the authorized P8 final evaluation."
            )
        manifest = _load_split_manifest(
            DEFAULT_SPLIT_DIRECTORY / f"{resolved_split.value}.json", resolved_split
        )
        source = self._source_loader.load(raw_root)
        _validate_manifest_against_source(manifest, source)
        questions_by_id = {question.question_id: question for question in source.questions}
        return tuple(
            RetrievalBenchmarkCase(
                benchmark_id=BENCHMARK_ID,
                split=resolved_split,
                source_snapshot_id=source.snapshot.source_snapshot_id,
                question_id=question_id,
                question=questions_by_id[question_id].question,
                relevant_passage_id=questions_by_id[question_id].relevant_passage_id,
            )
            for question_id in manifest.question_ids
        )


@dataclass(frozen=True, slots=True)
class _SplitManifest:
    benchmark: str
    dataset_revision: str
    qa_sha256: str
    split: BenchmarkSplit
    count: int
    question_ids: tuple[int, ...]


def _load_split_manifest(path: Path, split: BenchmarkSplit) -> _SplitManifest:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        ids = payload["question_ids"]
        if not isinstance(ids, list) or any(
            not isinstance(question_id, int) or isinstance(question_id, bool) for question_id in ids
        ):
            raise TypeError("question_ids must be JSON integer values")
        manifest = _SplitManifest(
            benchmark=payload["benchmark"],
            dataset_revision=payload["dataset_revision"],
            qa_sha256=payload["qa_sha256"],
            split=BenchmarkSplit(payload["split"]),
            count=payload["count"],
            question_ids=tuple(ids),
        )
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise BenchmarkSplitError("The retrieval benchmark split manifest is invalid.") from error
    if (
        manifest.benchmark != BENCHMARK_ID
        or manifest.split is not split
        or manifest.count != len(manifest.question_ids)
        or not manifest.question_ids
        or len(set(manifest.question_ids)) != len(manifest.question_ids)
        or any(question_id <= 0 for question_id in manifest.question_ids)
    ):
        raise BenchmarkSplitError("The retrieval benchmark split manifest is inconsistent.")
    return manifest


def _validate_manifest_against_source(
    manifest: _SplitManifest, source: LoadedLegalRagBench
) -> None:
    source_ids = {question.question_id for question in source.questions}
    if (
        manifest.dataset_revision != source.snapshot.dataset_revision
        or manifest.qa_sha256 != source.snapshot.qa_sha256
        or not set(manifest.question_ids).issubset(source_ids)
    ):
        raise BenchmarkSplitError(
            "The retrieval benchmark split does not match the source snapshot."
        )
