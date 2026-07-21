# ADR-002: Ollama default with generic OpenAI-compatible adapter

- Status: Accepted
- Date: 2026-07-21

## Context

The application must run offline by default while demonstrating that business workflow is not coupled to a local model runtime.

## Decision

Define typed model protocols at the application boundary. Ollama is the default offline implementation. A generic OpenAI-compatible adapter is implemented and validated with local LM Studio. Provider, base URL, model, optional local key, timeout, and capability flags are configuration, not business logic. v1 does not validate or require a cloud service; adding one is a separate explicit decision.

Tests use fake providers. Core ingestion, retrieval, and deterministic evaluation cannot require network access or a provider key.

## Consequences

- Two runtime paths must pass the same contract/capability tests.
- Provider-specific features may require explicit capability negotiation.
- The abstraction is judged by actual LM Studio validation, not interface shape alone.
- Multiple cloud SDK integrations are outside v1.
