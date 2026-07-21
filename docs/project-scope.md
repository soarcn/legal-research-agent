# Project scope

## Mission

Build a local-first Australian legal research assistant as a complete AI application engineering project. The first learning milestone emphasizes measurable RAG engineering; constrained Agent behaviour is added only after retrieval and evidence handling are reliable.

## Current project audience

The current audience is the developer and technical reviewers evaluating architecture, reproducibility, and AI engineering practice. It is not a service for real legal users.

The longer-term product direction is enterprise legal and compliance work, including contract analysis and policy/regulatory research. Those workflows do not enter v1 merely because they are the long-term destination.

## v1 use case

The system answers English legal research questions from a frozen Victorian criminal-law corpus. It supports:

- natural-language research questions grounded in the corpus;
- exact section or reference lookup where metadata permits;
- concise one-to-three-paragraph English answers;
- user-readable citations plus stable internal passage references;
- explicit partial support, lack of support, or conflicting evidence;
- CLI for development/evaluation and a versioned REST API for demonstration.

## Evidence policy

The system may use only retrieved passages from the configured corpus. Model prior knowledge is not evidence. Retrieved text is untrusted content, not instruction.

Evidence states are `supported`, `partially_supported`, `unsupported`, and `conflicting`. Numeric model confidence is not exposed as a correctness claim. Every substantive claim must map to one or more citations whose passage, document version, quote, and offsets can be verified.

The pinned dataset revision identifies the evidence snapshot; it is not a legal effective date. Legal RAG Bench does not provide sufficient temporal/version metadata for historical answers. A v1 question specifying `effective_at` is therefore `unsupported`. Responses return `corpus_id`/`source_snapshot_id`, never a claim that the corpus represents current law on its retrieval date.

## Operating boundary

- Primary platform: macOS Apple Silicon.
- Reference machine: Apple M5 Max, 48 GB unified memory.
- Disk budget: 100 GB for models, data, indexes, and artifacts.
- PostgreSQL and Weaviate run in Docker.
- Python application, evaluation, Ollama, and LM Studio run on the host.
- Ollama is the offline default provider.
- A generic OpenAI-compatible adapter is validated with LM Studio.
- Core ingestion, retrieval, and deterministic tests work without a cloud API key.

Daily development starts with an 8B-class local model. After the reliable workflow is stable, the project compares 8B, 14B, and one larger model under the same corpus, retrieval configuration, and prompt. Selection prioritizes answer reliability, structured-output stability, tool-call correctness, latency, then memory; largest is not automatically best.

## Non-goals for v1

- legal advice, case strategy, outcome prediction, or action recommendations;
- production use by the public, lawyers, or enterprises;
- multiple jurisdictions or legal domains;
- live web research or automatic legal updates;
- private contracts, client matters, personal information, or privileged material;
- cross-lingual querying or non-English answers;
- a web/mobile front end;
- multi-agent coordination or long-term user memory;
- automatic legal/compliance actions;
- model fine-tuning, cloud deployment, production SLA, or high throughput;
- a complete legal memorandum.

## Privacy and disclosure

v1 uses only public, non-sensitive benchmark material. Test questions, retrieved passages, outputs, and observable traces may be retained for audit. Secrets must never enter logs. The README, startup experience, and API documentation state that the project provides research assistance, not legal advice; individual answers do not repeat a full disclaimer but return corpus version and snapshot information.

## Final deliverables

- runnable CLI and REST API;
- reproducible PostgreSQL, Weaviate, Ollama, and LM Studio configuration;
- rebuildable corpus and index;
- BM25, dense, hybrid, and reranker comparison reports;
- reliable claim-level cited answers and abstention behaviour;
- constrained Agent with observable tool traces;
- Harbor end-to-end regression suite;
- architecture, ADRs, risks, dataset/licence, local setup, known-limitations, and demo documentation.

## Repository and release intent

Development remains private until the open-source checklist passes. The intended code licence is Apache License 2.0; datasets, model weights, and third-party dependencies remain under their own terms. Raw benchmark data is not distributed in the repository.
