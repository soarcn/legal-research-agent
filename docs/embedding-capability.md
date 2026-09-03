# BGE-M3 embedding capability

P1 validates that the reference machine can create **dense**, normalised BGE-M3
embeddings. This is a runtime capability check, not corpus ingestion or a
retrieval-quality experiment.

## Boundary

`BgeM3EmbeddingProvider` is an async application boundary around the host
`sentence-transformers` runtime. It binds one model configuration; callers
cannot choose a model or revision per request. The configuration pins:

- model ID `BAAI/bge-m3`;
- Hub commit `3806044eb869c8756693584f7eb5dd04ab2bdd95`;
- dense pooling, normalisation, device, batch size, and maximum sequence length;
- expected dimension `1024`, which is a future Weaviate index contract.

The adapter loads lazily off the event loop, caches the model, applies the
configured maximum sequence length, and rejects an entire response if its
vector count, dimension, or numeric values are invalid. It applies
normalisation itself after validation, so the vector-space contract does not
depend on an SDK option. It does not load source passages, create an index, or
calculate retrieval metrics. The BGE-M3 model card documents
`SentenceTransformer` as a supported loading path and is the source for this
model selection.

## Installation and smoke check

The heavyweight runtime is optional so the normal deterministic gate remains
model-free:

```bash
uv sync --locked --group embedding
make embedding-smoke
```

The first command may download Python runtime packages. The smoke command
explicitly permits one download of the pinned model if it is not already in the
local Hugging Face cache. It may take several minutes and needs several GB of
disk space. Normal application configuration uses `local_files_only=true`, so
readiness does not make outbound Hub requests after that setup. The smoke test
is never run by `make check` or CI.

The command writes the ignored report
`artifacts/capability-reports/embedding-bge-m3.json`. It records the model and
package identities, safe settings, first and cached latency, process peak RSS,
cache-size observation, vector count and dimension checks. It deliberately
omits vectors, source passages, local cache paths, credentials, and raw SDK
exceptions.

## Configuration

`.env.example` contains the supported `EMBEDDING__...` overrides. Keep the
revision as a 40-character commit SHA; changing it, dimensions, normalisation,
or pooling changes the later index contract and needs a versioned experiment
decision. `mps` is the reference Apple Silicon device. Use `cpu` only for a
documented troubleshooting run.

## Readiness and failure semantics

`EmbeddingReadinessProbe` runs one fixed non-legal sentinel through the
configured provider. Set `EMBEDDING_ENABLED=true` to add it to `/ready`; it is
disabled by default until the remaining P1 generator and reranker capability
work has been accepted. This keeps normal local API bootstrap independent of
optional model packages. The probe maps internal failures to the safe shared
readiness vocabulary:

| Internal category | `/ready` status |
| --- | --- |
| unavailable | `failed` |
| timeout | `timed_out` |
| load failure, invalid output, transport error | `error` |

The common readiness service owns external diagnostics and never returns raw
model-library errors. P1 exit enables it together with the generation and
reranker probes.

## Troubleshooting

| Observation | Meaning | Safe action |
| --- | --- | --- |
| Report says `unavailable` | Package, cache, or Hub access is unavailable. | Run the optional-group sync; check network access without sharing tokens. |
| Report says `load_failure` | The model runtime could not initialise with the configured settings. | Check the pinned revision and device; retry once with `EMBEDDING__DEVICE=cpu`. |
| Report says `invalid_output` | The provider returned vectors that violate the index contract. | Do not ingest data; preserve the report and investigate package/model compatibility. |
| Disk budget grows unexpectedly | Model/cache artefacts are consuming storage. | Inspect the local cache and remove only explicitly disposable artefacts; do not delete formal reports automatically. |
