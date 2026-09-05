from pathlib import Path

import pytest

from legal_research.application.exact_reference_evaluation import (
    ExactReferenceSuite,
    evaluate_exact_references,
)
from legal_research.domain import SourcePassage


def fixture() -> tuple[ExactReferenceSuite, tuple[SourcePassage, ...]]:
    suite = ExactReferenceSuite.model_validate_json(
        Path("evals/exact_references/v1.json").read_bytes()
    )
    ids = {i for c in suite.cases for i in c.expected_passage_ids}
    # Prefix collisions and child sections must not be included in an exact lookup.
    ids.update({"8.12.1-c1-s1", "8.120-c1-s1", "1.10-c1-s1"})
    return suite, tuple(
        SourcePassage(
            source_snapshot_id=suite.source_snapshot_id,
            passage_id=i,
            title="synthetic",
            text="synthetic",
            footnotes=None,
            content_sha256="a" * 64,
        )
        for i in sorted(ids)
    )


def test_frozen_suite_resolves_complete_sets_without_prefix_leakage() -> None:
    suite, passages = fixture()
    result = evaluate_exact_references(suite, passages)
    assert result["supported_count"] == 20
    assert result["supported_accuracy"] == 1
    assert result["boundary_count"] == 10
    assert result["boundary_accuracy"] == 1


def test_missing_passage_is_a_failure_not_partial_credit() -> None:
    suite, passages = fixture()
    result = evaluate_exact_references(
        suite, tuple(p for p in passages if p.passage_id != "1.1-c1-s1")
    )
    assert result["supported_pass"] == 19


def test_wrong_snapshot_and_duplicate_ids_are_rejected() -> None:
    suite, passages = fixture()
    with pytest.raises(ValueError, match="snapshot"):
        evaluate_exact_references(
            suite, (passages[0].model_copy(update={"source_snapshot_id": "wrong"}),)
        )
    with pytest.raises(ValueError, match="duplicate"):
        evaluate_exact_references(suite, (*passages, passages[0]))
