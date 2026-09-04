# Australian Legal Research Agent

A local-first, evidence-grounded legal research system for learning how to build reliable RAG and constrained AI-agent workflows. It is **research assistance only**, not legal advice.

The current supported development target is macOS Apple Silicon. The reference environment is an M5 Max with 48 GB unified memory and a 100 GB project disk budget.

## Scope

The first release indexes the Victoria Criminal Charge Book content supplied by Legal RAG Bench. It answers only from the local corpus, attaches claim-level passage citations, and abstains where the evidence is insufficient.

Out of scope for v1: legal advice, autonomous web research, document editing, multi-agent orchestration, user memory, and all-jurisdiction coverage.

## Design principles

- PostgreSQL is the system of record; Weaviate is a rebuildable search index.
- Deterministic code owns ingestion, version filtering, retrieval, citation checks, auditing, and permissions.
- The LLM has a narrow role: query planning, evidence assessment, and evidence-bound answer drafting.
- Retrieved text is untrusted evidence, never executable instruction.
- Every answer must identify its corpus snapshot ID, jurisdiction, evidence status, and passage-level sources. A snapshot date is shown only when the source publishes one; v1 records it as unavailable.

## Architecture

```text
FastAPI → LegalResearchWorkflow → RetrievalRouter → Weaviate
                                  ↘ Run repository → PostgreSQL
                                  ↘ Ollama (local generation)

Frozen corpus → validate unchanged source passages → embeddings → Weaviate
```

The v1 benchmark preserves the source-provided passage IDs used by its gold labels. Re-chunking is evaluated only in a separate corpus/index protocol.

The workflow will route exact statute/case references to deterministic lookup; natural-language questions use BM25 + dense hybrid retrieval followed by reranking. Claim/citation verification is performed before a response is returned.

## Technology choices

| Area | Choice | Role |
| --- | --- | --- |
| Runtime | Python 3.12 + uv | Application and reproducible dependency management |
| API and contracts | FastAPI + Pydantic | Typed HTTP boundary and structured outputs |
| Agent runtime | PydanticAI | Added in P7 for constrained tool use only |
| Generation | Ollama + OpenAI-compatible adapter | Offline default; LM Studio validates provider portability |
| Embeddings / reranking | BGE-M3 / BGE reranker | Semantic recall and candidate ranking |
| Search index | Weaviate | BM25, vector, hybrid search, and metadata filters |
| System of record | PostgreSQL + SQLAlchemy + Alembic | Source provenance, research runs, configurations, and audits |
| Testing | pytest + Harbor | Component correctness and agent-level regression evaluation |

`PydanticAI` is deliberately not responsible for parsing documents, owning the workflow, querying databases directly, or validating legal citations. Those stay in ordinary, testable Python components.

## Frozen dataset snapshot

Legal RAG Bench is stored only in ignored local files. Fetch its pinned source
revision, then verify it on later runs without network access:

```bash
make dataset-fetch
make dataset-verify
```

The command validates the committed hash/count contract and the restrictive
licence policy before replacing files. It does not make the corpus current law,
create database records, or build a search index. To create authoritative
source records and the rebuildable derived index after verification, run:

```bash
make migrate
make ingest
```

See [source ingestion](docs/ingestion.md) and the
[data and evaluation strategy](docs/data-and-evaluation.md).

## Repository layout

```text
apps/api/                          FastAPI entry point (thin transport layer)
src/legal_research/
├── domain/                        Domain models, value objects, protocols
├── application/                   Workflow orchestration and services
├── ports/                         Abstract interfaces for infrastructure
├── adapters/
│   ├── postgres/                  SQLAlchemy models and repositories
│   └── weaviate/                  Search index client (P3)
└── config.py                      Runtime settings
migrations/                        Alembic database migrations
data/                              Local raw, normalized, snapshot, and manifest data
evals/                             Fast retrieval evaluators and Harbor tasks
tests/
├── unit/                          Fast, no external dependencies
└── integration/                   HTTP seam tests; real-service tests are added with their adapters
```

## Quick start

