# Evaluation layout

```text
evals/
├── splits/              Frozen Legal RAG Bench v1 ID manifests
├── golden_documents/    Synthetic ingestion/version fixtures (P2)
├── retrieval/           Fast evaluator cases and configurations (P4–P5)
├── answerability/       Supported/refusal/conflict cases (P6)
├── agent_behavior/      Query/tool budget cases (P7)
├── adversarial/         Prompt injection and tool misuse (P8–P9)
└── harbor/              Generated Harbor tasks and verifier (P8)
```

The current committed split manifests contain IDs only. Raw Legal RAG Bench data is downloaded into ignored `data/raw/` and verified against `data/manifests/legal-rag-bench-v1.json`.

The primary v1 retrieval unit is the unchanged source passage. Re-chunked or future-source experiments live under a separately versioned corpus/index and cannot silently reuse source-passage gold scoring.

The P2 [`golden_documents/`](golden_documents/) fixture is fictional input for
provenance and identity tests only. It is deliberately separate from the
frozen benchmark and must not be used to report retrieval quality.

Do not change validation or holdout semantics in place. Once the v1 holdout is used formally it is consumed; reshuffling the same questions does not create a new holdout. Follow [the benchmark governance policy](../docs/data-and-evaluation.md).
