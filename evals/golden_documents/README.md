# Synthetic golden documents

`v1.json` is a small, entirely fictional corpus used to test P2 identity,
provenance, version, and section-hierarchy contracts. It is not Legal RAG
Bench, a legal source, or an evaluation set for retrieval quality.

The fixture deliberately contains ten documents, nested section paths, one
document with two source versions, and repeated section text in different
documents. It lets deterministic tests prove that:

- a source snapshot is distinct from a legal document version;
- version-specific content produces a new version identity;
- nested sections retain their parent hierarchy; and
- identical text never collapses separate source locations.

Do not replace this fixture with copyrighted legal text. Changes that alter
its semantics require a new fixture version and corresponding test updates.
