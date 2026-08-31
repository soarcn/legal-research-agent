# ADR-006: Source passages are the v1 benchmark retrieval unit

- Status: Accepted
- Date: 2026-08-31

Legal RAG Bench supplies source passages and gold `relevant_passage_id` values, but not a reconstructable document/version hierarchy. v1 therefore indexes each source passage unchanged and preserves its source-native ID for retrieval evaluation. Re-chunking and richer document modelling use separate synthetic or future corpora, indexes, and evaluation protocols; they cannot be presented as directly comparable passage-ID benchmark runs without an explicit mapping and scorer.
