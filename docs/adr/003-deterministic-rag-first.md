# ADR-003: Deterministic RAG before constrained Agent

- Status: Accepted
- Date: 2026-07-21

## Context

The first learning goal is RAG engineering. Introducing query planning, tool calls, and multi-step model behaviour before measuring retrieval would make failures harder to attribute and conflict with legal reliability needs.

## Decision

P1–P6 use an explicit `LegalResearchWorkflow`. P4/P5 retrieval is evaluated without answer generation or Agent orchestration. PydanticAI and model-driven planning are deferred to P7.

When added, the Agent may rewrite/decompose questions, choose from approved retrieval tools, decide on one bounded retry, and draft from selected evidence. Deterministic code retains scope validation, filters, version checks, citation integrity, permissions, persistence, and output policy.

## Consequences

- The project produces useful retrieval results before a chat experience.
- Agent value can be compared with a deterministic pipeline baseline.
- Some orchestration code is explicit rather than hidden in a framework.
- Multi-agent systems, durable graphs, and long-term memory are deferred.
