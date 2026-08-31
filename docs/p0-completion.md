# P0 completion record

- Status: **Confirmed**
- Decision date: 2026-07-21
- Sign-off date: 2026-07-21

## Sign-off notes

Owner confirmed the operational defaults (split seed, structured-output attempts, performance protocol, and P7 bootstrap parameters) and the development-readiness decisions recorded in ADR-006 and ADR-007. Architecture review identified one inconsistency: `pydantic-ai` was in main dependencies but ADR-003 defers it to P7. It is isolated in the optional `agent` dependency group.

## Required outputs

| P0 output | Source of truth | Status |
| --- | --- | --- |
| Product/project scope and non-goals | `docs/project-scope.md` | Complete |
| Success metrics | `docs/success-metrics.md` | Complete |
| Dataset, splits, and evaluation strategy | `docs/data-and-evaluation.md` | Complete |
| System context and boundaries | `docs/architecture/system-context.md` | Complete |
| Definition of Done | `docs/definition-of-done.md` | Complete |
| Risk register | `docs/risks.md` | Complete |
| Initial architecture decisions | `docs/adr/001`–`007` | Complete |
| Domain language | `CONTEXT.md` | Complete |
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
- Source passages remain unchanged for v1 gold-passage evaluation; richer modelling and chunking are separate experiments.
- The P8 v1 holdout is consumed after one formal run and is not refreshed by reshuffling known questions.
- The repository remains private until licence, security, documentation, and reproduction gates pass.

## Accepted operational defaults

The owner accepted these operational values:

1. Split seed `20260721`, the P0 decision date.
2. Two structured-output attempts: initial generation plus one repair retry.
3. Performance protocol: three warm-ups, five measured development runs, and `>20%` relative regression requiring analysis.
4. P7 comparison: 10,000 paired percentile-bootstrap resamples, seed `20260721`, with a two-percentage-point non-inferiority margin.

Changing the split seed cannot make the same 100 questions an independent benchmark or fresh holdout. A benchmark revision preserves v1 and documents the changed protocol; a new formal holdout requires previously unseen cases under ADR-007.
