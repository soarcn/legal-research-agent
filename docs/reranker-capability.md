# BGE reranker capability

P1.7 validates a pinned local cross-encoder that scores `(query, passage)`
pairs. It is a capability check only: it does not retrieve, reorder a legal
corpus, or establish a relevance-quality metric.

## Fixed contract

`BgeM3RerankerProvider` binds `BAAI/bge-reranker-v2-m3` at commit
`953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`. It lazily loads the local model
off the event loop, caches it, preserves candidate order, and rejects a batch
unless it receives exactly one finite scalar score per passage. The model card
describes this as a cross-encoder that directly scores a query and passage.

The optional model runtime is isolated from the deterministic quality gate:

```bash
uv sync --locked --group reranker
make reranker-smoke
```

The explicit smoke command may download the pinned model on first use. It
scores two fixed non-legal passages and writes an ignored, redacted report at
`artifacts/capability-reports/reranker-bge-m3.json`. The report omits source
text and raw scores. Normal configuration uses local files only, so it does
not make a Hub request during future readiness work.

Changing the model, revision, device, maximum sequence length, or batch size
requires a versioned experiment decision. Candidate-k, final-k, latency, and
retrieval-quality comparison remain P5 work.

## Readiness integration

Set `RERANKER_ENABLED=true` to include a bounded reranker probe in `/ready`.
It scores two fixed non-legal passages and maps unavailable, timeout, loading,
or invalid-output failures to the shared readiness vocabulary without exposing
library details. It does not use legal source text or prove retrieval quality.
Use `make api-with-model-capabilities` to enable it alongside the optional
embedding probe.
