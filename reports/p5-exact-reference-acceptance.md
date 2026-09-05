# P5 exact-reference acceptance

`exact-reference-v1` was run against all 4,876 verified source passages at
revision `31f047b57b15e14c515c12d080b86d5c2da06ec0`.

| Metric | Result | Requirement |
| --- | ---: | ---: |
| Supported exact-section accuracy | 20/20 = 1.00 | >= 0.95 |
| Boundary-case accuracy (separate) | 10/10 = 1.00 | All authored regressions pass |

Artifact: `artifacts/exact-reference-v1-run1/result.json`.
Suite SHA-256: `15b55448f5b41ebc4f7fce2673bd7e6174648caa26ccec8f7bc28aaab918ab80`.
Corpus SHA-256: `3a3565bc5429f6cead90548e81f87352b449927e4be1cdd804c28d766bb9c246`.

This meets the narrow supported source-section lookup gate on the authored
suite. Each positive case requires the complete exact ID set, with no extra
passages. Boundary cases are not pooled into the positive accuracy metric.
The source-ID review was performed by Codex and is not independent legal
review. Cases contain no benchmark questions or answers; holdout remains unused.

See [suite documentation](../evals/exact_references/README.md) for reproduction,
gold provenance, and coverage. This evaluates the resolver against verified
source data, not a network API or query-router integration. It makes no claim
about resolving arbitrary statutory/case citations, answering legal questions,
or achieving natural-language Recall@5. Overall P5 remains unaccepted.
