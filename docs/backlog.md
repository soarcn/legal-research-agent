# P1–P9 epic backlog

Each task follows the repository Definition of Done. IDs encode epic and sequence; dependencies are explicit.

The backlog is dependency-driven and intentionally contains no time estimates. AI may accelerate drafting, but phase exits depend on tests, evaluation, failure analysis, and documentation—not elapsed time or generated code volume.

## P1 — Local environment

**Goal:** start and verify the complete local topology.

| Task | Depends on | Output and acceptance |
| --- | --- | --- |
| P1.1 Repository quality setup | P0 | Git/CI-ready Ruff, type checker, pytest, coverage and secret-scan config |
| P1.2 PostgreSQL and Weaviate runtime | P1.1 | Compose services, health checks, persistent volumes, documented reset path |
| P1.3 Database bootstrap | P1.2 | SQLAlchemy engine, Alembic baseline, connection/transaction test; no premature domain tables |
| P1.4 `/health` | P1.2–P1.3 | Unversioned process liveness without external dependency calls |
| P1.5 Model provider contracts | P1.1 | Typed protocol, fake provider, configuration model |
| P1.6 Ollama and LM Studio smoke tests | P1.5 | Text and structured-output capability report for both providers |
| P1.7 Embedding/reranker smoke tests | P1.1 | Pinned model revisions, dimension/score checks, resource report |
| P1.8 `/ready` | P1.2–P1.7 | Unversioned conditional readiness for Postgres, Weaviate, configured model, embedder, and reranker |

**Exit:** clean-machine setup starts infrastructure and all deterministic/smoke tests pass.

## P2 — Dataset and legal data model

**Goal:** represent provenance, identity, structure, and version semantics before indexing.

| Task | Depends on | Output and acceptance |
| --- | --- | --- |
| P2.1 Dataset fetch/verify CLI | P1.1 | Pinned revision download, counts/hashes/licence validation |
| P2.2 Domain models | P0 | `SourceSnapshot`, `SourcePassage`, `BenchmarkQuestion`, `ResearchRun`, `IngestionJob`; richer legal entities only where source metadata supports them |
| P2.3 Stable ID specification | P2.2 | Deterministic IDs with repeated-run tests |
| P2.4 First domain schema | P1.3, P2.2 | Alembic migration for accepted provenance, source-passage, ingestion, and research-run entities |
| P2.5 Golden corpus fixtures | P2.2–P2.3 | Nested sections, duplicates, and two-version cases |
| P2.6 Licence register | P2.1 | Dataset/model/source attribution and redistribution rules |

**Exit:** repeated processing of golden inputs produces identical IDs, hashes, and valid relationships.

## P3 — Ingestion and index

**Goal:** build an idempotent, recoverable, auditable ingestion pipeline.

| Task | Depends on | Output and acceptance |
| --- | --- | --- |
| P3.1 Legal RAG Bench loader | P2.1–P2.2 | Pure validation/loader returning unchanged Source Passages |
| P3.2 Future-source chunker | P2.3, P2.5 | Separate synthetic/future-corpus path; no cross-section splits and offsets round-trip |
| P3.3 Embedding adapter | P1.7, P3.1 | BGE-M3 batches over unchanged v1 Source Passages with fixed dimension/revision/settings |
| P3.4 Weaviate v1 schema | P1.2, P2.2 | Flat-vector baseline, BM25 fields, metadata filters, versioned collection |
| P3.5 Ingestion service and CLI | P2.4, P3.1, P3.3–P3.4 | Job state, idempotency, isolated failures, report |
| P3.6 Rebuild command | P3.5 | Delete/recreate derived index with stable expected IDs/counts |

**Exit:** two imports and a full index rebuild produce the same accepted corpus representation.

## P4 — Retrieval baselines

**Goal:** measure retrieval without generation or Agent behaviour.

| Task | Depends on | Output and acceptance |
| --- | --- | --- |
| P4.1 Benchmark loader | P2.1 | Split-aware QA loader preventing accidental holdout runs |
| P4.2 BM25 retriever | P3.5 | Ranked results over an ingested pinned corpus and configuration snapshot |
| P4.3 Dense retriever | P3.3–P3.5 | Query embeddings match the ingested corpus settings |
| P4.4 Fast evaluator | P3.6, P4.1–P4.3 | Recall@k, MRR, nDCG, latency, per-case JSON on a reproducibly rebuilt index |
| P4.5 Baseline report | P4.4 | BM25 vs dense metrics plus categorized failures |

**Exit:** reproducible development results explain the main failures of both baselines.

## P5 — Production-shaped retrieval

**Goal:** improve evidence recall and ranking through controlled experiments.

| Task | Depends on | Output and acceptance |
| --- | --- | --- |
| P5.1 Hybrid fusion | P4 | Alpha/fusion experiments with one-variable comparisons |
| P5.2 Exact-reference resolver | P2.2, P4 | Deterministic supported-reference lookup and test set |
| P5.3 BGE reranker | P1.7, P5.1 | Candidate-k/final-k experiments and latency profile |
| P5.4 Rule-first query router | P5.1–P5.2 | `EXACT_REFERENCE`, `SEMANTIC_QUESTION`, `MULTI_PART_QUESTION` |
| P5.5 Validation acceptance report | P5.1–P5.4 | Complete: report records unmet Recall@5/MRR gates and the next retrieval-remediation work; P6 remains blocked |

