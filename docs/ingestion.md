# Source ingestion

P3.5 ingests the verified, frozen Legal RAG Bench v1 bytes into two distinct stores:

- PostgreSQL receives the authoritative source snapshot, unchanged source passages, benchmark questions, and an observable ingestion-job record.
- Weaviate receives only the derived `LegalPassageV1` search representation: source metadata, unchanged passage text, and a BGE-M3 vector.

The operation never treats the dataset retrieval timestamp as a legal effective date. It preserves the configured source snapshot identifier and source-native passage IDs.

## Run

Start the local services and apply the authoritative schema first:

```bash
make up
make migrate
make dataset-verify
make ingest
```

`make ingest` requires the locally cached, pinned BGE-M3 model. It prints only a job UUID, source snapshot ID, and record counts; it never prints source text or vectors.

## Retry behaviour

Each invocation creates a new PostgreSQL ingestion-job record. Immutable source rows use conflict-safe writes, and Weaviate objects use stable UUIDs derived from the source snapshot and original passage ID. Retrying an interrupted ingestion therefore restores the same derived objects without creating duplicates.

If a source persistence, embedding, or index operation fails, the job records only the safe category (`persistence`, `embedding`, or `index`). Detailed source content and vectors are not stored in error messages.

## Boundaries

- The raw files must first pass `make dataset-verify`.
- PostgreSQL remains authoritative; Weaviate is an index that P3.6 will rebuild independently.
- This command indexes source-native v1 passages unchanged. It does not use P3.2 future-source chunking.
