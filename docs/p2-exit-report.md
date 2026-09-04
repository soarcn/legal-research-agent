# P2 exit report: dataset and legal data model

## Outcome

P2 establishes the data/provenance boundary required before P3 ingestion and
indexing work. It does not index the Legal RAG Bench corpus, infer legal
effective dates, or introduce an Agent loop.

| P2 task | Delivered evidence |
| --- | --- |
| P2.1 Dataset fetch/verify | Pinned-revision CLI validates source-card licence metadata, hashes, counts, JSONL shape, source IDs, and QA references before atomically updating ignored raw files. |
| P2.2 Domain models | Immutable source snapshot, source passage, benchmark question, ingestion job, research-run, and evidence-state contracts. |
| P2.3 Stable identities | Source-native benchmark IDs remain unchanged and snapshot-scoped; future document/version/section/derived-passage IDs are deterministic UUIDs. |
| P2.4 Provenance schema | Alembic migration adds PostgreSQL authority tables for snapshots, passages, questions, ingestion jobs, and observable runs. |
| P2.5 Golden fixtures | Ten fictional documents with nested paths, duplicate text, and two versions of one document exercise hierarchy and version semantics without copying legal text. |
| P2.6 Licence register | Dataset/model selection, observed upstream signals, attribution sources, and non-redistribution rules are recorded in the [licence register](licence-register.md). |

## Acceptance evidence

The P2 deterministic suite proves that fixture inputs yield stable source,
document, version, and section identities; version content changes create a
new version identity; nested paths survive; and duplicate text at different
locations remains distinct. The source snapshot date remains separate from a
synthetic document's legal effective range.

On the P2.6 implementation branch, the quality gate recorded:

```text
make check  -> 111 passed, 3 skipped; Ruff and Pyright clean
make audit  -> no known vulnerabilities
```

The P2.4 real-service migration check separately recorded three selected
integration tests passing against the local PostgreSQL service. It verifies the
new provenance tables alongside the Alembic version table; it does not prove
future P3 ingestion or retrieval behaviour.

## Remaining boundaries

- Legal RAG Bench remains a frozen source-passage benchmark. Re-chunking has a
  separate future-source path and cannot silently alter v1 scoring semantics.
- Its source metadata does not establish legal document versions or historical
  effective dates. A v1 request containing `effective_at` remains unsupported.
- PostgreSQL is the authority for P2 provenance. Weaviate has no P2 data and
  remains a later rebuildable index.
- The P2 work is accepted into the project only when every P2 change is present
  on `main` through reviewed pull requests. This report records branch-level
  implementation evidence; it does not override GitHub review or merge state.

## P3 handoff

P3 may now implement a pure Legal RAG Bench loader, then an idempotent
ingestion service that writes accepted source facts to PostgreSQL and a
versioned derived Weaviate index. Preserve the source passages and IDs exactly
for v1, record the P2 provenance fields on every import, and keep real legal
effective dates unavailable unless a future source supplies them.
