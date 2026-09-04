# Data and evaluation strategy

## Purpose

This document defines the frozen v1 corpus, benchmark splits, evaluation layers, and benchmark-change policy. It is the source of truth for P0 evaluation decisions.

## Dataset boundary

The v1 corpus is [Legal RAG Bench](https://huggingface.co/datasets/isaacus/legal-rag-bench), built from the Judicial College of Victoria Criminal Charge Book.

| Item | Value |
| --- | --- |
| Dataset | `isaacus/legal-rag-bench` |
| Pinned revision | `db0b31dc6d195ce9916897e1ac5e4e6209736c8a` |
| Corpus | 4,876 passages |
| Benchmark | 100 question/answer/gold-passage records |
| Jurisdiction | Victoria, Australia |
| Domain | Criminal law and procedure |
| Language | English (`en-AU`) |
| Local manifest | `data/manifests/legal-rag-bench-v1.json` |

Raw corpus files live under `data/raw/`, are ignored by Git, and must not be redistributed with this repository. The manifest records source revision, hashes, counts, retrieval time, and licence policy.

Fetch or verify the frozen snapshot with:

```bash
make dataset-fetch
make dataset-verify
```

`dataset-fetch` uses immutable Hugging Face URLs containing the committed
revision. It validates the source-card licence metadata, file hashes, JSONL
shape, source-native IDs, and QA gold references before atomically replacing
the ignored raw files. A failure leaves an existing valid local snapshot in
place. `dataset-verify` performs the same content checks without network
access. Neither command indexes, chunks, embeds, or redistributes the corpus.

P3.1's `LegalRagBenchSourceLoader` is the next, still side-effect-free step:
it first performs the same local verification, then maps the raw JSONL into
immutable `SourceSnapshot`, unchanged `SourcePassage`, and
`BenchmarkQuestion` values. It performs no network request, database write,
chunking, embedding, Weaviate call, or model call. A passage's `content_sha256`
is a SHA-256 of its canonical source record (all source-visible fields, not
JSONL whitespace), while the manifest's corpus hash remains the integrity hash
for the complete upstream file.

Each corpus row is a source-provided passage with `id`, `title`, `text`, and an
optional `footnotes` field. For `legal-rag-benchmark-v1`, that unchanged Source
Passage is the retrieval and scoring unit because QA gold labels point directly
to its source ID. The primary benchmark does not re-chunk these passages.
Chunking experiments use a separate versioned index and evaluation protocol and
must not report source-passage Recall@k unless an explicit, reviewed mapping
preserves the gold semantics.

The dataset metadata declares `CC BY-NC-SA 4.0`, while its prose licence section says `CC BY-NC 4.0`. This project applies the more restrictive `CC BY-NC-SA 4.0` policy until clarified. It is a non-commercial learning project.

The source, model, and synthetic-fixture handling rules are recorded in the
[licence register](licence-register.md). The register is an attribution and
release-control record; it does not override upstream terms or provide legal
advice.

## Frozen benchmark split

The source publishes only a `test` split. For this private learning project, the 100 records are deterministically partitioned once and treated as `legal-rag-benchmark-v1`:

| Split | Count | Permitted use |
| --- | ---: | --- |
| Development | 60 | Daily debugging, parameter tuning, failure analysis |
| Validation | 20 | Phase acceptance and selection between frozen candidates |
| Holdout | 20 | Final P8 evaluation only; no subsequent tuning against its results |

The manifests are in `evals/splits/`. They contain question IDs only, not question text or answers. Generation uses Python `random.Random(20260721).shuffle(...)`; the seed is the P0 decision date. Recreate them with:

```bash
.venv/bin/python scripts/generate_legal_rag_bench_splits.py \
  --qa data/raw/legal-rag-bench-qa.jsonl \
  --output evals/splits \
  --seed 20260721
```

This split is an internal project protocol, not an official split published by Legal RAG Bench. Any public report must state that distinction.

## Evaluation layers

### Deterministic tests

`pytest` covers parser behaviour, stable IDs, section boundaries, hashes, metadata filters, quote offsets, citation existence, schema validation, index rebuilds, and provider abstraction. Synthetic fixtures are preferred for unit tests.

### Retrieval evaluator

The fast evaluator runs without answer generation or an Agent. It reports:

- Recall@1, Recall@5, and Recall@10;
- MRR and nDCG;
- exact-passage hit and rank;
- p50 and p95 latency;
- per-case results and categorized failures.

P4 establishes BM25 and dense baselines. P5 compares hybrid fusion, exact-reference lookup, and reranking while changing one variable at a time.

### Answer reliability

P6 adds:

- claim-level citation precision;
- unsupported-claim rate;
- answerability and abstention accuracy;
- supported-case answer rate and false-refusal rate;
- structured-output success rate;
- deterministic citation integrity checks.

Claim-level citation recall is **not calculated on Legal RAG Bench**, because the source supplies one most-relevant passage rather than exhaustive evidence labels for every answer claim. It is calculated only on a versioned, human-reviewed suite whose gold record enumerates all required `(claim_id, passage_id)` links. For that suite, recall is `matched required links / all required links`, micro-aggregated across cases; passage IDs must match exactly. It remains diagnostic until a separate ADR introduces a gate.

LLM-as-a-judge is auxiliary only. Judge results never replace deterministic pass/fail criteria and must record model and prompt versions.

### Agent and Harbor evaluation

P7 measures tool-call success, repeated searches, invalid arguments, retrieval rounds, and budget violations. P8 uses Harbor for isolated end-to-end regression and adversarial behaviour. Harbor does not replace the fast retrieval evaluator or `pytest`.

## Acceptance thresholds

These are project learning gates, not production legal-system guarantees:

| Metric | Gate |
| --- | ---: |
| Recall@5 | `>= 0.80` |
| MRR | `>= 0.60` |
| Exact-reference lookup | `>= 0.95` |
| Citation precision | `>= 0.95` |
| Unsupported-claim rate | `<= 0.05` |
| Unanswerable abstention accuracy | `>= 0.80` |
| Supported-case answer rate | `>= 0.80` |
| Structured-output success | `>= 0.98` |
| Agent budget violations | `0` |

Threshold changes require a documented rationale and an ADR update; historical results must not be rewritten.

## Additional test suites

Versioned project-created suites are added as capabilities appear:

- golden ingestion corpus: nested sections, duplicate text, and two versions;
- exact-reference, multi-part, and metadata-filter cases;
- answerability: supported, partial, unsupported, conflicting, and multi-passage;
- Agent behaviour: rewrite, decomposition, retry, and no-retry cases;
- red-team: prompt injection, tool misuse, conflicting evidence, historical requests, and out-of-scope questions.

The planned minimum sets are:

| Suite | Composition |
| --- | --- |
| P2 golden corpus | 10 synthetic documents, 30–50 sections, nested headings, duplicates, and two versions |
| P5 retrieval extensions | 20 exact-reference, 10 multi-part, 10 metadata-filter cases |
| P6 answerability | 20 supported, 15 unsupported, 10 partial, 10 multi-passage, 5 common-knowledge-temptation cases |
| P7 Agent behaviour | 10 single-search, 10 rewrite, 10 two-part, 5 retry-needed, 5 no-retry, 5 invalid-argument-risk cases |
| P9 red team | 10 prompt injection, 5 tool misuse, 5 conflict, 5 historical, 5 out-of-scope cases |

Project-created cases must record author, reviewer, expected evidence state, expected passages where applicable, and corpus version. Before P8 holdout, the full red-team suite must be authored and pass; P9.1 is therefore a cross-epic prerequisite rather than post-holdout tuning.

## Benchmark governance

The official 60/20/20 IDs are frozen for `legal-rag-benchmark-v1`; none of its three splits expands in place. Project-authored suites carry independent versions and may add cases by publishing a new suite version. Any change to validation or holdout IDs, gold passages, answerability labels, or scoring semantics creates a new benchmark version. Corrections remain append-only: preserve the old manifest and results, publish a new version, and explain the difference.

Routine regression commands exclude holdout. A holdout run requires an explicit `--allow-holdout` acknowledgement and writes operator, UTC time, Git revision, corpus hash, configuration hash, and reason to the experiment record. After the first formal holdout run, the v1 holdout is marked consumed and remains available only as an historical result. Behavioural changes may continue against development, validation, project-authored regression, and red-team suites, but the same 100 questions cannot produce a fresh holdout through reshuffling or renaming. A later formal unseen evaluation requires independently sourced or authored cases that were not exposed during prior development or reporting.

The primary benchmark always uses the frozen corpus. Fresh Criminal Charge Book snapshots and document-version experiments use a separate corpus and separate results; they never overwrite v1 benchmark reports.
