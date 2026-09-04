# Project documentation

P0 is complete when these documents are current and reviewed:

- [Project scope](project-scope.md)
- [Success metrics](success-metrics.md)
- [Data and evaluation strategy](data-and-evaluation.md)
- [System context](architecture/system-context.md)
- [Definition of Done](definition-of-done.md)
- [Task evidence template](task-template.md)
- [Risks](risks.md)
- [Engineering governance](engineering-governance.md)
- [Quality gates and CI](quality-gates.md)
- [Service liveness and readiness](readiness.md)
- [PostgreSQL runtime capability](postgresql.md)
- [Weaviate runtime capability](weaviate.md)
- [Weaviate v1 derived-index schema](weaviate-schema.md)
- [BGE-M3 embedding capability](embedding-capability.md)
- [P3 source-passage embedding adapter](embedding-capability.md#p3-source-passage-adapter)
- [BGE reranker capability](reranker-capability.md)
- [P1 exit report](p1-exit-report.md)
- [P2 domain model](domain-model.md)
- [Stable identity rules](stable-identities.md)
- [Licence register](licence-register.md)
- [P2 exit report](p2-exit-report.md)
- [P3 source-loader boundary](data-and-evaluation.md#dataset-boundary)
- [Future-source section-aware chunking](future-source-chunking.md)
- [BGE-M3 reference capability report](capability-reports/embedding-bge-m3-reference.md)
- [Generation-provider configuration](generation-providers.md)
- [Local generation capability reference report](capability-reports/generation-local-reference.md)
- [Local service lifecycle](service-lifecycle.md)
- [Experiment versioning](experiment-versioning.md)
- [P1–P9 backlog](backlog.md)
- [P0 completion record](p0-completion.md)
- [P1 entry review](p1-entry-review.md)
- [Open-source release checklist](open-source-release-checklist.md)
- [Architecture decisions](adr/)
- [Domain language](../CONTEXT.md)
- [Agent skill configuration](agents/)

## Accepted P0 operating decisions

1. The accepted 60/20/20 split uses seed `20260721`, the decision date. A changed split is a protocol revision, not an independent fresh holdout.
2. Legal RAG Bench lacks legal effective-date/version metadata sufficient for historical legal answers. The pinned dataset revision is a reproducibility snapshot, not a representation that the law is current on the download date. Its published snapshot date is unavailable and recorded as `null` with a reason.
3. The exact 8B development model and larger comparison models are selected through later capability tests; P0 fixes selection criteria, not a winning model.
4. LM Studio is the reference OpenAI-compatible validation runtime. The adapter remains product-neutral.
5. Acceptance thresholds are project learning gates and may not be represented as production legal-system assurance.
6. P6 structured output uses two total attempts (initial plus one repair retry).
7. Performance comparison uses three warm-ups and five measured development runs on the reference machine; `>20%` relative regression triggers analysis.
8. P7 non-inferiority uses 10,000 paired percentile-bootstrap resamples with seed `20260721` and a two-percentage-point margin.
9. Legal RAG Bench source passages remain unchanged for the v1 benchmark; re-chunking uses a separate experiment and scorer.
10. The v1 holdout is consumed after its first authorized P8 run and cannot be refreshed by reshuffling the same questions.