**Exit:** retrieval gates are met before answer generation begins.

## P6 — Reliable cited RAG MVP

**Goal:** produce concise answers controlled by verified evidence, without an open Agent loop.

| Task | Depends on | Output and acceptance |
| --- | --- | --- |
| P6.1 Context builder | P5 | Deduped, delimited, token-bounded evidence |
| P6.2 Claim/citation schemas | P2.2 | Typed answer, claims, evidence state, readable/internal citations |
| P6.3 Evidence gate | P6.1–P6.2 | Supported/partial/unsupported/conflicting outcomes |
| P6.4 Answer generator | P1.5–P1.6, P6.3 | Same workflow over Ollama and LM Studio adapter |
| P6.5 Citation verifier | P6.2–P6.4 | ID/version/quote/offset/evidence membership checks |
| P6.6 CLI and `POST /v1/questions` | P6.3–P6.5 | Demonstrable answer and abstention paths |
| P6.7 Reliability evaluation | P6.6 | Citation, unsupported-claim, abstention, supported-answer, confusion-matrix, and schema metrics |

**Exit:** all P6 reliability gates pass; this is the Legal RAG MVP milestone.

## P7 — Constrained Agent

**Goal:** add only dynamic retrieval decisions that demonstrate measurable value.

| Task | Depends on | Output and acceptance |
| --- | --- | --- |
| P7.1 PydanticAI integration | P6 | Agent contained inside `LegalResearchWorkflow` |
| P7.2 Typed read-only tools | P7.1 | Search, exact resolve, passage/metadata fetch, submit answer |
| P7.3 Budgets and policy | P7.2 | 2 retrieval rounds, 6 tool calls, 3 queries, 8 passages |
| P7.4 Query rewrite/decomposition | P7.2–P7.3 | Behaviour cases for when to retry or split |
| P7.5 Observable trace | P2.4, P7.2 | Queries, tool args/results, evidence, retries; no chain-of-thought |
| P7.6 Pipeline vs Agent report | P7.1–P7.5 | No safety gate regression; quality benefit or Agent removal |

**Exit:** no budget violation; tool/argument gates pass; result is no worse than P6 baseline.

## P8 — Harbor evaluation

**Goal:** run isolated, repeatable black-box Agent regression.

| Task | Depends on | Output and acceptance |
| --- | --- | --- |
| P8.1 Harbor adapter | P7 | CLI/API adapter with artifact contract |
| P8.2 Task generator | P4.1, P8.1 | Versioned Harbor tasks from project test suites |
| P8.3 Deterministic verifier | P8.2 | Multi-metric `reward.json`, not opaque reward only |
| P8.4 Safety gate | P7.6, P8.1–P8.3, P9.1 | Full versioned red-team suite passes before release-candidate freeze |
| P8.5 Experiment matrix | P8.1–P8.4 | Pipeline/Agent, model size, reranker, rounds, prompt comparisons on non-holdout suites |
| P8.6 Holdout guard and audit | P4.1, P8.3 | Default exclusion, `--allow-holdout` opt-in, operator/reason/config audit, rerun refusal |
| P8.7 Holdout final run | P8.5–P8.6 | Explicitly authorized first/final 20-case holdout report; mark consumed and do not treat reshuffles as fresh holdout |
| P8.8 One-command regression | P8.1–P8.7 | Default command excludes holdout; separate formal-holdout command is documented |

**Exit:** formal benchmark report and comparable artifacts exist for the frozen configuration.

## P9 — Safety, observability, and delivery

**Goal:** make the project safe to demonstrate, explain, reproduce, and prepare for release.

| Task | Depends on | Output and acceptance |
| --- | --- | --- |
| P9.1 Versioned red-team suite | P7 | 10 prompt injection, 5 tool misuse, 5 conflict, 5 historical, and 5 out-of-scope cases; prerequisite to P8 holdout |
| P9.2 Temporal/conflict experiment | P2, P6 | Separate versioned fixtures and correct scope limitations |
| P9.3 Structured observability | P6–P7 | Request/retrieval/rerank/generation/verification timings and IDs |
| P9.4 Resource and cleanup tooling | P3–P8 | Disk report, temporary artifact cleanup, formal-result protection |
| P9.5 Known limitations and demo | P6–P9 | Five documented demo scenarios and honest limits |
| P9.6 Release audit | P9.1–P9.5 | Open-source checklist, licence, notice, security scans |

Any P9 discovery that changes behavioural code or configuration invalidates the current release candidate. It must pass validation and safety again and use a new benchmark/release-candidate version rather than rerunning the consumed v1 holdout silently.

**Exit:** the system answers where evidence exists, refuses safely, explains its observable evidence path, reproduces results, and passes the private-to-open release gate.
