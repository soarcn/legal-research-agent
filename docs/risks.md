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
| R-14 | Logs expose API keys or future sensitive inputs | Low | High | Full-history Gitleaks CI scan is active; secret redaction and log tests remain P9 work | P1/P9 | Open |
| R-15 | BGE-M3/reranker OOM or accuracy regression on Apple Silicon MPS/CPU | Medium | Medium | Pin model revisions, compare MPS vs CPU metrics, record device in experiment, set memory ceiling | P1/P3 | Open |
| R-16 | Weaviate client or server upgrade introduces breaking API changes | Medium | Medium | Pin Weaviate image version, pin client version, test rebuild on upgrade, document version policy | P1/P3 | Open |
| R-17 | Single-developer project has no peer review safety net | High | Medium | Thorough DoD enforcement, deterministic tests for all critical paths, architecture review at phase exits, explicit self-review records | All | Open |
| R-18 | Re-chunking breaks the source passage IDs used by benchmark gold labels | High | High | Index source passages unchanged for v1; isolate chunking experiments and scorers under ADR-006 | P2–P5 | Mitigated |
| R-19 | An always-refuse policy appears safe under one-sided abstention metrics | Medium | High | Gate supported-case answer rate separately and report evidence-state confusion matrix | P6–P8 | Mitigated |
| R-20 | Reshuffled known questions are misrepresented as a fresh holdout | Medium | High | Mark v1 holdout consumed; require genuinely unseen cases for later formal evaluation | P8 | Mitigated |
| R-21 | A Python dependency contains a published vulnerability | Medium | High | Locked dependencies, `pip-audit` in local/CI gates, explicit upgrade and re-lock on findings | P1/All | Mitigated |

## Escalation rule

A high-impact risk that becomes likely or is observed blocks the current phase exit until its mitigation is implemented, the scope is reduced, or an ADR explicitly accepts the residual risk.
