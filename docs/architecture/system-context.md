# System context and target architecture

## Context

The system is a local research application around a frozen legal corpus. It separates authoritative data, derived search indexes, deterministic workflow logic, model adapters, and external evaluation.

```text
Developer / Evaluator
        │
        ├── CLI
        └── REST API /v1
                │
        LegalResearchWorkflow
          ├── scope and input validation
          ├── query router
          ├── retrieval and reranking
          ├── evidence gate
          ├── answer generation
          ├── claim/citation verification
          └── audit recording
                │
      ┌─────────┼───────────────┐
      │         │               │
 PostgreSQL  Weaviate      ModelProvider
 authority   derived       ├── Ollama
 and audit   index         └── OpenAI-compatible / LM Studio

Harbor ── black-box API/CLI evaluation ──> system
```

## Ownership and dependency direction

`LegalResearchWorkflow` owns the use case. PydanticAI may later implement narrowly bounded model interactions, but does not own ingestion, retrieval, filtering, citation integrity, permissions, or persistence.

Dependencies point inward through typed protocols:

```text
FastAPI / CLI
    → application workflow
        → domain protocols and models
            ← PostgreSQL, Weaviate, Ollama, LM Studio adapters
```

API handlers stay thin. They validate transport inputs, call application services, and map results to `/v1` response models. They do not query databases directly.

## Data lifecycle

```text
Pinned source + committed metadata manifest
    → source-passage loader and validation
    → unchanged source passages with source-native IDs
    ├── PostgreSQL provenance/version metadata
    └── embeddings + searchable metadata → versioned Weaviate collection
```

The frozen v1 benchmark does not reconstruct a legal document/version hierarchy that the source does not publish. A separate ingestion path may parse richer future sources into documents, versions, sections, and generated chunks. Those derived chunks never replace the source-passage benchmark unit silently.

PostgreSQL is authoritative. Weaviate contains rebuildable passages, vectors, BM25 fields, and filter metadata. A destructive search-schema change creates a new collection version; it does not mutate the accepted collection in place.

## Retrieval path

```text
Question
    → deterministic scope and reference parsing
    ├── exact-reference metadata lookup
    └── BM25 / dense / hybrid retrieval
            → candidate fusion
            → cross-encoder reranking
            → evidence selection
```

Phase 1 implements this path without Agent planning. P7 later permits at most three generated queries, two retrieval rounds, six tool calls, and eight selected passages.

## Model portability

Business code depends on a model protocol and typed request/response models, not a provider SDK. Configuration supplies provider, base URL, model name, key, timeout, and capabilities. Ollama is the offline default; LM Studio validates a generic OpenAI-compatible adapter. Automated tests use fakes and do not require either runtime.

## Runtime topology

| Component | Location | Reason |
| --- | --- | --- |
| PostgreSQL | Docker | Repeatable relational store |
| Weaviate | Docker | Repeatable derived search service |
| Python API/CLI | macOS host | Fast local development |
| Ollama / LM Studio | macOS host | Apple Silicon acceleration |
| Embedding/reranker | host process | Pin revision, tokenizer, pooling, and device settings |
| Harbor | host, controlling task containers | Independent system evaluation |

## API outline

- `POST /v1/questions`
- `GET /v1/runs/{run_id}`
- `POST /v1/documents/ingest`
- `GET /health` (unversioned process liveness only)
- `GET /ready` (unversioned configured dependency capability checks)

Operational endpoints are unversioned. Business endpoints and resources use `/v1`. The first implementation may expose only the endpoints required by its current phase.

## Security boundary

The model receives read-only, narrow tools only. It never receives shell, Python execution, arbitrary HTTP, SQL, raw Weaviate query, or data-write tools. Retrieved documents are delimited as evidence and treated as untrusted input. Observable actions are audited; private chain-of-thought is neither requested nor stored.
