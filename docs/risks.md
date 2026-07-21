# Project risks

Risk status is reviewed at every phase exit. Probability and impact use `low`, `medium`, or `high`.

| ID | Risk | Probability | Impact | Mitigation | Owner phase | Status |
| --- | --- | --- | --- | --- | --- | --- |
| R-01 | Good retrieval metrics hide unsupported generated claims | Medium | High | Claim-level evidence model, deterministic citation checks, abstention set | P6 | Open |
| R-02 | The 100-question benchmark is overfit through repeated tuning | High | High | Frozen 60/20/20 manifests, holdout-use policy, append-only benchmark versions | P0/P8 | Mitigated |
| R-03 | Local model structured output or tool calls are unstable | Medium | High | Capability tests, bounded retries, schema validation, provider comparison | P1/P7 | Open |
| R-04 | Chunking destroys section boundaries or citation offsets | Medium | High | Golden corpus, stable IDs, round-trip offset tests | P2/P3 | Open |
| R-05 | Dataset snapshot is mistaken for current Victorian law | Medium | High | Display corpus version/as-of, fixed-snapshot language, known limitations | P6/P9 | Open |
| R-06 | Models, indexes, and artifacts exceed 100 GB | Medium | Medium | Model allowlist, disk report, artifact cleanup, no uncontrolled downloads | All | Open |
| R-07 | Harbor integration distracts from retrieval baselines | Medium | Medium | Defer Harbor system regression until P8; use fast evaluator first | P8 | Mitigated |
| R-08 | AI-generated code introduces unnecessary libraries or abstractions | High | Medium | Dependency decision rule, architecture review, task DoD | All | Open |
| R-09 | Dataset/model licences block public release | Medium | High | Stricter data-licence policy, no raw redistribution, release audit | P0/P9 | Open |
| R-10 | Provider abstraction leaks Ollama/LM Studio semantics into workflow | Medium | Medium | Protocol contracts, fake provider tests, capability matrix | P1/P6 | Open |
| R-11 | Prompt injection in retrieved passages influences tool behaviour | Medium | High | Untrusted-evidence boundary, read-only tools, Harbor adversarial suite | P7/P9 | Open |
| R-12 | Temporal metadata implies version support the corpus cannot provide | High | High | Disable historical-answer path for v1; separate versioned experiment corpus | P2/P9 | Open |
| R-13 | LLM judge variability becomes a hidden release gate | Medium | Medium | Deterministic primary metrics; record judge model/prompt; auxiliary only | P6/P8 | Mitigated |
| R-14 | Logs expose API keys or future sensitive inputs | Low | High | Secret redaction, non-sensitive v1 data, CI secret scan, log tests | P1/P9 | Open |

## Escalation rule

A high-impact risk that becomes likely or is observed blocks the current phase exit until its mitigation is implemented, the scope is reduced, or an ADR explicitly accepts the residual risk.
