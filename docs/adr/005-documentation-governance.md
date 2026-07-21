# ADR-005: Documentation is a versioned project deliverable

- Status: Accepted
- Date: 2026-07-21

## Context

The project uses extensive AI-assisted development and contains coupled decisions about data, prompts, models, evaluation, legal scope, and safety. Conversation history is not a stable project fact source.

## Decision

Repository documentation is authoritative. Every implementation, configuration, benchmark, metric, or architecture change updates the relevant document in the same task. Decision changes update or supersede an ADR. Documentation completion is part of the task Definition of Done.

## Consequences

- Pull requests include documentation impact.
- README stays concise and links to detailed sources of truth.
- AI-generated code cannot silently redefine scope or evaluation.
- Documentation maintenance is planned work, not post-project cleanup.
