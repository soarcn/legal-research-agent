# Future-source section-aware chunking

This component is intentionally separate from Legal RAG Bench v1. The v1
benchmark's source passages and IDs are frozen retrieval units; sending them
through a chunker would silently invalidate its gold-passage scoring semantics.

`SectionAwareChunker` accepts structured `FutureSourceSection` inputs and
returns `DerivedPassage` values. Each output preserves:

- the source snapshot ID;
- the complete section path and a deterministic parent section ID;
- exact zero-based `start_char` / exclusive `end_char` offsets into that
  section's original text; and
- a deterministic derived passage ID based on its parent section, offsets, and
  chunk content hash.

The first policy is deliberately simple: non-overlapping chunks no larger than
`max_chars`, preferring a space boundary where one fits. An unbroken token is
split at the hard limit so the algorithm always makes progress. Concatenating a
section's chunks recreates the original section text exactly.

The component has no database, vector index, embedding, LLM, network, or
parser dependency. A future tokenizer-aware policy must be separately
versioned and tested against the same no-cross-section and offset round-trip
contracts.
