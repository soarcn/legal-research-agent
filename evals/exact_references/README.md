# Exact-reference suite v1

Twenty supported section references and ten boundary cases, pinned to the
existing source snapshot. Expected passage IDs are literal source-ID lists,
independently extracted from the frozen corpus by section prefix; the resolver
did not generate them. No legal text, benchmark question, or answer is copied
into this suite. Author/reviewer attribution is suite-wide and inherited by
every case; review is by Codex against source IDs, not an independent legal
expert. This suite tests mechanical lookup only.

Supported references must return every passage of exactly that section, with
no child-section or prefix-collision leakage. Bare references, `section` prefixes,
capitalization, outer whitespace, and four-level sections are covered.
Three missing sections and seven unsupported/malformed references separately
test boundary behavior. Unsupported references must not produce evidence.

Scoring requires exact status and full ID-set equality. Supported accuracy
has a denominator of 20; boundary accuracy has a denominator of 10. Boundary
passes cannot inflate the supported-reference gate of 0.95. CI uses synthetic
passage text with fixed IDs and decoys. The real-data run verifies the pinned
source hashes and evaluates against all 4,876 source passages:

```bash
PYTHONPATH=src uv run python scripts/evaluate_exact_references.py \
  --output artifacts/exact-reference-v1-run1
```

Choose a new output directory for every run. Results record suite/corpus hashes,
Git revision, UTC time, and actual per-case status/IDs. Source and suite snapshots
are unchanged during scoring. The command exits nonzero on any failing case;
the project acceptance threshold is separately documented as 0.95.

Changes to expected IDs, cases, or semantics require a new suite version. A
passing result does not establish statute/case lookup, legal correctness, or
natural-language retrieval quality, and does not consume the P8 holdout.
