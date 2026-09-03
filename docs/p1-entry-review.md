# P1 entry review

- Decision: **Go for P1 development**
- Review date: 2026-08-31
- Scope: readiness of P0 decisions and artifacts, not completion of P1

## Entry evidence

- Scope, non-goals, architecture boundaries, quality gates, risks, and phase backlog are versioned.
- The owner accepted all P0 operating defaults and the decisions in ADR-006 and ADR-007.
- `legal-rag-benchmark-v1` is pinned to revision `db0b31dc6d195ce9916897e1ac5e4e6209736c8a`.
- The committed metadata manifest records the verified local corpus/QA hashes and counts without redistributing raw data.
- Development, validation, and holdout manifests contain 60/20/20 unique question IDs covering IDs 1–100 exactly once.
- The source-passage benchmark unit and richer future document/chunking model are explicitly separated.
- Evidence metrics include both unsupported-case abstention and supported-case answer rate.
- Domain language distinguishes Source Snapshot, Source Passage, Legal Document, Research Run, Agent Step, and Consumed Holdout.
- Current deterministic lint, type, unit-test, and Compose-configuration checks pass.

## P1 boundary

P1 establishes local runtime, quality automation, database connectivity, model-provider contracts, capability smoke tests, and operational health/readiness endpoints. It does not introduce legal domain tables, corpus ingestion, retrieval algorithms, answer generation, PydanticAI orchestration, or Agent tools.

The P1 Alembic revision is an empty baseline by design. The first accepted domain tables are introduced in P2 after source identity and provenance contracts are implemented. If a local development database previously applied an earlier draft of revision `0001_initial`, its disposable Docker volume must be recreated through the documented P1 reset procedure before migration verification; this review does not authorize deletion automatically.

## P1 starting order

1. Finish P1.1 quality/CI and secret-scan configuration.
2. Verify P1.2 PostgreSQL and Weaviate lifecycle, health checks, volumes, and safe reset documentation.
3. Complete P1.3 async SQLAlchemy connection/transaction tests and Alembic baseline verification.
4. Complete unversioned `/health`, then provider contracts and capability smoke tests.
5. Add unversioned `/ready` only after its dependency checks exist.

P1 exits only when the clean-machine workflow and all P1 deterministic/smoke checks pass. The current `Go` decision authorizes starting P1; it is not a claim that P1 has already passed.

P1 exit evidence and the formal phase decision are recorded in the
[P1 exit report](p1-exit-report.md).