Current prerequisites: Python 3.12, [uv](https://docs.astral.sh/uv/), and
Docker Desktop (or another running Docker-compatible daemon). Ollama and local
models are required only for the optional generation, embedding, and reranker
capability checks; the deterministic repository gate does not require them.

```bash
cp .env.example .env
uv sync --locked --group dev
make up
make migrate
make api
```

Check the running API at `http://127.0.0.1:8000/health` and its configured
capabilities at `http://127.0.0.1:8000/ready`. `/health` answers only whether
the API process is alive; `/ready` returns `503` when a configured capability
is unavailable. See [service liveness and readiness](docs/readiness.md) for
the response contract, safe diagnostics, and troubleshooting.

The default readiness composition checks PostgreSQL, Weaviate, and the one
configured local generation provider through host-Python adapters. Generation
readiness verifies only that its configured model is visible; it does not
generate text. The P1 embedding and reranker probes are opt-in with
`EMBEDDING_ENABLED=true` and `RERANKER_ENABLED=true`, or together through
`make api-with-model-capabilities`. They use fixed non-legal inputs and may
load their models on the first `/ready` request. A `200` proves only the
configured runtime capabilities were reachable at that instant; it does not
prove a Weaviate collection exists, a corpus is loaded, law is current, or a
legal answer is reliable. Source ingestion is an explicit local P3 operation;
it is never triggered by readiness checks.
See [local service lifecycle](docs/service-lifecycle.md) for non-destructive
start/stop, opt-in real-service tests, recovery, and explicit reset commands.

Generation is configured as exactly one active provider: Ollama is the offline
default, while a generic OpenAI-compatible endpoint is designed to be
validated against LM Studio. See
[generation-provider configuration](docs/generation-providers.md) for safe
environment variables and local examples.

Install local models separately before running an explicit generation smoke test:

```bash
ollama pull qwen3:8b  # example development model; not yet selected as the final default
ollama pull bge-m3
```

Run one non-legal text and JSON-schema test against a model you have already
installed or loaded. The report is local and redacted:

```bash
GENERATION_MODEL=gpt-oss:20b make generation-smoke-ollama
GENERATION_MODEL=your-lm-studio-model make generation-smoke-lm-studio
```

The P1 dense BGE-M3 host adapter is separate from Ollama. Install its optional
runtime and run the capability check only when working on embeddings:

```bash
uv sync --locked --group embedding
make embedding-smoke
```

The check downloads the pinned model on first use and writes a redacted local
report; it does not ingest the corpus or run during CI. See
[BGE-M3 embedding capability](docs/embedding-capability.md).

Run the deterministic quality gate, then audit the installed Python dependencies:

```bash
make check
make audit
# P7 only: uv sync --group agent
```

`make check` is the single local command for formatting, lint, type checking, and tests. GitHub
Actions runs the same command on pull requests and pushes to `main`, without models, downloaded
corpora, or local services. See [docs/quality-gates.md](docs/quality-gates.md) for the purpose of each
check and how to respond to failures.

## Delivery plan

1. Retrieval baselines: ingest Legal RAG Bench and compare BM25, dense, hybrid, and reranking.
2. Reliable answers: structured claims, temporal metadata, evidence gates, and deterministic citation validation.
3. Constrained agent: query decomposition/rewrite with strict search and tool budgets.
4. Evaluation: fast offline metrics first; Harbor for end-to-end, adversarial, and policy regressions.

The concrete corpus, frozen 60/20/20 project split, and evaluation protocol are defined in
[docs/data-and-evaluation.md](docs/data-and-evaluation.md). The source publishes only a test split;
this repository's development, validation, and holdout partitions are internal project conventions.

All P0 decisions and the executable backlog are indexed in [docs/README.md](docs/README.md).
The project domain language is defined in [CONTEXT.md](CONTEXT.md).

## Safety and data handling

Use benchmark and source data only under their applicable licences. Preserve source URLs, hashes, retrieval timestamps, parser versions, snapshot IDs, and published snapshot dates—or an explicit unavailable status. Do not expose SQL, shell, arbitrary network, raw vector queries, or write tools to the model.
