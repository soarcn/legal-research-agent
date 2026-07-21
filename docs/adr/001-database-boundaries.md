# ADR-001: PostgreSQL authority and Weaviate derived index

- Status: Accepted
- Date: 2026-07-21

## Context

Legal research requires provenance, version relationships, repeatable ingestion, run audit, and search. A vector database alone is a poor system of record; duplicating all search functions in PostgreSQL would reduce the intended Weaviate learning scope.

## Decision

PostgreSQL is authoritative for documents, versions, source snapshots, ingestion jobs, experiment/run records, prompt/model configuration, retrieval traces, and citations. Weaviate stores rebuildable searchable passages, vectors, BM25 fields, and duplicated filter metadata.

Raw source files and manifests are the reconstruction inputs. Deleting Weaviate must not lose authoritative legal or audit data. PostgreSQL changes use Alembic; incompatible Weaviate changes create a new explicit index version.

## Consequences

- Search metadata is deliberately duplicated and must be derived consistently.
- Rebuild and consistency checks are mandatory.
- The Agent never receives raw database query tools.
- More infrastructure is accepted in exchange for realistic data and audit boundaries.
