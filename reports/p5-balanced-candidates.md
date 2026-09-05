# P5 balanced candidate experiment

The rank audit found that low-alpha weighted fusion discarded strong dense-only
hits before reranking. This experiment alternates BM25 and dense candidates,
deduplicates by passage ID, and reranks the first 30 retained candidates.
The existing weighted-RRF behavior remains the default; balanced selection is
available explicitly with `--candidate-selection balanced`.

The paired runs fix alpha 0.25, 30 candidates from each retriever, 30 candidates
passed to the cross-encoder, final-k 10, full original queries, and pinned
BGE-M3 / BGE-reranker models. Both use MPS and batch size 4. The runtime-code
revision is `538fe4e`. Only candidate selection differs. Gold source passage IDs
and the 60/20/20 splits are unchanged; holdout unused.

| Development (60 questions) | Recall@5 | Recall@10 | MRR | p95 ms |
| --- | ---: | ---: | ---: | ---: |
| Weighted RRF + reranker | 0.400 | 0.433 | 0.303 | 2511 |
| Balanced candidates + reranker | 0.483 | 0.533 | 0.352 | 2475 |

Six cases newly enter top five (66, 10, 39, 61, 99, 94), while case 34 leaves:
net five additional gold passages. Selection was fixed after this development
comparison, before the paired validation runs.

| Validation (20 questions) | Recall@5 | Recall@10 | MRR | p95 ms |
| --- | ---: | ---: | ---: | ---: |
| Weighted RRF + reranker | 0.200 | 0.250 | 0.140 | 2526 |
| Balanced candidates + reranker | 0.500 | 0.550 | 0.320 | 2919 |

Decision: balanced selection improves this fixed comparison and is available
as an opt-in evaluated configuration. The small validation set gives only
directional evidence; it does not justify production claims. Recall@5 0.500
and MRR 0.320 remain below 0.80/0.60 gates. P5 remains unaccepted and #72 stays
open for residual retrieval misses and the required exact-reference suite.

For example, question 99 asks about a cooling-off interval and the mental state
required for provocation. Its gold source passage is dense rank 2, but low-alpha
fusion previously excluded it. Balanced selection plus reranking returns it
at rank 2. This is retrieval evidence from a fixed research corpus, not a claim
about current law.

Artifacts (ignored local directories): `p5-weighted30-development-v1`,
`p5-balanced30-development-v1`, `p5-weighted30-validation-v1`, and
`p5-balanced30-validation-v1`. Each records model settings, code revision,
original queries, full split identity, per-case ranks, and aggregate metrics.

Reproduce with a new experiment ID (existing directories cannot be overwritten):

```bash
PYTHONPATH=src uv run --group embedding --group reranker python scripts/run_retrieval_baseline.py \
  --mode hybrid-rerank --split development --top-k 10 --alpha 0.25 \
  --candidate-k 30 --candidate-selection balanced --experiment-id YOUR_NEW_ID
```

Demo:

```bash
PYTHONPATH=src uv run --group embedding --group reranker python scripts/demo_retrieval.py \
  'After a grave insult, Jordan cools off for several hours, then calmly returns and kills. Which state of mind required for provocation is missing on these facts, and what is the technical term for it?' \
  --mode hybrid-rerank --candidate-k 30 --candidate-selection balanced --alpha 0.25
```

The demo reports total retrieval-plus-reranker latency. Relevance scores are
model ranking signals, not probabilities of legal correctness.
