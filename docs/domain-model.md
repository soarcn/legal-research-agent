# P2 domain model

P2 introduces immutable Python contracts before database persistence. Their job
is to preserve what the frozen source actually says, not to invent legal
metadata that Legal RAG Bench does not publish.

| Model | Meaning | Important boundary |
| --- | --- | --- |
| `SourceSnapshot` | One acquired corpus revision and its provenance | It is not current law or a legal document version. |
| `SourcePassage` | One unchanged source-provided retrieval unit | Its native ID remains the benchmark ID. |
| `BenchmarkQuestion` | One source QA row and exact gold passage ID | It does not make the gold answer exhaustive evidence. |
| `ResearchRun` | One observable workflow execution | It is not an Agent conversation or hidden reasoning trace. |
| `IngestionJob` | Later ingestion lifecycle state | It does not persist anything until P2.4. |

`SourceSnapshot.retrieved_at` records when the project obtained data. It is
separate from a published corpus snapshot date and from legal effective dates.
For v1, `legal_effective_at` is intentionally unavailable because the source
does not support historical-law answers.

Evidence uses one of four verifiable states: `supported`,
`partially_supported`, `unsupported`, or `conflicting`. The model does not
contain a numeric legal-confidence field.
