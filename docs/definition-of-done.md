# Definition of Done

## Task-level Done

A task is complete only when all applicable items are satisfied:

- implementation matches the approved scope and dependency boundaries;
- public APIs are typed and important assumptions are explicit;
- deterministic unit and integration tests exist and pass;
- relevant evaluation has run and results are preserved;
- failures are classified rather than silently ignored;
- configuration, model, prompt, dataset, and index versions are recorded;
- security, error handling, and resource cleanup have been reviewed;
- README, ADR, design, risk, or operating documentation is updated;
- no secret, private data, downloaded corpus, or large generated artifact is committed;
- Ruff, type checking, pytest, and applicable integration checks pass.

AI-generated code is a draft until these conditions are met. Generation alone never satisfies Done.

## Project-level Done

The project is complete when:

- the pinned Legal RAG Bench corpus imports reproducibly;
- PostgreSQL records authoritative provenance and audit state;
- Weaviate can be deleted and rebuilt with stable expected objects and IDs;
- BM25, dense, hybrid, exact lookup, and reranking have measured comparisons and failure analysis;
- the system returns concise structured English answers with claim-level verified citations;
- unsupported, partial, and conflicting evidence paths behave correctly;
- supported questions meet the answer-rate gate and are not hidden by an always-refuse policy;
- Ollama and an LM Studio-validated OpenAI-compatible endpoint run the same workflow;
- constrained Agent tools, limits, and observable traces are implemented;
- Harbor runs the complete end-to-end regression suite with one documented command;
- all agreed acceptance gates are met on the correct benchmark split;
- documentation, ADRs, risks, known limitations, data licences, release checklist, and demo are complete;
- the project remains within the 100 GB disk budget.

## Task evidence and approval

Every task uses `docs/task-template.md` or an equivalent issue/PR body. The implementer records commands, result locations, configuration IDs, documentation changes, residual risks, and applicable/not-applicable reasons. The project owner approves phase exits; self-review is acceptable during solo development but must be explicitly recorded.
