# P0 completion record

- Status: Documentation complete; P0 awaits owner confirmation of operational defaults
- Decision date: 2026-07-21

## Required outputs

| P0 output | Source of truth | Status |
| --- | --- | --- |
| Product/project scope and non-goals | `docs/project-scope.md` | Complete |
| Success metrics | `docs/success-metrics.md` | Complete |
| Dataset, splits, and evaluation strategy | `docs/data-and-evaluation.md` | Complete |
| System context and boundaries | `docs/architecture/system-context.md` | Complete |
| Definition of Done | `docs/definition-of-done.md` | Complete |
| Risk register | `docs/risks.md` | Complete |
| Initial architecture decisions | `docs/adr/001`–`005` | Complete |
| P1–P9 dependency backlog | `docs/backlog.md` | Complete |
| Experiment/configuration rules | `docs/experiment-versioning.md` | Complete |
| AI, dependency, CI, Git, failure, and artifact governance | `docs/engineering-governance.md` | Complete |
| Open-source release gate | `docs/open-source-release-checklist.md` | Complete |
| Dataset provenance manifest | `data/manifests/legal-rag-bench-v1.json` | Complete |
| Development/validation/holdout manifests | `evals/splits/*.json` | Complete |

## Decisions fixed by P0

- Full AI application engineering is the overall learning goal; RAG engineering is first.
- v1 is an English, local, Victorian criminal-law research demonstration.
- Evidence, citation, and abstention reliability precede Agent autonomy.
- The deterministic workflow is built and measured before PydanticAI is introduced.
- Ollama is offline default; LM Studio validates a generic OpenAI-compatible adapter.
- Reproducibility, auditability, and maintainability outrank latency and throughput.
- Documentation is versioned work and part of every task's Done criteria.
- The repository remains private until licence, security, documentation, and reproduction gates pass.

## Operational defaults introduced during documentation

The discussion fixed the policies but not all operational values. Documentation uses these proposed defaults:

1. Split seed `20260721`, the P0 decision date.
2. Two structured-output attempts: initial generation plus one repair retry.
3. Performance protocol: three warm-ups, five measured development runs, and `>20%` relative regression requiring analysis.
4. P7 comparison: 10,000 paired percentile-bootstrap resamples, seed `20260721`, with a two-percentage-point non-inferiority margin.

Owner confirmation closes P0. Changing the split seed after confirmation creates `legal-rag-benchmark-v2`; it does not overwrite v1.
