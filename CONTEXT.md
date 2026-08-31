# Legal Research Context

This context defines the language used for the frozen legal-retrieval benchmark and the research workflow built around it. Terms intentionally distinguish source facts from structures derived by the application.

## Corpus and provenance

**Corpus**:
The complete set of source passages available to retrieval for one configured run.
_Avoid_: Knowledge base, current law

**Source Snapshot**:
An immutable, identified acquisition of a corpus, including its source revision, retrieval timestamp, hashes, licence policy, and any published snapshot date.
_Avoid_: Document version, legal effective date

**Source Passage**:
One passage supplied by a source snapshot with its source-native stable identifier and text. In `legal-rag-benchmark-v1`, this is the retrieval and gold-evaluation unit.
_Avoid_: Generated chunk, legal section

**Legal Document**:
A source-recognized legal instrument, judgment, bench-book entry, or other document whose identity is supported by explicit source metadata.
_Avoid_: Source passage, inferred document

**Document Version**:
An immutable representation of a Legal Document at a source-supported version. A source retrieval date alone does not establish a Document Version's legal effective date.
_Avoid_: Source snapshot, latest law

## Evaluation

**Benchmark**:
A versioned set of questions, gold labels, scoring rules, and permitted-use splits evaluated against a specified Corpus.
_Avoid_: Corpus, test data

**Benchmark Question**:
A source-provided question with its answer and gold Source Passage identifier.
_Avoid_: User request, test prompt

**Consumed Holdout**:
A holdout split after its first authorized formal evaluation. It remains an historical result set and cannot become fresh holdout data through reshuffling or renaming.
_Avoid_: Reusable test set

## Research workflow

**Research Run**:
One observable execution of a legal research request through the deterministic workflow, regardless of whether a model-driven Agent participates.
_Avoid_: Agent run, conversation

**Agent Step**:
A bounded, observable P7-or-later model decision or read-only tool call within a Research Run.
_Avoid_: Chain-of-thought, workflow run

**Evidence State**:
The verified relationship between available passages and the requested answer: `supported`, `partially_supported`, `unsupported`, or `conflicting`.
_Avoid_: Confidence score, probability of correctness

**Internal Citation**:
A machine-verifiable link from a claim to a Source Passage, including snapshot/passage identity and validated quote offsets.
_Avoid_: Source list, model citation

**Readable Citation**:
A user-facing source label derived from available source metadata. It never replaces the Internal Citation used for verification.
_Avoid_: Internal citation ID
