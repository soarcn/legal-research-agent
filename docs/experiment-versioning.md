# Experiment versioning

## Required identity

Every formal experiment has an immutable `experiment_id` and records:

- Git commit or source snapshot identifier;
- corpus manifest and SHA-256;
- benchmark and split version;
- chunker strategy/version and token settings;
- embedding model, exact revision, tokenizer, pooling, normalization, dimension, batch size, and device;
- retrieval mode, filters, fusion method/weight, candidate count, and top-k;
- reranker model/revision and final-k;
- generator/provider/model and capability settings when applicable;
- prompt/schema versions when applicable;
- runtime, latency, memory, and disk measurements.

## Storage

```text
config/experiments/<experiment_id>.toml   committed immutable configuration
reports/<experiment_id>.md                committed summary and failure analysis
artifacts/<experiment_id>/                ignored detailed outputs and traces
```

Formal experiments never overwrite an existing directory or report. A rerun uses a run suffix and links back to the same immutable configuration.

## Example

```toml
experiment_id = "retrieval-hybrid-001"
corpus_manifest = "data/manifests/legal-rag-bench-v1.json"
benchmark = "legal-rag-benchmark-v1"
split = "development"

[chunking]
strategy = "source-passages"
version = "1"

[embedding]
model = "BAAI/bge-m3"
revision = "PIN_BEFORE_RUN"
normalized = true

[retrieval]
mode = "hybrid"
alpha = 0.5
candidate_k = 30
final_k = 5
```

Placeholders such as `PIN_BEFORE_RUN` invalidate a formal experiment until resolved.
