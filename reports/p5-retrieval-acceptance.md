# P5 retrieval acceptance report

## Decision

**Core P5 components are implemented; P5 acceptance work is incomplete.** The
hybrid, exact-reference, reranker, and rule-first router capabilities are in
place and exercised locally. The frozen v1 validation results do not meet the
project's retrieval gates, so P6 must not begin as though retrieval quality
were accepted.

This report does not consume the holdout split.

## Fixed experiment conditions

- Corpus: `legal-rag-benchmark-v1`, source snapshot
  `legal-rag-bench@db0b31dc6d195ce9916897e1ac5e4e6209736c8a`.
- Code revision: `f02cda4` (the evaluator records its full SHA in each local
  artifact).
- Dense retrieval: pinned BGE-M3 source-index contract.
- Hybrid: weighted reciprocal-rank fusion, 30 candidates, returned top 10.
- Reranker: pinned BGE reranker, top 10 from the hybrid candidate set.
- Splits: development for choosing `alpha`; frozen validation for acceptance.
  Holdout was not run.

Raw per-case artifacts are local and ignored by Git. Their experiment IDs are
listed below so the work can be reproduced without overwriting a result.

## Hybrid selection on development

| Alpha (dense weight) | Recall@5 | MRR | nDCG@10 | p95 latency |
| ---: | ---: | ---: | ---: | ---: |
| 0.25 | 0.350 | 0.249 | 0.282 | 460 ms |
| 0.50 | 0.350 | 0.236 | 0.283 | 483 ms |
| 0.75 | 0.350 | 0.232 | 0.280 | 453 ms |

`alpha=0.25` was selected because it has the best development MRR. Artifacts:
`p5-hybrid-a025-development-v1`, `p5-hybrid-a050-development-v1`, and
`p5-hybrid-a075-development-v1`.

## Frozen validation result

| Method | Recall@5 | MRR | nDCG@10 | p95 latency |
| --- | ---: | ---: | ---: | ---: |
| Hybrid, alpha 0.25 | 0.250 | 0.112 | 0.145 | 534 ms |
| Hybrid + reranker, 10 candidates | 0.250 | 0.192 | 0.207 | 1,015 ms |

Hybrid artifact: `p5-hybrid-a025-validation-v2`. Reranker artifact:
`p5-rerank-k10-b1-validation-v1`.

The reranker improves the position of retrieved gold passages, but cannot
recover a gold passage absent from the hybrid top-10 candidate set; therefore
Recall@5 is unchanged. Its roughly 1.9x p95 latency is expected for a local
cross-encoder and is recorded rather than treated as a pass/fail gate.

## Exact references and query routing

The v1 resolver correctly handles only source-native dotted references (for
example `section 8.1.2`). It explicitly returns `unsupported` for statute and
case citations because Legal RAG Bench does not provide authoritative metadata
for those citations. Unit coverage verifies supported, missing, and
unsupported paths; it is not the planned 20-case exact-reference suite, so it
does **not** establish the `>= 0.95` exact-reference gate.

The router is deterministic: dotted references use exact lookup; only clear
two- or three-part English questions are decomposed; all other requests use a
single semantic query. It does not use a model or an Agent loop.

## Runtime evidence correction

The earlier version of this report incorrectly interpreted partial command
output as a process exit. Inspection now confirms complete 60-case artifacts:
`p5-rerank-k10-development-v1` (batch 4) and
`p5-rerank-k10-development-v3` (batch 1), both with Recall@5 0.317 and MRR
0.276. There is no established batch-size runtime failure from those runs.
The validation artifact above predates full runtime-configuration capture;
its batch size 1 is supported by the recorded command, not its JSON identity.

Also, the table above compares hybrid candidate-k 30 with reranker retrieval
candidate-k 10. It is descriptive, not a controlled reranker-only ablation;
equal aggregate recall does not prove that the candidate sets are equal.
Future comparisons must fix retrieval depth when measuring reranker benefit.

The subsequent [query-focus experiment](p5-query-focus-experiment.md) rejected
discarding background facts after a controlled development regression.

## Gate assessment and next action

| Gate | Required | Observed validation | Status |
| --- | ---: | ---: | --- |
| Recall@5 | >= 0.80 | 0.250 | Not met |
| MRR | >= 0.60 | 0.192 (reranked) | Not met |
| Exact-reference accuracy | >= 0.95 | Not yet measured on its required suite | Not established |

The next backlog item is **retrieval failure analysis and remediation**, not
P6 answer generation. Likely investigation areas are source-passage retrieval
limits, hybrid candidate coverage, query normalization, and a versioned exact
reference test suite. Any new experiment must keep the v1 source-passage IDs
unchanged and must not tune against holdout.
