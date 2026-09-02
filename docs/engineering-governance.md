# Engineering governance

## Repository and workflow

Use one repository for application code, ingestion, evaluation, Harbor adapters, configuration, and documentation. Work uses short-lived feature branches and pull requests. The current directory may be bootstrapped before a remote repository exists, but the same quality rules apply.

P0–P9 are epics. Each task records objective, dependencies, scope, non-goals, outputs, tests, evaluation, documentation updates, and acceptance criteria.

## Documentation as source of truth

Repository documentation is the project fact source. Code, configuration, evaluation, or architecture changes include their documentation update in the same task. An unfinished documentation update means the task is not Done.

Decision changes update or supersede an ADR. Metrics and benchmark changes record rationale and preserve historical results. README remains an entry point; detailed facts live in focused documents.

## AI-assisted development

- AI may generate implementation, tests, configuration, and documentation drafts.
- The developer confirms architectural and product decisions.
- Generated code must be explainable through its responsibilities and dependencies.
- Core deterministic logic requires tests.
- AI must not silently modify benchmark splits, gates, licences, or architecture boundaries.
- Retrieval improvements require evaluation evidence, not selected demos.
- Security, exception handling, and resource cleanup receive explicit review.

## Dependency policy

Prefer the standard library and existing dependencies. A new dependency must document:

- the problem it solves and expected value;
- why a small local implementation is inappropriate;
- project maintenance status and licence compatibility;
- relevant transitive dependency and resource cost;
- how it is isolated behind an interface and can be replaced.

## Configuration and secrets

Environment variables manage secrets and environment-specific credentials. Versioned YAML/TOML files manage application, model, retrieval, and experiment settings. Experimental parameters are not hard-coded in business logic.

`.env` never enters Git. Logs do not include keys. CI runs full-history secret scanning and Python dependency auditing. A baseline container scan is added when the P1 container images are finalized.

## Failure handling

- Invalid configuration, schema mismatch, or unavailable required infrastructure fails fast.
- Batch ingestion isolates a document failure, continues where safe, and emits a failure report.
- Transport retries and semantic retries are separate. A logical model attempt may retry connection errors, timeouts, HTTP 429, and HTTP 5xx at most twice with 0.5 s then 1 s backoff, within a 60 s total attempt timeout; schema/validation failures are not transport-retried.
- P6 structured output permits two logical attempts: initial generation plus one schema-guided repair. P7 retrieval retry is a separate workflow action and does not reset the logical output-attempt budget.
- Provider parity means Ollama and LM Studio accept the same typed logical request and satisfy the same output schema/error contract; transport-level retry counts may differ but are recorded.
- Evaluation preserves case ID, error type, configuration, and observable trace.
- Exceptions are never silently ignored.

## Quality gates

- Ruff format/check;
- mypy or pyright once configured;
- pytest unit and core integration tests;
- at least 80% coverage for core deterministic modules once they exist;
- relevant behaviour evaluation for model-dependent code;
- documentation and risk updates.

`make check` is the shared local and CI entry point for formatting, lint, type checking, and deterministic tests. `make audit` checks the installed Python environment for published vulnerabilities and fails on findings. CI runs both commands without Agent-only dependencies, downloaded corpora, local models, or service containers. Full Weaviate/PostgreSQL/Ollama/Harbor experiments remain local in v1.

## Artifact retention

Formal experiment configuration, summary metrics, and failure analysis are committed. Full per-case outputs, traces, model responses, and bulky artifacts live under ignored `artifacts/`. Formal results are retained; temporary development artifacts may be removed through an explicit cleanup command. Frozen raw corpus files are not automatically deleted.
