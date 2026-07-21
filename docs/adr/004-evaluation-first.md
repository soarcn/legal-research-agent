# ADR-004: Deterministic, layered evaluation first

- Status: Accepted
- Date: 2026-07-21

## Context

RAG and Agent behaviour is probabilistic, but many critical properties—passage rank, citation existence, offsets, schema validity, and tool budgets—are deterministic. A single aggregate reward or LLM judge would hide failure causes.

## Decision

Use `pytest` for code and data invariants, a fast evaluator for retrieval experiments, pipeline evaluation for answer/citation behaviour, and Harbor for end-to-end Agent and adversarial regression. Metrics remain separate. LLM judges are auxiliary and versioned.

Legal RAG Bench is pinned and split 60/20/20 for this private project. Development is used for tuning, validation for acceptance, and holdout only at P8 after the full safety suite passes. Results and benchmark changes are append-only and versioned. Routine regression excludes holdout; formal holdout requires explicit audited authorization.

## Consequences

- Evaluation tooling is a first-class deliverable.
- Development is slower initially but changes become explainable.
- Holdout discipline is procedural, because IDs are present in the repository.
- Public reporting must disclose that the split is project-defined.
