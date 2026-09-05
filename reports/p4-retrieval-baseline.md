# P4 retrieval baseline report

## Scope

This report records the first reproducible retrieval-only baselines over the
frozen `legal-rag-benchmark-v1` source-passage corpus. It uses the P4 fast
evaluator, a rebuilt derived Weaviate index, and no generation model or Agent.
The 20-question holdout was not loaded or run.

## Configuration

- corpus: `legal-rag-bench@db0b31dc6d195ce9916897e1ac5e4e6209736c8a`;
- retrieval unit: unchanged Legal RAG Bench source passage;
- jurisdiction: `VIC`;
- index: `LegalPassageV1`, rebuilt from the pinned raw snapshot;
- BM25: Weaviate BM25, top-k 10;
- dense: pinned BGE-M3, normalised 1024-dimensional vectors, Weaviate flat
  vector index, top-k 10;
- code revision: `a0d2153` for the formal run artifacts.

## Results

| Split | Method | Recall@1 | Recall@5 | Recall@10 | MRR | nDCG@10 | p50 / p95 latency |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Development (60) | BM25 | 0.183 | 0.283 | 0.367 | 0.227 | 0.260 | 167 / 188 ms |
| Development (60) | Dense | 0.133 | 0.333 | 0.383 | 0.214 | 0.255 | 239 / 268 ms |
| Validation (20) | BM25 | 0.050 | 0.200 | 0.250 | 0.121 | 0.152 | 161 / 182 ms |
| Validation (20) | Dense | 0.100 | 0.350 | 0.350 | 0.171 | 0.215 | 236 / 379 ms |

Detailed, schema-versioned aggregate and per-case artifacts are local and
ignored under `artifacts/retrieval-*-{development,validation}-v1/`.

## Interpretation

Neither baseline meets the P5 acceptance targets of Recall@5 >= 0.80 and MRR
>= 0.60. This is an expected starting point, not a failed experiment: it shows
that simple lexical or vector-only search is insufficient for these legal
questions. Dense retrieval has better Recall@5 and Recall@10 on both splits;
BM25 is faster and has better development Recall@1/MRR. The next controlled
variable is hybrid retrieval, followed by reranking; no prompt or generation
change is implicated in these metrics.

## Limitations and next action

The validation split is small (20 questions), so these are directional
comparisons rather than a final quality claim. The v1 holdout remains unused.
P5 will compare BM25+dense fusion and reranking under the same corpus, split,
top-k, evaluator, and artifact protocol.
