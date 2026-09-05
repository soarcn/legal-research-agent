# P5 candidate-coverage diagnosis

The original-query hybrid experiment `p5-coverage-k100-development-v1` requests
100 candidates per retriever and returns 100 fused passages, with alpha 0.25.
It uses the frozen 60-question development split and unchanged source IDs.
The artifact records revision `d7fb0f2`, merged through PR #74.
No validation or holdout questions are used.

Coverage is computed from each case's recorded `exact_passage_rank`:

| Fused depth | Gold passages found | Coverage |
| ---: | ---: | ---: |
| 5 | 21 / 60 | 35.0% |
| 10 | 24 / 60 | 40.0% |
| 20 | 28 / 60 | 46.7% |
| 30 | 31 / 60 | 51.7% |
| 50 | 37 / 60 | 61.7% |
| 100 | 39 / 60 | 65.0% |

These are prefix counts from the same 100-candidate run, not separate
candidate-k experiments: changing retrieval depth can also change rank fusion.
MRR from this diagnostic has depth 100 and should not be compared directly
with the earlier depth-10 MRR.

Even an ideal reranker restricted to these candidates can reach only 65%
Recall@5 on this development set. Increasing reranker capacity alone cannot
reach the 80% gate with these candidates.

The 21 missing development question IDs are: 29, 12, 18, 7, 53, 9, 93, 40,
41, 84, 47, 66, 14, 89, 46, 42, 3, 83, 8, 99, 94.

Next steps under #72: verify those gold passages are present and correctly
represented in the live index; inspect their independent BM25/dense ranks and
the competing passages; distinguish an index defect from semantic mismatch.
Keep the original factual context: the separate query-focus experiment
demonstrated that dropping it reduced retrieval quality. The exact-reference
suite and other P5 acceptance work remain outstanding, and P6 remains blocked.
