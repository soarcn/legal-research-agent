# P5 missing-passage rank audit

Scope: the 21 development questions absent from the fused top 100 in
`p5-coverage-k100-development-v1`. Each original question was searched
independently with BM25 and dense retrieval, depth 1000, using the configured
VIC/source-snapshot filters. Local evidence:
`artifacts/p5-missing-rank-audit-v1/audit.json` (questions, gold titles,
independent ranks, competing top-three passage IDs/titles, vector comparison).
This is diagnostic evidence, not a new full-split benchmark score.

All 21 gold texts were re-embedded with the pinned BGE-M3 configuration and
compared to the stored vectors. Cosine similarity was 1.0 within floating-point
roundoff (minimum 0.9999999999999987). Together with the prior exact-text and
snapshot check, this provides no evidence of incorrect vectors for these
passages. It does not establish semantic suitability of the embedding model.

| Question | BM25 rank | Dense rank |
| ---: | ---: | ---: |
| 3 | 179 | 373 |
| 7 | >1000 or absent | >1000 |
| 8 | 568 | 278 |
| 9 | 163 | 56 |
| 12 | >1000 or absent | 523 |
| 14 | 179 | 263 |
| 18 | 107 | 762 |
| 29 | 380 | >1000 |
| 40 | 317 | 47 |
| 41 | 110 | 130 |
| 42 | 150 | 392 |
| 46 | 658 | 28 |
| 47 | 479 | 18 |
| 53 | 190 | 6 |
| 66 | 968 | 5 |
| 83 | 713 | 25 |
| 84 | >1000 or absent | >1000 |
| 89 | >1000 or absent | 31 |
| 93 | 272 | 22 |
| 94 | 646 | 3 |
| 99 | 325 | 2 |

Eleven of these misses are dense top-100 hits, including four in its top six.
Weighted reciprocal-rank fusion at alpha 0.25 suppresses dense-only candidates:
with rank constant 60, a dense-only rank-2 hit scores 0.25/62 = 0.00403,
less than a BM25-only rank-100 hit at 0.75/160 = 0.00469. Therefore truncating
the fused list can discard very strong dense hits before reranking.

The next controlled experiment keeps original questions and model settings
fixed, comparing weighted fusion with a balanced deduplicated candidate list
at the same depth. Balanced selection alternates BM25 and dense ranks, starting
with BM25; each first occurrence is retained until the budget is reached.
Scores and source ranks remain audit metadata; the candidate order is not a
calibrated relevance score. The cross-encoder then ranks that bounded set.

The other ten misses are outside both retrievers' top 100, so candidate
balancing cannot by itself solve all retrieval failures. P5 gates and the
remaining acceptance suites still apply.
