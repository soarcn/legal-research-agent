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

Do not change validation or holdout semantics in place. Follow [the benchmark governance policy](../docs/data-and-evaluation.md).
