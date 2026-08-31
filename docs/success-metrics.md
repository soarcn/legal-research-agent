# Success metrics

## Priority order

1. Retrieval quality.
2. Answer reliability.
3. Engineering completeness.
4. Agent capability.

Non-functional priorities are reproducibility, auditability, maintainability, latency, then throughput.

## Metric definitions

| Metric | Definition | Initial gate |
| --- | --- | ---: |
| Recall@5 | Fraction of questions whose gold passage appears in top five | `>= 0.80` |
| MRR | Mean reciprocal rank of the first gold passage | `>= 0.60` |
| Exact-reference accuracy | Correct deterministic resolution of supported exact references | `>= 0.95` |
| Citation precision | Fraction of returned citations that validly support their linked claim | `>= 0.95` |
| Unsupported-claim rate | Fraction of substantive claims without sufficient cited evidence | `<= 0.05` |
| Abstention accuracy | Correct refusal on questions unsupported by the configured corpus | `>= 0.80` |
| Supported-case answer rate | Fraction of labelled supported cases that receive a substantive supported answer rather than a refusal | `>= 0.80` |
| Structured-output success | Valid output within two attempts (initial response plus one repair retry) | `>= 0.98` |
| Index rebuild | Rebuild from source produces expected stable IDs/counts | `100%` |
| Provider portability | Same workflow works with Ollama and configured OpenAI-compatible endpoint | required |
| Agent budget violations | Runs exceeding retrieval/tool limits | `0` |

These thresholds are learning-project acceptance gates, not claims of legal correctness or production readiness.

## Performance baselines

Performance is recorded but has no hard P0 SLA. Every formal experiment captures ingestion duration, embedding duration, retrieval and reranking p50/p95, generation p50/p95, model-load time, peak memory, and disk footprint.

The accepted comparison protocol is:

- reference environment: documented M5 Max / 48 GB, concurrency 1, same corpus/index/model revisions;
- three untimed warm-up queries, then five full development-split runs;
- compare the median of the five run-level p95 values and the median peak memory/disk values;
- record service/model load state, power mode, relevant background load, and UTC start time;
- baseline is the most recent accepted formal experiment for the same phase and capability.

A relative regression greater than 20% is “material” and requires analysis; it becomes a hard failure only if unexplained, if it breaches the 100 GB boundary, or if the owning phase explicitly sets a tighter gate.

## Decision rules

- Change one major experimental variable at a time.
- Select retrieval configurations on development data; use validation only for phase acceptance or candidate selection.
- Run holdout only during final P8 evaluation and do not tune against it afterward.
- Preserve per-case outputs, aggregate metrics, configuration, corpus hash, model revision, and code revision.
- A more complex Agent is retained only if it meets all safety gates and does not regress the deterministic P6 pipeline baseline.
- Report the evidence-state confusion matrix. Abstention accuracy and supported-case answer rate are separate hard gates so an always-refuse policy cannot pass.

For P7 non-inferiority, both candidates must pass every hard gate applicable to their case type. `Not applicable` is permitted only when the case has no labelled denominator and must be recorded per case.

Compare candidates on the same validation IDs and case-level scorer outputs using 10,000 paired bootstrap resamples, seed `20260721`, and the percentile interval at 2.5%/97.5%. The Agent's lower bound must be no worse than `-0.02` for Recall@5, citation precision, and abstention accuracy; unsupported-claim rate uses an upper bound no worse than `+0.02`. P7 may revise the margin or statistical protocol only through an ADR before comparison begins.
