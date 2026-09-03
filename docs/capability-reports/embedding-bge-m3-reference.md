# BGE-M3 reference capability report

**Report schema:** `1`  
**Run date:** 2026-09-03  
**Reference platform:** macOS Apple Silicon, M5 Max, 48 GB unified memory

## Result

The opt-in `make embedding-smoke` run passed. It explicitly permitted the
pinned model download, then loaded and reused the dense BGE-M3 model without
accessing legal source passages or an index. Normal application readiness runs
from the local cache only.

| Observation | Result |
| --- | ---: |
| Model revision | `3806044eb869c8756693584f7eb5dd04ab2bdd95` |
| Runtime | sentence-transformers 5.7.0; torch 2.14.0 |
| Device | `mps` |
| Expected/observed dimension | 1024 / 1024 |
| First embedding latency | 9,442.16 ms |
| Cached repeat latency | 15.59 ms |
| Process peak RSS after run | 925,024,256 bytes |
| Model-cache observation | 4,586,489,872 bytes |

The local JSON artifact is ignored by Git. It contains the same safe summary
plus the exact command-time configuration. Neither artifact contains vectors,
legal passages, cache paths, API keys, or raw provider exceptions.

## Interpretation

This proves the reference host can load the selected revision and return a
finite 1024-dimensional dense vector through the application adapter. It is
not a claim about retrieval quality, semantic accuracy, benchmark performance,
or future production latency.
