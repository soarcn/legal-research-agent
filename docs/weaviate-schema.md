# Weaviate v1 derived-index schema

`LegalPassageV1` is the first planned Weaviate collection for the frozen Legal
RAG Bench source-passage benchmark. It is an explicit, rebuildable derived
index, not a legal system of record; PostgreSQL and the raw verified snapshot
remain authoritative.

| Area | v1 decision |
| --- | --- |
| Collection and index version | `LegalPassageV1` / `legal-passage-v1` |
| Vector index | Flat exact search, appropriate for the 4,876-passage baseline |
| Vector generation | `none` in Weaviate; the P3.3 pinned BGE-M3 adapter supplies 1,024-dimensional vectors |
| BM25 fields | `title`, `text`, `footnotes` |
| Filter fields | `sourceSnapshotId`, `passageId`, `contentSha256`, `jurisdiction`, `language` |

The schema deliberately excludes document-version and legal-effective-date
fields: Legal RAG Bench v1 does not publish metadata that supports them. The
source snapshot ID identifies the benchmark acquisition, not current law.

P3.4 defines this contract only. P3.5 will create the collection, validate it
against this contract, and write idempotent derived objects. A vector dimension
or incompatible-property change requires a new collection/index version, never
an in-place mutation of the accepted v1 collection.
