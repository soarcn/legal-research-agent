# Licence register

This register records the licence signals observed for assets intentionally
selected by this project. It is an engineering record, not legal advice or a
substitute for a release-time licence review.

## Rules that apply to every entry

- The repository contains source code and small fictional fixtures only. It
  does not redistribute raw Legal RAG Bench files, model weights, model caches,
  vector indexes, or database volumes.
- A pinned revision identifies a reproducible technical input. It does not
  replace the upstream licence or establish that later changes carry the same
  terms.
- Before making the repository public, rerun the source checks, generate the
  dependency notice from the locked environment, and complete the
  [open-source release checklist](open-source-release-checklist.md).

## Selected data and models

| Asset | Pinned selection | Observed upstream licence signal | Project handling and redistribution rule | Source |
| --- | --- | --- | --- | --- |
| Legal RAG Bench | `isaacus/legal-rag-bench` at `db0b31dc6d195ce9916897e1ac5e4e6209736c8a` | Dataset metadata: `CC BY-NC-SA 4.0`; the dataset-card prose has a conflicting `CC BY-NC 4.0` statement. | Apply the stricter `CC BY-NC-SA 4.0` policy unless the publisher clarifies the discrepancy. Keep the project non-commercial and do not commit or redistribute raw/derived corpus content. The fetch command retrieves the pinned upstream files into ignored `data/raw/`. | [Dataset revision](https://huggingface.co/datasets/isaacus/legal-rag-bench/tree/db0b31dc6d195ce9916897e1ac5e4e6209736c8a) |
| BGE-M3 embedding weights | `BAAI/bge-m3` at `3806044eb869c8756693584f7eb5dd04ab2bdd95` | Model card: `MIT`. | Download only into the local Hugging Face cache; never commit or redistribute weights. Reconfirm the card and exact revision before a public release. | [Model card](https://huggingface.co/BAAI/bge-m3) |
| BGE reranker weights | `BAAI/bge-reranker-v2-m3` at `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e` | Model card: `Apache-2.0`. | Download only into the local Hugging Face cache; never commit or redistribute weights. Reconfirm the card and exact revision before a public release. | [Model card](https://huggingface.co/BAAI/bge-reranker-v2-m3) |
| Synthetic golden fixtures | `evals/golden_documents/v1.json` | Project-authored fictional content. | May be committed and redistributed with the application code. It is not legal source material and cannot be used as a substitute for benchmark data. | [Fixture readme](../evals/golden_documents/README.md) |

## Application and dependency status

The intended application-code licence is Apache License 2.0, but the
repository is private and has not yet passed its public-release gate. Adding a
`LICENSE` and `NOTICE` file is therefore an explicit release prerequisite, not
an implied present-state assertion.

Python packages are resolved in `uv.lock`. Their licences and transitive
notices are not assumed from direct dependencies or copied into this document.
The release owner must generate and review a lockfile-specific third-party
notice at release time.

## Operating procedure

1. Use `make dataset-fetch` or `make dataset-verify` to check the pinned data
   against its manifest; neither command changes the recorded licence policy.
2. Record a changed dataset/model selection, licence signal, or redistribution
   rule in this register and in the relevant ADR or experiment configuration.
3. Stop a public release if an upstream term is ambiguous, incompatible, or
   cannot be verified. Do not solve that uncertainty by removing attribution.
