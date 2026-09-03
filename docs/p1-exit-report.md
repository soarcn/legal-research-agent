# P1 exit report

- Decision: **Pass — proceed to P2**
- Report date: 2026-09-03
- Reference host: macOS Apple Silicon (M5 Max, 48 GB unified memory)
- Evaluated commit: `d51811351d8f2bf44e03ce670c4c7d16690b759b`

P1 establishes a repeatable local runtime and verifies its capabilities. It
does not establish corpus ingestion, retrieval quality, legal correctness, or
Agent behaviour.

## Bootstrap and deterministic checks

An isolated virtual environment at
`/private/tmp/legal-agent-p1-exit-venv-20260903` was created with:

```bash
UV_PROJECT_ENVIRONMENT=/private/tmp/legal-agent-p1-exit-venv-20260903 \
  uv sync --locked --group dev
UV_PROJECT_ENVIRONMENT=/private/tmp/legal-agent-p1-exit-venv-20260903 make check
UV_PROJECT_ENVIRONMENT=/private/tmp/legal-agent-p1-exit-venv-20260903 make audit
```

The locked environment installed successfully. `make check` passed with 86
tests passing and 3 explicitly skipped real-service tests; `make audit` found
no known vulnerabilities. The FastAPI test client emitted its known upstream
deprecation warning for `starlette.testclient`; it did not affect the outcome.

This is an equivalent-clean Python bootstrap, rather than a destructive reset
of the developer's Docker volumes or model caches. The documented reset path
remains available for a future full-machine rehearsal.

## Service and readiness evidence

With the documented local Compose services running:

```bash
make up
UV_PROJECT_ENVIRONMENT=/private/tmp/legal-agent-p1-exit-venv-20260903 make migrate
RUN_REAL_INTEGRATION=1 UV_PROJECT_ENVIRONMENT=/private/tmp/legal-agent-p1-exit-venv-20260903 \
  uv run pytest tests/integration -m real_service -q
```

PostgreSQL and Weaviate were healthy, the empty Alembic baseline applied, and
the three real-service integration tests passed. A temporary API configured
with Ollama `gpt-oss:20b`, BGE-M3, and the BGE reranker returned:

| Endpoint | Result | Observation |
| --- | --- | --- |
| `/health` | `200` | 1.48 ms; process-only liveness |
| `/ready` | `200` | 7.25 s; PostgreSQL, Weaviate, generation, embedding, and reranker all `ready` |

The readiness result proves only that these configured host capabilities were
reachable at that moment. It does not prove that a corpus has been indexed or
that a legal response is correct.

## Provider and model capability evidence

All checks use non-legal fixtures and write ignored, redacted reports under
`artifacts/capability-reports/`.

| Capability | Configuration | Result |
| --- | --- | --- |
| Ollama generation | `gpt-oss:20b` | Text and schema output passed; 21,619.90 ms / 974.45 ms |
| OpenAI-compatible generation | LM Studio `qwen/qwen3.5-9b` | Text and schema output passed; 6,383.13 ms / 255.61 ms |
| Embedding | BGE-M3, pinned revision, MPS | 1,024 dimensions; first/repeat 7,570.24 ms / 17.18 ms |
| Reranking | BGE reranker v2 M3, pinned revision, MPS | Two finite scores; 7,082.72 ms |

The two generation configurations were checked independently. Only the active
provider is required by application readiness.

## Resource observations

All values are reference-host observations, not service-level objectives.

| Item | Observation |
| --- | ---: |
| Repository including development virtual environment | 1.1 GB |
| Raw pinned benchmark data | 7.3 MB |
| BGE-M3 cache | 2.1 GB |
| BGE reranker cache | 2.1 GB |
| Ollama model store (all locally installed models) | 64 GB |
| Project-relevant working set: repository + BGE caches + selected 13 GB generator | approximately 18.3 GB |
| Embedding peak RSS after probe | approximately 928 MB |
| Reranker peak RSS after probe | approximately 961 MB |

The project-relevant working set is within the 100 GB project disk budget. The
64 GB Ollama store includes unrelated locally installed models; it is tracked
separately and should be managed before downloading additional large models.

## Residual risks and follow-up

- The local host has not been wiped; a full machine/bootstrap rehearsal remains
  optional operational evidence, not a prerequisite for P2.
- Capability smoke tests prove shape and availability only. P4/P5 must measure
  retrieval quality, while P6 must measure citation integrity and abstention.
- The P1 report has no production latency or concurrency claim.
- The frozen Legal RAG Bench corpus remains ignored, not committed or
  redistributed. P2.1 must make fetch and hash verification reproducible.
- Hugging Face emitted an unauthenticated-rate-limit warning during explicit
  smoke checks. Normal readiness keeps `local_files_only=true`; no token is
  needed for the verified cached capability path.

## Exit conclusion

P1 acceptance criteria are met with the evidence above. The next tracked work
is P2.1: a pinned Legal RAG Bench fetch-and-verify command that preserves raw
source passages and validates the committed manifest.
