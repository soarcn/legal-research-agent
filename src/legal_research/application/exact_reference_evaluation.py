"""Deterministic scoring for a separately versioned exact-reference suite."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from legal_research.application.exact_reference import ExactReferenceResolver, ExactReferenceStatus
from legal_research.domain import SourcePassage


class ExactReferenceCase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    case_id: str
    reference: str
    expected_status: ExactReferenceStatus
    expected_passage_ids: tuple[str, ...]

    @model_validator(mode="after")
    def consistent_gold(self) -> "ExactReferenceCase":
        ids = self.expected_passage_ids
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate gold passage IDs")
        if bool(ids) != (self.expected_status == ExactReferenceStatus.RESOLVED):
            raise ValueError("only resolved cases must have gold passages")
        return self


class ExactReferenceSuite(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    suite_id: str
    source_snapshot_id: str
    author: str
    reviewer: str
    gold_method: str
    cases: tuple[ExactReferenceCase, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_cases(self) -> "ExactReferenceSuite":
        if len({case.case_id for case in self.cases}) != len(self.cases):
            raise ValueError("duplicate case IDs")
        if not any(c.expected_status == ExactReferenceStatus.RESOLVED for c in self.cases):
            raise ValueError("suite requires supported reference cases")
        return self


def evaluate_exact_references(
    suite: ExactReferenceSuite, passages: tuple[SourcePassage, ...]
) -> dict[str, object]:
    """Require exact status and full ID set; score supported and boundary cases separately."""
    if not passages or any(p.source_snapshot_id != suite.source_snapshot_id for p in passages):
        raise ValueError("all passages must belong to the suite snapshot")
    if len({p.passage_id for p in passages}) != len(passages):
        raise ValueError("duplicate source passage IDs")
    resolver = ExactReferenceResolver()
    rows: list[dict[str, object]] = []
    supported_pass = supported_count = boundary_pass = boundary_count = 0
    for case in suite.cases:
        result = resolver.resolve(case.reference, passages)
        passed = result.status == case.expected_status and set(result.passage_ids) == set(
            case.expected_passage_ids
        )
        if case.expected_status == ExactReferenceStatus.RESOLVED:
            supported_count += 1
            supported_pass += int(passed)
        else:
            boundary_count += 1
            boundary_pass += int(passed)
        rows.append(
            {
                "case_id": case.case_id,
                "passed": passed,
                "actual_status": result.status.value,
                "actual_passage_ids": result.passage_ids,
            }
        )
    return {
        "suite_id": suite.suite_id,
        "source_snapshot_id": suite.source_snapshot_id,
        "supported_count": supported_count,
        "supported_pass": supported_pass,
        "supported_accuracy": supported_pass / supported_count,
        "boundary_count": boundary_count,
        "boundary_pass": boundary_pass,
        "boundary_accuracy": boundary_pass / boundary_count if boundary_count else None,
        "cases": rows,
    }
